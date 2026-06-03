"""Explainer HTML renderer — explains methodology via Playwright PDF."""
import datetime
from explanations_default import EXPLANATIONS_DEFAULT
from html_themes import FONTS, build_styles, build_theme_bar


def render_explainer_html(config: dict = None, brand: dict = None) -> str:
    config = config or {}
    brand = brand or {}
    content = config.get("content", {})
    explanations = content.get("explanations") or EXPLANATIONS_DEFAULT

    colors = config.get("style", {}).get("colors", {})
    accent = brand.get("accent") or colors.get("accent", "#b08d57")
    report_css = config.get("style", {}).get("report_css", {})
    theme = report_css.get("html_theme", "A")
    custom_css = report_css.get("custom_css", "")

    title = content.get("explainer_title", "GIẢI THÍCH PHƯƠNG PHÁP ĐỊNH GIÁ")
    subtitle = content.get("explainer_subtitle", "Hướng dẫn đọc báo cáo ValuAI")
    intro = content.get("explainer_intro",
        "Tài liệu này giải thích các công thức, chỉ số và phương pháp phân tích "
        "được sử dụng trong báo cáo định giá ValuAI.")
    today = datetime.date.today().strftime("%d/%m/%Y")
    year = datetime.date.today().year

    # ── COVER PAGE ─────────────────────────────────────────────────
    toc_items = "".join(
        f'<div class="toc-item"><span class="num">{i:02d}</span><span>{e.get("title","")}</span></div>'
        for i, e in enumerate(explanations, 1)
    )
    cover = f"""
<div class="page">
  <div class="wm">EXPLAINER</div>
  <div class="page-tag">Explainer</div>
  <div class="cov">
    <div class="top">
      <div class="logo"><i>V</i>ValuAI</div>
      <div class="kicker">Phương Pháp Định Giá &nbsp;·&nbsp; {today}</div>
    </div>
    <div style="margin-top:auto;">
      <div class="ribbon"></div>
      <div class="kicker">HƯỚNG DẪN ĐỌC BÁO CÁO</div>
      <h1>{title}</h1>
      <div class="sub">{subtitle}</div>
      <div class="intro">{intro}</div>
      <div class="toc">
        <div class="toc-title">Mục lục phương pháp</div>
        {toc_items}
      </div>
    </div>
    <div class="foot">
      <span style="font-style:italic;">Tài liệu bổ sung cho báo cáo định giá</span>
      <span>ValuAI © {year}</span>
    </div>
  </div>
</div>"""

    # ── CONTENT PAGES — Expl blocks (Direction C style) ───────────
    items_per_page = 3
    pages_html = [cover]
    page_num = 2

    for i in range(0, len(explanations), items_per_page):
        batch = explanations[i:i + items_per_page]
        expl_blocks = ""
        for expl in batch:
            var_items = ""
            for v in (expl.get("variables") or [])[:6]:
                var_items += f"""<div class="var-item">
                  <div class="vname">{v.get("name","")}</div>
                  <div class="vdesc">{v.get("desc","")}</div>
                </div>"""
            var_grid = f'<div class="var-grid">{var_items}</div>' if var_items else ""
            expl_blocks += f"""
<div class="expl-block">
  <div class="expl-left">
    <div class="cat">Phương pháp</div>
    <div class="nm">{expl.get("title","")}</div>
    <div class="fx">{expl.get("formula","")}</div>
  </div>
  <div class="expl-right">
    <div class="body-txt">{expl.get("body","")}</div>
    {var_grid}
  </div>
</div>"""

        pages_html.append(f"""
<div class="page">
  <div class="page-tag">{page_num}</div>
  <div class="sec">
    <div class="sec-hd">
      <div class="num">{page_num:02d}</div>
      <div>
        <h2>Phương Pháp &amp; Công Thức</h2>
        <div class="en">Methodology &amp; Formulas</div>
      </div>
    </div>
    {expl_blocks}
    <div class="pagefoot">
      <span>ValuAI — Explainer</span>
      <span>Trang {page_num}</span>
    </div>
  </div>
</div>""")
        page_num += 1

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>ValuAI — Explainer</title>
{FONTS}
{build_styles(accent, theme, custom_css)}
</head>
<body>
{build_theme_bar(theme, custom_css)}
<div id="stage">
{"".join(pages_html)}
</div>
</body>
</html>"""
