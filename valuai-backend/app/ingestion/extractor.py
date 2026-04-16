"""
Extraction Layer — Groq (llama-3.3-70b) extracts structured JSON from parsed text.
Falls back to regex parsing for Vietnamese numbers when AI extraction returns nulls.
"""

import logging
import re
from typing import Any

from app.core.ai_clients import groq_json
from app.models.schemas import FinancialData, QualitativeData

logger = logging.getLogger(__name__)

# ─── System prompts ───────────────────────────────────────────────────────────

FINANCIAL_SYSTEM_PROMPT = """You are a financial analyst extracting data from a Vietnamese business document.

CRITICAL: All returned monetary values MUST be in VND billions (tỷ đồng).

Conversion rules:
- "45 tỷ đồng" → 45
- "45,200 triệu đồng" → 45.2  (triệu ÷ 1000 = tỷ)
- "45,200,000,000 đồng" → 45.2  (raw VND ÷ 1,000,000,000)
- "500 triệu" → 0.5
- "$2 million USD" → 50  (×25,000 VND/USD ÷ 1,000,000,000)

Vietnamese keyword mapping:
- Revenue = "doanh thu", "doanh thu thuần", "tổng doanh thu"
- Profit  = "lợi nhuận", "lợi nhuận sau thuế", "lợi nhuận ròng"
- EBITDA  = "EBITDA", "lợi nhuận trước lãi vay thuế và khấu hao"
- Assets  = "tổng tài sản"
- Debt    = "nợ phải trả", "nợ vay", "vay ngân hàng"
- Employees = "nhân viên", "nhân sự", "lao động", "cán bộ nhân viên"
- Founded = "năm thành lập", "thành lập năm"

Return ONLY valid JSON (no markdown, no explanation):
{
  "revenue": <VND billions float or null — NEVER invent, return null if not found>,
  "profit": <VND billions float or null>,
  "ebitda": <VND billions float or null>,
  "total_assets": <VND billions float or null>,
  "debt": <VND billions float or null>,
  "employees": <integer or null>,
  "founding_year": <4-digit year or null>,
  "industry": "<industry in English: technology/retail/manufacturing/food_beverage/real_estate/healthcare/education/logistics/finance/agriculture/construction — pick closest>",
  "products": ["up to 5 main products or services"],
  "markets": ["up to 5 target markets or customer segments"],
  "growth_rate": <annual revenue growth as decimal e.g. 0.15 for 15%, or null>,
  "currency": "VND",
  "fiscal_year": <4-digit year the financial data covers, or null>
}"""

QUALITATIVE_SYSTEM_PROMPT = """You are a business analyst extracting qualitative information from a Vietnamese SME document.

This document may be in Vietnamese — extract accurately regardless of language.

Return ONLY valid JSON (no markdown):
{
  "team_strength": "<describe management team quality, experience — null if not mentioned>",
  "product_uniqueness": "<what differentiates products/services — null if not mentioned>",
  "market_size": "<size and growth potential of target market — null if not mentioned>",
  "competitive_moat": "<competitive advantages, barriers to entry — null if not mentioned>",
  "customer_traction": "<customer count, key clients, revenue proof — null if not mentioned>",
  "legal_status": "<company registration, licenses, certificates — null if not mentioned>",
  "key_risks": ["2-5 business risks explicitly mentioned, or empty array"],
  "strategic_plans": ["2-5 growth plans or expansion goals explicitly mentioned, or empty array"]
}"""


# ─── Regex fallback for Vietnamese numbers ────────────────────────────────────

def _regex_find_revenue(text: str) -> float | None:
    """Last-resort: scan text for Vietnamese revenue patterns."""
    t = text.lower()
    patterns = [
        # "doanh thu: 45 tỷ" or "doanh thu 45.2 tỷ đồng"
        (r'doanh\s*thu[^:\n]{0,30}?([\d,\.]+)\s*tỷ', 'ty'),
        (r'doanh\s*thu[^:\n]{0,30}?([\d,\.]+)\s*triệu', 'trieu'),
        # raw numbers after doanh thu
        (r'doanh\s*thu[^\n]{0,50}?([\d]{9,})', 'raw'),
        # revenue keyword
        (r'revenue[^:\n]{0,30}?([\d,\.]+)\s*tỷ', 'ty'),
        (r'revenue[^:\n]{0,30}?([\d,\.]+)\s*billion', 'ty'),
    ]
    for pattern, unit in patterns:
        m = re.search(pattern, t)
        if m:
            try:
                val = float(m.group(1).replace(',', ''))
                if unit == 'ty':
                    return val
                elif unit == 'trieu':
                    return val / 1000
                elif unit == 'raw':
                    return val / 1_000_000_000
            except (ValueError, TypeError):
                continue
    return None


