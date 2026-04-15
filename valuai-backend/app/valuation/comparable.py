"""
Comparable (Market Multiples) Valuation Engine.

Fetches P/E, EV/EBITDA multiples from Fireant API for Vietnamese listed peers.
Falls back to hardcoded industry medians if Fireant is unavailable.

Private company illiquidity discount: 25% (configurable).
"""

import logging
import statistics
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# ─── Fallback industry P/E and EV/EBITDA medians ─────────────────────────────
# Source: Ho Chi Minh Stock Exchange industry averages (approximate)
INDUSTRY_FALLBACK: dict[str, dict[str, float]] = {
    "technology": {"pe": 18.0, "ev_ebitda": 12.0, "ev_revenue": 2.5},
    "retail": {"pe": 14.0, "ev_ebitda": 8.0, "ev_revenue": 0.8},
    "manufacturing": {"pe": 12.0, "ev_ebitda": 7.0, "ev_revenue": 0.6},
    "food_beverage": {"pe": 16.0, "ev_ebitda": 9.0, "ev_revenue": 1.2},
    "real_estate": {"pe": 10.0, "ev_ebitda": 11.0, "ev_revenue": 1.5},
    "healthcare": {"pe": 20.0, "ev_ebitda": 14.0, "ev_revenue": 2.0},
    "education": {"pe": 22.0, "ev_ebitda": 15.0, "ev_revenue": 3.0},
    "logistics": {"pe": 13.0, "ev_ebitda": 8.5, "ev_revenue": 0.7},
    "construction": {"pe": 10.0, "ev_ebitda": 6.0, "ev_revenue": 0.5},
    "agriculture": {"pe": 11.0, "ev_ebitda": 7.0, "ev_revenue": 0.6},
    "finance": {"pe": 12.0, "ev_ebitda": 10.0, "ev_revenue": 2.0},
    "default": {"pe": 13.0, "ev_ebitda": 8.0, "ev_revenue": 1.0},
}


@dataclass
class ComparableResult:
    ev_estimate: float
    value_low: float
    value_mid: float
    value_high: float
    peers: list[dict]
    multiples_used: dict[str, float]
    confidence: float
    source: str  # "fireant" or "fallback"


async def _fetch_fireant_peers(industry_code: str) -> list[dict]:
    """Fetch listed company fundamentals from Fireant API."""
    if not settings.FIREANT_TOKEN:
        return []

    headers = {"Authorization": f"Bearer {settings.FIREANT_TOKEN}"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{settings.FIREANT_BASE_URL}/symbols",
                params={"industryCode": industry_code, "exchange": "HOSE,HNX,UPCOM"},
                headers=headers,
            )
            r.raise_for_status()
            symbols = r.json()

        # Fetch fundamentals for up to 10 peers
        peers = []
        for sym_data in symbols[:10]:
            symbol = sym_data.get("symbol", "")
            if not symbol:
                continue
            try:
                r2 = await httpx.AsyncClient(timeout=10.0).__aenter__()
                resp = await r2.get(
                    f"{settings.FIREANT_BASE_URL}/symbols/{symbol}/fundamental",
                    headers=headers,
                )
                if resp.status_code == 200:
                    peers.append(resp.json())
            except Exception:
                pass

        return peers
    except Exception as exc:
        logger.warning(f"[COMPARABLE] Fireant fetch failed: {exc}")
        return []


