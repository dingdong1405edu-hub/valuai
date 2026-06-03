"""Trailer HTML renderer — 4-page free preview via Playwright."""
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
    s = "+" if g >= 0 else ""
    return f'<span style="color:{c};font-weight:700;">{s}{g:.1f}%</span>'


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
    custom_css = config.get("style", {}).get("report_css", {}).get("custom_css", "")

    # ── TOOLBAR ───────────────────────────────────────────────────
    toolbar = f"""
<div class="toolbar">
  <div class="tb-brand">{brand_name}<b>Báo Cáo Định Giá</b></div>
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
  <div class="tb-group" style="font-family:var(--hand);font-size:14px;opacity:.7;">{company_name} &nbsp;·&nbsp; {today}</div>
</div>"""

    # ── PAGE 1: COVER ─────────────────────────────────────────────
    pg1 = f"""
<div class="page">
  <div class="wm">PREVIEW</div>
  <div class="page-tag">1 / 4</div>
  <div class="cov">
    <div class="top">
      <div class="logo"><i>V</i>{brand_name}</div>
      <div class="kicker">Xem Trước Miễn Phí &nbsp;·&nbsp; {today}</div>
    </div>
    <div style="margin-top:auto;">
      <div class="ribbon"></div>
      <div class="kicker">BÁO CÁO ĐỊNH GIÁ DOANH NGHIỆP</div>
      <h1>Xem Trước</h1>
      <div class="company">{company_name}</div>
      <div class="intro">
        Báo cáo định giá chuyên nghiệp tạo bởi pipeline 9-agent AI.
        Kỳ báo cáo: <b>{period_cur}</b> · Đơn vị: {unit}.
      </div>
      <div class="lock-box">
        <div class="lbl">ĐỊNH GIÁ ƯỚC TÍNH — EQUITY VALUE</div>
        <div class="val">███████ – ███████</div>
        <div class="note-txt">Mua báo cáo đầy đủ để xem con số thực tế</div>
      </div>
    </div>
    <div class="foot">
      <span class="disc">Tài liệu chỉ mang tính tham khảo, không phải tư vấn đầu tư</span>
      <span>{brand_name} © {year}</span>
    </div>
  </div>
</div>"""

    # ── PAGE 2: FINANCIAL SNAPSHOT — Direction B ───────────────────
    kpis = [
        ("Doanh thu thuần", "net_revenue",
         income_cur.get("net_revenue") or income_cur.get("revenue"),
         income_prev.get("net_revenue") or income_prev.get("revenue")),
        ("Lợi nhuận gộp", "gross_profit",
         income_cur.get("gross_profit"), income_prev.get("gross_profit")),
        ("EBIT (Lợi nhuận từ HĐKD)", "operating_profit",
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
        cells = f"""<div class="cell">
          <div class="lab">{period_cur}</div>
          <div class="val">{_fmt(cur)} {unit}</div>
        </div>"""
        if prev is not None:
            cells += f"""<div class="cell src">
          <div class="lab">{period_prev}</div>
          <div class="val">{_fmt(prev)} {unit}</div>
        </div>
        <div class="cell">
          <div class="lab">Tăng trưởng YoY</div>
          <div class="val">{_growth(cur, prev)}</div>
        </div>"""
        bands_html += f"""
<div class="band">
  <div class="left"><div class="nm">{label}</div><div class="fx">{key}</div></div>
  <div class="right">{cells}</div>
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
        <div class="d">Số liệu tài chính kỳ gần nhất · Đơn vị: {unit}</div>
      </div>
    </div>
    {bands_html}
    <div class="pagefoot"><span>{brand_name} — Tài chính</span><span>Trang 2 / 4</span></div>
  </div>
</div>"""

    # ── PAGE 3: INDUSTRY + RATIOS — Direction A ────────────────────
    ratio_defs = [
        ("Biên lợi nhuận gộp", "GP / Revenue", r.get("profitability",{}).get("gross_margin",{}), "%"),
        ("Biên lợi nhuận ròng", "LNST / Revenue", r.get("profitability",{}).get("net_margin",{}), "%"),
        ("EBITDA Margin", "EBITDA / Revenue", r.get("profitability",{}).get("ebitda_margin",{}), "%"),
        ("ROE", "LNST / Vốn chủ sở hữu", r.get("profitability",{}).get("roe",{}), "%"),
        ("ROA", "LNST / Tổng tài sản", r.get("profitability",{}).get("roa",{}), "%"),
        ("Current Ratio", "Tài sản ngắn hạn / Nợ ngắn hạn", r.get("liquidity",{}).get("current_ratio",{}), "x"),
        ("Quick Ratio", "(TSNH - HTK) / Nợ ngắn hạn", r.get("liquidity",{}).get("quick_ratio",{}), "x"),
        ("Debt / Equity", "Tổng nợ / Vốn chủ", r.get("leverage",{}).get("debt_to_equity",{}), "x"),
    ]
    _eval = {"good": ("Tốt", "color:#10b981;font-weight:700;"),
             "warning": ("Chú ý", "color:#f59e0b;font-weight:700;"),
             "poor": ("Yếu", "color:#ef4444;font-weight:700;"),
             "n/a": ("—", "color:var(--ink-soft);")}
    ratio_rows = ""
    for label, formula, rd, suffix in ratio_defs:
        val = rd.get("value")
        rating = rd.get("rating", "n/a")
        eval_text, eval_style = _eval.get(rating, ("—", ""))
        val_str = (_fmt(val, 1) + suffix) if val is not None else "N/A"
        ratio_rows += f"""<tr>
          <td><span class="nm">{label}</span></td>
          <td><span class="fx">{formula}</span></td>
          <td class="sr">{val_str}</td>
          <td class="mn"><span style="{eval_style}">{eval_text}</span></td>
        </tr>"""

    swot = ind.get("swot", {})
    s1 = (swot.get("strengths") or [""])[0][:60]
    o1 = (swot.get("opportunities") or [""])[0][:60]
    outlook = (ind.get("industry_outlook_3y") or "")[:60]

    pg3 = f"""
<div class="page">
  <div class="page-tag">3 / 4</div>
  <div class="sec">
    <div class="a-head">
      <div class="a-eyebrow">03 &nbsp;·&nbsp; <b>NGÀNH &amp; TỶ SỐ</b></div>
      <div class="a-title">Phân Tích Ngành &amp; Tỷ Số Tài Chính</div>
      <div class="a-en">Industry Analysis &amp; Financial Ratios</div>
      <div class="a-desc">{ind.get("industry_name","N/A")} — CAGR {ind.get("industry_cagr_5y_pct","N/A")}%/năm · {outlook}</div>
    </div>
    <div class="legend">
      <i>Tốt</i><i class="src">Giá trị</i><i class="mean">Đánh giá</i>
    </div>
    <table class="ledger">
      <colgroup><col class="c-name"><col class="c-f"><col class="c-s"><col class="c-m"></colgroup>
      <thead><tr><th>Chỉ số</th><th>Công thức</th><th>Giá trị</th><th>Đánh giá</th></tr></thead>
      <tbody>{ratio_rows}</tbody>
    </table>
    <div style="margin-top:auto;padding:14px 0;border-top:1px solid var(--line-soft);font-size:11.5px;color:var(--ink-soft);line-height:1.7;">
      <b style="color:var(--ink);">Điểm mạnh:</b> {s1} &nbsp;·&nbsp; <b style="color:var(--ink);">Cơ hội:</b> {o1}
    </div>
    <div class="pagefoot"><span>{brand_name} — Ngành &amp; Tỷ số</span><span>Trang 3 / 4</span></div>
  </div>
</div>"""

    # ── PAGE 4: CTA — Direction C ──────────────────────────────────
    cta = [
        ("Báo cáo định giá ~37 trang", "full_report_pdf",
         "DCF, Multiples, Football Field, Waterfall", "PDF chuyên nghiệp chuẩn sell-side"),
        ("Dự phóng tài chính 5 năm", "projection_5y",
         "Mô hình FCFF, giả định tăng trưởng", "S-curve revenue · EBITDA margin"),
        ("Investment Thesis & Risk Matrix", "thesis_risk",
         "Luận điểm đầu tư, rủi ro định lượng", "Bull / Base / Bear scenarios"),
        ("Deal Recommendation & Exit", "deal_exit",
         "Cấu trúc giao dịch M&A", "IRR · MOIC · Timeline"),
        ("Sensitivity Analysis", "sensitivity",
         "Ma trận WACC × terminal growth 5×5", "Kịch bản nhạy cảm tham số"),
        ("Explainer PDF + Excel (Pro)", "explainer_excel",
         "Giải thích phương pháp + Excel model", "openpyxl · formatted"),
    ]
    metrics_html = ""
    for nm, fx, tx1, tx2 in cta:
        metrics_html += f"""
<div class="c-metric">
  <div class="nm">{nm}</div>
  <span class="fx">{fx}</span>
  <div class="grid2">
    <div><div class="lab">Nội dung</div><div class="tx">{tx1}</div></div>
    <div><div class="lab s">Chi tiết</div><div class="tx s">{tx2}</div></div>
  </div>
</div>"""

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
        Báo cáo định giá chuyên nghiệp ~37 trang, tạo bởi pipeline 9-agent AI.
        Phân tích ngành, dự phóng 5 năm, DCF &amp; Multiples đầy đủ.
      </div>
      <div class="sidefoot">{brand_name} &mdash; Định giá SME Việt Nam<br>Thanh toán qua PayOS</div>
    </div>
    <div class="c-main">
      {metrics_html}
      <div class="c-mainfoot">
        <span>PayOS &mdash; An toàn &amp; bảo mật</span>
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
{FONTS}
{build_styles(accent, custom_css)}
</head>
<body>
{toolbar}
<div id="stage">
{pg1}
{pg2}
{pg3}
{pg4}
</div>
{STYLE_JS}
</body>
</html>"""
