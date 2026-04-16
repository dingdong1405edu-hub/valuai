"""
Valuation Orchestrator — coordinates the full valuation pipeline.

Flow:
  1. Aggregate all extractions for a company
  2. Run DCF + Comparable + Scorecard in PARALLEL (asyncio.gather)
  3. Synthesize with Gemini 2.5 Flash + RAG context from pgvector
  4. Persist results to valuations table

AI routing:
  DCF       → Gemini (simple 4-param JSON, deterministic math in Python)
  Comparable → Groq + Fireant data
  Scorecard  → Groq
  Synthesis  → Gemini
"""

import asyncio
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_clients import gemini_json
from app.db.models import Extraction, Valuation
from app.ingestion.embedder import semantic_search
from app.valuation.dcf import run_dcf, DEFAULT_WACC
from app.valuation.comparable import run_comparable
from app.valuation.scorecard import run_scorecard

logger = logging.getLogger(__name__)

BASE_WEIGHTS = {"dcf": 0.45, "comparable": 0.35, "scorecard": 0.20}

SYNTHESIS_PROMPT = """You are a senior M&A advisor writing a business valuation report for a Vietnamese SME.

Valuation method results (all values in VND billions unless stated):
- DCF Method: mid = {dcf_mid:,.1f}, range [{dcf_low:,.1f} — {dcf_high:,.1f}], confidence = {dcf_conf:.0%}
- Comparable Method: mid = {comp_mid:,.1f}, range [{comp_low:,.1f} — {comp_high:,.1f}], confidence = {comp_conf:.0%}
- Scorecard Method: score = {score_total:.1f}/10, mid = {score_mid:,.1f}, confidence = {score_conf:.0%}
- SYNTHESIZED FINAL RANGE: min = {final_min:,.1f}, mid = {final_mid:,.1f}, max = {final_max:,.1f}

Business context from documents:
{rag_context}

Write a professional valuation analysis in English. Return ONLY valid JSON:
{{
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "weaknesses": ["<weakness 1>", "<weakness 2>"],
  "opportunities": ["<opportunity 1>", "<opportunity 2>", "<opportunity 3>"],
  "threats": ["<threat 1>", "<threat 2>"],
  "recommendations": [
    "<actionable recommendation to increase valuation 1>",
    "<actionable recommendation 2>",
    "<actionable recommendation 3>"
  ],
  "executive_summary": "<150-200 word narrative explaining the valuation range, key value drivers, and main risks. Professional M&A tone.>"
}}"""


async def _aggregate_extractions(company_id: str, session: AsyncSession) -> dict[str, Any]:
    """Merge all extraction data for a company into a single aggregated dict."""
    result = await session.execute(
        select(Extraction).where(Extraction.company_id == company_id)
    )
    extractions = result.scalars().all()

    merged: dict[str, Any] = {"financial": {}, "qualitative": {}}

    for ext in extractions:
        data = ext.data or {}
        fin = data.get("financial", {})
        qual = data.get("qualitative", {})

        for k, v in fin.items():
            if v is not None and merged["financial"].get(k) is None:
                merged["financial"][k] = v
            elif v is not None and isinstance(v, (int, float)) and v > 0:
                merged["financial"][k] = v

        for k, v in qual.items():
            if v is None:
                continue
            if isinstance(v, list):
                existing = merged["qualitative"].get(k, [])
                merged["qualitative"][k] = list(set(existing + v))
            elif isinstance(v, str) and v.strip():
                if not merged["qualitative"].get(k):
                    merged["qualitative"][k] = v

    logger.info(f"[ORCHESTRATOR] aggregated {len(extractions)} extractions for company={company_id}")
    logger.info(f"[ORCHESTRATOR] merged financial keys: {list(merged['financial'].keys())}")
    logger.info(
        f"[ORCHESTRATOR] revenue={merged['financial'].get('revenue')}, "
        f"profit={merged['financial'].get('profit')}, "
        f"employees={merged['financial'].get('employees')}"
    )
    return merged


