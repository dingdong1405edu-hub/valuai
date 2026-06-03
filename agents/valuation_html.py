"""Full valuation HTML report — admin preview only."""
import datetime

_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,400;0,600;0,700;1,400'
    '&family=IBM+Plex+Serif:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600'
    '&family=Architects+Daughter&display=swap" rel="stylesheet">'
)

_CSS = """<style>
:root{
  --ink:#1a2b4a;--ink-soft:#3a4a66;--accent:#b08d57;
  --line:#c9cfd9;--line-soft:#e4e8ef;--paper:#ffffff;--bg:#6b7280;--grey-fill:#eef1f5;
  --sans:'IBM Plex Sans',sans-serif;--serif:'IBM Plex Serif',serif;
  --mono:'IBM Plex Mono',monospace;--hand:'Architects Daughter',cursive;--head:var(--serif);
}
*{box-sizing:border-box;margin:0;padding:0;}
html,body{background:var(--bg);font-family:var(--sans);color:var(--ink);}

/* ---------- toolbar ---------- */
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

/* ---------- stage / A4 sheets ---------- */
#stage{padding:30px 0 80px;display:flex;flex-direction:column;align-items:center;gap:34px;}
.page{
  width:794px;min-height:1123px;background:var(--paper);position:relative;
  box-shadow:0 18px 50px #00000040;overflow:hidden;
}
.page-tag{
  position:absolute;top:14px;right:18px;font-family:var(--hand);font-size:13px;
  color:var(--accent);transform:rotate(3deg);opacity:.85;z-index:5;
}
.wm{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) rotate(-28deg);
  font-family:var(--hand);font-size:120px;color:#1a2b4a08;letter-spacing:6px;
  pointer-events:none;z-index:0;font-weight:400;white-space:nowrap;}
.logo{display:inline-flex;align-items:center;gap:8px;font-family:var(--hand);font-size:13px;color:var(--ink-soft);}
.logo i{width:26px;height:26px;border:1.5px dashed var(--ink-soft);border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-style:normal;font-size:11px;font-family:var(--sans);font-weight:700;}

/* ── COVER ── */
.cov{height:1123px;display:flex;flex-direction:column;padding:74px 76px 60px;position:relative;z-index:1;}
.cov .top{display:flex;justify-content:space-between;align-items:flex-start;}
.cov .kicker{font-family:var(--sans);font-size:11px;letter-spacing:3px;text-transform:uppercase;color:var(--accent);font-weight:600;}
.cov h1{font-family:var(--head);font-weight:700;font-size:46px;line-height:1.05;color:var(--ink);margin-top:auto;letter-spacing:-.5px;}
.cov .sub{font-family:var(--sans);font-size:15px;color:var(--ink-soft);margin-top:16px;}
.cov .sub b{color:var(--accent);}
.cov .intro{margin-top:20px;font-size:13.5px;line-height:1.7;color:var(--ink-soft);border-left:3px solid var(--accent);padding-left:16px;}
.cov .foot{margin-top:auto;display:flex;justify-content:space-between;font-size:12px;color:var(--ink-soft);border-top:1px solid var(--line);padding-top:16px;}
.ribbon{height:8px;width:120px;background:var(--accent);margin-bottom:34px;}

/* ── SECTION SHARED ── */
.sec{padding:64px 64px 100px;position:relative;z-index:1;min-height:1123px;display:flex;flex-direction:column;}
.pagefoot{position:absolute;left:64px;right:64px;bottom:34px;display:flex;justify-content:space-between;
  font-size:10.5px;color:var(--ink-soft);border-top:1px solid var(--line-soft);padding-top:10px;}

/* ── Direction B ── */
.b-head{display:flex;align-items:flex-end;gap:18px;border-bottom:3px solid var(--ink);padding-bottom:14px;margin-bottom:24px;}
.b-num{font-family:var(--head);font-size:64px;font-weight:700;color:var(--accent);line-height:.8;}
.b-htext h2{font-family:var(--head);font-size:28px;font-weight:700;}
.b-htext .en{font-family:var(--hand);color:var(--ink-soft);font-size:16px;}
.b-htext .d{font-size:12px;color:var(--ink-soft);margin-top:4px;}
.band{display:grid;grid-template-columns:36% 1fr;border:1px solid var(--line);border-radius:8px;overflow:hidden;margin-bottom:10px;}
.band .left{background:var(--ink);color:#fff;padding:13px 16px;display:flex;flex-direction:column;justify-content:center;}
.band .left .nm{font-family:var(--head);font-weight:600;font-size:14px;line-height:1.25;}
.band .left .fx{font-family:var(--mono);font-size:10px;color:#cdd6e6;margin-top:7px;border-top:1px solid #ffffff22;padding-top:6px;}
.band .right{padding:11px 18px;display:flex;gap:26px;align-items:center;flex-wrap:wrap;}
.cell .lab{font-size:8.5px;letter-spacing:1.5px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:2px;}
.cell .val{font-size:14px;font-weight:600;color:var(--ink);font-family:var(--mono);}
.cell .note{font-size:10px;color:var(--ink-soft);margin-top:1px;}
.pos{color:#10b981;font-weight:700;} .neg{color:#ef4444;font-weight:700;}

/* ── Direction A ── */
.a-head{margin-bottom:18px;}
.a-eyebrow{display:flex;align-items:center;gap:12px;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--ink-soft);font-weight:600;}
.a-eyebrow b{color:var(--accent);}
.a-title{font-family:var(--head);font-size:28px;font-weight:700;margin-top:6px;}
.a-en{font-family:var(--hand);color:var(--accent);font-size:16px;}
table.ledger{width:100%;border-collapse:collapse;font-size:11.5px;margin-top:14px;table-layout:fixed;}
.ledger thead th{background:var(--ink);color:#fff;text-align:left;padding:10px 12px;font-size:10px;letter-spacing:1px;text-transform:uppercase;font-weight:600;}
.ledger tbody td{border-bottom:1px solid var(--line-soft);padding:10px 12px;vertical-align:middle;}
.ledger tbody tr:nth-child(even) td{background:#f7f9fb;}
.ledger .nm{font-weight:600;color:var(--ink);}
.ledger .v{font-family:var(--mono);font-size:12px;font-weight:600;}
.ledger .good{color:#10b981;font-weight:700;}
.ledger .warning{color:#f59e0b;font-weight:700;}
.ledger .poor{color:#ef4444;font-weight:700;}
.ledger .accent{color:var(--accent);font-weight:700;}

/* ── KPI strip ── */
.kpi-strip{display:flex;gap:12px;margin-bottom:24px;}
.kpi-card{flex:1;background:var(--grey-fill);border:1px solid var(--line);border-radius:8px;padding:14px 16px;text-align:center;}
.kpi-card .lbl{font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:6px;}
.kpi-card .val{font-family:var(--head);font-size:22px;font-weight:700;color:var(--ink);}
.kpi-card .sub{font-size:10px;color:var(--ink-soft);margin-top:3px;}
.kpi-card.hl{background:var(--ink);border-color:var(--ink);}
.kpi-card.hl .lbl{color:var(--accent);}
.kpi-card.hl .val{color:#fff;}
.kpi-card.hl .sub{color:#cdd6e6;}

/* ── rec badge ── */
.rec{display:inline-flex;align-items:center;gap:8px;background:var(--accent);color:#fff;
  font-family:var(--head);font-weight:700;font-size:16px;padding:6px 18px;border-radius:6px;}

/* ── section divider ── */
.divider{border-top:1.5px solid var(--line);margin:20px 0;}

/* ── page visibility (tab switching) ── */
.pg-section{display:none;}
.pg-section.active{display:flex;flex-direction:column;align-items:center;gap:34px;}

@media print{.toolbar,.note{display:none;} body{background:white;padding:0;}
  #stage{padding:0;gap:0;} .page{box-shadow:none;} .pg-section{display:flex!important;flex-direction:column;align-items:center;gap:0;}}
</style>"""


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
    return f'<span class="{cls}">{"+" if g>=0 else ""}{g:.1f}%</span>'


