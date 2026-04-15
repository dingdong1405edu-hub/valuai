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
import math
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


DCF_SCENARIO_PROMPT = """You are a financial analyst building a DCF model for a Vietnamese SME.

Company financial data:
{financial_summary}

Your task: Generate THREE cash flow projection scenarios (conservative, base, optimistic) for 5 years.

Rules:
- Use Vietnamese market context: high-growth sectors 15-30%, stable 5-15%, declining 0-5%
- EBITDA margins: manufacturing 8-15%, services 15-25%, tech 20-40%
- Base case should reflect current trajectory
- Conservative = base × 0.7 growth rate
- Optimistic = base × 1.4 growth rate

Return ONLY this JSON:
{{
  "base_revenue": <current annual revenue in VND billions>,
  "scenarios": {{
    "conservative": {{
      "growth_rates": [<yr1>, <yr2>, <yr3>, <yr4>, <yr5>],
      "ebitda_margin": <decimal>,
      "capex_ratio": <capex as % of revenue decimal>
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
  "confidence": <0.0-1.0 based on data quality>,
  "data_quality": <"high"|"medium"|"low">
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
    confidence = 0.4  # default: low confidence

    try:
        prompt = DCF_SCENARIO_PROMPT.format(financial_summary=summary)
        scenarios_data, tokens_used = await gemini_json(prompt)

        base_revenue = scenarios_data.get("base_revenue") or max(revenue, 1)
        scenarios = scenarios_data.get("scenarios", {})
        confidence = float(scenarios_data.get("confidence", 0.4))

        # Adjust confidence based on data quality
        dq = scenarios_data.get("data_quality", "low")
        if dq == "high":
            confidence = min(confidence + 0.2, 1.0)
        elif dq == "low":
            confidence = max(confidence - 0.2, 0.1)

        results: dict[str, float] = {}
        for scenario_name, params in scenarios.items():
            growth_rates = params.get("growth_rates", [growth_rate] * 5)
            ebitda_margin = params.get("ebitda_margin", 0.10)
            capex_ratio = params.get("capex_ratio", 0.05)

            fcfs = _project_fcf(base_revenue, growth_rates, ebitda_margin, capex_ratio)
            pv_fcfs = _discount_cash_flows(fcfs, wacc)
            tv = _terminal_value(fcfs[-1], wacc)
            enterprise_value = pv_fcfs + tv
            results[scenario_name] = enterprise_value

        value_low = results.get("conservative", 0)
        value_mid = results.get("base", 0)
        value_high = results.get("optimistic", 0)

        # Sanity check: if mid is 0 fall back to revenue multiple
        if value_mid == 0 and revenue > 0:
            value_mid = revenue * 2
            value_low = value_mid * 0.7
            value_high = value_mid * 1.5
            confidence = 0.2

        assumptions = {
            "wacc": wacc,
            "terminal_growth": TERMINAL_GROWTH,
            "base_revenue": base_revenue,
            "scenarios": scenarios,
            "data_quality": dq,
        }

    except Exception as exc:
        logger.error(f"[DCF] Gemini scenario generation failed: {exc}")
        # Fallback: simple revenue multiple if AI call fails
        base_rev = max(revenue, 1)
        value_mid = base_rev * 2.5
        value_low = value_mid * 0.6
        value_high = value_mid * 1.6
        confidence = 0.15
        assumptions = {"wacc": wacc, "fallback": True, "error": str(exc)[:200]}

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
