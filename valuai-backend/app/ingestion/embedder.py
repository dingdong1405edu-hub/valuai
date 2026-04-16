"""
Embedding Layer — chunk text → Google text-embedding-004 → store in pgvector.
Also provides semantic_search for RAG retrieval.
"""

import logging
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_clients import embed_text, embed_texts
from app.db.models import Embedding

logger = logging.getLogger(__name__)

CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 50     # overlap between consecutive chunks


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks of ~chunk_size characters."""
    if not text or not text.strip():
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap  # slide forward with overlap

    return chunks


async def embed_and_store(
    session: AsyncSession,
    document_id: str,
    company_id: str,
    text: str,
) -> int:
    """
    Chunk a document's text, embed each chunk, and store in the embeddings table.
    Returns the number of chunks stored.
    """
    logger.info(f"[EMBEDDER] embed_and_store — doc={document_id}, text_len={len(text)}")

    chunks = chunk_text(text)
    if not chunks:
        logger.warning(f"[EMBEDDER] no chunks from document {document_id}")
        return 0

    logger.info(f"[EMBEDDER] {len(chunks)} chunks to embed")

    # Embed in batches of 10 to avoid rate limits
    batch_size = 10
    stored = 0

    for batch_start in range(0, len(chunks), batch_size):
        batch = chunks[batch_start: batch_start + batch_size]

        try:
            vectors = await embed_texts(batch)
        except Exception as exc:
            logger.error(f"[EMBEDDER] batch embedding failed: {exc}")
            # Try one-by-one fallback
            vectors = []
            for chunk in batch:
                try:
                    vec = await embed_text(chunk)
                    vectors.append(vec)
                except Exception as e2:
                    logger.error(f"[EMBEDDER] single embed failed: {e2}")
                    vectors.append(None)

        for i, (chunk, vector) in enumerate(zip(batch, vectors)):
            if vector is None:
                continue
            chunk_idx = batch_start + i
            row = Embedding(
                document_id=document_id,
                company_id=company_id,
                chunk_index=chunk_idx,
                content=chunk,
                embedding=vector,
            )
            session.add(row)
            stored += 1

        await session.flush()  # flush each batch

    logger.info(f"[EMBEDDER] stored {stored} embeddings for doc={document_id}")
    return stored


async def semantic_search(
    session: AsyncSession,
    query: str,
    company_id: str,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Find top_k most relevant chunks for a query using cosine similarity.
    Uses pgvector <=> operator (cosine distance, lower = more similar).
    """
    logger.info(f"[EMBEDDER] semantic_search — company={company_id}, query='{query[:60]}...'")

    query_vector = await embed_text(query, task_type="retrieval_query")

    # Format vector as PostgreSQL literal (safe — only floats, no SQL injection possible)
    vec_literal = "[" + ",".join(str(f) for f in query_vector) + "]"

    # Raw SQL for pgvector cosine similarity — vector embedded directly to avoid
    # asyncpg's incompatibility with :param::type cast syntax in SQLAlchemy text()
    sql = text(f"""
        SELECT id, content, chunk_index, document_id,
               1 - (embedding <=> '{vec_literal}'::vector) AS similarity
        FROM embeddings
        WHERE company_id = :company_id
          AND embedding IS NOT NULL
        ORDER BY embedding <=> '{vec_literal}'::vector
        LIMIT :top_k
    """)

    result = await session.execute(
        sql,
        {"company_id": company_id, "top_k": top_k},
    )
    rows = result.fetchall()

    chunks = [
        {
            "id": str(row.id),
            "content": row.content,
            "chunk_index": row.chunk_index,
            "document_id": str(row.document_id),
            "similarity": float(row.similarity),
        }
        for row in rows
    ]

    logger.info(f"[EMBEDDER] found {len(chunks)} relevant chunks")
    return chunks
