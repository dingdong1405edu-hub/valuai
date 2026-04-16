"""
AI client layer — Groq (fast extraction) + Gemini (parsing + reasoning).

Groq:
  groq_json  → llama-3.3-70b-versatile  (JSON extraction, scorecard)
  groq_text  → deepseek-r1-distill-llama-70b (reasoning, text tasks)

Gemini:
  gemini_parse_pdf   → 2.0-flash (inline bytes — no Files API to avoid processing delay)
  gemini_parse_image → 2.0-flash (inline bytes)
  gemini_json        → 2.0-flash (structured JSON output)
  gemini_text        → 2.0-flash (free-form text)

Embeddings:
  embed_text / embed_texts → gemini-embedding-001 (768-dim)
"""

import asyncio
import base64
import json
import logging
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

# ─── Initialize clients ───────────────────────────────────────────────────────

genai.configure(api_key=settings.GOOGLE_API_KEY)

_groq = AsyncGroq(api_key=settings.GROQ_API_KEY)

_gemini_text = genai.GenerativeModel(
    settings.GEMINI_MODEL,
    generation_config={"temperature": 0.2, "max_output_tokens": 8192},
)
_gemini_json_model = genai.GenerativeModel(
    settings.GEMINI_MODEL,
    generation_config={
        "temperature": 0.0,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
    },
)


# ─── Groq helpers ─────────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=30),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def groq_json(system: str, user: str, max_tokens: int = 4096) -> tuple[dict[str, Any], int]:
    """Structured JSON extraction via Groq llama-3.3-70b-versatile."""
    model = settings.GROQ_EXTRACTION_MODEL
    logger.info(f"[GROQ] json — model={model}, user_len={len(user)}")
    response = await _groq.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=max_tokens,
    )
    tokens = response.usage.total_tokens if response.usage else 0
    content = response.choices[0].message.content
    logger.info(f"[GROQ] json done — tokens={tokens}, response_len={len(content)}")
    return json.loads(content), tokens


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=30),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def groq_text(system: str, user: str, max_tokens: int = 2048) -> tuple[str, int]:
    """Plain text via Groq deepseek-r1 (better reasoning)."""
    model = settings.GROQ_MODEL
    logger.info(f"[GROQ] text — model={model}")
    response = await _groq.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        max_tokens=max_tokens,
    )
    tokens = response.usage.total_tokens if response.usage else 0
    logger.info(f"[GROQ] text done — tokens={tokens}")
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
    Parse a PDF using Gemini Vision — inline base64 (no Files API).
    Avoids the Files API 'PROCESSING' delay that causes intermittent failures.
    Supports up to ~20 MB PDFs.
    """
    size_kb = len(file_bytes) // 1024
    logger.info(f"[GEMINI] parse_pdf — {size_kb} KB (inline base64)")

    pdf_b64 = base64.standard_b64encode(file_bytes).decode("utf-8")

    # Pass inline_data dict — SDK converts this to a Part automatically
    content_parts = [
        {
            "inline_data": {
                "mime_type": "application/pdf",
                "data": pdf_b64,
            }
        },
        prompt,
    ]

    response = await asyncio.to_thread(
        _gemini_text.generate_content,
        content_parts,
    )

    text_out = response.text or ""
    tokens = (
        response.usage_metadata.total_token_count
        if hasattr(response, "usage_metadata") and response.usage_metadata
        else 0
    )
    logger.info(f"[GEMINI] parse_pdf done — tokens={tokens}, output_len={len(text_out)}")
    return text_out, tokens


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def gemini_parse_image(file_bytes: bytes, mime_type: str, prompt: str) -> tuple[str, int]:
    """Extract text/data from an image (PNG/JPG/WEBP) using Gemini Vision — inline bytes."""
    size_kb = len(file_bytes) // 1024
    logger.info(f"[GEMINI] parse_image — mime={mime_type}, {size_kb} KB")

    img_b64 = base64.standard_b64encode(file_bytes).decode("utf-8")

    content_parts = [
        {
            "inline_data": {
                "mime_type": mime_type,
                "data": img_b64,
            }
        },
        prompt,
    ]

    response = await asyncio.to_thread(
        _gemini_text.generate_content,
        content_parts,
    )

    text_out = response.text or ""
    tokens = (
        response.usage_metadata.total_token_count
        if hasattr(response, "usage_metadata") and response.usage_metadata
        else 0
    )
    logger.info(f"[GEMINI] parse_image done — tokens={tokens}, output_len={len(text_out)}")
    return text_out, tokens


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def gemini_json(prompt: str) -> tuple[dict[str, Any], int]:
    """Call Gemini and return parsed JSON. Uses response_mime_type=application/json."""
    logger.info(f"[GEMINI] json — prompt_len={len(prompt)}")
    response = await asyncio.to_thread(_gemini_json_model.generate_content, prompt)
    text_out = response.text or "{}"
    tokens = (
        response.usage_metadata.total_token_count
        if hasattr(response, "usage_metadata") and response.usage_metadata
        else 0
    )
    logger.info(f"[GEMINI] json done — tokens={tokens}")
    try:
        return json.loads(text_out), tokens
    except json.JSONDecodeError as e:
        logger.error(f"[GEMINI] json parse failed: {e} — raw: {text_out[:200]}")
        raise


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def gemini_text(prompt: str) -> tuple[str, int]:
    """Call Gemini and return plain text."""
    logger.info(f"[GEMINI] text — prompt_len={len(prompt)}")
    response = await asyncio.to_thread(_gemini_text.generate_content, prompt)
    text_out = response.text or ""
    tokens = (
        response.usage_metadata.total_token_count
        if hasattr(response, "usage_metadata") and response.usage_metadata
        else 0
    )
    logger.info(f"[GEMINI] text done — tokens={tokens}")
    return text_out, tokens


# ─── Embedding helpers ────────────────────────────────────────────────────────

def _embed_kwargs() -> dict:
    """
    Build kwargs for genai.embed_content.
    output_dimensionality=768 is only passed for models that support it
    (gemini-embedding-001 etc). text-embedding-004 natively returns 768 dims
    and does NOT accept this param — passing it raises a 400 error.
    """
    model = settings.EMBEDDING_MODEL
    kwargs: dict[str, Any] = {"model": model}
    # Only newer embedding models support output_dimensionality
    if "gemini-embedding" in model or "embedding-exp" in model:
        kwargs["output_dimensionality"] = 768
    return kwargs


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=15),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def embed_text(text: str, task_type: str = "retrieval_document") -> list[float]:
    """Embed a single text. Returns a 768-dim float vector."""
    kwargs = _embed_kwargs()
    result = await asyncio.to_thread(
        genai.embed_content,
        content=text,
        task_type=task_type,
        **kwargs,
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
    kwargs = _embed_kwargs()
    result = await asyncio.to_thread(
        genai.embed_content,
        content=texts,
        task_type="retrieval_document",
        **kwargs,
    )
    emb = result["embedding"]
    # Normalize: single-text result may return a flat list
    if texts and isinstance(emb[0], (int, float)):
        return [emb]
    return emb
