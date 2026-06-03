"""Full valuation HTML report — admin preview only."""
import datetime
from html_themes import FONTS, build_styles, build_theme_bar, THEME_CSS, THEME_META, _js_esc


def _fmt(v, d=0) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):,.{d}f}"
    except Exception:
        return str(v)


def _yoy(cur, prev) -> str:
    if cur is None or prev is None or prev == 0:
        return ""
    g = (cur - prev) / abs(prev) * 100
    cls = "pos" if g >= 0 else "neg"
    sign = "+" if g >= 0 else ""
    return f'<span class="{cls}">{sign}{g:.1f}%</span>'


_ADMIN_TOOLBAR_CSS = """\
<style>
.toolbar{
  position:sticky;top:0;z-index:50;background:#14182099;
  backdrop-filter:blur(10px);border-bottom:1px solid #00000033;
  display:flex;align-items:center;gap:22px;flex-wrap:wrap;
  padding:12px 24px;color:#fff;
}
.tb-brand{font-family:var(--hand);font-size:18px;letter-spacing:.3px;opacity:.95;}
.tb-brand b{display:block;font-family:var(--sans);font-weight:700;font-size:11px;letter-spacing:2px;text-transform:uppercase;opacity:.6;}
.tabs{display:flex;gap:8px;}
.tab{
  font-family:var(--hand);font-size:16px;color:#fff;background:transparent;
  border:1.5px solid #ffffff40;border-radius:7px;padding:6px 16px;cursor:pointer;
  transition:.15s;line-height:1.1;
}
.tab small{display:block;font-family:var(--sans);font-size:9px;letter-spacing:1px;text-transform:uppercase;opacity:.55;font-weight:600;}
.tab:hover{border-color:#ffffff90;}
.tab.active{background:#fff;color:var(--ink);border-color:#fff;}
.tab.active small{opacity:.5;}
.tb-group{display:flex;align-items:center;gap:9px;margin-left:auto;font-size:11px;color:#fff;font-family:var(--hand);}
.note{padding:10px 24px;color:#fff;font-family:var(--hand);font-size:14px;opacity:.9;display:flex;gap:8px;align-items:center;}
.note span{font-family:var(--sans);font-size:10px;letter-spacing:1px;text-transform:uppercase;background:#ffffff22;padding:2px 8px;border-radius:20px;font-weight:600;}
.pg-section{display:none;}
.pg-section.active{display:flex;flex-direction:column;align-items:center;gap:34px;}
@media print{
  .toolbar,.note,.theme-bar{display:none!important;}
  .pg-section{display:flex!important;flex-direction:column;align-items:center;gap:0;}
}
</style>"""


def render_valuation_html(payload: dict, config: dict = None,
                           brand: dict = None) -> str:
    config = config or {}
    brand = brand or {}
    content = config.get("content", {})
    colors = config.get("style", {}).get("colors", {})
    accent = brand.get("accent") or colors.get("accent", "#b08d57")
    report_css = config.get("style", {}).get("report_css", {})
    theme = report_css.get("html_theme", "A")
    custom_css = report_css.get("custom_css", "")

    financials = payload.get("financials", {})
    company = financials.get("company", {})
    unit = financials.get("unit", "")
    thesis = payload.get("thesis", {})
    val = payload.get("valuation", {})
    vd = val.get("valuation", val) if "valuation" in val else val
    summary = vd.get("summary", {})
    income_cur = financials.get("income_statement", {}).get("current", {})
    bs_cur = (financials.get("balance_sheet", {}).get("current") or {})
    proj_data = payload.get("projection", {})
    proj = proj_data.get("projection", proj_data) if isinstance(proj_data, dict) else {}
    projections = proj.get("projections", [])
    es = thesis.get("executive_summary", {})
    industry = payload.get("industry", {})
    ind = industry.get("industry", industry) if isinstance(industry, dict) else {}
    today = datetime.date.today().strftime("%d/%m/%Y")
    year = datetime.date.today().year

    company_name = company.get("name", "N/A")
    recommendation = es.get("recommendation", "N/A")
    rec_color = {"BUY": "#10b981", "HOLD": "#f59e0b", "SELL": "#ef4444"}.get(recommendation, "var(--accent)")

    # ── PAGE: COVER (Cover layout) ────────────────────────────────
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
      <h1>{company_name}</h1>
      <div class="sub">Ngành: <b>{ind.get("industry_name", company.get("industry","N/A"))}</b></div>
      <div class="intro">{es.get("headline","")}</div>
    </div>
    <div class="foot">
      <span style="font-style:italic;">{content.get("disclaimer_default","")[:120]}</span>
      <span>ValuAI © {year}</span>
    </div>
  </div>
