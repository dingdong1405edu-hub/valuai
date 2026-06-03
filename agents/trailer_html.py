"""Trailer HTML renderer — 4-page free preview via Playwright."""
from typing import Optional


def _css_vars(config: dict, brand: dict) -> str:
    colors = config.get("style", {}).get("colors", {})
    css = config.get("style", {}).get("report_css", {})
    primary = brand.get("primary") or colors.get("primary", "#1e3a8a")
    secondary = brand.get("secondary") or colors.get("secondary", "#2563eb")
    primary_light = brand.get("primary_light") or colors.get("primary_light", "#eff6ff")
    accent = brand.get("accent") or colors.get("accent", "#10b981")
    text_primary = colors.get("text_primary", "#1f2937")
    text_body = colors.get("text_body", "#374151")
    text_muted = colors.get("text_muted", "#6b7280")
    text_faint = colors.get("text_faint", "#9ca3af")
    border = colors.get("border", "#d1d5db")
    grid = colors.get("grid", "#e5e7eb")
    stripe = colors.get("stripe", "#f8fafc")
    head = css.get("head", "Inter, system-ui, sans-serif")

    return f"""
:root {{
  --primary: {primary};
  --secondary: {secondary};
  --primary-light: {primary_light};
  --accent: {accent};
  --ink: {text_primary};
  --ink-soft: {text_body};
  --muted: {text_muted};
  --faint: {text_faint};
  --line: {border};
  --line-soft: {grid};
  --grey-fill: {stripe};
  --head: {head};
}}
"""


def _base_style(config: dict, brand: dict) -> str:
    return f"""
<style>
{_css_vars(config, brand)}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: var(--head); color: var(--ink); background: white; }}
.sheet {{
  width: 210mm;
  min-height: 297mm;
  page-break-after: always;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}}
.header {{
  background: var(--primary);
  color: white;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: space-between;
}}
.accent-bar {{ height: 4px; background: var(--secondary); }}
.body {{ flex: 1; padding: 16px 20px; }}
.footer {{
  background: var(--primary);
  color: rgba(255,255,255,0.8);
  font-size: 9px;
  padding: 5px 20px;
  display: flex;
  justify-content: space-between;
}}
.badge {{
  background: var(--secondary);
  color: white;
  padding: 3px 12px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  display: inline-block;
}}
.company-name {{
  font-size: 22px;
  font-weight: 800;
  color: var(--primary);
  margin-top: 12px;
}}
.val-box {{
  background: var(--primary-light);
  border: 1.5px solid var(--primary);
  border-radius: 8px;
  padding: 14px 20px;
  text-align: center;
  margin: 16px 0;
}}
.val-box-title {{ font-size: 11px; color: var(--muted); font-weight: 600; margin-bottom: 6px; }}
.val-box-value {{ font-size: 20px; font-weight: 800; color: var(--faint); letter-spacing: 2px; }}
.val-box-note {{ font-size: 9px; color: var(--muted); margin-top: 4px; }}
.kpi-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
.kpi-table th {{
  background: var(--primary); color: white;
  font-size: 10px; padding: 5px 8px; text-align: left;
}}
.kpi-table td {{ font-size: 10px; padding: 5px 8px; border-bottom: 1px solid var(--line-soft); }}
.kpi-table tr:nth-child(even) td {{ background: var(--grey-fill); }}
.kpi-num {{ font-weight: 700; color: var(--ink); }}
.growth-pos {{ color: #10b981; font-weight: 700; }}
.growth-neg {{ color: #ef4444; font-weight: 700; }}
.ratio-good {{ color: #10b981; }}
.ratio-warning {{ color: #f59e0b; }}
.ratio-poor {{ color: #ef4444; }}
.section-title {{ font-size: 14px; font-weight: 800; color: var(--primary); margin-bottom: 8px; }}
.cta-box {{
  background: var(--primary-light);
  border: 1.5px solid var(--primary);
  border-radius: 8px;
  padding: 20px;
  margin: 16px 0;
}}
.cta-item {{ font-size: 10.5px; color: var(--ink-soft); margin-bottom: 5px; }}
.tagline {{ font-size: 13px; color: var(--muted); text-align: center; margin-top: 20px; }}
.industry-box {{ background: var(--grey-fill); border-radius: 6px; padding: 10px 14px; margin-bottom: 10px; }}
</style>
"""


