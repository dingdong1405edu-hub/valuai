"""Full valuation HTML report — admin preview only."""
import datetime
from html_themes import FONTS, STYLE_JS, build_styles, build_swatches


def _fmt(v, d=0) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):,.{d}f}"
    except Exception:
        return str(v)


def _growth(cur, prev) -> str:
    if cur is None or prev is None or prev == 0:
        return "—"
    g = (cur - prev) / abs(prev) * 100
    c = "#10b981" if g >= 0 else "#ef4444"
    return f'<span style="color:{c};font-weight:700;">{"+" if g>=0 else ""}{g:.1f}%</span>'


def render_valuation_html(payload: dict, config: dict = None,
                           brand: dict = None) -> str:
    config = config or {}
    brand = brand or {}
    content = config.get("content", {})
    colors = config.get("style", {}).get("colors", {})
    accent = brand.get("accent") or colors.get("accent", "#b08d57")
    custom_css = config.get("style", {}).get("report_css", {}).get("custom_css", "")

    financials = payload.get("financials", {})
    company = financials.get("company", {})
    unit = financials.get("unit", "")
    thesis = payload.get("thesis", {})
    val = payload.get("valuation", {})
    vd = val.get("valuation", val) if "valuation" in val else val
    summary = vd.get("summary", {})
    income_cur = financials.get("income_statement", {}).get("current", {})
    income_prev = financials.get("income_statement", {}).get("previous", {})
    bs_cur = (financials.get("balance_sheet", {}).get("current") or {})
    proj_data = payload.get("projection", {})
    proj = proj_data.get("projection", proj_data) if isinstance(proj_data, dict) else {}
    projections = proj.get("projections", [])
    es = thesis.get("executive_summary", {})
    industry = payload.get("industry", {})
    ind = industry.get("industry", industry) if isinstance(industry, dict) else {}
    period_cur = financials.get("period", {}).get("current", {}).get("label", "Hiện tại")
    period_prev = financials.get("period", {}).get("previous", {}).get("label", "Kỳ trước")
    today = datetime.date.today().strftime("%d/%m/%Y")
    year = datetime.date.today().year
    company_name = company.get("name", "N/A")
    recommendation = es.get("recommendation", "N/A")
    rec_color = {"BUY": "#10b981", "HOLD": "#f59e0b", "SELL": "#ef4444"}.get(recommendation, "var(--accent)")

    # ── TOOLBAR (tabs + swatches + ftoggle) ───────────────────────
    toolbar = f"""
<div class="toolbar">
  <div class="tb-brand">ValuAI<b>Admin Preview</b></div>
  <div class="tabs">
    <button class="tab active" onclick="showSec('exec')">Executive<small>Cover + Summary</small></button>
    <button class="tab" onclick="showSec('val')">Định giá<small>Valuation</small></button>
    <button class="tab" onclick="showSec('proj')">Dự phóng<small>5Y Projection</small></button>
    <button class="tab" onclick="showSec('deal')">Deal<small>Recommendation</small></button>
  </div>
  <div class="tb-group">
    <span class="tb-label">Màu</span>
    {build_swatches(accent)}
  </div>
  <div class="tb-group">
    <span class="tb-label">Font</span>
    <div class="ftoggle">
      <button class="on" data-f="serif" onclick="setFont(this)">Serif</button>
      <button data-f="sans" onclick="setFont(this)">Sans</button>
    </div>
  </div>
</div>
<div class="note">
  <span>Admin</span> Preview nội bộ — Không phải báo cáo cuối cùng · {company_name} · {today}
</div>"""

    # ── COVER PAGE ────────────────────────────────────────────────
    wacc = _fmt(vd.get("assumptions", {}).get("wacc_pct"), 1)
    tg = _fmt(vd.get("assumptions", {}).get("terminal_growth_pct"), 1)
    fv_low = _fmt(summary.get("fair_value_low"))
    fv_mid = _fmt(summary.get("fair_value_mid"))
    fv_high = _fmt(summary.get("fair_value_high"))

    page_cover = f"""
<div class="page">
  <div class="wm">ADMIN</div>
  <div class="page-tag">Cover</div>
  <div class="cov">
    <div class="top">
      <div class="logo"><i>V</i>ValuAI</div>
      <div class="kicker">Admin Preview &nbsp;·&nbsp; {today}</div>
    </div>
    <div style="margin-top:auto;">
      <div class="ribbon"></div>
      <div class="kicker">BÁO CÁO ĐỊNH GIÁ DOANH NGHIỆP</div>
      <h1>Báo Cáo Định Giá</h1>
      <div class="company">{company_name}</div>
      <div class="sub">Ngành: <b>{ind.get("industry_name", company.get("industry","N/A"))}</b></div>
      <div class="intro">{es.get("headline","")}</div>
    </div>
    <div class="foot">
      <span class="disc">{content.get("disclaimer_default","")[:120]}</span>
      <span>ValuAI © {year}</span>
    </div>
  </div>
</div>"""

    # ── EXECUTIVE SUMMARY — Direction B ───────────────────────────
    # KPI bands for key valuation outputs
    kpi_bands = f"""
<div class="band">
  <div class="left"><div class="nm">Fair Value (Equity)</div><div class="fx">fair_value_summary</div></div>
  <div class="right">
    <div class="cell"><div class="lab">Mid</div><div class="val">{fv_mid} {unit}</div></div>
    <div class="cell src"><div class="lab">Range</div><div class="val">{fv_low} – {fv_high} {unit}</div></div>
    <div class="cell"><div class="lab">Khuyến nghị</div><div class="val" style="color:{rec_color};font-weight:700;">{recommendation}</div></div>
  </div>
</div>
<div class="band">
  <div class="left"><div class="nm">Tham số định giá</div><div class="fx">valuation_parameters</div></div>
  <div class="right">
    <div class="cell"><div class="lab">WACC</div><div class="val">{wacc}%</div></div>
    <div class="cell src"><div class="lab">Terminal Growth</div><div class="val">{tg}%</div></div>
    <div class="cell"><div class="lab">DCF Equity Value</div><div class="val">{_fmt(vd.get("dcf",{}).get("equity_value"))} {unit}</div></div>
  </div>
</div>"""

    # Key value drivers in ledger
    kvd_rows = "".join(f"""<tr>
      <td><span class="nm">{d.get("rank","")}.&nbsp;{d.get("driver","")}</span></td>
      <td><span class="fx">driver_{d.get("rank","")}</span></td>
      <td class="sr">&nbsp;</td>
      <td class="mn">{d.get("rationale","")[:80]}</td>
    </tr>""" for d in thesis.get("key_value_drivers_ranked", [])[:5])

    page_exec = f"""
<div class="page">
  <div class="page-tag">Exec</div>
  <div class="sec">
    <div class="b-head">
      <div class="b-num">01</div>
      <div class="b-htext">
        <h2>Executive Summary</h2>
        <div class="en">Tóm tắt điều hành</div>
        <div class="d">Đơn vị: {unit} &nbsp;·&nbsp; {period_cur}</div>
      </div>
    </div>
    {kpi_bands}
    <div class="a-head" style="margin-top:18px;">
      <div class="a-eyebrow"><b>KEY VALUE DRIVERS</b></div>
      <div class="a-desc">{es.get("investment_thesis","") or thesis.get("investment_case_summary","")[:200]}</div>
    </div>
    <table class="ledger">
      <colgroup><col class="c-name"><col class="c-f"><col class="c-s"><col class="c-m"></colgroup>
      <thead><tr><th>Driver</th><th>Key</th><th>&nbsp;</th><th>Rationale</th></tr></thead>
      <tbody>{kvd_rows}</tbody>
    </table>
    <div class="pagefoot"><span>ValuAI Admin Preview — Executive Summary</span><span>Trang 1</span></div>
  </div>
</div>"""

    # ── VALUATION — Direction A (Ledger) ──────────────────────────
    ff = vd.get("football_field", [])
    ff_rows = "".join(f"""<tr>
      <td><span class="nm">{row.get("method","")}</span></td>
      <td><span class="fx">{row.get("method","").lower().replace("/","_").replace(" ","_")}</span></td>
      <td class="sr">{_fmt(row.get("low"))} – {_fmt(row.get("high"))}</td>
      <td class="mn"><b>{_fmt(row.get("mid"))}</b> {unit}</td>
    </tr>""" for row in ff)

    sc = vd.get("scenarios", {})
    sc_rows = "".join(f"""<tr>
      <td><span class="nm">{label}</span></td>
      <td><span class="fx">{key}_scenario</span></td>
      <td class="sr">{_fmt(data.get("equity_value"))} {unit}</td>
      <td class="mn">{data.get("description","")[:60]}</td>
    </tr>""" for label, key, data in [
        ("Bull 🐂 +25%", "bull", sc.get("bull",{})),
        ("Base (cơ sở)", "base", sc.get("base",{})),
        ("Bear 🐻 -30%", "bear", sc.get("bear",{})),
    ])

    wf = vd.get("waterfall", {})
    wf_rows = "".join(f"""<tr>
      <td><span class="nm">{lbl}</span></td>
      <td><span class="fx">{key}</span></td>
      <td class="sr">{_fmt(wf.get(key))} {unit}</td>
      <td class="mn">&nbsp;</td>
    </tr>""" for lbl, key in [
        ("Enterprise Value", "enterprise_value"),
        ("(-) Nợ vay ròng", "less_debt"),
        ("(+) Tiền mặt", "plus_cash"),
        ("= Equity Value", "equity_value"),
    ])

    page_val = f"""
<div class="page">
  <div class="page-tag">Valuation</div>
  <div class="sec">
    <div class="a-head">
      <div class="a-eyebrow">02 &nbsp;·&nbsp; <b>ĐỊNH GIÁ</b></div>
      <div class="a-title">Kết Quả Định Giá</div>
      <div class="a-en">Valuation Results</div>
      <div class="a-desc">WACC {wacc}% · Terminal growth {tg}% · Đơn vị: {unit}</div>
    </div>
    <table class="ledger" style="margin-bottom:16px;">
      <colgroup><col class="c-name"><col class="c-f"><col class="c-s"><col class="c-m"></colgroup>
      <thead><tr><th>Phương pháp</th><th>Key</th><th>Low – High</th><th>Mid Value</th></tr></thead>
      <tbody>{ff_rows}</tbody>
    </table>
    <div class="legend" style="margin-bottom:4px;"><i>Football Field</i><i class="src">Waterfall Bridge</i></div>
    <table class="ledger" style="margin-bottom:16px;">
      <colgroup><col class="c-name"><col class="c-f"><col class="c-s"><col class="c-m"></colgroup>
      <thead><tr><th>Kịch bản</th><th>Key</th><th>Equity Value</th><th>Mô tả</th></tr></thead>
      <tbody>{sc_rows}</tbody>
    </table>
    <table class="ledger">
      <colgroup><col class="c-name"><col class="c-f"><col class="c-s"><col class="c-m"></colgroup>
      <thead><tr><th colspan="4">Waterfall: EV → Equity</th></tr></thead>
      <tbody>{wf_rows}</tbody>
    </table>
    <div class="pagefoot"><span>ValuAI Admin Preview — Định giá</span><span>Trang 2</span></div>
  </div>
</div>"""

    # ── 5Y PROJECTION — Direction B ───────────────────────────────
    proj_bands = ""
    for p in projections:
        yr = p.get("year_label", f"Y{p.get('year_index','')}")
        g = p.get("growth_pct", 0) or 0
        g_str = f'<span style="color:{"#10b981" if g>=0 else "#ef4444"};font-weight:700;">{"+" if g>=0 else ""}{g:.1f}%</span>'
        proj_bands += f"""
<div class="band">
  <div class="left">
    <div class="nm">{yr}</div>
    <div class="fx">revenue_growth: {g:+.1f}%</div>
  </div>
  <div class="right">
    <div class="cell"><div class="lab">Doanh thu</div><div class="val">{_fmt(p.get("revenue"))} {unit}</div></div>
    <div class="cell src"><div class="lab">EBITDA ({_fmt(p.get("ebitda_margin_pct"),1)}%)</div><div class="val">{_fmt(p.get("ebitda"))} {unit}</div></div>
    <div class="cell"><div class="lab">FCFF</div><div class="val">{_fmt(p.get("fcff"))} {unit}</div></div>
  </div>
</div>"""

    page_proj = f"""
<div class="page">
  <div class="page-tag">5Y</div>
  <div class="sec">
    <div class="b-head">
      <div class="b-num">5Y</div>
      <div class="b-htext">
        <h2>Dự Phóng 5 Năm</h2>
        <div class="en">5-Year Financial Projection</div>
        <div class="d">Đơn vị: {unit} &nbsp;·&nbsp; Kỳ cơ sở: {proj.get("base_year_label","")}</div>
      </div>
    </div>
    {proj_bands}
    <div class="pagefoot"><span>ValuAI Admin Preview — Dự phóng tài chính</span><span>Trang 3</span></div>
  </div>
</div>"""

    # ── DEAL RECOMMENDATION — Direction C ─────────────────────────
    deal = thesis.get("deal_recommendation", {})
    exit_s = thesis.get("exit_strategy", {})
    ret_scenarios = thesis.get("return_scenarios", [])

    deal_metrics = [
        ("Mục tiêu giao dịch", "primary_objective", deal.get("primary_objective","")[:60], deal.get("deal_structure","")[:60]),
        ("Khoảng định giá", "fair_value_range", deal.get("fair_value_range_text","")[:60], f"Pre-money: {_fmt(deal.get('pre_money_valuation'))} {unit}"),
        ("Chiến lược thoát vốn", "exit_strategy", f"{exit_s.get('primary_exit','')} · {exit_s.get('target_timeline_years','')} năm", f"Target EV: {_fmt(exit_s.get('target_ev_at_exit'))} {unit}"),
    ]
    for r in ret_scenarios[:3]:
        deal_metrics.append((
            f"Kịch bản {r.get('scenario','')}",
            f"irr_{r.get('scenario','').lower()}",
            f"IRR: {_fmt(r.get('irr_pct'),1)}% · MOIC: {_fmt(r.get('moic'),2)}x",
            r.get("description","")[:60],
        ))

    metrics_html = ""
    for nm, fx, tx1, tx2 in deal_metrics:
        metrics_html += f"""
<div class="c-metric">
  <div class="nm">{nm}</div>
  <span class="fx">{fx}</span>
  <div class="grid2">
    <div><div class="lab">Giá trị</div><div class="tx">{tx1}</div></div>
    <div><div class="lab s">Chi tiết</div><div class="tx s">{tx2}</div></div>
  </div>
</div>"""

    page_deal = f"""
<div class="page">
  <div class="page-tag">Deal</div>
  <div class="c-wrap">
    <div class="c-side">
      <div class="big">04</div>
      <div class="lbl">DEAL RECOMMENDATION</div>
      <h2>Khuyến Nghị Đầu Tư</h2>
      <div class="en">Investment Recommendation</div>
      <div class="d">
        Investment: {_fmt(deal.get("investment_amount_suggested"))} {unit}<br>
        Post-money: {_fmt(deal.get("post_money_valuation"))} {unit}<br>
        Next: {deal.get("next_steps","")[:60]}
      </div>
      <div class="sidefoot">ValuAI Admin Preview<br>{today}</div>
    </div>
    <div class="c-main">
      {metrics_html}
      <div class="c-mainfoot">
        <span>Cập nhật: {today}</span>
        <span>ValuAI © {year}</span>
      </div>
    </div>
  </div>
</div>"""

    # ── PAGE-SECTION JS ───────────────────────────────────────────
    tab_js = """<script>
function showSec(id){
  document.querySelectorAll('.pg-section').forEach(function(s){s.classList.remove('active');});
  document.querySelectorAll('.tab').forEach(function(t){t.classList.remove('active');});
  var el=document.getElementById('sec-'+id);
  if(el)el.classList.add('active');
  if(event&&event.currentTarget)event.currentTarget.classList.add('active');
}
window.addEventListener('DOMContentLoaded',function(){
  document.getElementById('sec-exec').classList.add('active');
});
</script>"""

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>ValuAI Admin — {company_name}</title>
{FONTS}
{build_styles(accent, custom_css)}
<style>
.pg-section{{display:none;}}
.pg-section.active{{display:flex;flex-direction:column;align-items:center;gap:34px;}}
@media print{{
  .toolbar,.note{{display:none;}}
  .pg-section{{display:flex!important;flex-direction:column;align-items:center;gap:0;}}
}}
</style>
</head>
<body>
{toolbar}
<div id="stage">
  <div id="sec-exec" class="pg-section">{page_cover}{page_exec}</div>
  <div id="sec-val" class="pg-section">{page_val}</div>
  <div id="sec-proj" class="pg-section">{page_proj}</div>
  <div id="sec-deal" class="pg-section">{page_deal}</div>
</div>
{STYLE_JS}
{tab_js}
</body>
</html>"""
