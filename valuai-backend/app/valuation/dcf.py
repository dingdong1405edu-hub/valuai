"""
DCF (Discounted Cash Flow) Valuation Engine.

Gemini provides growth parameters (simple JSON — 4 numbers).
All financial math is done in Python deterministically.

Vietnamese SME defaults: WACC 15%, terminal growth 3%, 5-year projection.
"""

import logging
from dataclasses import dataclass
from typing import Any

from app.core.ai_clients import gemini_json

logger = logging.getLogger(__name__)

DEFAULT_WACC = 0.15
TERMINAL_GROWTH = 0.03
PROJECTION_YEARS = 5

# Revenue-per-employee estimates (VND billions/year) by industry keyword
_REV_PER_EMP: list[tuple[list[str], float]] = [
    (["tech", "software", "it", "công nghệ", "edtech", "education"], 3.0),
    (["retail", "bán lẻ", "trade", "thương mại"], 4.0),
    (["manufacturing", "sản xuất", "factory", "nhà máy"], 1.5),
    (["food", "f&b", "nhà hàng", "ăn uống", "beverage"], 1.8),
    (["healthcare", "y tế", "bệnh viện", "clinic"], 2.5),
    (["logistics", "vận tải", "giao vận"], 2.0),
    (["real_estate", "bất động sản", "real estate"], 2.0),
]
_DEFAULT_REV_PER_EMP = 2.0


def _estimate_revenue(employees: int | None, industry: str) -> float:
    ind = (industry or "").lower()
    rev_per_emp = _DEFAULT_REV_PER_EMP
    for keywords, rate in _REV_PER_EMP:
        if any(k in ind for k in keywords):
            rev_per_emp = rate
            break
    return max(float(employees or 10) * rev_per_emp, 5.0)


@dataclass
class DCFResult:
    present_value: float
    value_low: float
    value_mid: float
    value_high: float
    assumptions: dict[str, Any]
    confidence: float
    tokens_used: int


# Simplified prompt — only asks for 4 numbers, not 15
DCF_PARAMS_PROMPT = """You are an M&A analyst assessing a Vietnamese SME for DCF valuation.

Company data (all monetary values in VND billions):
{summary}

Vietnamese SME benchmarks:
- Technology/Edtech: growth 20-35%/yr, EBITDA margin 20-35%
- Retail/Trading: growth 8-18%/yr, EBITDA margin 5-12%
- Manufacturing: growth 5-12%/yr, EBITDA margin 8-15%
- F&B/Restaurant: growth 10-20%/yr, EBITDA margin 12-20%
- Healthcare: growth 12-20%/yr, EBITDA margin 15-25%
- Services/General: growth 8-18%/yr, EBITDA margin 10-20%

Task: estimate these 4 parameters for the BASE case scenario.
Conservative = base × 0.6, Optimistic = base × 1.5 (Python will calculate automatically).

Return ONLY valid JSON:
{{
  "base_revenue_billions": <current annual revenue in VND billions — estimate from employees if unknown, never 0>,
  "annual_growth_rate": <base case annual growth rate decimal, e.g. 0.15 for 15%>,
  "ebitda_margin": <EBITDA as fraction of revenue, e.g. 0.18 for 18%>,
  "wacc": <recommended WACC for this company, typically 0.14-0.20 for VN SMEs>,
  "confidence": <your confidence 0.0-1.0 — use 0.5 if data is scarce>
}}"""


def _calc_dcf(base_revenue: float, growth: float, margin: float, capex: float, wacc: float) -> float:
    """Calculate DCF present value: sum of FCFs + terminal value."""
    revenue = base_revenue
    pv = 0.0
    fcf_final = 0.0
    for t in range(1, PROJECTION_YEARS + 1):
        revenue = revenue * (1 + growth)
        fcf = max(revenue * (margin - capex), 0)
        pv += fcf / ((1 + wacc) ** t)
        fcf_final = fcf

    # Terminal value (Gordon Growth)
    g = min(TERMINAL_GROWTH, wacc * 0.7)
    tv = fcf_final * (1 + g) / (wacc - g)
    pv += tv / ((1 + wacc) ** PROJECTION_YEARS)
    return pv


