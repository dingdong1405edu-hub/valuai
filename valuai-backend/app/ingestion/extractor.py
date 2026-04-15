"""
Extraction Layer — Groq (llama-3.3-70b) extracts structured JSON from parsed text.

Two extraction types:
  1. Financial data   → FinancialData schema
  2. Qualitative data → QualitativeData schema
"""

import json
import logging
from typing import Any

from app.core.ai_clients import groq_json
from app.models.schemas import FinancialData, QualitativeData

logger = logging.getLogger(__name__)

# ─── System prompts ───────────────────────────────────────────────────────────

FINANCIAL_SYSTEM_PROMPT = """You are a senior financial analyst specializing in Vietnamese SME valuation.
Extract structured financial data from the provided document text.

Return ONLY valid JSON matching this exact schema (use null for missing fields):
{
  "revenue": <number in VND or original currency>,
  "profit": <net profit number>,
  "ebitda": <EBITDA number>,
  "total_assets": <total assets number>,
  "debt": <total debt/liabilities number>,
  "employees": <employee count integer>,
  "founding_year": <year integer>,
  "industry": <industry name string>,
  "products": ["list", "of", "main", "products/services"],
  "markets": ["list", "of", "target", "markets"],
  "growth_rate": <annual revenue growth rate as decimal e.g. 0.15 for 15%>,
  "currency": <"VND" or "USD" etc>,
  "fiscal_year": <year of the financial data>
}

Rules:
- All monetary values should be in the same unit as the source document
- If revenue is in billions VND (tỷ đồng), return the value in billions
- Use null for any field not found in the document
- Do not invent data — only extract what is explicitly stated"""

QUALITATIVE_SYSTEM_PROMPT = """You are a business analyst specializing in Vietnamese SME assessment.
Extract qualitative business information from the provided document text.

Return ONLY valid JSON matching this exact schema (use null for missing fields):
{
  "team_strength": <description of management team quality and experience>,
  "product_uniqueness": <what makes the product/service unique or differentiated>,
  "market_size": <description of target market size and opportunity>,
  "competitive_moat": <description of competitive advantages and barriers>,
  "customer_traction": <evidence of customer adoption, revenue, retention>,
  "legal_status": <company registration, licenses, compliance status>,
  "key_risks": ["list", "of", "identified", "business", "risks"],
  "strategic_plans": ["list", "of", "stated", "growth", "plans"]
}

Rules:
- Extract only explicitly stated information
- Use null for fields with no relevant content
- Keep descriptions concise (1-3 sentences each)
- Lists should have 2-5 items maximum"""


# ─── Extraction functions ─────────────────────────────────────────────────────

async def extract_financial_data(text: str, doc_type: str = "financial_report") -> tuple[dict[str, Any], int]:
    """
    Extract structured financial data from parsed document text using Groq.
    Returns (data_dict, tokens_used).
    """
    logger.info(f"[EXTRACTOR] financial extraction — doc_type={doc_type}, text_len={len(text)}")

    # Truncate very long texts to avoid token limits (keep first 12k chars)
    truncated = text[:12000] if len(text) > 12000 else text

    user_msg = f"""Document type: {doc_type}

Document content:
{truncated}

Extract all financial data from this document. Return JSON only."""

    try:
        data, tokens = await groq_json(FINANCIAL_SYSTEM_PROMPT, user_msg)
        logger.info(f"[EXTRACTOR] financial OK — tokens={tokens}")
        # Validate with Pydantic
        validated = FinancialData(**data)
        return validated.model_dump(), tokens
    except Exception as exc:
        logger.error(f"[EXTRACTOR] financial extraction failed: {exc}")
        # Return empty structure on failure
        return FinancialData().model_dump(), 0


async def extract_qualitative_data(text: str, doc_type: str = "business_plan") -> tuple[dict[str, Any], int]:
    """
    Extract qualitative business data from parsed document text using Groq.
    Returns (data_dict, tokens_used).
    """
    logger.info(f"[EXTRACTOR] qualitative extraction — doc_type={doc_type}, text_len={len(text)}")

    truncated = text[:12000] if len(text) > 12000 else text

    user_msg = f"""Document type: {doc_type}

Document content:
{truncated}

Extract all qualitative business information. Return JSON only."""

    try:
        data, tokens = await groq_json(QUALITATIVE_SYSTEM_PROMPT, user_msg)
        logger.info(f"[EXTRACTOR] qualitative OK — tokens={tokens}")
        validated = QualitativeData(**data)
        return validated.model_dump(), tokens
    except Exception as exc:
        logger.error(f"[EXTRACTOR] qualitative extraction failed: {exc}")
        return QualitativeData().model_dump(), 0


# Mapping: doc_type → which extractors to run
EXTRACTOR_MAP: dict[str, list[str]] = {
    "financial_report": ["financial", "qualitative"],
    "catalogue":        ["qualitative"],
    "business_plan":    ["financial", "qualitative"],
    "cv":               ["qualitative"],
    "capability_profile": ["qualitative"],
    "web_content":      ["qualitative"],
    "crm":              ["financial"],
    "accounting":       ["financial"],
    "erp":              ["financial"],
}


async def run_extraction(text: str, doc_type: str) -> tuple[dict[str, Any], int]:
    """
    Run the appropriate extractors for a given document type.
    Returns merged data dict and total tokens used.
    """
    extractors = EXTRACTOR_MAP.get(doc_type, ["qualitative"])
    merged: dict[str, Any] = {}
    total_tokens = 0

    if "financial" in extractors:
        fin_data, fin_tokens = await extract_financial_data(text, doc_type)
        merged["financial"] = fin_data
        total_tokens += fin_tokens

    if "qualitative" in extractors:
        qual_data, qual_tokens = await extract_qualitative_data(text, doc_type)
        merged["qualitative"] = qual_data
        total_tokens += qual_tokens

    logger.info(f"[EXTRACTOR] run_extraction complete — doc_type={doc_type}, total_tokens={total_tokens}")
    return merged, total_tokens
