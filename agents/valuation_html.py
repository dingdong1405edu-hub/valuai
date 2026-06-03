"""Full valuation HTML report — admin preview only."""
import datetime


_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,400;0,600;0,700;1,400'
    '&family=IBM+Plex+Serif:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600'
    '&family=Architects+Daughter&display=swap" rel="stylesheet">'
)


def _css(accent: str) -> str:
    return f"""<style>
:root{{
  --ink:#1a2b4a;--ink-soft:#3a4a66;--accent:{accent};
  --line:#c9cfd9;--line-soft:#e4e8ef;--paper:#ffffff;--bg:#6b7280;--grey-fill:#eef1f5;
  --sans:'IBM Plex Sans',sans-serif;--serif:'IBM Plex Serif',serif;
  --mono:'IBM Plex Mono',monospace;--hand:'Architects Daughter',cursive;--head:var(--serif);
}}
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{background:var(--bg);font-family:var(--sans);color:var(--ink);}}
/* ── TOOLBAR ── */
.toolbar{{
  position:sticky;top:0;z-index:50;background:#14182099;
  backdrop-filter:blur(10px);border-bottom:1px solid #00000033;
  display:flex;align-items:center;gap:22px;flex-wrap:wrap;
  padding:12px 24px;color:#fff;
}}
.tb-brand{{font-family:var(--hand);font-size:18px;letter-spacing:.3px;opacity:.95;}}
.tb-brand b{{display:block;font-family:var(--sans);font-weight:700;font-size:11px;letter-spacing:2px;text-transform:uppercase;opacity:.6;}}
.tabs{{display:flex;gap:8px;}}
.tab{{
  font-family:var(--hand);font-size:16px;color:#fff;background:transparent;
  border:1.5px solid #ffffff40;border-radius:7px;padding:6px 16px;cursor:pointer;
  transition:.15s;line-height:1.1;
}}
.tab small{{display:block;font-family:var(--sans);font-size:9px;letter-spacing:1px;text-transform:uppercase;opacity:.55;font-weight:600;}}
.tab:hover{{border-color:#ffffff90;}}
.tab.active{{background:#fff;color:var(--ink);border-color:#fff;}}
.tab.active small{{opacity:.5;}}
.tb-group{{display:flex;align-items:center;gap:9px;margin-left:auto;font-size:11px;color:#fff;font-family:var(--hand);}}
.note{{padding:10px 24px;color:#fff;font-family:var(--hand);font-size:14px;opacity:.9;display:flex;gap:8px;align-items:center;}}
.note span{{font-family:var(--sans);font-size:10px;letter-spacing:1px;text-transform:uppercase;background:#ffffff22;padding:2px 8px;border-radius:20px;font-weight:600;}}
/* ── STAGE / A4 SHEETS ── */
#stage{{padding:30px 0 80px;display:flex;flex-direction:column;align-items:center;gap:34px;}}
.page{{width:794px;min-height:1123px;background:var(--paper);position:relative;box-shadow:0 18px 50px #00000040;overflow:hidden;}}
.page-tag{{position:absolute;top:14px;right:18px;font-family:var(--hand);font-size:13px;color:var(--accent);transform:rotate(3deg);opacity:.85;z-index:5;}}
.wm{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) rotate(-28deg);font-family:var(--hand);font-size:120px;color:#1a2b4a08;letter-spacing:6px;pointer-events:none;z-index:0;font-weight:400;white-space:nowrap;}}
.logo{{display:inline-flex;align-items:center;gap:8px;font-family:var(--hand);font-size:13px;color:var(--ink-soft);}}
.logo i{{width:26px;height:26px;border:1.5px dashed var(--ink-soft);border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-style:normal;font-size:11px;font-family:var(--sans);font-weight:700;}}
/* ── COVER ── */
.cov{{height:1123px;display:flex;flex-direction:column;padding:74px 76px 60px;position:relative;z-index:1;}}
.cov .top{{display:flex;justify-content:space-between;align-items:flex-start;}}
.cov .kicker{{font-family:var(--sans);font-size:11px;letter-spacing:3px;text-transform:uppercase;color:var(--accent);font-weight:600;}}
.cov h1{{font-family:var(--head);font-weight:700;font-size:50px;line-height:1.05;color:var(--ink);margin-top:auto;letter-spacing:-.5px;}}
.cov .sub{{font-family:var(--sans);font-size:16px;color:var(--ink-soft);margin-top:18px;}}
.cov .sub b{{color:var(--accent);font-weight:600;}}
.cov .intro{{margin-top:22px;font-size:14px;line-height:1.7;color:var(--ink-soft);max-width:62ch;border-left:3px solid var(--accent);padding-left:16px;}}
.cov .foot{{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;font-size:12px;color:var(--ink-soft);border-top:1px solid var(--line);padding-top:16px;}}
.ribbon{{height:8px;width:120px;background:var(--accent);margin-bottom:34px;}}
/* ── SECTION SHARED ── */
.sec{{padding:64px 64px 100px;position:relative;z-index:1;min-height:1123px;display:flex;flex-direction:column;}}
.pagefoot{{position:absolute;left:64px;right:64px;bottom:34px;display:flex;justify-content:space-between;font-size:10.5px;color:var(--ink-soft);border-top:1px solid var(--line-soft);padding-top:10px;}}
/* ── KPI STRIP ── */
.kpi-strip{{display:flex;gap:12px;margin-bottom:24px;}}
.kpi-card{{flex:1;background:var(--grey-fill);border:1px solid var(--line);border-radius:8px;padding:14px 16px;text-align:center;}}
.kpi-card .lbl{{font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:6px;}}
.kpi-card .val{{font-family:var(--head);font-size:22px;font-weight:700;color:var(--ink);}}
.kpi-card .sub{{font-size:10px;color:var(--ink-soft);margin-top:3px;}}
.kpi-card.hl{{background:var(--ink);border-color:var(--ink);}}
.kpi-card.hl .lbl{{color:var(--accent);}}
.kpi-card.hl .val{{color:#fff;}}
.kpi-card.hl .sub{{color:#cdd6e6;}}
/* ── DIRECTION A — Ledger matrix ── */
.a-head{{margin-bottom:20px;}}
.a-eyebrow{{display:flex;align-items:center;gap:12px;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--ink-soft);font-weight:600;}}
.a-eyebrow b{{color:var(--accent);}}
.a-title{{font-family:var(--head);font-size:32px;font-weight:700;margin-top:6px;}}
.a-en{{font-family:var(--hand);color:var(--accent);font-size:17px;}}
table.ledger{{width:100%;border-collapse:collapse;font-size:12px;margin-top:14px;table-layout:fixed;}}
.ledger thead th{{background:var(--ink);color:#fff;text-align:left;padding:10px 12px;font-size:10px;letter-spacing:1px;text-transform:uppercase;font-weight:600;}}
.ledger tbody td{{border-bottom:1px solid var(--line-soft);padding:11px 12px;vertical-align:middle;}}
.ledger tbody tr:nth-child(even) td{{background:#f7f9fb;}}
.ledger .nm{{font-weight:600;color:var(--ink);}}
.ledger .v{{font-family:var(--mono);font-size:12px;font-weight:600;}}
.ledger .accent{{color:var(--accent);font-weight:700;}}
.ledger .good{{color:#10b981;font-weight:700;}}
.ledger .warning{{color:#f59e0b;font-weight:700;}}
.ledger .poor{{color:#ef4444;font-weight:700;}}
.ledger .na{{color:var(--ink-soft);}}
.divider{{border-top:1.5px solid var(--line);margin:20px 0;}}
/* ── DIRECTION B — Banded rows ── */
.b-head{{display:flex;align-items:flex-end;gap:18px;border-bottom:3px solid var(--ink);padding-bottom:14px;margin-bottom:24px;}}
.b-num{{font-family:var(--head);font-size:64px;font-weight:700;color:var(--accent);line-height:.8;}}
.b-htext h2{{font-family:var(--head);font-size:30px;font-weight:700;}}
.b-htext .en{{font-family:var(--hand);color:var(--ink-soft);font-size:16px;}}
.b-htext .d{{font-size:13px;color:var(--ink-soft);margin-top:4px;}}
.band{{display:grid;grid-template-columns:36% 1fr;border:1px solid var(--line);border-radius:8px;overflow:hidden;margin-bottom:11px;}}
.band .left{{background:var(--ink);color:#fff;padding:14px 18px;display:flex;flex-direction:column;justify-content:center;}}
.band .left .nm{{font-family:var(--head);font-weight:600;font-size:15px;line-height:1.25;}}
.band .left .fx{{font-family:var(--mono);font-size:10px;color:#cdd6e6;margin-top:8px;border-top:1px solid #ffffff22;padding-top:7px;}}
.band .right{{padding:12px 20px;display:flex;gap:30px;align-items:center;flex-wrap:wrap;}}
.cell .lab{{font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:3px;}}
.cell .val{{font-size:15px;font-weight:600;color:var(--ink);font-family:var(--mono);}}
.cell .yoy{{font-size:12px;margin-top:2px;}}
.pos{{color:#10b981;font-weight:700;}}
.neg{{color:#ef4444;font-weight:700;}}
/* ── DIRECTION C — Sidebar ── */
.c-wrap{{display:grid;grid-template-columns:260px 1fr;min-height:1123px;}}
.c-side{{background:var(--ink);color:#fff;padding:60px 32px;display:flex;flex-direction:column;}}
.c-side .big{{font-family:var(--head);font-size:90px;font-weight:700;color:#ffffff1c;line-height:.8;}}
.c-side .lbl{{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-top:26px;}}
.c-side h2{{font-family:var(--head);font-size:26px;font-weight:600;margin-top:8px;line-height:1.15;}}
.c-side .en{{font-family:var(--hand);font-size:15px;color:#cdd6e6;margin-top:4px;}}
.c-side .d{{font-size:12px;line-height:1.65;color:#c2cad8;margin-top:22px;border-top:1px solid #ffffff22;padding-top:18px;}}
.c-side .sidefoot{{margin-top:auto;font-size:10px;color:#9aa6bd;line-height:1.6;}}
.c-main{{padding:50px 44px;display:flex;flex-direction:column;}}
.c-list{{flex:1;display:flex;flex-direction:column;justify-content:center;}}
.c-row{{display:flex;align-items:flex-start;gap:16px;padding:13px 0;border-bottom:1px solid var(--line-soft);}}
.c-row:last-child{{border-bottom:0;}}
.c-row .ico{{font-size:18px;flex-shrink:0;margin-top:1px;}}
.c-row .txt .nm{{font-family:var(--head);font-size:14px;font-weight:600;color:var(--ink);}}
.c-row .txt .d{{font-size:11px;color:var(--ink-soft);line-height:1.5;margin-top:2px;}}
.c-mainfoot{{margin-top:auto;padding-top:14px;border-top:1px solid var(--line-soft);display:flex;justify-content:space-between;font-size:10px;color:var(--ink-soft);}}
/* ── SECTION TABS ── */
.pg-section{{display:none;}}
.pg-section.active{{display:flex;flex-direction:column;align-items:center;gap:34px;}}
@media print{{
  .toolbar,.note{{display:none;}}
  body{{background:white;padding:0;}}
  #stage{{padding:0;gap:0;}}
  .page{{box-shadow:none;}}
  .pg-section{{display:flex!important;flex-direction:column;align-items:center;gap:0;}}
}}
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
    sign = "+" if g >= 0 else ""
    return f'<span class="{cls}">{sign}{g:.1f}%</span>'


def render_valuation_html(payload: dict, config: dict = None,
                           brand: dict = None) -> str:
    config = config or {}
    brand = brand or {}
    content = config.get("content", {})
    colors = config.get("style", {}).get("colors", {})
    accent = brand.get("accent") or colors.get("accent", "#b08d57")

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
    cur_a = bs_cur.get("assets", {}) or {}
    cur_e = bs_cur.get("equity", {}) or {}
    period_cur = financials.get("period", {}).get("current", {}).get("label", "Hiện tại")
    period_prev = financials.get("period", {}).get("previous", {}).get("label", "Kỳ trước")
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

    # ── PAGE 1: COVER (Cover layout) ─────────────────────────────────
    fv_low = _fmt(summary.get("fair_value_low"))
    fv_mid = _fmt(summary.get("fair_value_mid"))
    fv_high = _fmt(summary.get("fair_value_high"))
    wacc = _fmt(vd.get("assumptions", {}).get("wacc_pct"), 1)
    tg = _fmt(vd.get("assumptions", {}).get("terminal_growth_pct"), 1)

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
      <span style="font-style:italic;">{content.get("disclaimer_default","Tài liệu tham khảo nội bộ")[:120]}</span>
      <span>ValuAI © {year}</span>
    </div>
  </div>
</div>"""

    # ── PAGE 2: EXECUTIVE SUMMARY (Direction A — Ledger) ─────────────
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
    <div class="pagefoot">
      <span>ValuAI Admin Preview — Executive Summary</span>
      <span>Trang 1</span>
    </div>
  </div>