async def run_dcf(financial_data: dict[str, Any], wacc: float = DEFAULT_WACC) -> DCFResult:
    """Run DCF valuation. Returns DCFResult with low/mid/high range."""
    logger.info(f"[DCF] run_dcf — wacc={wacc:.1%}")

    fin = financial_data.get("financial", {})
    revenue = float(fin.get("revenue") or 0)
    ebitda = float(fin.get("ebitda") or 0)
    profit = float(fin.get("profit") or 0)
    employees = fin.get("employees")
    industry = fin.get("industry", "")
    growth_rate = float(fin.get("growth_rate") or 0)
    fiscal_year = fin.get("fiscal_year", "recent")

    summary = (
        f"Revenue (FY{fiscal_year}): {revenue:.1f} tỷ VND\n"
        f"EBITDA: {ebitda:.1f} tỷ\n"
        f"Net profit: {profit:.1f} tỷ\n"
        f"Historical growth: {growth_rate:.0%}\n"
        f"Industry: {industry or 'General'}\n"
        f"Employees: {employees or 'Unknown'}"
    )

    tokens_used = 0
    try:
        prompt = DCF_PARAMS_PROMPT.format(summary=summary)
        params, tokens_used = await gemini_json(prompt)

        base_revenue = float(params.get("base_revenue_billions") or 0)
        if base_revenue <= 0:
            base_revenue = revenue if revenue > 0 else _estimate_revenue(employees, industry)
            logger.warning(f"[DCF] Gemini returned 0 revenue — using {base_revenue:.1f} tỷ")

        growth = float(params.get("annual_growth_rate") or growth_rate or 0.12)
        margin = float(params.get("ebitda_margin") or (ebitda / base_revenue if base_revenue > 0 and ebitda > 0 else 0.15))
        wacc_rec = float(params.get("wacc") or wacc)
        if 0.08 <= wacc_rec <= 0.35:
            wacc = wacc_rec
        confidence = float(params.get("confidence") or 0.45)

        # Clamp parameters to realistic ranges
        growth = max(0.02, min(growth, 0.60))
        margin = max(0.03, min(margin, 0.50))
        capex = 0.05  # default capex ratio

        # Calculate 3 scenarios
        value_mid = _calc_dcf(base_revenue, growth, margin, capex, wacc)
        value_low = _calc_dcf(base_revenue, growth * 0.6, margin * 0.85, capex * 1.2, wacc * 1.05)
        value_high = _calc_dcf(base_revenue, growth * 1.5, margin * 1.15, capex * 0.8, wacc * 0.95)

        # Sanity check
        if value_mid <= 0:
            value_mid = base_revenue * 3.0
            value_low = value_mid * 0.6
            value_high = value_mid * 1.7
            confidence = 0.20

        assumptions = {
            "wacc": wacc,
            "base_revenue_billions": base_revenue,
            "growth_rate": growth,
            "ebitda_margin": margin,
            "terminal_growth": TERMINAL_GROWTH,
        }

    except Exception as exc:
        logger.error(f"[DCF] Gemini call failed: {exc}", exc_info=True)
        base_rev = revenue if revenue > 0 else _estimate_revenue(employees, industry)
        value_mid = base_rev * 3.0
        value_low = value_mid * 0.60
        value_high = value_mid * 1.70
        confidence = 0.20
        assumptions = {"wacc": wacc, "fallback": True, "base_revenue_billions": base_rev, "error": str(exc)[:200]}

    logger.info(f"[DCF] result — low={value_low:,.1f}, mid={value_mid:,.1f}, high={value_high:,.1f}, conf={confidence:.2f}")
    return DCFResult(
        present_value=value_mid,
        value_low=value_low,
        value_mid=value_mid,
        value_high=value_high,
        assumptions=assumptions,
        confidence=confidence,
        tokens_used=tokens_used,
    )
