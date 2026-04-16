"""
DCF (Discounted Cash Flow) Valuation Engine.

Uses Gemini 2.0 Flash to generate growth scenarios from extracted financial data,
then applies Gordon Growth Model for terminal value.

Vietnamese SME defaults:
  - WACC: 15% (range 12–20%)
  - Long-term growth rate (g): 3%
  - Projection: 5 years
"""

import logging
from dataclasses import dataclass
from typing import Any

from app.core.ai_clients import gemini_json

logger = logging.getLogger(__name__)

DEFAULT_WACC = 0.15
TERMINAL_GROWTH = 0.03
PROJECTION_YEARS = 5


@dataclass
class DCFResult:
    present_value: float
    value_low: float
    value_mid: float
    value_high: float
    assumptions: dict[str, Any]
    confidence: float
    tokens_used: int


DCF_SCENARIO_PROMPT = """You are a senior M&A analyst building a DCF model for a Vietnamese SME.

⚠️ ALL monetary values below are in VND BILLIONS (tỷ đồng).

Company financial snapshot:
{financial_summary}

Vietnamese SME benchmarks by industry:
- Technology/Software: growth 20-40%/yr, EBITDA margin 20-40%, capex 2-5%
- Retail/Trading: growth 8-20%/yr, EBITDA margin 5-12%, capex 2-6%
- Manufacturing: growth 5-15%/yr, EBITDA margin 8-15%, capex 8-15%
- F&B/Restaurant: growth 10-25%/yr, EBITDA margin 10-20%, capex 5-10%
- Education/Edtech: growth 15-35%/yr, EBITDA margin 15-30%, capex 3-8%
- Healthcare: growth 12-25%/yr, EBITDA margin 12-25%, capex 5-12%
- Logistics: growth 8-18%/yr, EBITDA margin 5-10%, capex 8-15%
- General services: growth 8-18%/yr, EBITDA margin 10-20%, capex 3-7%

Task: Generate 3 DCF scenarios (conservative/base/optimistic) for 5 years.
Rules:
- If revenue data exists, base case reflects current trajectory
- If revenue is unknown, ESTIMATE based on employee count and industry (Vietnamese SME avg ~1-3 tỷ/employee/year for services)
- Conservative = base growth × 0.65, compressed margins
- Optimistic = base growth × 1.5, improving margins (EBITDA max 50%)
- WACC for Vietnamese private SME: 14-20% (higher risk = higher WACC)

Return ONLY valid JSON (no markdown):
{{
  "base_revenue_billions": <current revenue in VND billions — estimate if unknown, never 0>,
  "scenarios": {{
    "conservative": {{
      "growth_rates": [<yr1_decimal>, <yr2_decimal>, <yr3_decimal>, <yr4_decimal>, <yr5_decimal>],
      "ebitda_margin": <decimal 0.0-0.5>,
      "capex_ratio": <decimal 0.0-0.2>
    }},
    "base": {{
      "growth_rates": [<yr1>, <yr2>, <yr3>, <yr4>, <yr5>],
      "ebitda_margin": <decimal>,
      "capex_ratio": <decimal>
    }},
    "optimistic": {{
      "growth_rates": [<yr1>, <yr2>, <yr3>, <yr4>, <yr5>],
      "ebitda_margin": <decimal>,
      "capex_ratio": <decimal>
    }}
  }},
  "wacc_recommendation": <recommended WACC decimal, e.g. 0.16 for 16%>,
  "confidence": <0.0-1.0>,
  "data_quality": <"high"|"medium"|"low">,
  "revenue_estimated": <true if revenue was estimated, false if from document>
}}"""


def _project_fcf(
    base_revenue: float,
    growth_rates: list[float],
    ebitda_margin: float,
    capex_ratio: float,
) -> list[float]:
    """Project Free Cash Flow for each year."""
    fcfs: list[float] = []
    revenue = base_revenue
    for g in growth_rates:
        revenue = revenue * (1 + g)
        ebitda = revenue * ebitda_margin
        capex = revenue * capex_ratio
        # FCF = EBITDA - Capex (simplified; ignores working capital changes)
        fcf = ebitda - capex
        fcfs.append(max(fcf, 0))  # FCF cannot be negative in this model
    return fcfs


def _discount_cash_flows(fcfs: list[float], wacc: float) -> float:
    """Sum of discounted FCFs."""
    pv = 0.0
    for t, fcf in enumerate(fcfs, start=1):
        pv += fcf / ((1 + wacc) ** t)
    return pv


def _terminal_value(fcf_final: float, wacc: float, g: float = TERMINAL_GROWTH) -> float:
    """Gordon Growth Model terminal value, discounted to present."""
    if wacc <= g:
        g = wacc * 0.5  # safety: g must be < WACC
    tv = fcf_final * (1 + g) / (wacc - g)
    # Discount terminal value back from year 5
    return tv / ((1 + wacc) ** PROJECTION_YEARS)


