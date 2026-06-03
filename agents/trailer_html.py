"""Trailer HTML renderer — 4-page free preview via Playwright."""
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
body{{padding:30px 0 80px;display:flex;flex-direction:column;align-items:center;gap:34px;}}
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
.cov .disc{{font-style:italic;}}
.ribbon{{height:8px;width:120px;background:var(--accent);margin-bottom:34px;}}
.lock-box{{background:var(--grey-fill);border:1.5px dashed var(--line);border-radius:10px;padding:24px 30px;margin-top:30px;text-align:center;}}
.lock-box .lbl{{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:10px;}}
.lock-box .val{{font-size:28px;font-weight:700;font-family:var(--mono);color:#c9cfd9;letter-spacing:5px;}}
.lock-box .note{{font-size:11px;color:var(--ink-soft);margin-top:10px;font-family:var(--hand);}}
/* ── SECTION ── */
.sec{{padding:64px 64px 100px;position:relative;z-index:1;min-height:1123px;display:flex;flex-direction:column;}}
.pagefoot{{position:absolute;left:64px;right:64px;bottom:34px;display:flex;justify-content:space-between;font-size:10.5px;color:var(--ink-soft);border-top:1px solid var(--line-soft);padding-top:10px;}}
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
.band .right{{padding:12px 20px;display:flex;gap:30px;align-items:center;}}
.cell .lab{{font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:3px;}}
.cell .val{{font-size:15px;font-weight:600;color:var(--ink);font-family:var(--mono);}}
.cell .yoy{{font-size:12px;margin-top:2px;}}
.pos{{color:#10b981;font-weight:700;}}
.neg{{color:#ef4444;font-weight:700;}}
/* ── DIRECTION A — Ledger matrix ── */
.a-head{{margin-bottom:20px;}}
.a-eyebrow{{display:flex;align-items:center;gap:12px;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--ink-soft);font-weight:600;}}
.a-eyebrow b{{color:var(--accent);}}
.a-title{{font-family:var(--head);font-size:32px;font-weight:700;margin-top:6px;}}
.a-en{{font-family:var(--hand);color:var(--accent);font-size:17px;}}
.ind-box{{background:var(--grey-fill);border-radius:8px;padding:16px 20px;margin-bottom:18px;border-left:4px solid var(--accent);}}
.ind-box .nm{{font-family:var(--head);font-size:17px;font-weight:700;margin-bottom:6px;}}
.ind-box .ov{{font-size:11.5px;color:var(--ink-soft);line-height:1.6;}}
.ind-box .meta{{display:flex;gap:22px;font-size:11px;color:var(--ink-soft);margin-top:10px;flex-wrap:wrap;}}
.ind-box .meta b{{color:var(--accent);}}
table.ledger{{width:100%;border-collapse:collapse;font-size:12px;}}
.ledger thead th{{background:var(--ink);color:#fff;text-align:left;padding:10px 12px;font-size:10px;letter-spacing:1px;text-transform:uppercase;font-weight:600;}}
.ledger tbody td{{border-bottom:1px solid var(--line-soft);padding:11px 12px;vertical-align:middle;}}
.ledger tbody tr:nth-child(even) td{{background:#f7f9fb;}}
.ledger .nm{{font-weight:600;color:var(--ink);}}
.ledger .v{{font-family:var(--mono);font-size:12px;font-weight:600;}}
.ledger .good{{color:#10b981;font-weight:700;}}
.ledger .warning{{color:#f59e0b;font-weight:700;}}
.ledger .poor{{color:#ef4444;font-weight:700;}}
.ledger .na{{color:var(--ink-soft);}}
/* ── DIRECTION C — Sidebar report ── */
.c-wrap{{display:grid;grid-template-columns:260px 1fr;height:1123px;}}
.c-side{{background:var(--ink);color:#fff;padding:60px 32px;display:flex;flex-direction:column;}}
.c-side .big{{font-family:var(--head);font-size:90px;font-weight:700;color:#ffffff1c;line-height:.8;}}
.c-side .lbl{{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-top:26px;}}
.c-side h2{{font-family:var(--head);font-size:26px;font-weight:600;margin-top:8px;line-height:1.15;}}
.c-side .en{{font-family:var(--hand);font-size:15px;color:#cdd6e6;margin-top:4px;}}
.c-side .d{{font-size:12px;line-height:1.65;color:#c2cad8;margin-top:22px;border-top:1px solid #ffffff22;padding-top:18px;}}
.c-side .sidefoot{{margin-top:auto;font-size:10px;color:#9aa6bd;line-height:1.6;}}
.c-main{{padding:50px 44px;display:flex;flex-direction:column;}}
.cta-list{{flex:1;display:flex;flex-direction:column;justify-content:center;}}
.cta-row{{display:flex;align-items:flex-start;gap:16px;padding:13px 0;border-bottom:1px solid var(--line-soft);}}
.cta-row:last-child{{border-bottom:0;}}
.cta-row .ico{{font-size:18px;flex-shrink:0;margin-top:1px;}}
.cta-row .txt .nm{{font-family:var(--head);font-size:14px;font-weight:600;color:var(--ink);}}
.cta-row .txt .d{{font-size:11px;color:var(--ink-soft);line-height:1.5;margin-top:2px;}}
.c-mainfoot{{margin-top:auto;padding-top:14px;border-top:1px solid var(--line-soft);display:flex;justify-content:space-between;font-size:10px;color:var(--ink-soft);}}
@media print{{body{{background:white;padding:0;gap:0;}}.page{{box-shadow:none;}}}}
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


def render_trailer_html(payload: dict, config: dict = None,
                         brand: dict = None) -> str:
    config = config or {}
    brand = brand or {}
    financials = payload.get("financials", {})
    ratios_data = payload.get("ratios", {})
    industry_data = payload.get("industry", {})
    company = financials.get("company", {})
    unit = financials.get("unit", "")
    content = config.get("content", {})
    income_cur = financials.get("income_statement", {}).get("current", {})
    income_prev = financials.get("income_statement", {}).get("previous", {})
    bs_cur = (financials.get("balance_sheet", {}).get("current") or {})
    cur_a = bs_cur.get("assets", {}) or {}
    cur_e = bs_cur.get("equity", {}) or {}
    period_cur = financials.get("period", {}).get("current", {}).get("label", "Hiện tại")
    period_prev = financials.get("period", {}).get("previous", {}).get("label", "Kỳ trước")
    ind = industry_data.get("industry", industry_data) if isinstance(industry_data, dict) else {}
    r = ratios_data.get("ratios", ratios_data) if isinstance(ratios_data, dict) else {}
    today = datetime.date.today().strftime("%d/%m/%Y")
    year = datetime.date.today().year
    company_name = company.get("name", "Doanh nghiệp")
    company_industry = company.get("industry", "N/A")
    brand_name = content.get("trailer_brand_name", "ValuAI")

    colors = config.get("style", {}).get("colors", {})
    accent = brand.get("accent") or colors.get("accent", "#b08d57")

    # ── PAGE 1: COVER ─────────────────────────────────────────────
    pg1 = f"""
<div class="page">
  <div class="wm">PREVIEW</div>
  <div class="page-tag">1 / 4</div>
  <div class="cov">
    <div class="top">
      <div class="logo"><i>V</i>{brand_name}</div>
      <div class="kicker">Báo cáo Định giá &nbsp;·&nbsp; {today}</div>
    </div>
    <div style="margin-top:auto;">
      <div class="ribbon"></div>
      <div class="kicker">XEM TRƯỚC MIỄN PHÍ</div>
      <h1>{company_name}</h1>
      <div class="sub">Ngành: <b>{company_industry}</b></div>
      <div class="intro">
        Báo cáo định giá chuyên nghiệp được tạo bởi pipeline 9-agent AI.<br>
        Kỳ báo cáo: <b>{period_cur}</b> &nbsp;·&nbsp; Đơn vị: {unit}.
      </div>
      <div class="lock-box">
        <div class="lbl">ĐỊNH GIÁ ƯỚC TÍNH — EQUITY VALUE</div>
        <div class="val">███████ – ███████</div>
        <div class="note">Mua báo cáo đầy đủ để xem con số thực tế</div>
      </div>
    </div>
    <div class="foot">
      <span class="disc">Tài liệu chỉ mang tính tham khảo, không phải tư vấn đầu tư</span>
      <span>{brand_name} © {year}</span>
    </div>
  </div>
</div>"""

    # ── PAGE 2: FINANCIAL SNAPSHOT (Direction B) ───────────────────
    kpis = [
        ("Doanh thu thuần", "net_revenue",
         income_cur.get("net_revenue") or income_cur.get("revenue"),
         income_prev.get("net_revenue") or income_prev.get("revenue")),
        ("Lợi nhuận gộp", "gross_profit",
         income_cur.get("gross_profit"), income_prev.get("gross_profit")),
        ("EBIT", "operating_profit",
         income_cur.get("operating_profit"), income_prev.get("operating_profit")),
        ("Lợi nhuận ròng (LNST)", "net_profit_after_tax",
         income_cur.get("net_profit_after_tax"), income_prev.get("net_profit_after_tax")),
        ("Tổng tài sản", "total_assets",
         cur_a.get("total_assets"), None),
        ("Vốn chủ sở hữu", "total_equity",
         cur_e.get("total_equity"), None),
    ]
    bands_html = ""
    for label, key, cur, prev in kpis:
        prev_cell = ""
        yoy_cell = ""
        if prev is not None:
            prev_cell = f"""<div class="cell">
          <div class="lab">{period_prev}</div>
          <div class="val">{_fmt(prev)}</div>
        </div>"""
            yoy_cell = f"""<div class="cell">
          <div class="lab">YoY</div>
          <div class="yoy">{_yoy(cur, prev) or "—"}</div>
        </div>"""
        bands_html += f"""
<div class="band">
  <div class="left">
    <div class="nm">{label}</div>
    <div class="fx">{key}</div>
  </div>
  <div class="right">
    <div class="cell">
      <div class="lab">{period_cur}</div>
      <div class="val">{_fmt(cur)}</div>
    </div>
    {prev_cell}
    {yoy_cell}
  </div>
</div>"""

    pg2 = f"""
<div class="page">
  <div class="page-tag">2 / 4</div>
  <div class="sec">
    <div class="b-head">
      <div class="b-num">02</div>
      <div class="b-htext">
        <h2>Snapshot Tài Chính</h2>
        <div class="en">Financial Snapshot</div>
        <div class="d">Số liệu tài chính kỳ gần nhất &nbsp;·&nbsp; Đơn vị: {unit}</div>
      </div>
    </div>
    {bands_html}
    <div class="pagefoot">
      <span>{brand_name} — Báo cáo tài chính</span>
      <span>Trang 2 / 4</span>
    </div>
  </div>
</div>"""

    # ── PAGE 3: INDUSTRY + RATIOS (Direction A) ────────────────────
    key_ratios = [
        ("Biên lợi nhuận gộp", "gross_margin",
         r.get("profitability", {}).get("gross_margin", {}), "%"),
        ("Biên lợi nhuận ròng", "net_margin",
         r.get("profitability", {}).get("net_margin", {}), "%"),
        ("EBITDA Margin", "ebitda_margin",
         r.get("profitability", {}).get("ebitda_margin", {}), "%"),
        ("ROE", "roe",
         r.get("profitability", {}).get("roe", {}), "%"),
        ("ROA", "roa",
         r.get("profitability", {}).get("roa", {}), "%"),
        ("Current Ratio", "current_ratio",
         r.get("liquidity", {}).get("current_ratio", {}), "x"),
        ("Quick Ratio", "quick_ratio",
         r.get("liquidity", {}).get("quick_ratio", {}), "x"),
        ("Debt / Equity", "debt_to_equity",
         r.get("leverage", {}).get("debt_to_equity", {}), "x"),
    ]
    _rating_label = {"good": "Tốt ✓", "warning": "Chú ý ⚠", "poor": "Yếu ✗", "n/a": "—"}
    ratio_rows = ""
    for label, key, rd, suffix in key_ratios:
        val = rd.get("value")
        rating = rd.get("rating", "n/a")
        rating_cls = rating if rating in ("good", "warning", "poor") else "na"
        val_str = (_fmt(val, 1) + suffix) if val is not None else "N/A"
        ratio_rows += f"""<tr>
          <td class="nm">{label}</td>
          <td class="v">{val_str}</td>
          <td class="{rating_cls}">{_rating_label.get(rating, rating)}</td>
        </tr>"""

    swot = ind.get("swot", {})
    strengths = " · ".join((swot.get("strengths") or [])[:2])
    outlook = (ind.get("industry_outlook_3y") or "N/A")[:70]

    pg3 = f"""
<div class="page">
  <div class="page-tag">3 / 4</div>
  <div class="sec">
    <div class="a-head">
      <div class="a-eyebrow">03 &nbsp;·&nbsp; <b>NGÀNH &amp; TỶ SỐ</b></div>
      <div class="a-title">Phân Tích Ngành &amp; Tỷ Số Tài Chính</div>
      <div class="a-en">Industry Analysis &amp; Key Ratios</div>
    </div>
    <div class="ind-box">
      <div class="nm">{ind.get("industry_name", "N/A")}</div>
      <div class="ov">{(ind.get("industry_overview") or "")[:280]}</div>
      <div class="meta">
        <span>CAGR 5 năm: <b>{ind.get("industry_cagr_5y_pct", "N/A")}%</b></span>
        <span>Triển vọng: <b>{outlook}</b></span>
        <span>Điểm mạnh: <b>{strengths[:80] or "N/A"}</b></span>
      </div>
    </div>
    <table class="ledger">
      <thead>
        <tr><th>Chỉ số tài chính</th><th>Giá trị</th><th>Đánh giá</th></tr>
      </thead>
      <tbody>{ratio_rows}</tbody>
    </table>
    <div class="pagefoot">
      <span>{brand_name} — Phân tích ngành</span>
      <span>Trang 3 / 4</span>
    </div>
  </div>
</div>"""

    # ── PAGE 4: CTA (Direction C) ──────────────────────────────────
    cta_items = [
        ("📊", "Báo cáo định giá ~37 trang", "DCF, Multiples, Football Field, Waterfall Bridge"),
        ("📈", "Dự phóng tài chính 5 năm", "Mô hình FCFF đầy đủ, giả định chi tiết"),
        ("🎯", "Investment Thesis & Risk Matrix", "Phân tích sell-side chuyên nghiệp"),
        ("💼", "Deal Recommendation & Exit", "Cấu trúc giao dịch và chiến lược thoát vốn"),
        ("📋", "Sensitivity & Scenario Analysis", "Ma trận WACC × growth, Bull/Base/Bear"),
        ("📄", "Explainer PDF + Excel (Pro)", "Giải thích phương pháp + file Excel đầy đủ"),
    ]
    cta_rows = "".join(f"""<div class="cta-row">
      <div class="ico">{ico}</div>
      <div class="txt"><div class="nm">{nm}</div><div class="d">{d}</div></div>
    </div>""" for ico, nm, d in cta_items)

    pg4 = f"""
<div class="page">
  <div class="page-tag">4 / 4</div>
  <div class="c-wrap">
    <div class="c-side">
      <div class="big">04</div>
      <div class="lbl">NÂNG CẤP</div>
      <h2>Mở Khóa Báo Cáo Đầy Đủ</h2>
      <div class="en">Unlock Full Report</div>
      <div class="d">
        Báo cáo định giá chuyên nghiệp ~37 trang được tạo bởi pipeline 9-agent AI.
        Phân tích ngành, dự phóng 5 năm, DCF &amp; Multiples đầy đủ.
      </div>
      <div class="sidefoot">{brand_name}<br>Định giá SME Việt Nam</div>
    </div>
    <div class="c-main">
      <div style="font-family:var(--head);font-size:17px;font-weight:700;margin-bottom:18px;color:var(--ink);">
        Báo cáo đầy đủ bao gồm:
      </div>
      <div class="cta-list">{cta_rows}</div>
      <div class="c-mainfoot">
        <span>Thanh toán qua PayOS — An toàn &amp; bảo mật</span>
        <span>{today}</span>
      </div>
    </div>
  </div>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>ValuAI — Preview · {company_name}</title>
{_FONTS}
{_css(accent)}
</head>
<body>
{pg1}
{pg2}
{pg3}
{pg4}
</body>
</html>"""
