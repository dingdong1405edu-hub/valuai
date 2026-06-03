"""Full valuation HTML report — admin preview only."""


def _fmt(v, decimals=0) -> str:
    if v is None:
        return "N/A"
    try:
        if decimals == 0:
            return f"{float(v):,.0f}"
        return f"{float(v):,.{decimals}f}"
    except Exception:
        return str(v)


def render_valuation_html(payload: dict, config: dict = None,
                           brand: dict = None) -> str:
    config = config or {}
    brand = brand or {}
    colors = config.get("style", {}).get("colors", {})
    css = config.get("style", {}).get("report_css", {})
    content = config.get("content", {})

    primary = brand.get("primary") or colors.get("primary", "#1e3a8a")
    secondary = brand.get("secondary") or colors.get("secondary", "#2563eb")
    primary_light = brand.get("primary_light") or colors.get("primary_light", "#eff6ff")
    text_primary = colors.get("text_primary", "#1f2937")
    text_body = colors.get("text_body", "#374151")
    text_muted = colors.get("text_muted", "#6b7280")
    border = colors.get("border", "#d1d5db")
    stripe = colors.get("stripe", "#f8fafc")
    head = css.get("head", "Inter, system-ui, sans-serif")

    financials = payload.get("financials", {})
    company = financials.get("company", {})
    unit = financials.get("unit", "")
    thesis = payload.get("thesis", {})
    val = payload.get("valuation", {})
    vd = val.get("valuation", val) if "valuation" in val else val
    summary = vd.get("summary", {})
    income_cur = financials.get("income_statement", {}).get("current", {})
    proj_data = payload.get("projection", {})
    proj = proj_data.get("projection", proj_data) if isinstance(proj_data, dict) else {}
    projections = proj.get("projections", [])
    es = thesis.get("executive_summary", {})
    ratios = payload.get("ratios", {})
    r = ratios.get("ratios", {})
    industry = payload.get("industry", {})
    ind = industry.get("industry", industry) if isinstance(industry, dict) else {}
    today_str = __import__("datetime").date.today().strftime("%d/%m/%Y")

    style = f"""
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: {head}; color: {text_primary}; background: white; line-height: 1.5; }}
.page {{ width: 210mm; min-height: 297mm; page-break-after: always; display: flex; flex-direction: column; }}
.hdr {{ background: {primary}; color: white; padding: 10px 20px; font-size: 13px; font-weight: 700; }}
.hdr-sub {{ display: flex; justify-content: space-between; align-items: center; }}
.bar {{ height: 4px; background: {secondary}; }}
.body {{ flex: 1; padding: 18px 22px; overflow: hidden; }}
.foot {{ background: {primary}; color: rgba(255,255,255,.7); font-size: 8px; padding: 4px 20px; display: flex; justify-content: space-between; }}
h2 {{ font-size: 15px; color: {primary}; margin-bottom: 8px; font-weight: 800; }}
h3 {{ font-size: 12px; color: {primary}; margin: 10px 0 6px; font-weight: 700; }}
table {{ width: 100%; border-collapse: collapse; font-size: 9px; margin-bottom: 10px; }}
th {{ background: {primary}; color: white; padding: 5px 7px; text-align: left; }}
td {{ padding: 4px 7px; border-bottom: 1px solid {border}; color: {text_body}; }}
tr:nth-child(even) td {{ background: {stripe}; }}
.kpi-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 12px; }}
.kpi {{ background: {primary_light}; border: 1px solid {primary}; border-radius: 6px; padding: 10px; text-align: center; }}
.kpi-label {{ font-size: 8px; color: {text_muted}; margin-bottom: 3px; }}
.kpi-value {{ font-size: 16px; font-weight: 800; color: {primary}; }}
.good {{ color: #10b981; }} .warning {{ color: #f59e0b; }} .poor {{ color: #ef4444; }}
.badge {{ background: {primary}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; display: inline-block; }}
.section-divider {{ border-top: 2px solid {primary}; margin: 12px 0; }}
</style>
"""

    page1 = f"""
<div class="page">
  <div class="hdr">
    <div>{content.get('report_title','BÁO CÁO ĐỊNH GIÁ DOANH NGHIỆP')}</div>
    <div class="hdr-sub">
      <span style="font-size:10px;opacity:.8">{company.get('name','')}</span>
      <span style="font-size:9px;opacity:.7">{today_str}</span>
    </div>
  </div>
  <div class="bar"></div>
  <div class="body">
    <h2>EXECUTIVE SUMMARY</h2>
    <div class="kpi-grid">
      <div class="kpi">
        <div class="kpi-label">Fair Value (Mid)</div>
        <div class="kpi-value">{_fmt(summary.get('fair_value_mid'))}</div>
        <div style="font-size:8px;color:{text_muted};">{unit}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Fair Value Range</div>
        <div class="kpi-value" style="font-size:12px;">{_fmt(summary.get('fair_value_low'))} – {_fmt(summary.get('fair_value_high'))}</div>
        <div style="font-size:8px;color:{text_muted};">{unit}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Khuyến nghị</div>
        <div class="kpi-value" style="font-size:18px;">{es.get('recommendation','N/A')}</div>
      </div>
    </div>
    <p style="font-size:10px;color:{text_body};margin-bottom:8px;">{es.get('headline','')}</p>
    <table>
      <tr><th>Chỉ tiêu</th><th>Giá trị</th></tr>
      <tr><td>Ngành</td><td>{ind.get('industry_name','N/A')}</td></tr>
      <tr><td>Doanh thu</td><td>{_fmt(income_cur.get('net_revenue') or income_cur.get('revenue'))} {unit}</td></tr>
      <tr><td>Lợi nhuận ròng</td><td>{_fmt(income_cur.get('net_profit_after_tax'))} {unit}</td></tr>
      <tr><td>WACC</td><td>{_fmt(vd.get('assumptions',{}).get('wacc_pct'),1)}%</td></tr>
      <tr><td>Terminal Growth</td><td>{_fmt(vd.get('assumptions',{}).get('terminal_growth_pct'),1)}%</td></tr>
      <tr><td>DCF Equity Value</td><td>{_fmt(vd.get('dcf',{}).get('equity_value'))} {unit}</td></tr>
    </table>
    <div class="section-divider"></div>
    <h3>KEY VALUE DRIVERS</h3>
    <table>
      <tr><th>#</th><th>Driver</th><th>Rationale</th></tr>
"""
    for d in thesis.get("key_value_drivers_ranked", [])[:5]:
        page1 += f"<tr><td>{d.get('rank','')}</td><td>{d.get('driver','')}</td><td>{d.get('rationale','')}</td></tr>\n"
    page1 += """
    </table>
  </div>
  <div class="foot"><span>ValuAI Admin Preview</span><span>Trang 1</span></div>
</div>
"""

    proj_rows = ""
    for p in projections:
        proj_rows += f"""
<tr>
  <td>{p.get('year_label','')}</td>
  <td>{_fmt(p.get('revenue'))}</td>
  <td>{_fmt(p.get('ebitda'))}</td>
  <td>{_fmt(p.get('ebitda_margin_pct'),1)}%</td>
  <td>{_fmt(p.get('net_income'))}</td>
  <td>{_fmt(p.get('fcff'))}</td>
</tr>"""

    ff = vd.get("football_field", [])
    ff_rows = ""
    for row in ff:
        ff_rows += f"<tr><td>{row.get('method','')}</td><td>{_fmt(row.get('low'))}</td><td>{_fmt(row.get('mid'))}</td><td>{_fmt(row.get('high'))}</td></tr>\n"

    page2 = f"""
<div class="page">
  <div class="hdr"><div>ĐỊNH GIÁ & DỰ PHÓNG</div></div>
  <div class="bar"></div>
  <div class="body">
    <h2>DỰ PHÓNG 5 NĂM</h2>
    <table>
      <tr><th>Năm</th><th>Doanh thu</th><th>EBITDA</th><th>EBITDA %</th><th>LNST</th><th>FCFF</th></tr>
      {proj_rows}
    </table>
    <h2>FOOTBALL FIELD ({unit})</h2>
    <table>
      <tr><th>Phương pháp</th><th>Low</th><th>Mid</th><th>High</th></tr>
      {ff_rows}
    </table>
    <h3>DCF Details</h3>
    <table>
      <tr><td>PV FCFF</td><td>{_fmt(vd.get('dcf',{}).get('pv_fcff'))} {unit}</td></tr>
      <tr><td>Terminal Value PV</td><td>{_fmt(vd.get('dcf',{}).get('pv_terminal_value'))} {unit}</td></tr>
      <tr><td>Enterprise Value</td><td>{_fmt(vd.get('dcf',{}).get('enterprise_value'))} {unit}</td></tr>
      <tr><td>Net Debt</td><td>{_fmt(vd.get('dcf',{}).get('net_debt'))} {unit}</td></tr>
      <tr><td><b>Equity Value</b></td><td><b>{_fmt(vd.get('dcf',{}).get('equity_value'))} {unit}</b></td></tr>
    </table>
  </div>
  <div class="foot"><span>ValuAI Admin Preview</span><span>Trang 2</span></div>
</div>
"""

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>ValuAI — Admin Preview</title>
{style}
</head>
<body>
{page1}
{page2}
</body>
</html>"""
    return html
