"""Agent 6 — Valuator: hybrid LLM assumptions + Python DCF/Multiples."""
from agent_common import call_opus, parse_json_response, with_locked_schema

_SENTINEL = "TRẢ VỀ JSON (không markdown, chỉ assumptions):"

_ASSUMPTIONS_SCHEMA = """{
  "wacc_pct": 0.0,
  "wacc_breakdown": {
    "risk_free_rate_pct": 0.0,
    "equity_risk_premium_pct": 0.0,
    "beta": 0.0,
    "size_premium_pct": 0.0,
    "country_risk_pct": 0.0,
    "total_cost_of_equity_pct": 0.0,
    "cost_of_debt_pct": 0.0,
    "tax_shield_pct": 0.0,
    "after_tax_cost_of_debt_pct": 0.0,
    "debt_weight_pct": 0.0,
    "equity_weight_pct": 0.0
  },
  "terminal_growth_pct": 0.0,
  "terminal_growth_rationale": "...",
  "ev_ebitda_multiple": 0.0,
  "ev_ebitda_rationale": "...",
  "pe_multiple": 0.0,
  "pe_rationale": "...",
  "pb_multiple": 0.0,
  "pb_rationale": "...",
  "multiples_trading_vs_transaction": "...",
  "comparable_companies": [
    {"name": "...", "ev_ebitda": 0.0, "pe": 0.0, "pb": 0.0,
     "revenue_vnd_b": 0.0, "note": ""}
  ],
  "valuation_method_recommendation": "...",
  "weighting_rationale": "...",
  "minority_discount_pct": 20.0,
  "minority_discount_rationale": "..."
}"""

_DEFAULT_PREAMBLE = """Bạn là chuyên gia định giá doanh nghiệp M&A thị trường Việt Nam.

THÔNG TIN DOANH NGHIỆP:
- Ngành: {industry_name}
- EBITDA: {ebitda} {unit}
- ROE: {roe}%
- D/E ratio: {dte}x
- Tăng trưởng doanh thu YoY: {rev_growth}%
- Tăng trưởng EBITDA 5 năm dự phóng: {ebitda_cagr}%
- Tổng nợ vay: {total_debt} {unit}
- Tiền mặt: {cash} {unit}
- Vốn chủ sở hữu sổ sách: {book_equity} {unit}
- Lợi nhuận ròng: {net_income} {unit}
- CAGR ngành: {industry_cagr}%

Hãy xác định các assumptions định giá phù hợp:
1. WACC theo CAPM (điều chỉnh Việt Nam: lãi suất phi rủi ro ~4.5%, ERP ~7%, country risk ~1.5%)
2. Terminal growth rate phù hợp GDP dài hạn Việt Nam (~4-5%)
3. Bội số EV/EBITDA, P/E, P/B theo ngành và so sánh thị trường
4. Minority discount (thường 20-30% cho SME)
"""


def _claude_assumptions(financials: dict, ratios: dict, industry: dict,
                         projection: dict, prompt_override: str,
                         api_key: str = None) -> dict:
    company = financials.get("company", {})
    income_cur = financials.get("income_statement", {}).get("current", {})
    bs_cur = (financials.get("balance_sheet", {}).get("current") or {})
    cur_assets = bs_cur.get("assets") or {}
    unit = financials.get("unit", "triệu đồng")

    ind = industry.get("industry", industry) if isinstance(industry, dict) else {}
    proj = projection.get("projection", projection) if isinstance(projection, dict) else {}
    summary = proj.get("summary_5y", {})

    r = ratios.get("ratios", ratios) if isinstance(ratios, dict) else {}
    prof = r.get("profitability", {})
    lev = r.get("leverage", {})
    derived = ratios.get("_derived", {})

    ctx = {
        "industry_name": ind.get("industry_name", company.get("industry", "N/A")),
        "ebitda": derived.get("ebitda", 0),
        "unit": unit,
        "roe": (prof.get("roe") or {}).get("value", 0),
        "dte": (lev.get("debt_to_equity") or {}).get("value", 0),
        "rev_growth": ratios.get("growth", {}).get("revenue_growth_pct", 0),
        "ebitda_cagr": summary.get("ebitda_cagr_pct", 0),
        "total_debt": derived.get("total_debt", 0),
        "cash": cur_assets.get("cash_and_equivalents", 0),
        "book_equity": (bs_cur.get("equity") or {}).get("total_equity", 0),
        "net_income": income_cur.get("net_profit_after_tax", 0),
        "industry_cagr": ind.get("industry_cagr_5y_pct", 8),
    }

    preamble = prompt_override.strip() if prompt_override and prompt_override.strip() else _DEFAULT_PREAMBLE.format(**ctx)
    full_prompt = f"{preamble}\n\n{_SENTINEL}\n{_ASSUMPTIONS_SCHEMA}"

    raw = call_opus(
        full_prompt,
        system="You are a Vietnamese M&A valuation expert. Always respond with valid JSON only.",
        max_tokens=8000,
        effort="medium",
    )
    return parse_json_response(raw)


