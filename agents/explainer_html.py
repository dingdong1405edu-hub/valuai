"""Explainer HTML renderer — explains methodology via Playwright PDF."""
import datetime
from explanations_default import EXPLANATIONS_DEFAULT

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
.cov h1{{font-family:var(--head);font-weight:700;font-size:46px;line-height:1.05;color:var(--ink);margin-top:auto;letter-spacing:-.5px;}}
.cov .sub{{font-family:var(--sans);font-size:15px;color:var(--ink-soft);margin-top:16px;}}
.cov .intro{{margin-top:20px;font-size:13.5px;line-height:1.7;color:var(--ink-soft);max-width:62ch;border-left:3px solid var(--accent);padding-left:16px;}}
.cov .toc{{margin-top:28px;}}
.cov .toc-title{{font-family:var(--head);font-size:14px;font-weight:700;color:var(--ink);margin-bottom:12px;}}
.cov .toc-item{{font-size:11.5px;color:var(--ink-soft);padding:5px 0;border-bottom:1px solid var(--line-soft);display:flex;gap:10px;}}
.cov .toc-item .num{{color:var(--accent);font-weight:700;font-family:var(--mono);font-size:11px;min-width:20px;}}
.cov .foot{{margin-top:auto;display:flex;justify-content:space-between;font-size:12px;color:var(--ink-soft);border-top:1px solid var(--line);padding-top:16px;}}
.ribbon{{height:8px;width:120px;background:var(--accent);margin-bottom:34px;}}
/* ── SECTION ── */
.sec{{padding:64px 64px 100px;position:relative;z-index:1;min-height:1123px;display:flex;flex-direction:column;}}
.sec-hd{{display:flex;align-items:flex-end;gap:18px;border-bottom:3px solid var(--ink);padding-bottom:14px;margin-bottom:28px;}}
.sec-hd .num{{font-family:var(--head);font-size:56px;font-weight:700;color:var(--accent);line-height:.8;}}
.sec-hd h2{{font-family:var(--head);font-size:26px;font-weight:700;}}
.sec-hd .en{{font-family:var(--hand);color:var(--ink-soft);font-size:15px;}}
.pagefoot{{position:absolute;left:64px;right:64px;bottom:34px;display:flex;justify-content:space-between;font-size:10.5px;color:var(--ink-soft);border-top:1px solid var(--line-soft);padding-top:10px;}}
/* ── DIRECTION A — Ledger matrix ── */
table.ledger{{width:100%;border-collapse:collapse;font-size:12px;margin-bottom:16px;table-layout:fixed;}}
table.ledger col.c-name{{width:22%;}}
table.ledger col.c-f{{width:30%;}}
table.ledger col.c-s{{width:26%;}}
table.ledger col.c-m{{width:22%;}}
.ledger thead th{{background:var(--ink);color:#fff;text-align:left;padding:11px 12px;font-size:10.5px;letter-spacing:1px;text-transform:uppercase;font-weight:600;}}
.ledger tbody td{{border-bottom:1px solid var(--line-soft);padding:14px 12px;vertical-align:top;line-height:1.5;}}
.ledger tbody tr:nth-child(even) td{{background:#f7f9fb;}}
.ledger .nm{{font-weight:600;color:var(--ink);font-size:12.5px;}}
.ledger .fx{{font-family:var(--mono);font-size:10.5px;color:var(--ink);background:var(--grey-fill);padding:7px 9px;border-radius:4px;display:block;line-height:1.6;word-break:break-all;}}
.ledger .sr{{color:var(--ink-soft);font-size:11px;line-height:1.6;}}
.ledger .mn{{color:var(--ink);font-size:11px;line-height:1.6;}}
.ledger .mn b{{color:var(--accent);}}
/* ── DIRECTION C — Sidebar (for each explanation) ── */
.expl-block{{display:grid;grid-template-columns:200px 1fr;border:1px solid var(--line);border-radius:10px;overflow:hidden;margin-bottom:16px;}}
.expl-left{{background:var(--ink);color:#fff;padding:18px 20px;display:flex;flex-direction:column;}}
.expl-left .nm{{font-family:var(--head);font-weight:600;font-size:14px;line-height:1.3;}}
.expl-left .cat{{font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:8px;}}
.expl-left .fx{{font-family:var(--mono);font-size:9.5px;color:#cdd6e6;margin-top:12px;line-height:1.6;border-top:1px solid #ffffff22;padding-top:10px;word-break:break-all;}}
.expl-right{{padding:16px 20px;display:flex;flex-direction:column;gap:10px;}}
.expl-right .body-txt{{font-size:11.5px;color:var(--ink-soft);line-height:1.65;}}
.var-grid{{display:grid;grid-template-columns:1fr 1fr;gap:6px 14px;margin-top:8px;}}
.var-item .vname{{font-family:var(--mono);font-size:9.5px;color:var(--accent);font-weight:600;}}
.var-item .vdesc{{font-size:10px;color:var(--ink-soft);margin-top:1px;}}
@media print{{body{{background:white;padding:0;gap:0;}}.page{{box-shadow:none;}}}}
</style>"""


def render_explainer_html(config: dict = None, brand: dict = None) -> str:
    config = config or {}
    brand = brand or {}
    content = config.get("content", {})
    explanations = content.get("explanations") or EXPLANATIONS_DEFAULT

    colors = config.get("style", {}).get("colors", {})
    accent = brand.get("accent") or colors.get("accent", "#b08d57")

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

    # ── CONTENT PAGES — Direction A (ledger) ──────────────────────
    # Group explanations: use ledger table, 1 explanation per row
    # Each page holds ~4 explanation rows
    items_per_page = 3
    pages_html = [cover]
    page_num = 2

    for i in range(0, len(explanations), items_per_page):
        batch = explanations[i:i + items_per_page]
        expl_blocks = ""
        for expl in batch:
            # Build variables mini grid
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
{_FONTS}
{_css(accent)}
</head>
<body>
{"".join(pages_html)}
</body>
</html>"""
