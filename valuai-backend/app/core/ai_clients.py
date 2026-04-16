"""
AI client layer — Groq (fast) + Gemini (deep).

Routing:
  extract_fast      → Groq  llama-3.3-70b-versatile
  scorecard         → Groq
  read_pdf          → Gemini 2.0 Flash (multimodal)
  analyze_deep      → Gemini 2.0 Flash (long context)
  synthesize_report → Gemini 2.0 Flash
  embed             → Google text-embedding-004
"""

import asyncio
import json
import logging
import os
import tempfile
from enum import Enum
from typing import Any

import google.generativeai as genai
from groq import AsyncGroq
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

# ─── Initialize clients ──────────────────────────────────────────────────────

genai.configure(api_key=settings.GOOGLE_API_KEY)

_groq = AsyncGroq(api_key=settings.GROQ_API_KEY)

_gemini_text = genai.GenerativeModel(
    settings.GEMINI_MODEL,
    generation_config={"temperature": 0.3, "max_output_tokens": 8192},
)
_gemini_json = genai.GenerativeModel(
    settings.GEMINI_MODEL,
    generation_config={
        "temperature": 0.0,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
    },
)


class TaskType(str, Enum):
    EXTRACT_FAST = "extract_fast"
    READ_PDF = "read_pdf"
    ANALYZE_DEEP = "analyze_deep"
    SCORECARD = "scorecard"
    SYNTHESIZE_REPORT = "synthesize_report"
    EMBED = "embed"


def route_ai(task_type: TaskType) -> str:
    """Return 'groq' or 'gemini' for the given task type."""
    groq_tasks = {TaskType.EXTRACT_FAST, TaskType.SCORECARD}
    if task_type in groq_tasks:
        return "groq"
    return "gemini"


# ─── Groq helpers ────────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=30),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def groq_json(system: str, user: str, max_tokens: int = 4096) -> dict[str, Any]:
    """Call Groq and return parsed JSON dict. Retries up to 3×."""
    logger.info(f"[GROQ] json call — model={settings.GROQ_MODEL}")
    response = await _groq.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=max_tokens,
    )
    tokens = response.usage.total_tokens if response.usage else 0
    logger.info(f"[GROQ] tokens_used={tokens}")
    return json.loads(response.choices[0].message.content), tokens


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=30),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def groq_text(system: str, user: str, max_tokens: int = 2048) -> tuple[str, int]:
    """Call Groq and return plain text. Retries up to 3×."""
    logger.info(f"[GROQ] text call — model={settings.GROQ_MODEL}")
    response = await _groq.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        max_tokens=max_tokens,
    )
    tokens = response.usage.total_tokens if response.usage else 0
    logger.info(f"[GROQ] tokens_used={tokens}")
    return response.choices[0].message.content, tokens


# ─── Gemini helpers ───────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def gemini_parse_pdf(file_bytes: bytes, prompt: str) -> tuple[str, int]:
    """
    Upload PDF bytes to Gemini Files API and extract content.
    Gemini 2.0 Flash can read up to 20 MB PDFs directly.
    """
    logger.info(f"[GEMINI] parse_pdf — {len(file_bytes)//1024} KB")

    # Write to temp file, upload, then clean up
    suffix = ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        uploaded = await asyncio.to_thread(
            genai.upload_file, tmp_path, mime_type="application/pdf"
        )
        response = await asyncio.to_thread(
            _gemini_text.generate_content, [uploaded, prompt]
        )
        # Clean up uploaded file from Gemini Files API
        try:
            await asyncio.to_thread(uploaded.delete)
        except Exception:
            pass
        tokens = response.usage_metadata.total_token_count if hasattr(response, "usage_metadata") else 0
        logger.info(f"[GEMINI] parse_pdf tokens={tokens}")
        return response.text, tokens
    finally:
        os.unlink(tmp_path)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def gemini_parse_image(file_bytes: bytes, mime_type: str, prompt: str) -> tuple[str, int]:
    """Extract content from an image (PNG/JPG/WEBP) via Gemini Vision."""
    logger.info(f"[GEMINI] parse_image — mime={mime_type}, {len(file_bytes)//1024} KB")

    ext_map = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
    suffix = ext_map.get(mime_type, ".jpg")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        uploaded = await asyncio.to_thread(
            genai.upload_file, tmp_path, mime_type=mime_type
        )
        response = await asyncio.to_thread(
            _gemini_text.generate_content, [uploaded, prompt]
        )
        try:
            await asyncio.to_thread(uploaded.delete)
        except Exception:
            pass
        tokens = response.usage_metadata.total_token_count if hasattr(response, "usage_metadata") else 0
        return response.text, tokens
    finally:
        os.unlink(tmp_path)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def gemini_json(prompt: str) -> tuple[dict[str, Any], int]:
    """Call Gemini and return parsed JSON. Retries up to 3×."""
    logger.info("[GEMINI] json call")
    response = await asyncio.to_thread(_gemini_json.generate_content, prompt)
    tokens = response.usage_metadata.total_token_count if hasattr(response, "usage_metadata") else 0
    logger.info(f"[GEMINI] json tokens={tokens}")
    return json.loads(response.text), tokens


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def gemini_text(prompt: str) -> tuple[str, int]:
    """Call Gemini and return plain text. Retries up to 3×."""
    logger.info("[GEMINI] text call")
    response = await asyncio.to_thread(_gemini_text.generate_content, prompt)
    tokens = response.usage_metadata.total_token_count if hasattr(response, "usage_metadata") else 0
    logger.info(f"[GEMINI] text tokens={tokens}")
    return response.text, tokens


# ─── Embedding helper ─────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=15),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def embed_text(text: str, task_type: str = "retrieval_document") -> list[float]:
    """Embed a single text using gemini-embedding-001 (768 dims via output_dimensionality)."""
    result = await asyncio.to_thread(
        genai.embed_content,
        model=settings.EMBEDDING_MODEL,
        content=text,
        task_type=task_type,
        output_dimensionality=768,
    )
    return result["embedding"]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=15),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts. Returns list of 768-dim vectors."""
    result = await asyncio.to_thread(
        genai.embed_content,
        model=settings.EMBEDDING_MODEL,
        content=texts,
        task_type="retrieval_document",
        output_dimensionality=768,
    )
    return result["embedding"]
