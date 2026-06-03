"""Explainer HTML renderer — explains methodology via Playwright PDF."""
import datetime
from explanations_default import EXPLANATIONS_DEFAULT
from html_themes import FONTS, STYLE_JS, build_styles, build_swatches


def render_explainer_html(config: dict = None, brand: dict = None) -> str:
    config = config or {}
    brand = brand or {}
    content = config.get("content", {})
    explanations = content.get("explanations") or EXPLANATIONS_DEFAULT

    colors = config.get("style", {}).get("colors", {})
    accent = brand.get("accent") or colors.get("accent", "#b08d57")
    custom_css = config.get("style", {}).get("report_css", {}).get("custom_css", "")

    title = content.get("explainer_title", "GIẢI THÍCH PHƯƠNG PHÁP ĐỊNH GIÁ")
    subtitle = content.get("explainer_subtitle", "Hướng dẫn đọc báo cáo ValuAI")
    intro = content.get("explainer_intro",
        "Tài liệu này giải thích các công thức, chỉ số và phương pháp phân tích "
        "được sử dụng trong báo cáo định giá ValuAI.")
    today = datetime.date.today().strftime("%d/%m/%Y")
    year = datetime.date.today().year

    # ── TOOLBAR ───────────────────────────────────────────────────
    toolbar = f"""
<div class="toolbar">
  <div class="tb-brand">ValuAI<b>Explainer</b></div>
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
</div>"""

    # ── COVER PAGE ─────────────────────────────────────────────────
    toc_items = "".join(
        f'<div style="font-size:11.5px;color:var(--ink-soft);padding:5px 0;border-bottom:1px solid var(--line-soft);display:flex;gap:10px;">'
        f'<span style="color:var(--accent);font-weight:700;font-family:var(--mono);font-size:11px;min-width:20px;">{i:02d}</span>'
        f'<span>{e.get("title","")}</span></div>'
        for i, e in enumerate(explanations, 1)
    )
    cover = f"""
<div class="page">
  <div class="wm">EXPLAINER</div>
  <div class="page-tag">Cover</div>
  <div class="cov">
    <div class="top">
      <div class="logo"><i>V</i>ValuAI</div>
      <div class="kicker">Phương Pháp Định Giá &nbsp;·&nbsp; {today}</div>
    </div>
    <div style="margin-top:auto;">
      <div class="ribbon"></div>
      <div class="kicker">HƯỚNG DẪN ĐỌC BÁO CÁO</div>
      <h1>Explainer</h1>
      <div class="company">{title}</div>
      <div class="intro">{intro}</div>
      <div style="margin-top:28px;">
        <div style="font-family:var(--head);font-size:14px;font-weight:700;color:var(--ink);margin-bottom:12px;">Mục lục</div>
        {toc_items}
      </div>
    </div>
    <div class="foot">
      <span class="disc">Tài liệu bổ sung cho báo cáo định giá</span>
      <span>ValuAI © {year}</span>
    </div>
  </div>
</div>"""

    # ── CONTENT PAGES — Direction C (1 explanation per page) ──────
    pages_html = [cover]
    for i, expl in enumerate(explanations, 1):
        vars_html = ""
        for v in (expl.get("variables") or [])[:6]:
            vars_html += f"""<div>
              <div class="lab">{v.get("name","")}</div>
              <div class="tx s">{v.get("desc","")}</div>
            </div>"""

        pages_html.append(f"""
<div class="page">
  <div class="page-tag">{i:02d}</div>
  <div class="c-wrap">
    <div class="c-side">
      <div class="big">{i:02d}</div>
      <div class="lbl">PHƯƠNG PHÁP</div>
      <h2>{expl.get("title","")}</h2>
      <div class="en">Methodology</div>
      <div class="d">{expl.get("formula","")}</div>
      <div class="sidefoot">ValuAI Explainer<br>Trang {i + 1}</div>
    </div>
    <div class="c-main">
      <div class="c-metric">
        <div class="nm">Giải thích</div>
        <div class="tx" style="margin-top:10px;font-size:12.5px;line-height:1.7;color:var(--ink-soft);">{expl.get("body","")}</div>
      </div>
      {f'<div class="c-metric"><div class="nm">Biến số</div><div class="grid2" style="margin-top:12px;">{vars_html}</div></div>' if vars_html else ""}
      <div class="c-mainfoot">
        <span>ValuAI — Phương pháp định giá</span>
        <span>Trang {i + 1}</span>
      </div>
    </div>
  </div>
</div>""")

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>ValuAI — Explainer</title>
{FONTS}
{build_styles(accent, custom_css)}
</head>
<body>
{toolbar}
<div id="stage">
{"".join(pages_html)}
</div>
{STYLE_JS}
</body>
</html>"""