def _dcf_valuation(projection: dict, wacc: float, terminal_growth: float,
                    net_debt: float) -> dict:
    proj = projection.get("projection", projection) if isinstance(projection, dict) else {}
    projections = proj.get("projections", [])

    fcffs = [p.get("fcff", 0) or 0 for p in projections]
    n = len(fcffs)
    if n == 0:
        return {}

    w = wacc / 100
    g = terminal_growth / 100

    pv_fcff = sum(fcffs[i] / (1 + w) ** (i + 1) for i in range(n))

    fcff_last = fcffs[-1] if fcffs else 0
    if w <= g:
        terminal_value = 0
    else:
        terminal_value = fcff_last * (1 + g) / (w - g)

    pv_tv = terminal_value / (1 + w) ** n
    enterprise_value = pv_fcff + pv_tv
    equity_value = enterprise_value - net_debt

    return {
        "pv_fcff": round(pv_fcff, 2),
        "terminal_value": round(terminal_value, 2),
        "pv_terminal_value": round(pv_tv, 2),
        "enterprise_value": round(enterprise_value, 2),
        "net_debt": round(net_debt, 2),
        "equity_value": round(equity_value, 2),
    }


def _multiples_valuation(financials: dict, ratios: dict, projection: dict,
                          assumptions: dict) -> dict:
    income_cur = financials.get("income_statement", {}).get("current", {})
    bs_cur = (financials.get("balance_sheet", {}).get("current") or {})
    derived = ratios.get("_derived", {})

    ebitda = derived.get("ebitda", 0) or 0
    net_income = income_cur.get("net_profit_after_tax", 0) or 0
    book_equity = (bs_cur.get("equity") or {}).get("total_equity", 0) or 0
    net_debt = derived.get("net_debt", 0) or 0

    ev_ebitda_m = assumptions.get("ev_ebitda_multiple", 8.0) or 8.0
    pe_m = assumptions.get("pe_multiple", 12.0) or 12.0
    pb_m = assumptions.get("pb_multiple", 2.0) or 2.0

    ev_ebitda_ev = ebitda * ev_ebitda_m
    ev_ebitda_eq = ev_ebitda_ev - net_debt

    pe_eq = net_income * pe_m
    pb_eq = book_equity * pb_m

    return {
        "ev_ebitda": {
            "ebitda": ebitda,
            "multiple": ev_ebitda_m,
            "enterprise_value": round(ev_ebitda_ev, 2),
            "equity_value": round(ev_ebitda_eq, 2),
        },
        "pe": {
            "net_income": net_income,
            "multiple": pe_m,
            "equity_value": round(pe_eq, 2),
        },
        "pb": {
            "book_value": book_equity,
            "multiple": pb_m,
            "equity_value": round(pb_eq, 2),
        },
    }


def _sensitivity(projection: dict, wacc_base: float, g_base: float,
                  net_debt: float) -> dict:
    steps = [-2, -1, 0, 1, 2]
    wacc_range = [round(wacc_base + s * 0.5, 2) for s in steps]
    g_range = [round(g_base + s * 0.5, 2) for s in steps]

    matrix = []
    for w in wacc_range:
        row = []
        for g in g_range:
            dcf = _dcf_valuation(projection, w, g, net_debt)
            row.append(round(dcf.get("equity_value", 0), 0))
        matrix.append(row)

    return {"wacc_range": wacc_range, "g_range": g_range, "matrix": matrix}


def _scenario_analysis(projection: dict, wacc: float, g: float,
                         net_debt: float) -> dict:
    proj = projection.get("projection", projection) if isinstance(projection, dict) else {}
    projections = proj.get("projections", [])

    def _adj(factor: float) -> dict:
        adj_proj = {
            "projection": {
                **proj,
                "projections": [
                    {**p, "fcff": round((p.get("fcff", 0) or 0) * factor, 2)}
                    for p in projections
                ],
            }
        }
        return _dcf_valuation(adj_proj, wacc, g, net_debt)

    bull = _adj(1.25)
    base = _dcf_valuation(projection, wacc, g, net_debt)
    bear = _adj(0.70)

    return {
        "bull": {**bull, "fcff_adj": "+25%", "description": "Tăng trưởng vượt kỳ vọng"},
        "base": {**base, "fcff_adj": "Base", "description": "Kịch bản cơ sở"},
        "bear": {**bear, "fcff_adj": "-30%", "description": "Suy giảm thị trường"},
    }