</div>"""

    # ── PAGE: EXECUTIVE SUMMARY (Direction A — Ledger) ────────────
    fv_low = _fmt(summary.get("fair_value_low"))
    fv_mid = _fmt(summary.get("fair_value_mid"))
    fv_high = _fmt(summary.get("fair_value_high"))
    wacc = _fmt(vd.get("assumptions", {}).get("wacc_pct"), 1)
    tg = _fmt(vd.get("assumptions", {}).get("terminal_growth_pct"), 1)

    kpi_strip = f"""
<div class="kpi-strip">
  <div class="kpi-card hl">
    <div class="lbl">Fair Value Mid</div>
    <div class="val">{fv_mid}</div>
    <div class="sub">{unit}</div>
  </div>
  <div class="kpi-card">
    <div class="lbl">Fair Value Range</div>
    <div class="val" style="font-size:16px;">{fv_low} – {fv_high}</div>
    <div class="sub">{unit}</div>
  </div>
  <div class="kpi-card">
    <div class="lbl">Khuyến nghị</div>
    <div class="val" style="color:{rec_color};">{recommendation}</div>
    <div class="sub">WACC {wacc}% · g {tg}%</div>
  </div>
</div>"""

    kvd_rows = "".join(f"""<tr>
      <td style="text-align:center;font-family:var(--mono);color:var(--accent);font-weight:700;width:6%;">{d.get("rank","")}</td>
      <td class="nm" style="width:30%;">{d.get("driver","")}</td>
      <td style="font-size:11px;color:var(--ink-soft);">{d.get("rationale","")[:120]}</td>
    </tr>""" for d in thesis.get("key_value_drivers_ranked", [])[:6])

    page_exec = f"""
<div class="page">
  <div class="page-tag">Exec</div>
  <div class="sec">
    <div class="a-head">
      <div class="a-eyebrow">01 &nbsp;·&nbsp; <b>EXECUTIVE SUMMARY</b></div>
      <div class="a-title">Tóm Tắt Điều Hành</div>
      <div class="a-en">Executive Summary · {unit}</div>
    </div>
    {kpi_strip}
    <table class="ledger">
      <colgroup><col style="width:6%"><col style="width:30%"><col></colgroup>
      <thead><tr><th>#</th><th>Key Value Driver</th><th>Rationale</th></tr></thead>
      <tbody>{kvd_rows}</tbody>
    </table>
    <div class="divider"></div>
    <div style="font-size:12px;color:var(--ink-soft);line-height:1.75;">{es.get("investment_thesis","") or thesis.get("investment_case_summary","")[:500]}</div>
    <div class="pagefoot"><span>ValuAI Admin Preview — Executive Summary</span><span>Trang 1</span></div>
  </div>
</div>"""

    # ── PAGE: VALUATION (Direction A — Ledger) ────────────────────
    ff = vd.get("football_field", [])
    ff_rows = "".join(f"""<tr>
      <td class="nm">{row.get("method","")}</td>
      <td class="v">{_fmt(row.get("low"))}</td>
      <td class="v accent">{_fmt(row.get("mid"))}</td>
      <td class="v">{_fmt(row.get("high"))}</td>
    </tr>""" for row in ff)

    sc = vd.get("scenarios", {})
    sc_rows = "".join(f"""<tr>
      <td class="nm">{label}</td>
      <td class="v">{_fmt(data.get("equity_value"))}</td>
      <td style="font-size:10px;color:var(--ink-soft);">{data.get("description","")[:70]}</td>
    </tr>""" for label, data in [("Bull 🐂", sc.get("bull",{})), ("Base", sc.get("base",{})), ("Bear 🐻", sc.get("bear",{}))])

    waterfall = vd.get("waterfall", {})
    wf_rows = "".join(
        f'<tr><td class="nm">{lbl}</td><td class="v {cls}">{_fmt(waterfall.get(k))}</td><td style="font-size:10px;color:var(--ink-soft);">{unit}</td></tr>'
        for lbl, k, cls in [
            ("Enterprise Value", "enterprise_value", "accent"),
            ("(-) Nợ vay ròng", "less_debt", "poor"),
            ("(+) Tiền mặt", "plus_cash", "good"),
            ("= Equity Value", "equity_value", ""),
        ]
    )

    page_val = f"""
