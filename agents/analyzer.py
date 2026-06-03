"""Agent 4 — Analyzer: pure Python ratio calculations (no LLM)."""
from typing import Any, Optional


def _safe(a, b, default=None):
    try:
        if b is None or b == 0:
            return default
        return a / b
    except Exception:
        return default


def _rating_liquidity(name: str, value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    thresholds = {
        "current_ratio": [(1.5, "good"), (1.0, "warning")],
        "quick_ratio": [(1.0, "good"), (0.7, "warning")],
        "cash_ratio": [(0.5, "good"), (0.2, "warning")],
    }
    for threshold, rating in thresholds.get(name, []):
        if value >= threshold:
            return rating
    return "poor"


def _rating_leverage(name: str, value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    thresholds = {
        "debt_ratio": [(0.4, "good", True), (0.6, "warning", True)],
        "debt_to_equity": [(1.0, "good", True), (2.0, "warning", True)],
        "equity_multiplier": [(2.0, "good", True), (3.0, "warning", True)],
        "interest_coverage": [(3.0, "poor", False), (5.0, "warning", False)],
        "debt_to_ebitda": [(2.0, "good", True), (4.0, "warning", True)],
    }
    cfg = thresholds.get(name)
    if not cfg:
        return "n/a"
    if name == "interest_coverage":
        if value >= 5.0:
            return "good"
        if value >= 3.0:
            return "warning"
        return "poor"
    low_th, low_r, lower_is_better = cfg[0]
    mid_th, mid_r, _ = cfg[1]
    if lower_is_better:
        if value <= low_th:
            return "good"
        if value <= mid_th:
            return "warning"
        return "poor"
    if value >= low_th:
        return "good"
    if value >= mid_th:
        return "warning"
    return "poor"


def _rating_profitability(name: str, value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    thresholds = {
        "gross_margin": [(30, "good"), (15, "warning")],
        "operating_margin": [(15, "good"), (5, "warning")],
        "ebitda_margin": [(20, "good"), (10, "warning")],
        "net_margin": [(10, "good"), (3, "warning")],
        "roa": [(10, "good"), (5, "warning")],
        "roe": [(15, "good"), (8, "warning")],
    }
    for threshold, rating in thresholds.get(name, []):
        if value >= threshold:
            return rating
    return "poor"


def _rating_efficiency(name: str, value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    thresholds = {
        "asset_turnover": [(1.0, "good"), (0.5, "warning")],
        "inventory_turnover": [(4.0, "good"), (2.0, "warning")],
        "receivables_turnover": [(6.0, "good"), (3.0, "warning")],
    }
    for threshold, rating in thresholds.get(name, []):
        if value >= threshold:
            return rating
    return "poor"


def _rv(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
        if cur is None:
            return default
    return cur


def analyze(financials: dict) -> dict:
    bs = financials.get("balance_sheet", {})
    is_ = financials.get("income_statement", {})
    cf = financials.get("cash_flow", {})

    cur_assets = _rv(bs, "current", "assets") or {}
    cur_liab = _rv(bs, "current", "liabilities") or {}
    cur_eq = _rv(bs, "current", "equity") or {}
    cur_income = is_.get("current") or {}
    prev_income = is_.get("previous") or {}
    prev_assets = _rv(bs, "previous", "assets") or {}
    prev_eq = _rv(bs, "previous", "equity") or {}
    cur_cf = cf.get("current") or {}

    cash = cur_assets.get("cash_and_equivalents")
    inv = cur_assets.get("inventory")
    rec = cur_assets.get("short_term_receivables")
    total_cur_assets = cur_assets.get("current_assets_total")
    total_assets = cur_assets.get("total_assets")
    cur_liab_total = cur_liab.get("current_liabilities_total")
    total_liab = cur_liab.get("total_liabilities")
    total_eq = cur_eq.get("total_equity")
    st_debt = cur_liab.get("short_term_debt", 0) or 0
    lt_debt_cur = _rv(bs, "current", "liabilities", "long_term_debt", "default") or 0
    if isinstance(lt_debt_cur, dict):
        lt_debt_cur = 0
    lt_debt = _rv(bs, "current", "liabilities") or {}
    lt_debt = lt_debt.get("long_term_debt", 0) or 0

    revenue = cur_income.get("net_revenue") or cur_income.get("revenue")
    cogs = cur_income.get("cogs")
    gross_profit = cur_income.get("gross_profit")
    op_profit = cur_income.get("operating_profit")
    interest_exp = cur_income.get("interest_expense")
    tax = (cur_income.get("current_tax") or 0) + (cur_income.get("deferred_tax") or 0)
    net_profit = cur_income.get("net_profit_after_tax")
    ebit = op_profit
    dep_est = None

    prev_rev = prev_income.get("net_revenue") or prev_income.get("revenue")
    prev_net = prev_income.get("net_profit_after_tax")
    prev_total_assets = prev_assets.get("total_assets")
    prev_total_eq = prev_eq.get("total_equity")

    fixed_assets_cur = cur_assets.get("fixed_assets", 0) or 0
    fixed_assets_prev = prev_assets.get("fixed_assets", 0) or 0
    dep_est = max(0, (fixed_assets_prev or 0) - (fixed_assets_cur or 0)) if fixed_assets_prev else None

    if ebit is not None and dep_est is not None:
        ebitda = ebit + dep_est
    elif ebit is not None:
        ebitda = ebit
    else:
        ebitda = None

    total_debt = (st_debt or 0) + (lt_debt or 0)
    net_debt = total_debt - (cash or 0)

    # ── Liquidity ─────────────────────────────────────────────────────────────
    quick_assets = (total_cur_assets or 0) - (inv or 0) if total_cur_assets is not None else None
    current_ratio = _safe(total_cur_assets, cur_liab_total)
    quick_ratio = _safe(quick_assets, cur_liab_total)
    cash_ratio = _safe(cash, cur_liab_total)

    # ── Leverage ──────────────────────────────────────────────────────────────
    debt_ratio = _safe(total_liab, total_assets)
    dte = _safe(total_debt, total_eq)
    em = _safe(total_assets, total_eq)
    ic = _safe(ebit, interest_exp) if interest_exp and interest_exp > 0 else None
    dte_ebitda = _safe(total_debt, ebitda) if ebitda and ebitda > 0 else None

    # ── Profitability ─────────────────────────────────────────────────────────
    gm = _safe(gross_profit, revenue) * 100 if gross_profit is not None and revenue else None
    om = _safe(op_profit, revenue) * 100 if op_profit is not None and revenue else None
    ebitda_m = _safe(ebitda, revenue) * 100 if ebitda is not None and revenue else None
    nm = _safe(net_profit, revenue) * 100 if net_profit is not None and revenue else None
    avg_assets = _safe((total_assets or 0) + (prev_total_assets or 0), 2) if prev_total_assets else total_assets
    roa = _safe(net_profit, avg_assets) * 100 if net_profit is not None and avg_assets else None
    avg_eq = _safe((total_eq or 0) + (prev_total_eq or 0), 2) if prev_total_eq else total_eq
    roe = _safe(net_profit, avg_eq) * 100 if net_profit is not None and avg_eq else None

    # ── Efficiency ────────────────────────────────────────────────────────────
    at = _safe(revenue, avg_assets) if avg_assets else _safe(revenue, total_assets)
    inv_turn = _safe(cogs, inv) if inv and inv > 0 else None
    rec_turn = _safe(revenue, rec) if rec and rec > 0 else None

    # ── Growth ────────────────────────────────────────────────────────────────
    rev_growth = _safe((revenue or 0) - (prev_rev or 0), prev_rev) * 100 if prev_rev else None
    np_growth = _safe((net_profit or 0) - (prev_net or 0), prev_net) * 100 if prev_net else None
    asset_growth = _safe((total_assets or 0) - (prev_total_assets or 0), prev_total_assets) * 100 if prev_total_assets else None
    eq_growth = _safe((total_eq or 0) - (prev_total_eq or 0), prev_total_eq) * 100 if prev_total_eq else None

    # ── DuPont ────────────────────────────────────────────────────────────────
    dupont_nm = nm
    dupont_at = at
    dupont_em = em
    dupont_roe = None
    if dupont_nm is not None and dupont_at is not None and dupont_em is not None:
        dupont_roe = (dupont_nm / 100) * dupont_at * dupont_em * 100

    # ── Working capital days ──────────────────────────────────────────────────
    days = 365
    dso = _safe(rec, revenue) * days if rec and revenue else None
    dio = _safe(inv, cogs) * days if inv and cogs else None
    ap = _rv(bs, "current", "liabilities") or {}
    payables = ap.get("accounts_payable")
    dpo = _safe(payables, cogs) * days if payables and cogs else None
    ccc = (dso or 0) + (dio or 0) - (dpo or 0) if dso is not None and dio is not None else None

    # ── Quality of earnings ───────────────────────────────────────────────────
    ocf = cur_cf.get("cf_operating")
    qoe_assessment = "n/a"
    qoe_comment = ""
    accrual_ratio = None
    if net_profit is not None and ocf is not None and total_assets:
        accrual_ratio = _safe((net_profit - ocf), total_assets)
        if ocf >= net_profit:
            qoe_assessment = "good"
            qoe_comment = "OCF ≥ LNST: chất lượng lợi nhuận tốt."
        elif ocf >= net_profit * 0.7:
            qoe_assessment = "warning"
            qoe_comment = "OCF < LNST nhưng chấp nhận được."
        else:
            qoe_assessment = "poor"
            qoe_comment = "OCF thấp hơn nhiều so với LNST: rủi ro lợi nhuận."

    # ── Common size ───────────────────────────────────────────────────────────
    common_size = {}
    if revenue:
        for k, v in cur_income.items():
            if isinstance(v, (int, float)) and v is not None:
                common_size[k] = round(_safe(v, revenue, 0) * 100, 2)

    # ── Normalized EBITDA ─────────────────────────────────────────────────────
    normalized_ebitda = None
    adj_note = ""
    if ebitda is not None:
        normalized_ebitda = ebitda
        cur_admin = cur_income.get("admin_expense")
        prev_admin = prev_income.get("admin_expense")
        if cur_admin and prev_admin and prev_admin > 0:
            admin_change = abs(cur_admin - prev_admin) / prev_admin
            if admin_change > 0.3:
                adj = (cur_admin - prev_admin)
                normalized_ebitda = ebitda - adj
                adj_note = f"Điều chỉnh QLDN biến động {admin_change:.0%}"

    # ── Breakeven ────────────────────────────────────────────────────────────
    breakeven_revenue = None
    if revenue and gross_profit is not None and cogs is not None:
        variable_cost = cogs
        fixed_cost = (cur_income.get("selling_expense") or 0) + (cur_income.get("admin_expense") or 0)
        contribution_margin_ratio = _safe(gross_profit, revenue)
        if contribution_margin_ratio and contribution_margin_ratio > 0:
            breakeven_revenue = _safe(fixed_cost, contribution_margin_ratio)

    def _r(name: str, value, group: str) -> dict:
        v = round(value, 4) if value is not None else None
        fn = {"liquidity": _rating_liquidity,
              "leverage": _rating_leverage,
              "profitability": _rating_profitability,
              "efficiency": _rating_efficiency}.get(group, lambda n, v: "n/a")
        return {"value": v, "rating": fn(name, value)}

    return {
        "ratios": {
            "liquidity": {
                "current_ratio": _r("current_ratio", current_ratio, "liquidity"),
                "quick_ratio": _r("quick_ratio", quick_ratio, "liquidity"),
                "cash_ratio": _r("cash_ratio", cash_ratio, "liquidity"),
            },
            "leverage": {
                "debt_ratio": _r("debt_ratio", debt_ratio, "leverage"),
                "debt_to_equity": _r("debt_to_equity", dte, "leverage"),
                "equity_multiplier": _r("equity_multiplier", em, "leverage"),
                "interest_coverage": _r("interest_coverage", ic, "leverage"),
                "debt_to_ebitda": _r("debt_to_ebitda", dte_ebitda, "leverage"),
            },
            "profitability": {
                "gross_margin": _r("gross_margin", gm, "profitability"),
                "operating_margin": _r("operating_margin", om, "profitability"),
                "ebitda_margin": _r("ebitda_margin", ebitda_m, "profitability"),
                "net_margin": _r("net_margin", nm, "profitability"),
                "roa": _r("roa", roa, "profitability"),
                "roe": _r("roe", roe, "profitability"),
            },
            "efficiency": {
                "asset_turnover": _r("asset_turnover", at, "efficiency"),
                "inventory_turnover": _r("inventory_turnover", inv_turn, "efficiency"),
                "receivables_turnover": _r("receivables_turnover", rec_turn, "efficiency"),
            },
        },
        "growth": {
            "revenue_growth_pct": round(rev_growth, 2) if rev_growth is not None else None,
            "net_profit_growth_pct": round(np_growth, 2) if np_growth is not None else None,
            "total_assets_growth_pct": round(asset_growth, 2) if asset_growth is not None else None,
            "equity_growth_pct": round(eq_growth, 2) if eq_growth is not None else None,
        },
        "dupont": {
            "net_margin": round(dupont_nm, 4) if dupont_nm is not None else None,
            "asset_turnover": round(dupont_at, 4) if dupont_at is not None else None,
            "equity_multiplier": round(dupont_em, 4) if dupont_em is not None else None,
            "roe": round(dupont_roe, 4) if dupont_roe is not None else None,
        },
        "working_capital_days": {
            "dso": round(dso, 2) if dso is not None else None,
            "dio": round(dio, 2) if dio is not None else None,
            "dpo": round(dpo, 2) if dpo is not None else None,
            "ccc": round(ccc, 2) if ccc is not None else None,
        },
        "quality_of_earnings": {
            "net_income": net_profit,
            "cf_operating": ocf,
            "accrual_ratio": round(accrual_ratio, 4) if accrual_ratio is not None else None,
            "assessment": qoe_assessment,
            "comment": qoe_comment,
        },
        "common_size": common_size,
        "normalized_ebitda": {
            "value": round(normalized_ebitda, 2) if normalized_ebitda is not None else None,
            "adjustment_note": adj_note,
        },
        "breakeven": {
            "breakeven_revenue": round(breakeven_revenue, 2) if breakeven_revenue is not None else None,
        },
        "_derived": {
            "ebitda": round(ebitda, 2) if ebitda is not None else None,
            "net_debt": round(net_debt, 2) if net_debt is not None else None,
            "total_debt": round(total_debt, 2),
        },
    }