def render_valuation_html(payload: dict, config: dict = None,
                           brand: dict = None) -> str:
    config = config or {}
    brand = brand or {}
    content = config.get("content", {})

    financials = payload.get("financials", {})
    company = financials.get("company", {})
    unit = financials.get("unit", "")
    thesis = payload.get("thesis", {})
    val = payload.get("valuation", {})
    vd = val.get("valuation", val) if "valuation" in val else val
    summary = vd.get("summary", {})
    income_cur = financials.get("income_statement", {}).get("current", {})
    income_prev = financials.get("income_statement", {}).get("previous", {})
    proj_data = payload.get("projection", {})
    proj = proj_data.get("projection", proj_data) if isinstance(proj_data, dict) else {}
    projections = proj.get("projections", [])
    es = thesis.get("executive_summary", {})
    ratios = payload.get("ratios", {})
    r = ratios.get("ratios", {})
    industry = payload.get("industry", {})
    ind = industry.get("industry", industry) if isinstance(industry, dict) else {}
    today = datetime.date.today().strftime("%d/%m/%Y")
    year = datetime.date.today().year

    company_name = company.get("name", "N/A")
    recommendation = es.get("recommendation", "N/A")
    rec_color = {"BUY": "#10b981", "HOLD": "#f59e0b", "SELL": "#ef4444"}.get(recommendation, "var(--accent)")

    # ── SECTION 1: EXECUTIVE SUMMARY ──────────────────────────────
    fv_low = _fmt(summary.get("fair_value_low"))
    fv_mid = _fmt(summary.get("fair_value_mid"))
    fv_high = _fmt(summary.get("fair_value_high"))
    wacc = _fmt(vd.get("assumptions", {}).get("wacc_pct"), 1)
    tg = _fmt(vd.get("assumptions", {}).get("terminal_growth_pct"), 1)
    dcf_eq = _fmt(vd.get("dcf", {}).get("equity_value"))

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
    <div class="sub">{es.get("company_brief","")[:40]}</div>
  </div>