</div>"""

    # ── PAGE 3: ĐỊNH GIÁ (Direction A — Ledger for football field + scenarios) ──
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
    wf_rows = ""
    for label, key, cls in [
        ("Enterprise Value", "enterprise_value", "accent"),
        ("(-) Nợ vay ròng", "less_debt", "poor"),
        ("(+) Tiền mặt", "plus_cash", "good"),
        ("= Equity Value", "equity_value", ""),
    ]:
        v = waterfall.get(key)
        wf_rows += f'<tr><td class="nm">{label}</td><td class="v {cls}">{_fmt(v)}</td><td style="font-size:10px;color:var(--ink-soft);">{unit}</td></tr>'

    page_val = f"""
<div class="page">
  <div class="page-tag">Valuation</div>
  <div class="sec">
    <div class="a-head">
      <div class="a-eyebrow">02 &nbsp;·&nbsp; <b>ĐỊNH GIÁ</b></div>
      <div class="a-title">Kết Quả Định Giá</div>
      <div class="a-en">Valuation Results · WACC {wacc}% · Terminal g {tg}%</div>
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
    <div class="pagefoot">
      <span>ValuAI Admin Preview — Định giá</span>
      <span>Trang 2</span>
    </div>
  </div>
</div>"""

    # ── PAGE 4: DỰ PHÓNG 5Y (Direction B — Banded rows) ──────────────
    proj_bands = ""
    for p in projections:
        yr = p.get("year_label", f"Y{p.get('year_index','')}")
        rev = _fmt(p.get("revenue"))
        ebitda = _fmt(p.get("ebitda"))
        ebitda_m = _fmt(p.get("ebitda_margin_pct"), 1)
        fcff = _fmt(p.get("fcff"))
        rev_prev = None
        for q in projections:
            if q.get("year_index", 0) == (p.get("year_index", 1) - 1):
                rev_prev = q.get("revenue")
        proj_bands += f"""