def _regex_find_employees(text: str) -> int | None:
    """Scan text for employee count patterns."""
    t = text.lower()
    patterns = [
        r'([\d,]+)\s*nhân\s*viên',
        r'([\d,]+)\s*nhân\s*sự',
        r'([\d,]+)\s*lao\s*động',
        r'([\d,]+)\s*cán\s*bộ',
        r'employees?\s*:?\s*([\d,]+)',
        r'staff\s*:?\s*([\d,]+)',
        r'([\d,]+)\s*người',
    ]
    for pattern in patterns:
        m = re.search(pattern, t)
        if m:
            try:
                val = int(m.group(1).replace(',', ''))
                if 1 <= val <= 100_000:
                    return val
            except (ValueError, TypeError):
                continue
    return None


# ─── Unit normalization safety net ────────────────────────────────────────────

_MONEY_FIELDS = ("revenue", "profit", "ebitda", "total_assets", "debt")


def _normalize_to_vnd_billions(data: dict[str, Any]) -> dict[str, Any]:
    """
    If AI returned raw VND integers instead of billions, convert.
    Any monetary value >= 1,000,000,000 is treated as raw VND.
    Also handles USD conversion.
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
            val = val * 25_000 / 1_000_000_000
            data["currency"] = "VND"
        elif val >= 1_000_000_000:
            val = val / 1_000_000_000
        # Sanity check: single-company revenue > 500,000 tỷ is impossible
        if val > 500_000:
            data[field] = None
            logger.warning(f"[EXTRACTOR] {field}={val} exceeds sanity limit — set to null")
            continue
        data[field] = round(val, 3) if val else val
    return data


# ─── Extraction functions ─────────────────────────────────────────────────────

async def extract_financial_data(text: str, doc_type: str = "financial_report") -> tuple[dict[str, Any], int]:
    """Extract structured financial data using Groq + regex fallback."""
    logger.info(f"[EXTRACTOR] financial — doc_type={doc_type}, text_len={len(text)}")
    truncated = text[:12000] if len(text) > 12000 else text

    user_msg = f"Document type: {doc_type}\n\nDocument content:\n{truncated}\n\nExtract all financial data. Return JSON only."

    data: dict[str, Any] = {}
    tokens = 0

    try:
        data, tokens = await groq_json(FINANCIAL_SYSTEM_PROMPT, user_msg)
        data = _normalize_to_vnd_billions(data)
    except Exception as exc:
        logger.error(f"[EXTRACTOR] Groq financial failed: {exc}")
        data = {}

    # ── Regex fallback: fill nulls that AI missed ──
    if not data.get("revenue") or data["revenue"] <= 0:
        regex_rev = _regex_find_revenue(text)
        if regex_rev and regex_rev > 0:
            data["revenue"] = regex_rev
            logger.info(f"[EXTRACTOR] revenue filled by regex: {regex_rev} tỷ")

    if not data.get("employees"):
        regex_emp = _regex_find_employees(text)
        if regex_emp:
            data["employees"] = regex_emp
            logger.info(f"[EXTRACTOR] employees filled by regex: {regex_emp}")

    # Validate through schema (fills defaults)
    try:
        validated = FinancialData(**data)
        result = validated.model_dump()
    except Exception:
        result = FinancialData().model_dump()
        result.update({k: v for k, v in data.items() if k in result})

    logger.info(
        f"[EXTRACTOR] financial OK — tokens={tokens}, "
        f"revenue={result.get('revenue')}, profit={result.get('profit')}, "
        f"employees={result.get('employees')}, fiscal_year={result.get('fiscal_year')}"
    )
    return result, tokens


async def extract_qualitative_data(text: str, doc_type: str = "business_plan") -> tuple[dict[str, Any], int]:
    """Extract qualitative business data using Groq."""
    logger.info(f"[EXTRACTOR] qualitative — doc_type={doc_type}, text_len={len(text)}")
    truncated = text[:12000] if len(text) > 12000 else text

    user_msg = f"Document type: {doc_type}\n\nDocument content:\n{truncated}\n\nExtract qualitative business information. Return JSON only."

    try:
        data, tokens = await groq_json(QUALITATIVE_SYSTEM_PROMPT, user_msg)
        logger.info(f"[EXTRACTOR] qualitative OK — tokens={tokens}")
        validated = QualitativeData(**data)
        return validated.model_dump(), tokens
    except Exception as exc:
        logger.error(f"[EXTRACTOR] qualitative failed: {exc}")
        return QualitativeData().model_dump(), 0


# Mapping: doc_type → extractors to run
EXTRACTOR_MAP: dict[str, list[str]] = {
    "financial_report":   ["financial", "qualitative"],
    "catalogue":          ["qualitative"],
    "business_plan":      ["financial", "qualitative"],
    "cv":                 ["qualitative"],
    "capability_profile": ["qualitative"],
    "web_content":        ["qualitative"],
    "crm":                ["financial"],
    "accounting":         ["financial"],
    "erp":                ["financial"],
}


async def run_extraction(text: str, doc_type: str) -> tuple[dict[str, Any], int]:
    """Run extractors for the given document type. Returns merged data and total tokens."""
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

    logger.info(f"[EXTRACTOR] complete — doc_type={doc_type}, total_tokens={total_tokens}")
    return merged, total_tokens
