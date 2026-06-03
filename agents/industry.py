"""Agent 2 — Industry analyzer: financials → industry analysis."""
from agent_common import build_prompt, call_opus, parse_json_response

_SCHEMA_BLOCK = """Return ONLY valid JSON:
{
  "industry": {
    "industry_name": "...",
    "industry_classification_basis": "...",
    "industry_overview": "...",
    "market_size": {
      "tam_vnd_billion": 0,
      "sam_vnd_billion": 0,
      "som_vnd_billion": 0,
      "assumptions": "...",
      "company_market_share_pct": 0.0
    },
    "industry_cagr_5y_pct": 0.0,
    "industry_growth_drivers": ["..."],
    "industry_trends": ["..."],
    "key_competitors": [
      {"name": "...", "estimated_revenue_vnd_billion": 0, "market_share_pct": 0.0, "note": ""}
    ],
    "competitor_comparison": [
      {
        "name": "...", "is_subject": false,
        "revenue_vnd_billion": 0,
        "gross_margin_pct": 0.0, "net_margin_pct": 0.0, "roe_pct": 0.0,
        "ev_ebitda_est": 0.0, "pe_est": 0.0,
        "market_share_pct": 0.0,
        "strengths": "...", "weaknesses": "..."
      }
    ],
    "swot": {
      "strengths": ["..."],
      "weaknesses": ["..."],
      "opportunities": ["..."],
      "threats": ["..."]
    },
    "porters_5_forces": {
      "buyer_power": {"score": 3, "description": "..."},
      "supplier_power": {"score": 3, "description": "..."},
      "threat_of_substitutes": {"score": 3, "description": "..."},
      "threat_of_new_entrants": {"score": 3, "description": "..."},
      "competitive_rivalry": {"score": 3, "description": "..."}
    },
    "competitive_landscape": "...",
    "industry_risks": "...",
    "regulatory_environment": "...",
    "barriers_to_entry": ["..."],
    "industry_outlook_3y": "neutral — ..."
  }
}"""

_DEFAULT_PREAMBLE = """Bạn là chuyên gia phân tích ngành và chiến lược thị trường Việt Nam.

Doanh nghiệp cần phân tích:
- Tên: {name}
- Ngành (gợi ý): {industry_hint}
- Doanh thu hiện tại: {revenue} {unit}
- COGS: {cogs} {unit}

Hãy phân tích ngành mà doanh nghiệp này đang hoạt động, bao gồm:
1. Xác định ngành chính xác
2. Quy mô thị trường (TAM/SAM/SOM)
3. Đối thủ cạnh tranh chính
4. SWOT và Porter's 5 Forces
5. Triển vọng 3 năm tới

Tất cả số liệu quy về VND tỷ đồng."""


def analyze_industry(financials: dict, prompt_override: str = "",
                     api_key: str = None) -> dict:
    company = financials.get("company", {})
    income_cur = financials.get("income_statement", {}).get("current", {})
    unit = financials.get("unit", "triệu đồng")

    ctx = {
        "name": company.get("name", "Không rõ"),
        "industry_hint": company.get("industry", "Không rõ"),
        "revenue": income_cur.get("revenue") or income_cur.get("net_revenue", 0),
        "cogs": income_cur.get("cogs", 0),
        "unit": unit,
    }

    prompt = build_prompt(_DEFAULT_PREAMBLE, _SCHEMA_BLOCK, ctx, prompt_override)

    raw = call_opus(
        prompt,
        system="You are a Vietnamese market and industry analysis expert. Always respond with valid JSON only.",
        max_tokens=10000,
        effort="medium",
    )
    result = parse_json_response(raw)

    if "industry" in result:
        return result
    return {"industry": result}