def _fmt_num(v, decimals=0) -> str:
    if v is None:
        return "N/A"
    try:
        if decimals == 0:
            return f"{float(v):,.0f}"
        return f"{float(v):,.{decimals}f}"
    except Exception:
        return str(v)


def _growth_html(cur, prev) -> str:
    if cur is None or prev is None or prev == 0:
        return ""
    g = (cur - prev) / abs(prev) * 100
    cls = "growth-pos" if g >= 0 else "growth-neg"
    return f'<span class="{cls}">{g:+.1f}%</span>'


def render_trailer_html(payload: dict, config: dict = None,
                         brand: dict = None) -> str:
    config = config or {}
    brand = brand or {}
    financials = payload.get("financials", {})
    ratios = payload.get("ratios", {})
    industry = payload.get("industry", {})
    company = financials.get("company", {})
    unit = financials.get("unit", "")
    content = config.get("content", {})
    income_cur = financials.get("income_statement", {}).get("current", {})
    income_prev = financials.get("income_statement", {}).get("previous", {})
    bs_cur = (financials.get("balance_sheet", {}).get("current") or {})
    cur_a = bs_cur.get("assets", {}) or {}
    cur_e = bs_cur.get("equity", {}) or {}
    period_cur = financials.get("period", {}).get("current", {}).get("label", "Hiện tại")
    period_prev = financials.get("period", {}).get("previous", {}).get("label", "Trước")
    ind = industry.get("industry", industry) if isinstance(industry, dict) else {}
    r = ratios.get("ratios", ratios) if isinstance(ratios, dict) else {}
    today_str = __import__("datetime").date.today().strftime("%d/%m/%Y")

    style = _base_style(config, brand)

    # Page 1: Cover
    pg1 = f"""
<div class="sheet">
  <div class="header">
    <span>{content.get('trailer_brand_name', 'ValuAI')}</span>
    <span style="font-size:10px;opacity:.7">{today_str}</span>
  </div>
  <div class="accent-bar"></div>
  <div class="body" style="text-align:center;padding-top:30px;">
    <span class="badge">{content.get('trailer_preview_badge', 'XEM TRƯỚC')}</span>
    <div class="company-name">{company.get('name', 'Doanh nghiệp')}</div>
    <div style="color:var(--muted);font-size:12px;margin-top:6px;">
      Ngành: {company.get('industry', 'N/A')}
    </div>
    <div class="val-box">
      <div class="val-box-title">ĐỊNH GIÁ ƯỚC TÍNH (EQUITY VALUE)</div>
      <div class="val-box-value">██████████ – ██████████ {unit}</div>
      <div class="val-box-note">Mua báo cáo đầy đủ để xem con số thực</div>
    </div>
    <div class="tagline">{content.get('trailer_tagline', 'Định giá doanh nghiệp thông minh')}</div>
  </div>
  <div class="footer">
    <span>{content.get('trailer_footer', 'Mua báo cáo đầy đủ để xem chi tiết định giá')}</span>
    <span>Trang 1/4</span>
  </div>
</div>
"""

    # Page 2: Financial Snapshot
    kpi_rows = [
        ("Doanh thu thuần", income_cur.get("net_revenue") or income_cur.get("revenue"),
         income_prev.get("net_revenue") or income_prev.get("revenue")),
        ("Lợi nhuận gộp", income_cur.get("gross_profit"), income_prev.get("gross_profit")),
        ("EBIT", income_cur.get("operating_profit"), income_prev.get("operating_profit")),
        ("Lợi nhuận ròng", income_cur.get("net_profit_after_tax"), income_prev.get("net_profit_after_tax")),
        ("Tổng tài sản", cur_a.get("total_assets"), None),
        ("Vốn chủ sở hữu", cur_e.get("total_equity"), None),
    ]
    rows_html = ""
    for label, cur, prev in kpi_rows:
        g_html = _growth_html(cur, prev) if prev else ""
        rows_html += f"""
<tr>
  <td>{label}</td>
  <td class="kpi-num">{_fmt_num(cur)}</td>
  <td>{_fmt_num(prev) if prev else "—"}</td>
  <td>{g_html}</td>
</tr>"""

    pg2 = f"""
<div class="sheet">
  <div class="header">
    <span>SNAPSHOT TÀI CHÍNH</span><span style="font-size:10px;opacity:.7">{company.get('name','')}</span>
  </div>
  <div class="accent-bar"></div>
  <div class="body">
    <div style="font-size:9px;color:var(--muted);margin-bottom:6px;">Đơn vị: {unit}</div>
    <table class="kpi-table">
      <tr>
        <th>Chỉ tiêu</th>
        <th>{period_cur}</th>
        <th>{period_prev}</th>
        <th>YoY</th>
      </tr>
      {rows_html}
    </table>
  </div>
  <div class="footer">
    <span>ValuAI — Báo cáo tài chính</span><span>Trang 2/4</span>
  </div>
</div>
"""

    # Page 3: Industry + Ratios
    key_ratios = [
        ("Gross Margin", r.get("profitability", {}).get("gross_margin", {})),
        ("Net Margin", r.get("profitability", {}).get("net_margin", {})),
        ("ROE", r.get("profitability", {}).get("roe", {})),
        ("Current Ratio", r.get("liquidity", {}).get("current_ratio", {})),
        ("D/E Ratio", r.get("leverage", {}).get("debt_to_equity", {})),
    ]
    ratio_rows = ""
    for label, rd in key_ratios:
        val = rd.get("value")
        rating = rd.get("rating", "n/a")
        cls = f"ratio-{rating}"
        ratio_rows += f"""
<tr>
  <td>{label}</td>
  <td class="kpi-num {cls}">{_fmt_num(val, 2) if val is not None else 'N/A'}</td>
  <td class="{cls}">{rating}</td>
</tr>"""

    swot = ind.get("swot", {})
    strengths = ", ".join(swot.get("strengths", [])[:2])
    risks = ", ".join(swot.get("threats", [])[:2])

    pg3 = f"""
<div class="sheet">
  <div class="header"><span>NGÀNH & TỶ SỐ NỔI BẬT</span></div>
  <div class="accent-bar"></div>
  <div class="body">
    <div class="industry-box">
      <div class="section-title">{ind.get('industry_name', 'N/A')}</div>
      <div style="font-size:10px;color:var(--ink-soft);margin-bottom:4px;">
        {ind.get('industry_overview','')[:200]}
      </div>
      <div style="font-size:10px;color:var(--muted);">
        CAGR 5Y: <b>{ind.get('industry_cagr_5y_pct','N/A')}%</b> &nbsp;|&nbsp;
        Triển vọng: <b>{ind.get('industry_outlook_3y','N/A')[:40]}</b>
      </div>
      <div style="font-size:9px;color:var(--muted);margin-top:4px;">
        Điểm mạnh: {strengths} &nbsp;|&nbsp; Rủi ro: {risks}
      </div>
    </div>
    <div class="section-title" style="margin-top:12px;">TỶ SỐ TÀI CHÍNH</div>
    <table class="kpi-table">
      <tr><th>Chỉ số</th><th>Giá trị</th><th>Đánh giá</th></tr>
      {ratio_rows}
    </table>
  </div>
  <div class="footer"><span>ValuAI</span><span>Trang 3/4</span></div>
</div>
"""

    # Page 4: CTA
    cta_items = [
        "✓ Định giá đầy đủ DCF + Multiples (~37 trang)",
        "✓ Football Field & Sensitivity Analysis",
        "✓ Dự phóng tài chính 5 năm chi tiết",
        "✓ Investment Thesis & Risk Matrix chuyên nghiệp",
        "✓ Deal Recommendation & Exit Strategy",
        "✓ Explainer PDF giải thích phương pháp",
    ]
    cta_html = "".join(f'<div class="cta-item">{item}</div>' for item in cta_items)

    pg4 = f"""
<div class="sheet">
  <div class="header"><span>MUA BÁO CÁO ĐẦY ĐỦ</span></div>
  <div class="accent-bar"></div>
  <div class="body" style="text-align:center;">
    <div style="font-size:18px;font-weight:800;color:var(--primary);margin:20px 0 10px;">
      Mở khóa báo cáo định giá đầy đủ
    </div>
    <div class="cta-box" style="text-align:left;">
      <div style="font-size:13px;font-weight:700;color:var(--primary);margin-bottom:10px;">
        BÁO CÁO ĐẦY ĐỦ BAO GỒM:
      </div>
      {cta_html}
    </div>
    <div class="tagline">{content.get('trailer_footer','Mua ngay để nhận báo cáo trong vài phút')}</div>
  </div>
  <div class="footer"><span>ValuAI</span><span>Trang 4/4</span></div>
</div>
"""

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width">
<title>ValuAI — Preview</title>
{style}
</head>
<body>
{pg1}
{pg2}
{pg3}
{pg4}
</body>
</html>"""
    return html