</div>"""

    # Key value drivers
    kvd_rows = ""
    for d in thesis.get("key_value_drivers_ranked", [])[:6]:
        kvd_rows += f"""<tr>
          <td style="text-align:center;font-family:var(--mono);color:var(--accent);font-weight:700;">{d.get("rank","")}</td>
          <td class="nm">{d.get("driver","")}</td>
          <td style="font-size:11px;color:var(--ink-soft);">{d.get("rationale","")[:120]}</td>
        </tr>"""

    page_exec = f"""
<div class="page">
  <div class="wm">ADMIN</div>
  <div class="page-tag">Executive</div>
  <div class="cov">
    <div class="top">
      <div class="logo"><i>V</i>ValuAI</div>
      <div class="kicker">Admin Preview &nbsp;·&nbsp; {today}</div>
    </div>
    <div style="margin-top:auto;">
      <div class="ribbon"></div>
      <div class="kicker">BÁO CÁO ĐỊNH GIÁ — ADMIN PREVIEW</div>
      <h1>{company_name}</h1>
      <div class="sub">Ngành: <b>{ind.get("industry_name", company.get("industry","N/A"))}</b></div>
      <div class="intro">{es.get("headline","")}</div>
    </div>
    <div class="foot">
      <span style="font-style:italic;">{content.get("disclaimer_default","")[:120]}</span>
      <span>ValuAI © {year}</span>
    </div>
  </div>
</div>
<div class="page">
  <div class="page-tag">Exec Summary</div>
  <div class="sec">
    <div class="b-head">
      <div class="b-num">01</div>
      <div class="b-htext">
        <h2>Executive Summary</h2>
        <div class="en">Tóm tắt điều hành</div>
        <div class="d">Đơn vị: {unit}</div>
      </div>
    </div>
    {kpi_strip}
    <div class="a-head">
      <div class="a-eyebrow"><b>KEY VALUE DRIVERS</b></div>
    </div>
    <table class="ledger">
      <thead><tr><th style="width:6%;">#</th><th style="width:30%;">Driver</th><th>Rationale</th></tr></thead>
      <tbody>{kvd_rows}</tbody>
    </table>
    <div class="divider"></div>
    <div style="font-size:11.5px;color:var(--ink-soft);line-height:1.7;">{es.get("investment_thesis","") or thesis.get("investment_case_summary","")[:400]}</div>
    <div class="pagefoot">
      <span>ValuAI Admin Preview — Executive Summary</span>
      <span>Trang 1</span>
    </div>
  </div>
