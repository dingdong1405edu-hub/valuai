"""Agent 7 — Thesis writer: all data → investment thesis report."""
from datetime import date

from agent_common import call_opus, parse_json_response, with_locked_schema

_SENTINEL = "TRẢ VỀ JSON đầy đủ (không markdown):"

_SCHEMA_BLOCK = """{
  "thesis": {
    "report_version": "1.0",
    "report_date": "YYYY-MM-DD",
    "disclaimer": "...",
    "executive_summary": {
      "headline": "...",
      "company_brief": "...",
      "industry_brief": "...",
      "scale_brief": "...",
      "valuation_result": "...",
      "recommendation": "BUY | HOLD | SELL",
      "key_drivers": ["...", "..."]
    },
    "investment_case_summary": "...",
    "key_value_drivers_ranked": [
      {"rank": 1, "driver": "...", "rationale": "..."}
    ],
    "investment_thesis": {
      "thesis_points": [
        {"title": "...", "thesis": "...", "evidence": "..."}
      ],
      "catalysts": [
        {"type": "...", "description": "...", "horizon": "..."}
      ],
      "risks": [
        {
          "type": "...", "description": "...",
          "severity": "HIGH | MEDIUM | LOW",
          "mitigation": "...", "quantified_impact": "..."
        }
      ]
    },
    "risk_matrix": [
      {"risk": "...", "probability": 1, "impact": 1, "score": 1, "mitigation": "..."}
    ],
    "operations_analysis": {
      "revenue_drivers": "...",
      "margin_analysis": "...",
      "channel_breakdown": "...",
      "key_metrics_observations": "..."
    },
    "financial_analysis_commentary": {
      "balance_sheet_health": "...",
      "income_statement_quality": "...",
      "cash_flow_quality": "...",
      "leverage_view": "..."
    },
    "valuation_commentary": {
      "method_comparison": "...",
      "reconciliation": "...",
      "fair_value_view": "...",
      "weighting_applied": "...",
      "key_sensitivities": "..."
    },
    "deal_recommendation": {
      "primary_objective": "...",
      "fair_value_range_text": "...",
      "entry_price_recommendation": "...",
      "deal_structure": "...",
      "post_deal_governance": "...",
      "next_steps": "...",
      "pre_money_valuation": 0,
      "investment_amount_suggested": 0,
      "post_money_valuation": 0
    },
    "use_of_proceeds": [
      {"category": "...", "pct": 0, "amount_vnd_billion": 0, "note": ""}
    ],
    "dilution_table": [
      {"shareholder": "...", "pre_deal_pct": 0, "post_deal_pct": 0, "shares_note": ""}
    ],
    "exit_strategy": {
      "primary_exit": "...",
      "target_timeline_years": 5,
      "target_ev_at_exit": 0,
      "exit_multiple_assumption": 0.0,
      "description": "..."
    },
    "return_scenarios": [
      {
        "scenario": "Bull | Base | Bear",
        "irr_pct": 0, "moic": 0.0, "horizon_years": 5,
        "entry_ev": 0, "exit_ev": 0, "description": "..."
      }
    ]
  }
}"""

_DEFAULT_PREAMBLE = """Bạn là chuyên gia phân tích đầu tư và viết báo cáo sell-side equity research cho thị trường Việt Nam.

THÔNG TIN TỔNG HỢP:
Công ty: {company_name}
Ngành: {industry_name}
Doanh thu: {revenue} {unit}
Lợi nhuận ròng: {net_profit} {unit}
ROE: {roe}%
Định giá (Fair Value Range): {fair_value_low} - {fair_value_high} {unit}
Recommendation: Xác định BUY/HOLD/SELL dựa trên khoảng định giá và triển vọng

YÊU CẦU:
1. Viết báo cáo đầu tư chuyên nghiệp chuẩn sell-side equity research
2. IRR chuẩn: Bull 25-40%, Base 15-25%, Bear 5-15%
3. Risk matrix: score = probability × impact (low=1, medium=2, high=3)
4. use_of_proceeds tổng = 100%
5. Tất cả nhận định phải có bằng chứng từ dữ liệu tài chính
6. Ngôn ngữ: Tiếng Việt chuyên nghiệp
"""


def write_thesis(financials: dict, ratios: dict, industry: dict,
                 business: dict, projection: dict, valuation: dict,
                 prompt_override: str = "", api_key: str = None) -> dict:
    company = financials.get("company", {})
    income_cur = financials.get("income_statement", {}).get("current", {})
    unit = financials.get("unit", "triệu đồng")

    ind = industry.get("industry", industry) if isinstance(industry, dict) else {}
    val = valuation.get("valuation", valuation) if isinstance(valuation, dict) else {}
    summary = val.get("summary", {})

    r = ratios.get("ratios", ratios) if isinstance(ratios, dict) else {}
    prof = r.get("profitability", {})

    ctx = {
        "company_name": company.get("name", "N/A"),
        "industry_name": ind.get("industry_name", company.get("industry", "N/A")),
        "revenue": income_cur.get("net_revenue") or income_cur.get("revenue", 0),
        "net_profit": income_cur.get("net_profit_after_tax", 0),
        "roe": (prof.get("roe") or {}).get("value", 0),
        "fair_value_low": summary.get("fair_value_low", 0),
        "fair_value_high": summary.get("fair_value_high", 0),
        "unit": unit,
    }

    preamble = prompt_override.strip() if prompt_override and prompt_override.strip() else _DEFAULT_PREAMBLE.format(**ctx)

    context_data = f"""
CHI TIẾT DỮ LIỆU:
- Tỷ số tài chính: ROE={ctx['roe']}%, Gross margin={prof.get('gross_margin', {}).get('value', 0)}%
- DCF equity value: {val.get('dcf', {}).get('equity_value', 0)} {unit}
- Football field: {val.get('football_field', [])}
- Scenarios: {val.get('scenarios', {})}
- SWOT: {ind.get('swot', {})}
- Ngành outlook: {ind.get('industry_outlook_3y', 'N/A')}
- WACC: {val.get('assumptions', {}).get('wacc_pct', 0)}%
- Terminal growth: {val.get('assumptions', {}).get('terminal_growth_pct', 0)}%
"""

    full_prompt = f"{preamble}\n{context_data}\n\n{_SENTINEL}\n{_SCHEMA_BLOCK}"

    raw = call_opus(
        full_prompt,
        system="You are a Vietnamese sell-side equity research analyst. Always respond with valid JSON only.",
        max_tokens=16000,
        effort="high",
    )
    result = parse_json_response(raw)

    if "thesis" in result:
        return result
    return {"thesis": result}