<div class="band">
  <div class="left">
    <div class="nm">{yr}</div>
    <div class="fx">Tăng trưởng: {_fmt(p.get("growth_pct"),1)}% &nbsp;|&nbsp; Net margin: {_fmt(p.get("net_margin_pct"),1)}%</div>
  </div>
  <div class="right">
    <div class="cell"><div class="lab">Doanh thu</div><div class="val">{rev}</div></div>
    <div class="cell"><div class="lab">EBITDA</div><div class="val">{ebitda}</div></div>
    <div class="cell"><div class="lab">EBITDA %</div><div class="val">{ebitda_m}%</div></div>
    <div class="cell"><div class="lab">FCFF</div><div class="val">{fcff}</div></div>
  </div>
</div>"""

    page_proj = f"""
<div class="page">
  <div class="page-tag">5Y Proj</div>
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
    <div class="pagefoot">
      <span>ValuAI Admin Preview — Dự phóng tài chính</span>
      <span>Trang 3</span>
    </div>
  </div>
</div>"""

    # ── PAGE 5: DEAL & THESIS (Direction C — Sidebar) ─────────────────
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
      <div class="sidefoot">
        Bước tiếp: {deal.get("next_steps","")[:80]}<br>
        ValuAI Admin Preview
      </div>
    </div>
    <div class="c-main">
      <div class="c-list">{deal_rows}</div>
      <table class="ledger" style="margin-top:16px;">
        <colgroup><col style="width:25%"><col style="width:20%"><col style="width:20%"><col></colgroup>
        <thead><tr><th>Kịch bản</th><th>IRR</th><th>MOIC</th><th>Mô tả</th></tr></thead>
        <tbody>{ret_rows}</tbody>
      </table>
      <div class="c-mainfoot">
        <span>Cập nhật: {today}</span>
        <span>ValuAI © {year}</span>
      </div>
    </div>
  </div>
</div>"""

    # ── TOOLBAR ─────────────────────────────────────────────────────
    toolbar = f"""
<div class="toolbar">
  <div class="tb-brand">ValuAI<b>Admin Preview</b></div>
  <div class="tabs">
    <button class="tab active" onclick="showSection('exec')">
      Summary<small>Exec + Cover</small>
    </button>
    <button class="tab" onclick="showSection('val')">
      Định giá<small>Valuation</small>
    </button>
    <button class="tab" onclick="showSection('proj')">
      Dự phóng<small>5Y Projection</small>
    </button>
    <button class="tab" onclick="showSection('deal')">
      Deal<small>Recommendation</small>
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
{_css(accent)}
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
