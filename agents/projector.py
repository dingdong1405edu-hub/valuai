"""Agent 5 — Projector: financials + ratios + industry → 5-year projection."""
from agent_common import build_prompt, call_opus, parse_json_response

_SCHEMA_BLOCK = """Return ONLY valid JSON:
{
  "projection": {
    "base_year_label": "20XX",
    "assumptions": {
      "revenue_growth_pct": [0, 0, 0, 0, 0],
      "growth_rationale": "...",
      "gross_margin_pct": [0, 0, 0, 0, 0],
      "operating_expense_pct_revenue": [0, 0, 0, 0, 0],
      "tax_rate_pct": 20.0,
      "depreciation_pct_revenue": [0, 0, 0, 0, 0],
      "capex_pct_revenue": [0, 0, 0, 0, 0],
      "working_capital_days": {"dso": 0, "dio": 0, "dpo": 0},
      "rationale_capex": "...",
      "rationale_wc": "..."
    },
    "projections": [
      {
        "year_index": 1, "year_label": "20XX",
        "revenue": 0, "growth_pct": 0,
        "cogs": 0, "gross_profit": 0,
        "operating_expense": 0, "ebit": 0,
        "depreciation": 0, "ebitda": 0,
        "interest_expense": 0,
        "profit_before_tax": 0, "tax": 0,
        "net_income": 0,
        "capex": 0, "change_in_wc": 0, "fcff": 0,
        "ebitda_margin_pct": 0, "net_margin_pct": 0
      }
    ],
    "summary_5y": {
      "revenue_cagr_pct": 0.0,
      "ebitda_cagr_pct": 0.0,
      "fcff_cumulative": 0,
      "comments": "..."
    }
  }
}"""

_DEFAULT_PREAMBLE = """Bạn là chuyên gia mô hình tài chính và dự phóng doanh nghiệp Việt Nam.

DỮ LIỆU NĂM CƠ SỞ:
- Kỳ báo cáo: {period_label}
- Doanh thu thuần: {cur_revenue} {unit}
- COGS: {cogs} {unit}
- Lợi nhuận gộp: {gross_profit} {unit}
- Chi phí bán hàng: {selling_expense} {unit}
- Chi phí QLDN: {admin_expense} {unit}
- EBIT: {ebit} {unit}
- Chi phí lãi vay: {interest_expense} {unit}
- Thuế TNDN: {current_tax} {unit}
- Lợi nhuận ròng: {net_profit} {unit}
- Tài sản cố định: {fixed_assets} {unit}
- Tổng tài sản: {total_assets} {unit}
- Hàng tồn kho: {inventory} {unit}
- Phải thu: {receivables} {unit}
- Doanh thu kỳ trước: {prev_revenue} {unit}
- LNST kỳ trước: {prev_net_profit} {unit}
- Tăng trưởng doanh thu YoY: {revenue_yoy}%
- CAGR ngành 5 năm: {industry_cagr}%

YÊU CẦU DỰ PHÓNG 5 NĂM:
1. Tăng trưởng doanh thu theo S-curve (giảm dần từ năm 1 → 5)
2. FCFF = EBIT × (1 - thuế%) + Khấu hao - CAPEX - ΔVốn lưu động
3. Các giả định phải có cơ sở từ dữ liệu lịch sử và xu hướng ngành
4. Tính đủ 5 năm projection (year_index 1..5)
"""


def project(financials: dict, ratios: dict, industry: dict,
            prompt_override: str = "", api_key: str = None) -> dict:
    company = financials.get("company", {})
    income_cur = financials.get("income_statement", {}).get("current", {})
    income_prev = financials.get("income_statement", {}).get("previous", {})
    bs_cur = financials.get("balance_sheet", {}).get("current", {}) or {}
    cur_assets = bs_cur.get("assets") or {}
    unit = financials.get("unit", "triệu đồng")
    period = financials.get("period", {}).get("current", {}).get("label", "Năm hiện tại")

    ind = industry.get("industry", industry) if isinstance(industry, dict) else {}
    industry_cagr = ind.get("industry_cagr_5y_pct", 8.0)

    prev_rev = income_prev.get("net_revenue") or income_prev.get("revenue", 0) or 0
    cur_rev = income_cur.get("net_revenue") or income_cur.get("revenue", 0) or 0
    revenue_yoy = round((cur_rev - prev_rev) / prev_rev * 100, 1) if prev_rev else 0

    ctx = {
        "period_label": period,
        "cur_revenue": cur_rev,
        "cogs": income_cur.get("cogs", 0),
        "gross_profit": income_cur.get("gross_profit", 0),
        "selling_expense": income_cur.get("selling_expense", 0),
        "admin_expense": income_cur.get("admin_expense", 0),
        "ebit": income_cur.get("operating_profit", 0),
        "interest_expense": income_cur.get("interest_expense", 0),
        "current_tax": income_cur.get("current_tax", 0),
        "net_profit": income_cur.get("net_profit_after_tax", 0),
        "fixed_assets": cur_assets.get("fixed_assets", 0),
        "total_assets": cur_assets.get("total_assets", 0),
        "inventory": cur_assets.get("inventory", 0),
        "receivables": cur_assets.get("short_term_receivables", 0),
        "prev_revenue": prev_rev,
        "prev_net_profit": income_prev.get("net_profit_after_tax", 0),
        "revenue_yoy": revenue_yoy,
        "industry_cagr": industry_cagr,
        "unit": unit,
    }

    prompt = build_prompt(_DEFAULT_PREAMBLE, _SCHEMA_BLOCK, ctx, prompt_override)

    raw = call_opus(
        prompt,
        system="You are a Vietnamese financial modeling expert. Always respond with valid JSON only.",
        max_tokens=10000,
        effort="high",
    )
    result = parse_json_response(raw)

    if "projection" in result:
        return result
    return {"projection": result}