</div>"""

    # ── SECTION 2: VALUATION & PROJECTION ─────────────────────────
    # Football field table
    ff = vd.get("football_field", [])
    ff_rows = "".join(f"""<tr>
      <td class="nm">{row.get("method","")}</td>
      <td class="v">{_fmt(row.get("low"))}</td>
      <td class="v accent">{_fmt(row.get("mid"))}</td>
      <td class="v">{_fmt(row.get("high"))}</td>
    </tr>""" for row in ff)

    # Scenarios
    sc = vd.get("scenarios", {})
    sc_rows = ""
    for label, data in [("Bull 🐂", sc.get("bull",{})), ("Base", sc.get("base",{})), ("Bear 🐻", sc.get("bear",{}))]:
        sc_rows += f"""<tr>
          <td class="nm">{label}</td>
          <td class="v">{_fmt(data.get("equity_value"))}</td>
          <td style="font-size:10px;color:var(--ink-soft);">{data.get("description","")[:60]}</td>
        </tr>"""

    # 5Y projection bands
    proj_bands = ""
    for p in projections:
        yr = p.get("year_label", f"Y{p.get('year_index','')}")
        rev = _fmt(p.get("revenue"))
        ebitda = _fmt(p.get("ebitda"))
        ebitda_m = _fmt(p.get("ebitda_margin_pct"), 1)
        fcff = _fmt(p.get("fcff"))
        proj_bands += f"""
<div class="band">
  <div class="left">
    <div class="nm">{yr}</div>
    <div class="fx">Tăng trưởng: {_fmt(p.get("growth_pct"),1)}%</div>
  </div>
  <div class="right">
    <div class="cell"><div class="lab">Doanh thu</div><div class="val">{rev}</div></div>
    <div class="cell"><div class="lab">EBITDA</div><div class="val">{ebitda}</div></div>
    <div class="cell"><div class="lab">EBITDA %</div><div class="val">{ebitda_m}%</div></div>
    <div class="cell"><div class="lab">FCFF</div><div class="val">{fcff}</div></div>
  </div>
</div>"""

    page_val = f"""
<div class="page">
  <div class="page-tag">Valuation</div>
  <div class="sec">
    <div class="a-head">
      <div class="a-eyebrow">02 &nbsp;·&nbsp; <b>ĐỊNH GIÁ</b></div>
      <div class="a-title">Kết Quả Định Giá</div>
      <div class="a-en">Valuation Results · WACC {wacc}% · g {tg}%</div>
    </div>
    <table class="ledger" style="margin-bottom:18px;">
      <colgroup><col style="width:25%"><col style="width:20%"><col style="width:20%"><col style="width:35%"></colgroup>
      <thead><tr><th>Phương pháp</th><th>Low</th><th>Mid</th><th>High &nbsp;({unit})</th></tr></thead>
      <tbody>{ff_rows}</tbody>
    </table>
    <table class="ledger" style="margin-bottom:20px;">
      <thead><tr><th>Kịch bản</th><th>Equity Value</th><th>Mô tả</th></tr></thead>
      <tbody>{sc_rows}</tbody>
    </table>
    <div class="b-head" style="margin-top:4px;">
      <div class="b-num" style="font-size:48px;">5Y</div>
      <div class="b-htext">
        <h2>Dự Phóng 5 Năm</h2>
        <div class="en">5-Year Projection · {unit}</div>
      </div>
    </div>
    {proj_bands}
    <div class="pagefoot">
      <span>ValuAI Admin Preview — Định giá &amp; Dự phóng</span>
      <span>Trang 2</span>
    </div>
  </div>
</div>"""

    # ── TOOLBAR (admin browser view) ───────────────────────────────
    toolbar = f"""
<div class="toolbar">
  <div class="tb-brand">ValuAI<b>Admin Preview</b></div>
  <div class="tabs">
    <button class="tab active" onclick="showSection('exec')">
      Executive<small>Summary</small>
    </button>
    <button class="tab" onclick="showSection('val')">
      Định giá<small>Valuation</small>
    </button>
  </div>
  <div class="tb-group">
    <span style="font-family:var(--sans);font-size:11px;opacity:.7;">{company_name} &nbsp;·&nbsp; {today}</span>
  </div>
</div>
<div class="note">
  <span>Admin</span> Preview nội bộ — Không phải báo cáo cuối cùng
</div>"""

    js = """<script>
function showSection(id){
  document.querySelectorAll('.pg-section').forEach(s=>s.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('sec-'+id).classList.add('active');
  event.currentTarget.classList.add('active');
}
window.addEventListener('DOMContentLoaded',()=>{
  document.getElementById('sec-exec').classList.add('active');
});
</script>"""

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>ValuAI Admin — {company_name}</title>
{_FONTS}
{_CSS}
</head>
<body>
{toolbar}
<div id="stage">
  <div id="sec-exec" class="pg-section">{page_exec}</div>
  <div id="sec-val" class="pg-section">{page_val}</div>
</div>
{js}
</body>
</html>"""
