"""Shared theme system for all HTML report renderers."""

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,400;0,600;0,700;1,400'
    '&family=IBM+Plex+Serif:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600'
    '&family=Architects+Daughter&display=swap" rel="stylesheet">'
)

# ── 3 THEME PRESETS ───────────────────────────────────────────────────────────
# Each theme sets CSS variables + optional element overrides.
# --accent is always injected separately from brand scraper.
THEME_CSS = {
    "A": """\
:root{
  --ink:#1a2b4a;--ink-soft:#3a4a66;
  --line:#c9cfd9;--line-soft:#e4e8ef;
  --paper:#ffffff;--bg:#6b7280;--grey-fill:#eef1f5;
  --sans:'IBM Plex Sans',sans-serif;--serif:'IBM Plex Serif',serif;
  --mono:'IBM Plex Mono',monospace;--hand:'Architects Daughter',cursive;
  --head:var(--serif);
}""",
    "B": """\
:root{
  --ink:#1e3a5f;--ink-soft:#2d5282;
  --line:#bfdbfe;--line-soft:#dbeafe;
  --paper:#ffffff;--bg:#4a5568;--grey-fill:#eff6ff;
  --sans:'IBM Plex Sans',sans-serif;--serif:'IBM Plex Serif',serif;
  --mono:'IBM Plex Mono',monospace;--hand:'Architects Daughter',cursive;
  --head:var(--sans);
}
.band .left,.c-side,.expl-left{background:#1e40af;}
.ledger thead th{background:#1e40af;}
.cov h1{color:var(--ink);}""",
    "C": """\
:root{
  --ink:#0f172a;--ink-soft:#1e293b;
  --line:#e2e8f0;--line-soft:#f1f5f9;
  --paper:#fafafa;--bg:#374151;--grey-fill:#f0fdf4;
  --sans:'IBM Plex Sans',sans-serif;--serif:'IBM Plex Serif',serif;
  --mono:'IBM Plex Mono',monospace;--hand:'Architects Daughter',cursive;
  --head:var(--sans);
}
.band .left,.c-side,.expl-left{background:#0f172a;}
.ledger thead th{background:#0f172a;}
.ribbon{height:10px;}""",
}

THEME_META = {
    "A": ("Classique", "Serif · Navy · Formal"),
    "B": ("Corporate", "Sans · Blue · Modern"),
    "C": ("Contrast",  "Bold · Dark · Fresh"),
}

