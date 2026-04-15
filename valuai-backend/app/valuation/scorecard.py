"""
Scorecard Valuation Engine — qualitative method using Groq.

Scores 10 criteria (0-10 each), maps weighted total to a revenue multiplier,
and derives an implied enterprise value.

Uses: Groq llama-3.3-70b-versatile for fast JSON scoring.
"""

import logging
from dataclasses import dataclass
from typing import Any

from app.core.ai_clients import groq_json

logger = logging.getLogger(__name__)

# Score → revenue multiplier table
SCORE_TO_MULTIPLIER: list[tuple[float, float]] = [
    (8.0, 3.0),   # score > 8.0 → 3.0× revenue
    (7.0, 2.5),
    (6.0, 2.0),
    (5.0, 1.5),
    (4.0, 1.0),
    (3.0, 0.7),
    (0.0, 0.4),   # score < 3.0 → 0.4× revenue (distressed)
]

CRITERIA_WEIGHTS: dict[str, float] = {
    "team_experience":       0.15,
    "market_size":           0.10,
    "product_uniqueness":    0.12,
    "customer_traction":     0.13,
    "competitive_moat":      0.12,
    "financial_health":      0.12,
    "business_model":        0.10,
    "legal_compliance":      0.08,
    "esg_sustainability":    0.05,
    "growth_potential":      0.13,
}

SCORECARD_SYSTEM_PROMPT = """You are a startup and SME investment analyst scoring a Vietnamese company
for valuation purposes.

Score each criterion from 0 to 10 based on the provided business context:
  0-3 = weak/concerning
  4-6 = average/developing
  7-8 = strong
  9-10 = exceptional

Return ONLY valid JSON in this exact format:
{
  "team_experience": {"score": <0-10>, "reason": "<1 sentence>"},
  "market_size": {"score": <0-10>, "reason": "<1 sentence>"},
  "product_uniqueness": {"score": <0-10>, "reason": "<1 sentence>"},
  "customer_traction": {"score": <0-10>, "reason": "<1 sentence>"},
  "competitive_moat": {"score": <0-10>, "reason": "<1 sentence>"},
  "financial_health": {"score": <0-10>, "reason": "<1 sentence>"},
  "business_model": {"score": <0-10>, "reason": "<1 sentence>"},
  "legal_compliance": {"score": <0-10>, "reason": "<1 sentence>"},
  "esg_sustainability": {"score": <0-10>, "reason": "<1 sentence>"},
  "growth_potential": {"score": <0-10>, "reason": "<1 sentence>"}
}"""


@dataclass
class ScorecardResult:
    total_score: float
    breakdown: dict[str, dict[str, Any]]
    baseline_value: float
    value_low: float
    value_mid: float
    value_high: float
    confidence: float
    tokens_used: int


def _get_multiplier(score: float) -> float:
    """Map weighted score (0-10) to revenue multiplier."""
    for threshold, multiplier in SCORE_TO_MULTIPLIER:
        if score >= threshold:
            return multiplier
    return 0.4


def _weighted_score(breakdown: dict[str, dict[str, Any]]) -> float:
    """Calculate weighted total score from breakdown dict."""
    total = 0.0
    for criterion, weight in CRITERIA_WEIGHTS.items():
        criterion_data = breakdown.get(criterion, {})
        score = float(criterion_data.get("score", 5))
        total += score * weight
    return total


async def run_scorecard(
    financial_data: dict[str, Any],
    qualitative_data: dict[str, Any],
) -> ScorecardResult:
    """
    Run scorecard valuation using Groq for 10-criterion scoring.

    financial_data: merged financial extraction data.
    qualitative_data: merged qualitative extraction data.
    """
    logger.info("[SCORECARD] run_scorecard — calling Groq for scoring")

    fin = financial_data.get("financial", {})
    qual = qualitative_data.get("qualitative", {})

    # Build context for Groq
    revenue = fin.get("revenue") or 0
    context = f"""
FINANCIAL INDICATORS:
- Revenue: {revenue:,.0f} {fin.get('currency', 'VND')}
- Profit: {fin.get('profit') or 'unknown'}
- EBITDA: {fin.get('ebitda') or 'unknown'}
- Employees: {fin.get('employees') or 'unknown'}
- Founded: {fin.get('founding_year') or 'unknown'}
- Growth rate: {(fin.get('growth_rate') or 0):.1%}
- Products: {', '.join(fin.get('products', [])[:5]) or 'not specified'}
- Markets: {', '.join(fin.get('markets', [])[:5]) or 'not specified'}

QUALITATIVE INFORMATION:
- Team strength: {qual.get('team_strength') or 'not provided'}
- Product uniqueness: {qual.get('product_uniqueness') or 'not provided'}
- Market size: {qual.get('market_size') or 'not provided'}
- Competitive moat: {qual.get('competitive_moat') or 'not provided'}
- Customer traction: {qual.get('customer_traction') or 'not provided'}
- Legal status: {qual.get('legal_status') or 'not provided'}
- Key risks: {', '.join(qual.get('key_risks', [])[:4]) or 'not specified'}
- Strategic plans: {', '.join(qual.get('strategic_plans', [])[:4]) or 'not specified'}
"""

    tokens_used = 0
    try:
        breakdown, tokens_used = await groq_json(SCORECARD_SYSTEM_PROMPT, context)
        logger.info(f"[SCORECARD] Groq scoring complete — tokens={tokens_used}")
    except Exception as exc:
        logger.error(f"[SCORECARD] Groq call failed: {exc}")
        # Fallback: neutral scores (5/10 each)
        breakdown = {
            k: {"score": 5, "reason": "Insufficient data for scoring"}
            for k in CRITERIA_WEIGHTS
        }

    total_score = _weighted_score(breakdown)
    multiplier = _get_multiplier(total_score)

    # Base valuation on revenue × multiplier
    base_revenue = max(revenue, 1)  # avoid zero
    baseline = base_revenue * multiplier

    value_mid = baseline
    value_low = baseline * 0.80
    value_high = baseline * 1.20

    # Confidence: higher if more qualitative data was available
    qual_fields_present = sum(
        1 for v in qual.values() if v and v != "not provided" and v != "unknown"
    )
    confidence = min(0.3 + qual_fields_present * 0.08, 0.75)

    logger.info(
        f"[SCORECARD] score={total_score:.2f}/10, multiplier={multiplier}×, "
        f"mid={value_mid:,.0f}, confidence={confidence:.2f}"
    )

    return ScorecardResult(
        total_score=round(total_score, 2),
        breakdown=breakdown,
        baseline_value=baseline,
        value_low=value_low,
        value_mid=value_mid,
        value_high=value_high,
        confidence=confidence,
        tokens_used=tokens_used,
    )
