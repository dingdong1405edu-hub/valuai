"""Document upload and crawl endpoints."""

import logging
import os
import tempfile
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db, db_session
from app.db.models import Document, Extraction, Company
from app.ingestion.parser import parse_with_gemini, parse_excel, detect_mime_type
from app.ingestion.crawler import crawl_url
from app.ingestion.extractor import run_extraction
from app.ingestion.embedder import embed_and_store
from app.models.schemas import APIResponse, DocumentOut, CrawlRequest, VALID_DOC_TYPES

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)

EXCEL_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/csv",
}


@router.post("/upload", response_model=APIResponse[DocumentOut])
async def upload_document(
    file: UploadFile = File(...),
    company_id: str = Form(...),
    doc_type: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document file (PDF/Excel/image) for a company.
    Automatically parses, extracts structured data, and creates embeddings.
    """
    logger.info(f"[DOCS] upload — company={company_id}, type={doc_type}, file={file.filename}")

    if doc_type not in VALID_DOC_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid doc_type. Must be one of: {VALID_DOC_TYPES}")

    # Verify company exists
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    file_bytes = await file.read()
    mime_type = detect_mime_type(file.filename or "", file.content_type or "")

    # Save temp file for local reference
    suffix = os.path.splitext(file.filename or "doc")[1] or ".bin"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    # Create document record
    doc = Document(
        company_id=company_id,
        type=doc_type,
        file_url=tmp_path,
        mime_type=mime_type,
        file_size=len(file_bytes),
        status="parsing",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    logger.info(f"[DOCS] doc created id={doc.id}, starting parse pipeline")

    # ── Parse ──────────────────────────────────────────────────────────
    try:
        if mime_type in EXCEL_MIME_TYPES:
            parsed_text = parse_excel(file_bytes)
        else:
            parsed_text = await parse_with_gemini(file_bytes, mime_type)

        doc.parsed_text = parsed_text
        doc.status = "parsed"
        await db.commit()
        logger.info(f"[DOCS] parse OK — doc={doc.id}, {len(parsed_text)} chars")
    except Exception as exc:
        doc.status = "failed"
        doc.error_msg = str(exc)[:500]
        await db.commit()
        logger.error(f"[DOCS] parse FAILED — doc={doc.id}: {exc}")
        return APIResponse.ok(DocumentOut.model_validate(doc))

    # ── Extract ────────────────────────────────────────────────────────
    try:
        data, tokens = await run_extraction(parsed_text, doc_type)
        extraction = Extraction(
            document_id=doc.id,
            company_id=company_id,
            data=data,
            model_used="groq/llama-3.3-70b-versatile",
            tokens_used=tokens,
        )
        db.add(extraction)
        await db.commit()
        logger.info(f"[DOCS] extract OK — doc={doc.id}, tokens={tokens}")
    except Exception as exc:
        logger.error(f"[DOCS] extract FAILED — doc={doc.id}: {exc}")

    # ── Embed ──────────────────────────────────────────────────────────
    try:
        count = await embed_and_store(db, doc.id, company_id, parsed_text)
        await db.commit()
        logger.info(f"[DOCS] embed OK — doc={doc.id}, chunks={count}")
    except Exception as exc:
        logger.error(f"[DOCS] embed FAILED — doc={doc.id}: {exc}")

    doc.status = "extracted"
    await db.commit()
    await db.refresh(doc)
    return APIResponse.ok(DocumentOut.model_validate(doc))


@router.post("/crawl", response_model=APIResponse[DocumentOut])
async def crawl_document(
    payload: CrawlRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Crawl a website or fanpage URL and store the content as a document.
    """
    logger.info(f"[DOCS] crawl — company={payload.company_id}, url={payload.url}")

    company = await db.get(Company, payload.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Create document record
    doc = Document(
        company_id=payload.company_id,
        type="web_content",
        source_url=payload.url,
        status="parsing",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # ── Crawl ──────────────────────────────────────────────────────────
    try:
        content = await crawl_url(payload.url, payload.source_type)
        doc.parsed_text = content
        doc.status = "parsed"
        await db.commit()
        logger.info(f"[DOCS] crawl OK — doc={doc.id}, {len(content)} chars")
    except Exception as exc:
        doc.status = "failed"
        doc.error_msg = str(exc)[:500]
        await db.commit()
        logger.error(f"[DOCS] crawl FAILED — doc={doc.id}: {exc}")
        return APIResponse.ok(DocumentOut.model_validate(doc))

    # ── Extract ────────────────────────────────────────────────────────
    try:
        data, tokens = await run_extraction(content, "web_content")
        extraction = Extraction(
            document_id=doc.id,
            company_id=payload.company_id,
            data=data,
            model_used="groq/llama-3.3-70b-versatile",
            tokens_used=tokens,
        )
        db.add(extraction)
        await db.commit()
    except Exception as exc:
        logger.error(f"[DOCS] web extract FAILED: {exc}")

    # ── Embed ──────────────────────────────────────────────────────────
    try:
        count = await embed_and_store(db, doc.id, payload.company_id, content)
        await db.commit()
    except Exception as exc:
        logger.error(f"[DOCS] web embed FAILED: {exc}")

    doc.status = "extracted"
    await db.commit()
    await db.refresh(doc)
    return APIResponse.ok(DocumentOut.model_validate(doc))


@router.get("/{doc_id}/status", response_model=APIResponse[dict])
async def get_document_status(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return APIResponse.ok({"id": doc.id, "status": doc.status, "error": doc.error_msg})


@router.get("/company/{company_id}", response_model=APIResponse[List[DocumentOut]])
async def list_company_documents(company_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).where(Document.company_id == company_id).order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return APIResponse.ok([DocumentOut.model_validate(d) for d in docs])