# ── BASE STRUCTURAL CSS (layout only, no color values) ───────────────────────
BASE_CSS = """\
*{box-sizing:border-box;margin:0;padding:0;}
html,body{font-family:var(--sans);color:var(--ink);}
body{background:var(--bg);}
/* ── theme bar ── */
.theme-bar{display:flex;align-items:center;gap:10px;background:#111827;padding:10px 22px;position:sticky;top:0;z-index:60;flex-wrap:wrap;}
.th-lbl{font-family:var(--hand);font-size:12px;color:#9aa6bd;margin-right:4px;}
.th-btn{background:transparent;border:1.5px solid #ffffff30;color:#fff;padding:4px 14px;border-radius:6px;cursor:pointer;font-size:12px;line-height:1.3;transition:.12s;}
.th-btn b{font-family:var(--mono);display:block;font-size:13px;}
.th-btn small{font-size:9px;opacity:.5;display:block;letter-spacing:.5px;}
.th-btn.on{background:#fff;color:#111827;border-color:#fff;}
.th-btn:hover:not(.on){border-color:#ffffff70;}
/* ── A4 pages ── */
#stage{padding:30px 0 80px;display:flex;flex-direction:column;align-items:center;gap:34px;}
.page{width:794px;min-height:1123px;background:var(--paper);position:relative;box-shadow:0 18px 50px #00000040;overflow:hidden;}
.page-tag{position:absolute;top:14px;right:18px;font-family:var(--hand);font-size:13px;color:var(--accent);transform:rotate(3deg);opacity:.85;z-index:5;}
.wm{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) rotate(-28deg);font-family:var(--hand);font-size:120px;color:#1a2b4a08;letter-spacing:6px;pointer-events:none;z-index:0;font-weight:400;white-space:nowrap;}
.logo{display:inline-flex;align-items:center;gap:8px;font-family:var(--hand);font-size:13px;color:var(--ink-soft);}
.logo i{width:26px;height:26px;border:1.5px dashed var(--ink-soft);border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-style:normal;font-size:11px;font-family:var(--sans);font-weight:700;}
/* ── cover ── */
.cov{height:1123px;display:flex;flex-direction:column;padding:74px 76px 60px;position:relative;z-index:1;}
.cov .top{display:flex;justify-content:space-between;align-items:flex-start;}
.cov .kicker{font-family:var(--sans);font-size:11px;letter-spacing:3px;text-transform:uppercase;color:var(--accent);font-weight:600;}
.cov h1{font-family:var(--head);font-weight:700;font-size:50px;line-height:1.05;color:var(--ink);margin-top:auto;letter-spacing:-.5px;}
.cov .sub{font-family:var(--sans);font-size:16px;color:var(--ink-soft);margin-top:18px;}
.cov .sub b{color:var(--accent);font-weight:600;}
.cov .intro{margin-top:22px;font-size:14px;line-height:1.7;color:var(--ink-soft);max-width:62ch;border-left:3px solid var(--accent);padding-left:16px;}
.cov .foot{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;font-size:12px;color:var(--ink-soft);border-top:1px solid var(--line);padding-top:16px;}
.cov .disc{font-style:italic;}
.ribbon{height:8px;width:120px;background:var(--accent);margin-bottom:34px;}
.lock-box{background:var(--grey-fill);border:1.5px dashed var(--line);border-radius:10px;padding:24px 30px;margin-top:30px;text-align:center;}
.lock-box .lbl{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:10px;}
.lock-box .val{font-size:28px;font-weight:700;font-family:var(--mono);color:#c9cfd9;letter-spacing:5px;}
.lock-box .note{font-size:11px;color:var(--ink-soft);margin-top:10px;font-family:var(--hand);}
/* ── section shared ── */
.sec{padding:64px 64px 100px;position:relative;z-index:1;min-height:1123px;display:flex;flex-direction:column;}
.pagefoot{position:absolute;left:64px;right:64px;bottom:34px;display:flex;justify-content:space-between;font-size:10.5px;color:var(--ink-soft);border-top:1px solid var(--line-soft);padding-top:10px;}
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
/* ── Direction A — Ledger ── */
.a-head{margin-bottom:20px;}
.a-eyebrow{display:flex;align-items:center;gap:12px;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--ink-soft);font-weight:600;}
.a-eyebrow b{color:var(--accent);}
.a-title{font-family:var(--head);font-size:32px;font-weight:700;margin-top:6px;}
.a-en{font-family:var(--hand);color:var(--accent);font-size:17px;}
.ind-box{background:var(--grey-fill);border-radius:8px;padding:16px 20px;margin-bottom:18px;border-left:4px solid var(--accent);}
.ind-box .nm{font-family:var(--head);font-size:17px;font-weight:700;margin-bottom:6px;}
.ind-box .ov{font-size:11.5px;color:var(--ink-soft);line-height:1.6;}
.ind-box .meta{display:flex;gap:22px;font-size:11px;color:var(--ink-soft);margin-top:10px;flex-wrap:wrap;}
.ind-box .meta b{color:var(--accent);}
table.ledger{width:100%;border-collapse:collapse;font-size:12px;margin-top:14px;table-layout:fixed;}
.ledger thead th{background:var(--ink);color:#fff;text-align:left;padding:10px 12px;font-size:10px;letter-spacing:1px;text-transform:uppercase;font-weight:600;}
.ledger tbody td{border-bottom:1px solid var(--line-soft);padding:11px 12px;vertical-align:middle;}
.ledger tbody tr:nth-child(even) td{background:#f7f9fb;}
.ledger .nm{font-weight:600;color:var(--ink);}
.ledger .v{font-family:var(--mono);font-size:12px;font-weight:600;}
.ledger .accent{color:var(--accent);font-weight:700;}
.ledger .good{color:#10b981;font-weight:700;}
.ledger .warning{color:#f59e0b;font-weight:700;}
.ledger .poor{color:#ef4444;font-weight:700;}
.ledger .na{color:var(--ink-soft);}
.divider{border-top:1.5px solid var(--line);margin:20px 0;}
/* ── Direction B — Banded rows ── */
.b-head{display:flex;align-items:flex-end;gap:18px;border-bottom:3px solid var(--ink);padding-bottom:14px;margin-bottom:24px;}
.b-num{font-family:var(--head);font-size:64px;font-weight:700;color:var(--accent);line-height:.8;}
.b-htext h2{font-family:var(--head);font-size:30px;font-weight:700;}
.b-htext .en{font-family:var(--hand);color:var(--ink-soft);font-size:16px;}
.b-htext .d{font-size:13px;color:var(--ink-soft);margin-top:4px;}
.band{display:grid;grid-template-columns:36% 1fr;border:1px solid var(--line);border-radius:8px;overflow:hidden;margin-bottom:11px;}
.band .left{background:var(--ink);color:#fff;padding:14px 18px;display:flex;flex-direction:column;justify-content:center;}
.band .left .nm{font-family:var(--head);font-weight:600;font-size:15px;line-height:1.25;}
.band .left .fx{font-family:var(--mono);font-size:10px;color:#cdd6e6;margin-top:8px;border-top:1px solid #ffffff22;padding-top:7px;}
.band .right{padding:12px 20px;display:flex;gap:30px;align-items:center;flex-wrap:wrap;}
.cell .lab{font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:3px;}
.cell .val{font-size:15px;font-weight:600;color:var(--ink);font-family:var(--mono);}
.cell .yoy{font-size:12px;margin-top:2px;}
.pos{color:#10b981;font-weight:700;}
.neg{color:#ef4444;font-weight:700;}
/* ── Direction C — Sidebar ── */
.c-wrap{display:grid;grid-template-columns:260px 1fr;min-height:1123px;}
.c-side{background:var(--ink);color:#fff;padding:60px 32px;display:flex;flex-direction:column;}
.c-side .big{font-family:var(--head);font-size:90px;font-weight:700;color:#ffffff1c;line-height:.8;}
.c-side .lbl{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-top:26px;}
.c-side h2{font-family:var(--head);font-size:26px;font-weight:600;margin-top:8px;line-height:1.15;}
.c-side .en{font-family:var(--hand);font-size:15px;color:#cdd6e6;margin-top:4px;}
.c-side .d{font-size:12px;line-height:1.65;color:#c2cad8;margin-top:22px;border-top:1px solid #ffffff22;padding-top:18px;}
.c-side .sidefoot{margin-top:auto;font-size:10px;color:#9aa6bd;line-height:1.6;}
.c-main{padding:50px 44px;display:flex;flex-direction:column;}
.c-list{flex:1;display:flex;flex-direction:column;justify-content:center;}
.c-row{display:flex;align-items:flex-start;gap:16px;padding:13px 0;border-bottom:1px solid var(--line-soft);}
.c-row:last-child{border-bottom:0;}
.c-row .ico{font-size:18px;flex-shrink:0;margin-top:1px;}
.c-row .txt .nm{font-family:var(--head);font-size:14px;font-weight:600;color:var(--ink);}
.c-row .txt .d{font-size:11px;color:var(--ink-soft);line-height:1.5;margin-top:2px;}
.cta-row{display:flex;align-items:flex-start;gap:16px;padding:13px 0;border-bottom:1px solid var(--line-soft);}
.cta-row:last-child{border-bottom:0;}
.cta-row .ico{font-size:18px;flex-shrink:0;margin-top:1px;}
.cta-row .txt .nm{font-family:var(--head);font-size:14px;font-weight:600;color:var(--ink);}
.cta-row .txt .d{font-size:11px;color:var(--ink-soft);line-height:1.5;margin-top:2px;}
.c-mainfoot{margin-top:auto;padding-top:14px;border-top:1px solid var(--line-soft);display:flex;justify-content:space-between;font-size:10px;color:var(--ink-soft);}
/* ── Explainer blocks ── */
.cov .toc{margin-top:28px;}
.cov .toc-title{font-family:var(--head);font-size:14px;font-weight:700;color:var(--ink);margin-bottom:12px;}
.cov .toc-item{font-size:11.5px;color:var(--ink-soft);padding:5px 0;border-bottom:1px solid var(--line-soft);display:flex;gap:10px;}
.cov .toc-item .num{color:var(--accent);font-weight:700;font-family:var(--mono);font-size:11px;min-width:20px;}
.sec-hd{display:flex;align-items:flex-end;gap:18px;border-bottom:3px solid var(--ink);padding-bottom:14px;margin-bottom:28px;}
.sec-hd .num{font-family:var(--head);font-size:56px;font-weight:700;color:var(--accent);line-height:.8;}
.sec-hd h2{font-family:var(--head);font-size:26px;font-weight:700;}
.sec-hd .en{font-family:var(--hand);color:var(--ink-soft);font-size:15px;}
.expl-block{display:grid;grid-template-columns:200px 1fr;border:1px solid var(--line);border-radius:10px;overflow:hidden;margin-bottom:16px;}
.expl-left{background:var(--ink);color:#fff;padding:18px 20px;display:flex;flex-direction:column;}
.expl-left .nm{font-family:var(--head);font-weight:600;font-size:14px;line-height:1.3;}
.expl-left .cat{font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:8px;}
.expl-left .fx{font-family:var(--mono);font-size:9.5px;color:#cdd6e6;margin-top:12px;line-height:1.6;border-top:1px solid #ffffff22;padding-top:10px;word-break:break-all;}
.expl-right{padding:16px 20px;display:flex;flex-direction:column;gap:10px;}
.expl-right .body-txt{font-size:11.5px;color:var(--ink-soft);line-height:1.65;}
.var-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px 14px;margin-top:8px;}
.var-item .vname{font-family:var(--mono);font-size:9.5px;color:var(--accent);font-weight:600;}
.var-item .vdesc{font-size:10px;color:var(--ink-soft);margin-top:1px;}
/* ── print ── */
@media print{
  .theme-bar{display:none!important;}
  body{background:white;padding:0;}
  #stage{padding:0;gap:0;}
  .page{box-shadow:none;}
}"""