async def run_dcf(
    financial_data: dict[str, Any],
    wacc: float = DEFAULT_WACC,
) -> DCFResult:
    """
    Run DCF valuation. Returns DCFResult with low/mid/high range.

    financial_data: aggregated financial extraction from all company documents.
    wacc: Weighted Average Cost of Capital (default 15% for VN SMEs).
    """
    logger.info(f"[DCF] run_dcf — wacc={wacc:.1%}")

    # Build financial summary for Gemini prompt
    fin = financial_data.get("financial", {})
    revenue = fin.get("revenue") or 0
    ebitda = fin.get("ebitda") or 0
    profit = fin.get("profit") or 0
    growth_rate = fin.get("growth_rate") or 0.10
    fiscal_year = fin.get("fiscal_year", "recent")

    summary = f"""
Revenue (fiscal year {fiscal_year}): {revenue:,.0f} (currency: {fin.get('currency', 'VND')})
EBITDA: {ebitda:,.0f}
Net Profit: {profit:,.0f}
Historical growth rate: {growth_rate:.1%}
Industry: {fin.get('industry', 'General')}
Employees: {fin.get('employees', 'Unknown')}
"""

    tokens_used = 0
    confidence = 0.3

    try:
        prompt = DCF_SCENARIO_PROMPT.format(financial_summary=summary)
        scenarios_data, tokens_used = await gemini_json(prompt)

        # Use Gemini's estimated base revenue if extraction produced nothing
        base_revenue = (
            scenarios_data.get("base_revenue_billions")
            or scenarios_data.get("base_revenue")  # backward compat
            or (revenue if revenue and revenue > 0 else None)
        )
        if not base_revenue or base_revenue <= 0:
            # Last resort: rough estimate from employees
            employees = fin.get("employees") or 10
            base_revenue = max(employees * 1.5, 5.0)  # ~1.5 tỷ/employee, min 5 tỷ
            logger.warning(f"[DCF] revenue unknown — using employee-based estimate: {base_revenue:.1f} tỷ")

        scenarios = scenarios_data.get("scenarios", {})
        confidence = float(scenarios_data.get("confidence", 0.35))
        wacc_rec = scenarios_data.get("wacc_recommendation")
        if wacc_rec and 0.08 <= wacc_rec <= 0.35:
            wacc = wacc_rec  # use Gemini's WACC recommendation

        dq = scenarios_data.get("data_quality", "low")
        if dq == "high":
            confidence = min(confidence + 0.15, 0.95)
        elif dq == "low":
            confidence = max(confidence - 0.15, 0.15)
        if scenarios_data.get("revenue_estimated"):
            confidence = max(confidence - 0.10, 0.15)

        results: dict[str, float] = {}
        for scenario_name, params in scenarios.items():
            growth_rates = params.get("growth_rates", [growth_rate or 0.10] * 5)
            ebitda_margin = params.get("ebitda_margin", 0.12)
            capex_ratio = params.get("capex_ratio", 0.05)

            fcfs = _project_fcf(base_revenue, growth_rates, ebitda_margin, capex_ratio)
            pv_fcfs = _discount_cash_flows(fcfs, wacc)
            tv = _terminal_value(fcfs[-1], wacc)
            results[scenario_name] = pv_fcfs + tv

        value_low = results.get("conservative", 0)
        value_mid = results.get("base", 0)
        value_high = results.get("optimistic", 0)

        if value_mid <= 0:
            value_mid = base_revenue * 3.0
            value_low = value_mid * 0.65
            value_high = value_mid * 1.6
            confidence = max(confidence - 0.10, 0.15)

        assumptions = {
            "wacc": wacc,
            "terminal_growth": TERMINAL_GROWTH,
            "base_revenue_billions": base_revenue,
            "scenarios": scenarios,
            "data_quality": dq,
        }

    except Exception as exc:
        logger.error(f"[DCF] Gemini scenario generation failed: {exc}", exc_info=True)
        base_rev = revenue if revenue and revenue > 0 else 10.0  # 10 tỷ minimum estimate
        value_mid = base_rev * 3.0
        value_low = value_mid * 0.60
        value_high = value_mid * 1.70
        confidence = 0.15
        assumptions = {"wacc": wacc, "fallback": True, "base_revenue_billions": base_rev, "error": str(exc)[:200]}

    logger.info(f"[DCF] result — low={value_low:,.0f}, mid={value_mid:,.0f}, high={value_high:,.0f}, conf={confidence:.2f}")

    return DCFResult(
        present_value=value_mid,
        value_low=value_low,
        value_mid=value_mid,
        value_high=value_high,
        assumptions=assumptions,
        confidence=confidence,
        tokens_used=tokens_used,
    )
