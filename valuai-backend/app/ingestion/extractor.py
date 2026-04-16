"""
Extraction Layer — Groq (llama-3.3-70b) extracts structured JSON from parsed text.

Two extraction types:
  1. Financial data   → FinancialData schema
  2. Qualitative data → QualitativeData schema
"""

import logging
from typing import Any

from app.core.ai_clients import groq_json
from app.models.schemas import FinancialData, QualitativeData

logger = logging.getLogger(__name__)

# ─── System prompts ───────────────────────────────────────────────────────────

FINANCIAL_SYSTEM_PROMPT = """You are a senior financial analyst specializing in Vietnamese SME valuation.
Extract structured financial data from the provided document text.

⚠️ CRITICAL UNIT RULE — ALL monetary values MUST be returned in VND BILLIONS (tỷ đồng):
  • Document says "45 tỷ đồng"              → return 45
  • Document says "45,000 triệu đồng"       → return 45     (45,000 ÷ 1,000)
  • Document says "45,200,000,000 VND"      → return 45.2   (÷ 1,000,000,000)
  • Document says "500,000,000 đồng"        → return 0.5    (÷ 1,000,000,000)
  • Document says "2,000,000 USD"           → return 50     (× 25,000 VND then ÷ 10^9)
  • Revenue/profit NOT found in document    → return null (NEVER invent numbers)

Return ONLY valid JSON (no markdown, no explanation):
{
  "revenue": <VND billions float or null>,
  "profit": <net profit VND billions or null>,
  "ebitda": <EBITDA VND billions or null>,
  "total_assets": <VND billions or null>,
  "debt": <total debt VND billions or null>,
  "employees": <integer count or null>,
  "founding_year": <4-digit year or null>,
  "industry": <industry name in English e.g. "technology", "retail", "manufacturing">,
  "products": ["up to 5 main products or services"],
  "markets": ["up to 5 target markets or customer segments"],
  "growth_rate": <annual revenue growth as decimal e.g. 0.15 for 15%, or null>,
  "currency": "VND",
  "fiscal_year": <4-digit year the financial data covers, e.g. 2023>
}"""

QUALITATIVE_SYSTEM_PROMPT = """You are a business analyst specializing in Vietnamese SME assessment.
Extract qualitative business information from the provided document text.

Important: This may be a Vietnamese-language document. Extract content accurately regardless of language.

Return ONLY valid JSON (no markdown, no explanation):
{
  "team_strength": "<describe management team quality, experience, backgrounds — null if not mentioned>",
  "product_uniqueness": "<what differentiates products/services from competition — null if not mentioned>",
  "market_size": "<size and growth potential of target market — null if not mentioned>",
  "competitive_moat": "<competitive advantages, barriers to entry, patents — null if not mentioned>",
  "customer_traction": "<customer count, retention rates, key clients, revenue proof — null if not mentioned>",
  "legal_status": "<company registration type, licenses, certificates, compliance — null if not mentioned>",
  "key_risks": ["list 2-5 business risks explicitly mentioned, or empty array"],
  "strategic_plans": ["list 2-5 growth plans or expansion goals explicitly mentioned, or empty array"]
}"""


# ─── Unit normalization ───────────────────────────────────────────────────────

_MONEY_FIELDS = ("revenue", "profit", "ebitda", "total_assets", "debt")

def _normalize_to_vnd_billions(data: dict[str, Any]) -> dict[str, Any]:
    """
    Safety net: if the AI returned raw VND integers instead of billions,
    divide by 1e9.  Also converts USD amounts at ~25,000 VND/USD.
    Threshold: any monetary value >= 1_000_000_000 is treated as raw VND.
    """
    currency = data.get("currency", "VND")
    for field in _MONEY_FIELDS:
        val = data.get(field)
        if val is None:
            continue
        try:
            val = float(val)
        except (TypeError, ValueError):
            data[field] = None
            continue
        if currency == "USD":
            val = val * 25_000 / 1_000_000_000  # USD → VND billions
            data["currency"] = "VND"
        elif val >= 1_000_000_000:
            # Treat as raw VND → convert to billions
            val = val / 1_000_000_000
        data[field] = round(val, 3) if val else val
    return data


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
        data = _normalize_to_vnd_billions(data)
        validated = FinancialData(**data)
        result = validated.model_dump()
        logger.info(
            f"[EXTRACTOR] financial OK — tokens={tokens}, "
            f"revenue={result.get('revenue')}, profit={result.get('profit')}, "
            f"fiscal_year={result.get('fiscal_year')}"
        )
        return result, tokens
    except Exception as exc:
        logger.error(f"[EXTRACTOR] financial extraction failed: {exc}", exc_info=True)
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