def _synthesize_range(
    dcf_mid: float, dcf_low: float, dcf_high: float, dcf_conf: float,
    comp_mid: float, comp_low: float, comp_high: float, comp_conf: float,
    score_mid: float, score_low: float, score_high: float, score_conf: float,
) -> tuple[float, float, float]:
    """
    Confidence-weighted synthesis of three valuation methods.
    All methods included (no exclusion threshold) — low confidence gets low weight.
    Returns (final_min, final_mid, final_max).
    """
    methods = [
        ("dcf",        dcf_mid,   dcf_low,   dcf_high,   dcf_conf),
        ("comparable", comp_mid,  comp_low,  comp_high,  comp_conf),
        ("scorecard",  score_mid, score_low, score_high, score_conf),
    ]

    # Only exclude methods where mid value is literally 0
    valid = [(name, mid, low, high, conf) for name, mid, low, high, conf in methods if mid > 0]

    if not valid:
        logger.warning("[ORCHESTRATOR] all methods returned 0 — using minimum fallback")
        return 5.0, 10.0, 20.0  # absolute minimum: 10 tỷ mid

    # Confidence × base_weight — use 0.1 as minimum so no method is completely ignored
    raw_weights = {
        name: max(conf, 0.10) * BASE_WEIGHTS[name]
        for name, mid, low, high, conf in valid
    }
    total_w = sum(raw_weights.values())
    norm_weights = {k: v / total_w for k, v in raw_weights.items()}

    final_mid = sum(
        mid * norm_weights[name]
        for name, mid, low, high, conf in valid
    )
    final_min = min(low for _, _, low, _, _ in valid) * 0.90
    final_max = max(high for _, _, _, high, _ in valid) * 1.10

    logger.info(
        f"[ORCHESTRATOR] synthesis weights: {norm_weights}, "
        f"final=[{final_min:,.1f}, {final_mid:,.1f}, {final_max:,.1f}]"
    )
    return final_min, final_mid, final_max


