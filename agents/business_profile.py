"""Agent 3 — Business profile: financials + industry → business overview."""
from agent_common import get_groq_client, parse_json_response, with_locked_schema

_SENTINEL = "TRẢ VỀ JSON (không markdown):"

_SCHEMA_BLOCK = """{
  "business": {
    "history_inferred": "...",
    "ownership_summary": "...",
    "shareholders": [
      {"name": "Không xác định từ BCTC", "ownership_pct": 0, "type": "...", "note": ""}
    ],
    "management_team": [
      {"name": "Không xác định từ BCTC", "role": "...", "background": ""}
    ],
    "founding_milestones": [
      {"year": 0, "event": "..."}
    ],
    "headcount": "...",
    "management": "...",
    "business_model": {
      "summary": "...",
      "revenue_model": "...",
      "products_services": "...",
      "customer_segments": "..."
    },
    "revenue_breakdown": [
      {"product": "...", "pct_of_revenue": 0, "note": ""}
    ],
    "top_customers": [
      {"name": "Không xác định từ BCTC", "revenue_pct": 0, "note": ""}
    ],
    "top_suppliers": [
      {"name": "Không xác định từ BCTC", "cost_pct": 0, "note": ""}
    ],
    "unit_economics": {
      "gross_margin_pct": 0.0,
      "operating_margin_pct": 0.0,
      "comments": "..."
    },
    "value_chain": {
      "input": "...",
      "production": "...",
      "distribution": "...",
      "customer": "..."
    },
    "scale_indicators": {
      "revenue_size_class": "...",
      "employee_estimate": "...",
      "asset_intensity": "..."
    },
    "competitive_position": "challenger",
    "growth_stage": "mature"
  }
}"""

_DEFAULT_PREAMBLE = """Bạn là chuyên gia phân tích doanh nghiệp Việt Nam.

Dữ liệu tài chính doanh nghiệp:
Tên: {company_name}
Ngành: {industry_name}
Doanh thu: {revenue} {unit}
Lợi nhuận ròng: {net_profit} {unit}
Tổng tài sản: {total_assets} {unit}
Vốn chủ sở hữu: {equity} {unit}

Thông tin ngành:
{industry_summary}

QUAN TRỌNG:
- KHÔNG bịa thông tin ban lãnh đạo hoặc cổ đông nếu không có trong BCTC
- Ghi "Không xác định từ BCTC" cho những thông tin không có
- Suy luận hợp lý từ dữ liệu tài chính về mô hình kinh doanh

"""


def analyze_business(financials: dict, industry: dict,
                     prompt_override: str = "", api_key: str = None) -> dict:
    company = financials.get("company", {})
    income_cur = financials.get("income_statement", {}).get("current", {})
    bs_cur = financials.get("balance_sheet", {}).get("current", {})
    unit = financials.get("unit", "triệu đồng")

    industry_data = industry if not isinstance(industry, dict) or "industry" not in industry else industry["industry"]
    industry_summary = (
        f"Ngành: {industry_data.get('industry_name', 'N/A')}\n"
        f"CAGR 5 năm: {industry_data.get('industry_cagr_5y_pct', 'N/A')}%\n"
        f"Triển vọng: {industry_data.get('industry_outlook_3y', 'N/A')}"
    )

    ctx = {
        "company_name": company.get("name", "Không rõ"),
        "industry_name": company.get("industry", "Không rõ"),
        "revenue": income_cur.get("net_revenue") or income_cur.get("revenue", 0),
        "net_profit": income_cur.get("net_profit_after_tax", 0),
        "total_assets": (bs_cur.get("assets") or {}).get("total_assets", 0),
        "equity": (bs_cur.get("equity") or {}).get("total_equity", 0),
        "unit": unit,
        "industry_summary": industry_summary,
    }

    preamble = prompt_override.strip() if prompt_override and prompt_override.strip() else _DEFAULT_PREAMBLE.format(**ctx)
    full_prompt = f"{preamble}\n\n{_SENTINEL}\n{_SCHEMA_BLOCK}"

    client = get_groq_client()
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a Vietnamese business analysis expert. Always respond with valid JSON only."},
            {"role": "user", "content": full_prompt}
        ],
        max_tokens=6000,
    )

    raw = completion.choices[0].message.content or ""
    result = parse_json_response(raw)

    if "business" in result:
        return result
    return {"business": result}