def _get_industry_multiples(industry: Optional[str], peers: list[dict]) -> tuple[dict[str, float], float, str]:
    """
    Get median multiples either from Fireant peers or fallback table.
    Returns (multiples_dict, confidence, source).
    """
    if peers and len(peers) >= 3:
        # Extract from Fireant peer data
        pes = [p.get("pe") for p in peers if p.get("pe") and p["pe"] > 0]
        ev_ebitdas = [p.get("evEbitda") for p in peers if p.get("evEbitda") and p["evEbitda"] > 0]

        multiples = {
            "pe": statistics.median(pes) if pes else INDUSTRY_FALLBACK["default"]["pe"],
            "ev_ebitda": statistics.median(ev_ebitdas) if ev_ebitdas else INDUSTRY_FALLBACK["default"]["ev_ebitda"],
            "ev_revenue": INDUSTRY_FALLBACK.get(industry or "default", INDUSTRY_FALLBACK["default"])["ev_revenue"],
            "peer_count": len(peers),
        }
        confidence = min(0.8, 0.5 + len(peers) * 0.06)
        return multiples, confidence, "fireant"
    else:
        # Use hardcoded fallback
        # Try to match industry name
        industry_key = "default"
        if industry:
            ind_lower = industry.lower()
            for key in INDUSTRY_FALLBACK:
                if key in ind_lower or ind_lower in key:
                    industry_key = key
                    break

        multiples = INDUSTRY_FALLBACK.get(industry_key, INDUSTRY_FALLBACK["default"]).copy()
        multiples["peer_count"] = 0
        confidence = 0.35  # lower confidence when using fallback
        return multiples, confidence, "fallback"


async def run_comparable(
    financial_data: dict[str, Any],
    private_discount: float = 0.25,
) -> ComparableResult:
    """
    Run comparable company valuation.

    financial_data: aggregated extraction data.
    private_discount: illiquidity discount (default 25%).
    """
    logger.info(f"[COMPARABLE] run_comparable — private_discount={private_discount:.0%}")

    fin = financial_data.get("financial", {})
    revenue = fin.get("revenue") or 0
    ebitda = fin.get("ebitda") or 0
    profit = fin.get("profit") or 0
    industry = fin.get("industry", "")

    # Try Fireant first (only if token configured)
    peers = []
    if settings.FIREANT_TOKEN:
        # Map industry name to Fireant industry code (simplified mapping)
        industry_code = _map_industry_to_code(industry)
        peers = await _fetch_fireant_peers(industry_code)

    multiples, confidence, source = _get_industry_multiples(industry, peers)

    logger.info(f"[COMPARABLE] multiples source={source}, peers={len(peers)}, confidence={confidence:.2f}")

    # Calculate implied EV using available metrics
    ev_estimates: list[float] = []

    if ebitda and ebitda > 0:
        ev_from_ebitda = ebitda * multiples["ev_ebitda"] * (1 - private_discount)
        ev_estimates.append(ev_from_ebitda)

    if revenue and revenue > 0:
        ev_from_revenue = revenue * multiples["ev_revenue"] * (1 - private_discount)
        ev_estimates.append(ev_from_revenue)

    if profit and profit > 0:
        ev_from_pe = profit * multiples["pe"] * (1 - private_discount)
        ev_estimates.append(ev_from_pe)

    if not ev_estimates:
        # No financial data available
        logger.warning("[COMPARABLE] no financial metrics available for comparable")
        return ComparableResult(
            ev_estimate=0, value_low=0, value_mid=0, value_high=0,
            peers=[], multiples_used=multiples, confidence=0.1, source=source,
        )

    ev_mid = sum(ev_estimates) / len(ev_estimates)
    ev_low = min(ev_estimates) * 0.85
    ev_high = max(ev_estimates) * 1.15

    logger.info(f"[COMPARABLE] result — low={ev_low:,.0f}, mid={ev_mid:,.0f}, high={ev_high:,.0f}")

    return ComparableResult(
        ev_estimate=ev_mid,
        value_low=ev_low,
        value_mid=ev_mid,
        value_high=ev_high,
        peers=peers[:5],  # keep top 5 for display
        multiples_used=multiples,
        confidence=confidence,
        source=source,
    )


def _map_industry_to_code(industry: str) -> str:
    """Simple mapping from industry name to Fireant industry code."""
    mapping = {
        "technology": "IT", "tech": "IT", "software": "IT",
        "retail": "TRADE", "bán lẻ": "TRADE",
        "manufacturing": "MFG", "sản xuất": "MFG",
        "food": "FOOD", "thực phẩm": "FOOD",
        "real_estate": "REAL", "bất động sản": "REAL",
        "healthcare": "HEALTH", "y tế": "HEALTH",
        "finance": "BANK", "tài chính": "BANK",
    }
    if not industry:
        return "TRADE"  # default
    ind_lower = industry.lower()
    for key, code in mapping.items():
        if key in ind_lower:
            return code
    return "TRADE"