def _football_field(dcf: dict, multiples: dict) -> list:
    def _range(val: float, spread: float = 0.15):
        return round(val * (1 - spread), 0), round(val, 0), round(val * (1 + spread), 0)

    rows = []
    if dcf.get("equity_value"):
        lo, mid, hi = _range(dcf["equity_value"])
        rows.append({"method": "DCF", "low": lo, "mid": mid, "high": hi})

    if multiples.get("ev_ebitda", {}).get("equity_value"):
        lo, mid, hi = _range(multiples["ev_ebitda"]["equity_value"])
        rows.append({"method": "EV/EBITDA", "low": lo, "mid": mid, "high": hi})

    if multiples.get("pe", {}).get("equity_value"):
        lo, mid, hi = _range(multiples["pe"]["equity_value"])
        rows.append({"method": "P/E", "low": lo, "mid": mid, "high": hi})

    if multiples.get("pb", {}).get("equity_value"):
        lo, mid, hi = _range(multiples["pb"]["equity_value"])
        rows.append({"method": "P/B", "low": lo, "mid": mid, "high": hi})

    return rows


def _waterfall_bridge(enterprise_value: float, total_debt: float,
                       cash: float) -> dict:
    equity = enterprise_value - total_debt + cash
    return {
        "enterprise_value": round(enterprise_value, 2),
        "less_debt": round(-total_debt, 2),
        "plus_cash": round(cash, 2),
        "equity_value": round(equity, 2),
    }


def _build_summary(football_field: list, minority_discount_pct: float) -> dict:
    all_lows = [r["low"] for r in football_field]
    all_highs = [r["high"] for r in football_field]
    all_mids = [r["mid"] for r in football_field]

    fv_low = round(min(all_lows), 0) if all_lows else 0
    fv_high = round(max(all_highs), 0) if all_highs else 0
    fv_mid = round(sum(all_mids) / len(all_mids), 0) if all_mids else 0

    disc = minority_discount_pct / 100
    return {
        "fair_value_low": fv_low,
        "fair_value_mid": fv_mid,
        "fair_value_high": fv_high,
        "minority_discount_pct": minority_discount_pct,
        "fair_value_minority_low": round(fv_low * (1 - disc), 0),
        "fair_value_minority_mid": round(fv_mid * (1 - disc), 0),
        "fair_value_minority_high": round(fv_high * (1 - disc), 0),
    }


def value(financials: dict, ratios: dict, industry: dict, projection: dict,
          prompt_override: str = "", api_key: str = None) -> dict:
    assumptions = _claude_assumptions(
        financials, ratios, industry, projection, prompt_override, api_key
    )

    derived = ratios.get("_derived", {})
    net_debt = derived.get("net_debt", 0) or 0
    total_debt = derived.get("total_debt", 0) or 0
    cash = (financials.get("balance_sheet", {}).get("current") or {})
    cash = (cash.get("assets") or {}).get("cash_and_equivalents", 0) or 0

    wacc = assumptions.get("wacc_pct", 14.0)
    terminal_growth = assumptions.get("terminal_growth_pct", 4.0)
    minority_discount = assumptions.get("minority_discount_pct", 20.0)

    dcf = _dcf_valuation(projection, wacc, terminal_growth, net_debt)
    multiples = _multiples_valuation(financials, ratios, projection, assumptions)
    sensitivity = _sensitivity(projection, wacc, terminal_growth, net_debt)
    scenarios = _scenario_analysis(projection, wacc, terminal_growth, net_debt)
    football_field = _football_field(dcf, multiples)
    waterfall = _waterfall_bridge(
        dcf.get("enterprise_value", 0), total_debt, cash
    )
    summary = _build_summary(football_field, minority_discount)

    return {
        "valuation": {
            "assumptions": assumptions,
            "dcf": dcf,
            "multiples": multiples,
            "sensitivity": sensitivity,
            "scenarios": scenarios,
            "football_field": football_field,
            "waterfall": waterfall,
            "summary": summary,
        }
    }