def _js_esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")


def build_styles(accent: str, default_theme: str, custom_css: str) -> str:
    """Returns complete <style> tags: base structural + accent var + initial theme + custom."""
    t = THEME_CSS.get(default_theme, THEME_CSS["A"])
    safe_custom = custom_css or ""
    return (
        f"<style>{BASE_CSS}</style>\n"
        f'<style id="accent-css">:root{{--accent:{accent};}}</style>\n'
        f'<style id="theme-css">{t}</style>\n'
        f'<style id="custom-css">{safe_custom}</style>'
    )


def build_theme_bar(default_theme: str, custom_css: str) -> str:
    """Returns theme switcher bar + JS. Hidden in @media print."""
    btns = "".join(
        f'<button class="th-btn{" on" if t == default_theme else ""}" '
        f'onclick="setTheme(\'{t}\')" data-t="{t}">'
        f'<b>{t}</b><small>{THEME_META[t][0]}</small></button>'
        for t in ["A", "B", "C"]
    )
    themes_js = ", ".join(
        f'"{t}": `{_js_esc(THEME_CSS[t])}`' for t in ["A", "B", "C"]
    )
    safe_acc = _js_esc(f":root{{--accent:{default_theme};}}")  # placeholder, accent-css tag keeps real value
    return f"""<div class="theme-bar">
  <span class="th-lbl">Style</span>
  {btns}
</div>
<script>
const _TH={{{themes_js}}};
function setTheme(t){{
  var el=document.getElementById('theme-css');
  if(el&&_TH[t])el.textContent=_TH[t];
  document.querySelectorAll('.th-btn').forEach(function(b){{b.classList.toggle('on',b.dataset.t===t);}});
  try{{localStorage.setItem('vt',t);}}catch(e){{}}
}}
window.addEventListener('DOMContentLoaded',function(){{
  var saved;try{{saved=localStorage.getItem('vt');}}catch(e){{}}
  setTheme(saved||'{default_theme}');
}});
</script>"""
