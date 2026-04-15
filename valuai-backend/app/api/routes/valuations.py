"""Valuation trigger and results endpoints."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db, db_session
from app.db.models import Valuation, Company
from app.models.schemas import APIResponse, ValuationOut, ValuationRunRequest
from app.valuation.orchestrator import run_full_valuation
from app.report.generator import generate_pdf_report

router = APIRouter(prefix="/valuations", tags=["valuations"])
logger = logging.getLogger(__name__)


@router.post("/run", response_model=APIResponse[ValuationOut])
async def trigger_valuation(
    payload: ValuationRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger the full valuation pipeline for a company.
    Returns immediately with a 'running' status while pipeline executes in background.
    Poll GET /valuations/{id}/status to track progress.
    """
    logger.info(f"[VALUATIONS] trigger — company={payload.company_id}")

    company = await db.get(Company, payload.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Create a pending valuation record
    val = Valuation(company_id=payload.company_id, status="running")
    db.add(val)
    await db.commit()
    await db.refresh(val)

    # Run pipeline in background
    async def _run_bg():
        async with db_session() as bg_db:
            await run_full_valuation(
                company_id=payload.company_id,
                session=bg_db,
                wacc=payload.wacc,
                private_discount=payload.private_discount,
            )

    background_tasks.add_task(_run_bg)
    return APIResponse.ok(ValuationOut.model_validate(val))


@router.get("/{valuation_id}", response_model=APIResponse[ValuationOut])
async def get_valuation(valuation_id: str, db: AsyncSession = Depends(get_db)):
    val = await db.get(Valuation, valuation_id)
    if not val:
        raise HTTPException(status_code=404, detail="Valuation not found")
    return APIResponse.ok(ValuationOut.model_validate(val))


@router.get("/{valuation_id}/status", response_model=APIResponse[dict])
async def get_valuation_status(valuation_id: str, db: AsyncSession = Depends(get_db)):
    val = await db.get(Valuation, valuation_id)
    if not val:
        raise HTTPException(status_code=404, detail="Valuation not found")
    return APIResponse.ok({
        "id": val.id,
        "status": val.status,
        "error": val.error_msg,
        "final_range_mid": float(val.final_range_mid) if val.final_range_mid else None,
    })


@router.get("/company/{company_id}/latest", response_model=APIResponse[ValuationOut])
async def get_latest_valuation(company_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Valuation)
        .where(Valuation.company_id == company_id)
        .order_by(Valuation.created_at.desc())
        .limit(1)
    )
    val = result.scalar_one_or_none()
    if not val:
        raise HTTPException(status_code=404, detail="No valuation found for this company")
    return APIResponse.ok(ValuationOut.model_validate(val))


@router.post("/{valuation_id}/export", response_model=APIResponse[dict])
async def export_pdf(valuation_id: str, db: AsyncSession = Depends(get_db)):
    """Generate and return a PDF report for the valuation."""
    val = await db.get(Valuation, valuation_id)
    if not val:
        raise HTTPException(status_code=404, detail="Valuation not found")
    if val.status != "completed":
        raise HTTPException(status_code=400, detail=f"Valuation is not complete (status: {val.status})")

    company = await db.get(Company, val.company_id)

    try:
        pdf_path = await generate_pdf_report(val, company)
        return APIResponse.ok({"pdf_path": pdf_path, "message": "PDF generated successfully"})
    except Exception as exc:
        logger.error(f"[VALUATIONS] PDF export failed: {exc}")
        return APIResponse.fail("PDF_ERROR", f"PDF generation failed: {str(exc)}")