<div class="page">
  <div class="page-tag">Valuation</div>
  <div class="sec">
    <div class="a-head">
      <div class="a-eyebrow">02 &nbsp;·&nbsp; <b>ĐỊNH GIÁ</b></div>
      <div class="a-title">Kết Quả Định Giá</div>
      <div class="a-en">Valuation Results · WACC {wacc}% · g {tg}%</div>
    </div>
    <table class="ledger" style="margin-bottom:16px;">
      <colgroup><col style="width:28%"><col style="width:22%"><col style="width:22%"><col></colgroup>
      <thead><tr><th>Phương pháp</th><th>Low</th><th>Mid</th><th>High ({unit})</th></tr></thead>
      <tbody>{ff_rows}</tbody>
    </table>
    <table class="ledger" style="margin-bottom:16px;">
      <colgroup><col style="width:28%"><col style="width:30%"><col></colgroup>
      <thead><tr><th>Kịch bản</th><th>Equity Value ({unit})</th><th>Mô tả</th></tr></thead>
      <tbody>{sc_rows}</tbody>
    </table>
    <table class="ledger">
      <colgroup><col style="width:40%"><col style="width:30%"><col></colgroup>
      <thead><tr><th colspan="3">Waterfall Bridge: EV → Equity</th></tr></thead>
      <tbody>{wf_rows}</tbody>
    </table>
    <div class="pagefoot"><span>ValuAI Admin Preview — Định giá</span><span>Trang 2</span></div>
  </div>
</div>"""

    # ── PAGE: 5Y PROJECTION (Direction B — Banded) ───────────────
    proj_bands = ""
    for p in projections:
        yr = p.get("year_label", f"Y{p.get('year_index','')}")
        proj_bands += f"""
<div class="band">
  <div class="left">
    <div class="nm">{yr}</div>
    <div class="fx">Tăng trưởng: {_fmt(p.get("growth_pct"),1)}% &nbsp;|&nbsp; Net margin: {_fmt(p.get("net_margin_pct"),1)}%</div>
  </div>
  <div class="right">
    <div class="cell"><div class="lab">Doanh thu</div><div class="val">{_fmt(p.get("revenue"))}</div></div>
    <div class="cell"><div class="lab">EBITDA</div><div class="val">{_fmt(p.get("ebitda"))}</div></div>
    <div class="cell"><div class="lab">EBITDA %</div><div class="val">{_fmt(p.get("ebitda_margin_pct"),1)}%</div></div>
    <div class="cell"><div class="lab">FCFF</div><div class="val">{_fmt(p.get("fcff"))}</div></div>
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
    <div class="pagefoot"><span>ValuAI Admin Preview — Dự phóng</span><span>Trang 3</span></div>
  </div>
