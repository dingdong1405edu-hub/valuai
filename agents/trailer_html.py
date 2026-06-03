"""Trailer HTML renderer — 4-page free preview via Playwright."""
import datetime
from html_themes import FONTS, build_styles, build_theme_bar


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
    report_css = config.get("style", {}).get("report_css", {})
    theme = report_css.get("html_theme", "A")
    custom_css = report_css.get("custom_css", "")

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
            prev_cell = f'<div class="cell"><div class="lab">{period_prev}</div><div class="val">{_fmt(prev)}</div></div>'
            yoy_cell = f'<div class="cell"><div class="lab">YoY</div><div class="yoy">{_yoy(cur, prev) or "—"}</div></div>'
        bands_html += f"""
<div class="band">
  <div class="left"><div class="nm">{label}</div><div class="fx">{key}</div></div>
  <div class="right">
    <div class="cell"><div class="lab">{period_cur}</div><div class="val">{_fmt(cur)}</div></div>
    {prev_cell}{yoy_cell}
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
    <div class="pagefoot"><span>{brand_name} — Báo cáo tài chính</span><span>Trang 2 / 4</span></div>
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
      <thead><tr><th>Chỉ số tài chính</th><th>Giá trị</th><th>Đánh giá</th></tr></thead>
      <tbody>{ratio_rows}</tbody>
    </table>
    <div class="pagefoot"><span>{brand_name} — Phân tích ngành</span><span>Trang 3 / 4</span></div>
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
{FONTS}
{build_styles(accent, theme, custom_css)}
</head>
<body>
{build_theme_bar(theme, custom_css)}
<div id="stage">
{pg1}
{pg2}
{pg3}
{pg4}
</div>
</body>
</html>"""
