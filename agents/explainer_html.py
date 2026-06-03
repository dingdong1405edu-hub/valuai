"""Explainer HTML renderer — explains methodology via Playwright PDF."""
from explanations_default import EXPLANATIONS_DEFAULT


def _css_vars(config: dict, brand: dict) -> str:
    colors = config.get("style", {}).get("colors", {})
    css = config.get("style", {}).get("report_css", {})
    primary = brand.get("primary") or colors.get("primary", "#1e3a8a")
    secondary = brand.get("secondary") or colors.get("secondary", "#2563eb")
    primary_light = brand.get("primary_light") or colors.get("primary_light", "#eff6ff")
    text_primary = colors.get("text_primary", "#1f2937")
    text_body = colors.get("text_body", "#374151")
    text_muted = colors.get("text_muted", "#6b7280")
    border = colors.get("border", "#d1d5db")
    grid = colors.get("grid", "#e5e7eb")
    stripe = colors.get("stripe", "#f8fafc")
    head = css.get("head", "Inter, system-ui, sans-serif")
    return f"""
:root {{
  --primary: {primary};
  --secondary: {secondary};
  --primary-light: {primary_light};
  --ink: {text_primary};
  --ink-soft: {text_body};
  --muted: {text_muted};
  --line: {border};
  --line-soft: {grid};
  --grey-fill: {stripe};
  --head: {head};
}}
"""


def render_explainer_html(config: dict = None, brand: dict = None) -> str:
    config = config or {}
    brand = brand or {}
    content = config.get("content", {})
    explanations = content.get("explanations") or EXPLANATIONS_DEFAULT

    css_vars = _css_vars(config, brand)
    title = content.get("explainer_title", "GIẢI THÍCH PHƯƠNG PHÁP ĐỊNH GIÁ")
    subtitle = content.get("explainer_subtitle", "Hướng dẫn đọc báo cáo ValuAI")
    intro = content.get("explainer_intro", "")

    style = f"""
<style>
{css_vars}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: var(--head); color: var(--ink); background: white; }}
.sheet {{
  width: 210mm;
  min-height: 297mm;
  page-break-after: always;
  display: flex;
  flex-direction: column;
}}
.header {{
  background: var(--primary);
  color: white;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 700;
}}
.accent-bar {{ height: 4px; background: var(--secondary); }}
.body {{ flex: 1; padding: 18px 22px; }}
.footer {{
  background: var(--primary);
  color: rgba(255,255,255,0.75);
  font-size: 8px;
  padding: 5px 20px;
  display: flex;
  justify-content: space-between;
}}
.page-title {{
  font-size: 18px;
  font-weight: 800;
  color: var(--primary);
  margin-bottom: 6px;
}}
.page-subtitle {{
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 12px;
}}
.intro {{
  font-size: 10px;
  color: var(--ink-soft);
  line-height: 1.6;
  margin-bottom: 16px;
  padding: 10px 14px;
  background: var(--grey-fill);
  border-radius: 6px;
  border-left: 3px solid var(--primary);
}}
.expl-card {{
  margin-bottom: 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
}}
.expl-header {{
  background: var(--primary-light);
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 700;
  color: var(--primary);
  border-bottom: 1px solid var(--line);
}}
.expl-formula {{
  background: var(--primary);
  color: white;
  padding: 6px 14px;
  font-size: 9px;
  font-family: monospace;
  letter-spacing: 0.5px;
}}
.expl-body {{
  padding: 10px 14px;
  font-size: 9.5px;
  color: var(--ink-soft);
  line-height: 1.65;
}}
.var-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
.var-table th {{
  background: var(--primary);
  color: white;
  font-size: 8.5px;
  padding: 4px 8px;
  text-align: left;
}}
.var-table td {{
  font-size: 8.5px;
  padding: 4px 8px;
  border-bottom: 1px solid var(--line-soft);
}}
.var-table tr:nth-child(even) td {{ background: var(--grey-fill); }}
.var-name {{ font-weight: 700; color: var(--primary); font-family: monospace; }}
</style>
"""

    pages_html = []
    items_per_page = 3
    today_str = __import__("datetime").date.today().strftime("%d/%m/%Y")

    cover_html = f"""
<div class="sheet">
  <div class="header">{title}</div>
  <div class="accent-bar"></div>
  <div class="body">
    <div class="page-title">{title}</div>
    <div class="page-subtitle">{subtitle}</div>
    <div class="intro">{intro}</div>
    <div style="font-size:11px;font-weight:700;color:var(--primary);margin-bottom:10px;">
      MỤC LỤC PHƯƠNG PHÁP
    </div>
    <ul style="list-style:none;padding-left:0;">
"""
    for i, expl in enumerate(explanations, 1):
        cover_html += f'<li style="font-size:10px;color:var(--ink-soft);padding:3px 0;border-bottom:1px solid var(--line-soft);">{i}. {expl.get("title","")}</li>\n'
    cover_html += """
    </ul>
  </div>
  <div class="footer">
    <span>ValuAI — Explainer</span>
    <span>Trang 1</span>
  </div>
</div>
"""
    pages_html.append(cover_html)

    page_num = 2
    for i in range(0, len(explanations), items_per_page):
        batch = explanations[i:i + items_per_page]
        cards_html = ""
        for expl in batch:
            vars_rows = ""
            for v in expl.get("variables", []):
                vars_rows += f"""
<tr>
  <td><span class="var-name">{v.get('name','')}</span></td>
  <td>{v.get('desc','')}</td>
</tr>"""
            var_table = f"""
<table class="var-table">
  <tr><th>Biến số</th><th>Định nghĩa</th></tr>
  {vars_rows}
</table>""" if vars_rows else ""

            cards_html += f"""
<div class="expl-card">
  <div class="expl-header">{expl.get('title','')}</div>
  <div class="expl-formula">{expl.get('formula','')}</div>
  <div class="expl-body">
    <p>{expl.get('body','')}</p>
    {var_table}
  </div>
</div>
"""

        pages_html.append(f"""
<div class="sheet">
  <div class="header">{title}</div>
  <div class="accent-bar"></div>
  <div class="body">
    {cards_html}
  </div>
  <div class="footer">
    <span>ValuAI — Explainer</span>
    <span>Trang {page_num}</span>
  </div>
</div>
""")
        page_num += 1

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>ValuAI — Explainer</title>
{style}
</head>
<body>
{"".join(pages_html)}
</body>
</html>"""
    return html