</div>"""

    # ── PAGE: DEAL RECOMMENDATION (Direction C — Sidebar) ─────────
    deal = thesis.get("deal_recommendation", {})
    exit_s = thesis.get("exit_strategy", {})
    ret_scenarios = thesis.get("return_scenarios", [])

    deal_items = [
        ("🎯", "Mục tiêu giao dịch", deal.get("primary_objective","")[:80]),
        ("💰", "Khoảng định giá", deal.get("fair_value_range_text","")[:80]),
        ("📋", "Cấu trúc deal", deal.get("deal_structure","")[:80]),
        ("🏛️", "Quản trị sau M&A", deal.get("post_deal_governance","")[:80]),
        ("🚪", "Chiến lược thoát vốn", f"{exit_s.get('primary_exit','')} · {exit_s.get('target_timeline_years','')} năm"),
    ]
    deal_rows = "".join(f"""<div class="c-row">
      <div class="ico">{ico}</div>
      <div class="txt"><div class="nm">{nm}</div><div class="d">{d}</div></div>
    </div>""" for ico, nm, d in deal_items if d)

    ret_rows = "".join(f"""<tr>
      <td class="nm">{r.get("scenario","")}</td>
      <td class="v">{_fmt(r.get("irr_pct"),1)}%</td>
      <td class="v">{_fmt(r.get("moic"),2)}x</td>
      <td style="font-size:10px;color:var(--ink-soft);">{r.get("description","")[:50]}</td>
    </tr>""" for r in ret_scenarios)

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
        Pre-money: {_fmt(deal.get("pre_money_valuation"))} {unit}<br>
        Investment: {_fmt(deal.get("investment_amount_suggested"))} {unit}<br>
        Post-money: {_fmt(deal.get("post_money_valuation"))} {unit}
      </div>
      <div class="sidefoot">{deal.get("next_steps","")[:80]}<br>ValuAI Admin Preview</div>
    </div>
    <div class="c-main">
      <div class="c-list">{deal_rows}</div>
      <table class="ledger" style="margin-top:16px;">
        <colgroup><col style="width:25%"><col style="width:20%"><col style="width:20%"><col></colgroup>
        <thead><tr><th>Kịch bản</th><th>IRR</th><th>MOIC</th><th>Mô tả</th></tr></thead>
        <tbody>{ret_rows}</tbody>
      </table>
      <div class="c-mainfoot"><span>Cập nhật: {today}</span><span>ValuAI © {year}</span></div>
    </div>
  </div>
</div>"""

    # ── ADMIN TOOLBAR (with tab + theme switcher integrated) ───────
    # Build theme buttons inline in toolbar
    theme_btns = " ".join(
        f'<button class="th-btn{" on" if t == theme else ""}" onclick="setTheme(\'{t}\')" data-t="{t}">'
        f'<b>{t}</b><small>{THEME_META[t][0]}</small></button>'
        for t in ["A", "B", "C"]
    )
    themes_js = ", ".join(
        f'"{t}": `{_js_esc(THEME_CSS[t])}`' for t in ["A", "B", "C"]
    )

    toolbar = f"""
<div class="toolbar">
  <div class="tb-brand">ValuAI<b>Admin Preview</b></div>
  <div class="tabs">
    <button class="tab active" onclick="showSection('exec')">Summary<small>Cover + Exec</small></button>
    <button class="tab" onclick="showSection('val')">Định giá<small>Valuation</small></button>
    <button class="tab" onclick="showSection('proj')">Dự phóng<small>5Y</small></button>
    <button class="tab" onclick="showSection('deal')">Deal<small>Recommendation</small></button>
  </div>
  <div class="tb-group" style="gap:6px;">
    <span style="font-size:9px;opacity:.5;letter-spacing:1px;text-transform:uppercase;">STYLE</span>
    {theme_btns}
  </div>
  <div class="tb-group" style="margin-left:auto;">
    <span style="font-family:var(--sans);font-size:11px;opacity:.7;">{company_name} &nbsp;·&nbsp; {today}</span>
  </div>
</div>
<div class="note"><span>Admin</span> Preview nội bộ — Không phải báo cáo cuối cùng</div>"""

    js = f"""<script>
const _TH={{{themes_js}}};
function setTheme(t){{
  var el=document.getElementById('theme-css');
  if(el&&_TH[t])el.textContent=_TH[t];
  document.querySelectorAll('.th-btn').forEach(function(b){{b.classList.toggle('on',b.dataset.t===t);}});
  try{{localStorage.setItem('vt',t);}}catch(e){{}}
}}
function showSection(id){{
  document.querySelectorAll('.pg-section').forEach(s=>s.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('sec-'+id).classList.add('active');
  event.currentTarget.classList.add('active');
}}
window.addEventListener('DOMContentLoaded',function(){{
  document.getElementById('sec-exec').classList.add('active');
  var saved;try{{saved=localStorage.getItem('vt');}}catch(e){{}}
  if(saved&&_TH[saved])setTheme(saved);
}});
</script>"""

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>ValuAI Admin — {company_name}</title>
{FONTS}
{build_styles(accent, theme, custom_css)}
{_ADMIN_TOOLBAR_CSS}
</head>
<body>
{toolbar}
<div id="stage">
  <div id="sec-exec" class="pg-section">{page_cover}{page_exec}</div>
  <div id="sec-val" class="pg-section">{page_val}</div>
  <div id="sec-proj" class="pg-section">{page_proj}</div>
  <div id="sec-deal" class="pg-section">{page_deal}</div>
</div>
{js}
</body>
</html>"""