async def run_full_valuation(
    company_id: str,
    session: AsyncSession,
    wacc: float = DEFAULT_WACC,
    private_discount: float = 0.25,
) -> Valuation:
    """Full valuation pipeline. Creates/updates a Valuation record and returns it."""
    logger.info(f"[ORCHESTRATOR] run_full_valuation — company={company_id}")

    result = await session.execute(
        select(Valuation).where(Valuation.company_id == company_id)
        .order_by(Valuation.created_at.desc())
        .limit(1)
    )
    valuation = result.scalar_one_or_none()
    if not valuation:
        valuation = Valuation(company_id=company_id)
        session.add(valuation)

    valuation.status = "running"
    await session.commit()

    try:
        # Step 1: Aggregate extractions
        agg_data = await _aggregate_extractions(company_id, session)

        # Step 2: Run 3 methods in parallel
        logger.info("[ORCHESTRATOR] launching DCF + Comparable + Scorecard in parallel")
        dcf_result, comp_result, score_result = await asyncio.gather(
            run_dcf(agg_data, wacc=wacc),
            run_comparable(agg_data, private_discount=private_discount),
            run_scorecard(agg_data, agg_data),
            return_exceptions=True,
        )

        if isinstance(dcf_result, Exception):
            logger.error(f"[ORCHESTRATOR] DCF failed: {dcf_result}")
            dcf_result = None
        if isinstance(comp_result, Exception):
            logger.error(f"[ORCHESTRATOR] Comparable failed: {comp_result}")
            comp_result = None
        if isinstance(score_result, Exception):
            logger.error(f"[ORCHESTRATOR] Scorecard failed: {score_result}")
            score_result = None

        # Step 3: Extract values (0 if method failed)
        dcf_mid   = dcf_result.value_mid    if dcf_result   else 0
        dcf_low   = dcf_result.value_low    if dcf_result   else 0
        dcf_high  = dcf_result.value_high   if dcf_result   else 0
        dcf_conf  = dcf_result.confidence   if dcf_result   else 0

        comp_mid  = comp_result.value_mid   if comp_result  else 0
        comp_low  = comp_result.value_low   if comp_result  else 0
        comp_high = comp_result.value_high  if comp_result  else 0
        comp_conf = comp_result.confidence  if comp_result  else 0

        score_mid  = score_result.value_mid  if score_result else 0
        score_low  = score_result.value_low  if score_result else 0
        score_high = score_result.value_high if score_result else 0
        score_conf = score_result.confidence if score_result else 0

        logger.info(
            f"[ORCHESTRATOR] method results — "
            f"DCF={dcf_mid:,.1f}(conf={dcf_conf:.2f}), "
            f"Comp={comp_mid:,.1f}(conf={comp_conf:.2f}), "
            f"Score={score_mid:,.1f}(conf={score_conf:.2f})"
        )

        # Step 4: Synthesize
        final_min, final_mid, final_max = _synthesize_range(
            dcf_mid, dcf_low, dcf_high, dcf_conf,
            comp_mid, comp_low, comp_high, comp_conf,
            score_mid, score_low, score_high, score_conf,
        )

        # Step 5: RAG context for Gemini synthesis
        rag_chunks = await semantic_search(
            session, "company strengths products revenue growth competitive advantage",
            company_id, top_k=8,
        )
        rag_context = "\n---\n".join(c["content"] for c in rag_chunks)
        if not rag_context:
            fin = agg_data.get("financial", {})
            qual = agg_data.get("qualitative", {})
            rag_context = f"Financial data: {fin}\nQualitative data: {qual}"

        # Step 6: Gemini synthesis — SWOT + recommendations
        prompt = SYNTHESIS_PROMPT.format(
            dcf_mid=dcf_mid, dcf_low=dcf_low, dcf_high=dcf_high, dcf_conf=dcf_conf,
            comp_mid=comp_mid, comp_low=comp_low, comp_high=comp_high, comp_conf=comp_conf,
            score_total=score_result.total_score if score_result else 5.0,
            score_mid=score_mid, score_conf=score_conf,
            final_min=final_min, final_mid=final_mid, final_max=final_max,
            rag_context=rag_context[:6000],
        )

        synthesis_tokens = 0
        try:
            synthesis, synthesis_tokens = await gemini_json(prompt)
            strengths        = synthesis.get("strengths", [])
            weaknesses       = synthesis.get("weaknesses", [])
            opportunities    = synthesis.get("opportunities", [])
            threats          = synthesis.get("threats", [])
            recommendations  = synthesis.get("recommendations", [])
            executive_summary = synthesis.get("executive_summary", "")
        except Exception as exc:
            logger.error(f"[ORCHESTRATOR] Gemini synthesis failed: {exc}")
            strengths = weaknesses = opportunities = threats = recommendations = []
            executive_summary = "Report synthesis unavailable."

        # Step 7: Persist
        total_tokens = (
            (dcf_result.tokens_used if dcf_result else 0)
            + (score_result.tokens_used if score_result else 0)
            + synthesis_tokens
        )

        valuation.dcf_value           = dcf_mid or None
        valuation.dcf_assumptions     = dcf_result.assumptions if dcf_result else {}
        valuation.dcf_confidence      = dcf_conf

        valuation.comparable_value    = comp_mid or None
        valuation.comparable_peers    = comp_result.peers if comp_result else []
        valuation.comparable_confidence = comp_conf

        valuation.scorecard_value     = score_mid or None
        valuation.scorecard_breakdown = score_result.breakdown if score_result else {}
        valuation.scorecard_total     = score_result.total_score if score_result else 0
        valuation.scorecard_confidence = score_conf

        valuation.final_range_min     = final_min or None
        valuation.final_range_mid     = final_mid or None
        valuation.final_range_max     = final_max or None

        valuation.strengths           = strengths
        valuation.weaknesses          = weaknesses
        valuation.opportunities       = opportunities
        valuation.threats             = threats
        valuation.recommendations     = recommendations
        valuation.report_text         = executive_summary
        valuation.model_used          = "gemini-2.5-flash + groq/deepseek-r1 + groq/llama-3.3-70b"
        valuation.tokens_used         = total_tokens
        valuation.status              = "completed"

        await session.commit()
        await session.refresh(valuation)

        logger.info(
            f"[ORCHESTRATOR] DONE — id={valuation.id}, "
            f"range=[{final_min:,.1f}, {final_mid:,.1f}, {final_max:,.1f}]"
        )
        return valuation

    except Exception as exc:
        logger.error(f"[ORCHESTRATOR] pipeline FAILED: {exc}", exc_info=True)
        try:
            await session.rollback()
            valuation.status = "failed"
            valuation.error_msg = str(exc)[:500]
            await session.commit()
        except Exception as commit_exc:
            logger.error(f"[ORCHESTRATOR] could not save failed status: {commit_exc}")
        raise
