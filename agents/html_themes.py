"""Shared design system for all HTML report renderers.
CSS is used verbatim from the design spec. Users pick style via
accent swatches + serif/sans toggle in the toolbar.
"""

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,400;0,600;0,700;1,400'
    '&family=IBM+Plex+Serif:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600'
    '&family=Architects+Daughter&display=swap" rel="stylesheet">'
)

# Verbatim CSS from design spec
CSS = """\
:root{
  --ink:#1a2b4a;
  --ink-soft:#3a4a66;
  --accent:#b08d57;
  --line:#c9cfd9;
  --line-soft:#e4e8ef;
  --paper:#ffffff;
  --bg:#6b7280;
  --grey-fill:#eef1f5;
  --sans:'IBM Plex Sans',sans-serif;
  --serif:'IBM Plex Serif',serif;
  --mono:'IBM Plex Mono',monospace;
  --hand:'Architects Daughter',cursive;
  --head:var(--serif);
}
*{box-sizing:border-box;margin:0;padding:0;}
html,body{background:var(--bg);font-family:var(--sans);color:var(--ink);}

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
.tb-group{display:flex;align-items:center;gap:9px;margin-left:auto;font-size:11px;}
.tb-label{font-family:var(--hand);font-size:14px;opacity:.8;}
.swatch{width:22px;height:22px;border-radius:50%;border:2px solid #ffffff55;cursor:pointer;padding:0;}
.swatch.on{border-color:#fff;box-shadow:0 0 0 2px var(--ink);}
.ftoggle{display:flex;border:1.5px solid #ffffff40;border-radius:7px;overflow:hidden;}
.ftoggle button{background:transparent;color:#fff;border:0;padding:5px 11px;font-size:11px;cursor:pointer;font-family:var(--sans);}
.ftoggle button.on{background:#fff;color:var(--ink);}

.note{padding:14px 24px;color:#fff;font-family:var(--hand);font-size:15px;opacity:.9;display:flex;gap:8px;align-items:baseline;}
.note span{font-family:var(--sans);font-size:11px;letter-spacing:1px;text-transform:uppercase;background:#ffffff22;padding:2px 8px;border-radius:20px;font-weight:600;}

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

.cov{height:1123px;display:flex;flex-direction:column;padding:74px 76px 60px;position:relative;z-index:1;}
.cov .top{display:flex;justify-content:space-between;align-items:flex-start;}
.cov .kicker{font-family:var(--sans);font-size:11px;letter-spacing:3px;text-transform:uppercase;color:var(--accent);font-weight:600;}
.cov h1{font-family:var(--head);font-weight:700;font-size:52px;line-height:1.05;color:var(--ink);margin-top:auto;max-width:11ch;letter-spacing:-.5px;}
.cov .sub{font-family:var(--sans);font-size:16px;color:var(--ink-soft);margin-top:18px;}
.cov .sub b{color:var(--accent);font-weight:600;}
.cov .company{margin-top:30px;font-family:var(--head);font-size:22px;font-weight:600;}
.cov .intro{margin-top:14px;font-size:14px;line-height:1.7;color:var(--ink-soft);max-width:62ch;border-left:3px solid var(--accent);padding-left:16px;}
.cov .foot{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;font-size:12px;color:var(--ink-soft);border-top:1px solid var(--line);padding-top:16px;}
.cov .disc{font-style:italic;}
.ribbon{height:8px;width:120px;background:var(--accent);margin-bottom:34px;}
.lock-box{background:var(--grey-fill);border:1.5px dashed var(--line);border-radius:10px;padding:22px 28px;margin-top:28px;text-align:center;}
.lock-box .lbl{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:10px;}
.lock-box .val{font-size:26px;font-weight:700;font-family:var(--mono);color:#c9cfd9;letter-spacing:4px;}
.lock-box .note-txt{font-size:11px;color:var(--ink-soft);margin-top:10px;font-family:var(--hand);}

.sec{padding:64px 64px 80px;position:relative;z-index:1;height:1123px;display:flex;flex-direction:column;}
.pagefoot{position:absolute;left:64px;right:64px;bottom:34px;display:flex;justify-content:space-between;
  font-size:10.5px;color:var(--ink-soft);border-top:1px solid var(--line-soft);padding-top:10px;}
.legend{display:flex;gap:18px;font-size:10px;color:var(--ink-soft);}
.legend i{font-style:normal;display:inline-flex;align-items:center;gap:5px;}
.legend i::before{content:"";width:9px;height:9px;border-radius:2px;background:var(--accent);}
.legend i.src::before{background:var(--ink);}
.legend i.mean::before{background:var(--grey-fill);border:1px solid var(--line);}

.a-head{margin-bottom:22px;}
.a-eyebrow{display:flex;align-items:center;gap:12px;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--ink-soft);font-weight:600;}
.a-eyebrow b{color:var(--accent);}
.a-title{font-family:var(--head);font-size:32px;font-weight:700;margin-top:6px;}
.a-en{font-family:var(--hand);color:var(--accent);font-size:17px;}
.a-desc{font-size:13px;color:var(--ink-soft);margin-top:6px;max-width:70ch;}
table.ledger{width:100%;border-collapse:collapse;margin-top:20px;font-size:12px;table-layout:fixed;}
table.ledger col.c-name{width:23%;}
table.ledger col.c-f{width:30%;}
table.ledger col.c-s{width:24%;}
table.ledger col.c-m{width:23%;}
.ledger thead th{background:var(--ink);color:#fff;text-align:left;padding:11px 12px;font-size:10.5px;letter-spacing:1px;text-transform:uppercase;font-weight:600;}
.ledger tbody td{border-bottom:1px solid var(--line-soft);padding:13px 12px;vertical-align:top;line-height:1.5;}
.ledger tbody tr:nth-child(even) td{background:#f7f9fb;}
.ledger .nm{font-weight:600;color:var(--ink);font-size:12.5px;}
.ledger .fx{font-family:var(--mono);font-size:11px;color:var(--ink);background:var(--grey-fill);padding:6px 8px;border-radius:4px;display:inline-block;}
.ledger .sr{color:var(--ink-soft);}
.ledger .mn{color:var(--ink);}
.ledger .mn b{color:var(--accent);}

.b-head{display:flex;align-items:flex-end;gap:18px;border-bottom:3px solid var(--ink);padding-bottom:14px;margin-bottom:24px;}
.b-num{font-family:var(--head);font-size:64px;font-weight:700;color:var(--accent);line-height:.8;}
.b-htext h2{font-family:var(--head);font-size:30px;font-weight:700;}
.b-htext .en{font-family:var(--hand);color:var(--ink-soft);font-size:16px;}
.b-htext .d{font-size:13px;color:var(--ink-soft);margin-top:4px;max-width:64ch;}
.band{display:grid;grid-template-columns:34% 1fr;border:1px solid var(--line);border-radius:8px;overflow:hidden;margin-bottom:14px;}
.band .left{background:var(--ink);color:#fff;padding:16px 18px;display:flex;flex-direction:column;justify-content:center;}
.band .left .nm{font-family:var(--head);font-weight:600;font-size:16px;line-height:1.25;}
.band .left .fx{font-family:var(--mono);font-size:11px;color:#cdd6e6;margin-top:10px;line-height:1.5;border-top:1px solid #ffffff22;padding-top:9px;}
.band .right{padding:14px 18px;display:flex;flex-direction:column;gap:10px;justify-content:center;}
.cell .lab{font-size:9.5px;letter-spacing:1.5px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:2px;}
.cell .val{font-size:12.5px;line-height:1.5;color:var(--ink);}
.cell.src .val{color:var(--ink-soft);}

.c-wrap{display:grid;grid-template-columns:236px 1fr;height:1123px;}
.c-side{background:var(--ink);color:#fff;padding:60px 28px;position:relative;display:flex;flex-direction:column;}
.c-side .big{font-family:var(--head);font-size:90px;font-weight:700;color:#ffffff1c;line-height:.8;}
.c-side .lbl{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-top:26px;}
.c-side h2{font-family:var(--head);font-size:27px;font-weight:600;margin-top:8px;line-height:1.15;}
.c-side .en{font-family:var(--hand);font-size:16px;color:#cdd6e6;margin-top:4px;}
.c-side .d{font-size:12.5px;line-height:1.65;color:#c2cad8;margin-top:22px;border-top:1px solid #ffffff22;padding-top:18px;}
.c-side .sidefoot{margin-top:auto;font-size:10px;color:#9aa6bd;line-height:1.6;}
.c-main{padding:56px 48px;position:relative;display:flex;flex-direction:column;}
.c-metric{padding:16px 0;border-bottom:1px solid var(--line-soft);}
.c-metric:last-of-type{border-bottom:0;}
.c-metric .nm{font-family:var(--head);font-weight:600;font-size:16px;color:var(--ink);}
.c-metric .fx{font-family:var(--mono);font-size:11px;color:var(--ink);background:var(--grey-fill);padding:6px 9px;border-radius:4px;display:inline-block;margin:8px 0 9px;}
.c-metric .grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.c-metric .lab{font-size:9px;letter-spacing:1.5px;text-transform:uppercase;font-weight:600;color:var(--accent);margin-bottom:2px;}
.c-metric .lab.s{color:var(--ink-soft);}
.c-metric .tx{font-size:11.5px;line-height:1.5;color:var(--ink);}
.c-metric .tx.s{color:var(--ink-soft);}
.c-mainfoot{margin-top:auto;padding-top:14px;border-top:1px solid var(--line-soft);display:flex;justify-content:space-between;font-size:10px;color:var(--ink-soft);}

/* pg-section tabs for valuation admin */
.pg-section{display:none;}
.pg-section.active{display:flex;flex-direction:column;align-items:center;gap:34px;}

@media print{.toolbar,.note{display:none;}}
"""

# JS for accent swatch + font toggle switching
STYLE_JS = """\
<script>
function setAccent(btn){
  document.documentElement.style.setProperty('--accent',btn.dataset.accent);
  document.querySelectorAll('.swatch').forEach(function(s){s.classList.toggle('on',s===btn);});
  try{localStorage.setItem('vA',btn.dataset.accent);}catch(e){}
}
function setFont(btn){
  var f=btn.dataset.f;
  document.documentElement.style.setProperty('--head',f==='serif'?'var(--serif)':'var(--sans)');
  document.querySelectorAll('.ftoggle button').forEach(function(b){b.classList.toggle('on',b===btn);});
  try{localStorage.setItem('vF',f);}catch(e){}
}
window.addEventListener('DOMContentLoaded',function(){
  try{
    var a=localStorage.getItem('vA'),f=localStorage.getItem('vF');
    if(a){document.documentElement.style.setProperty('--accent',a);document.querySelectorAll('.swatch').forEach(function(s){s.classList.toggle('on',s.dataset.accent===a);});}
    if(f){document.documentElement.style.setProperty('--head',f==='serif'?'var(--serif)':'var(--sans)');document.querySelectorAll('.ftoggle button').forEach(function(b){b.classList.toggle('on',b.dataset.f===f);});}
  }catch(e){}
});
</script>"""


def build_styles(accent: str, custom_css: str = "") -> str:
    """Full CSS: design system + accent override + admin custom CSS."""
    out = f"<style>{CSS}</style>\n<style>:root{{--accent:{accent};}}</style>"
    if custom_css and custom_css.strip():
        out += f"\n<style id='custom-css'>{custom_css}</style>"
    return out


def build_swatches(accent: str) -> str:
    """3 swatch buttons: brand accent + blue + green."""
    colors = [accent, "#2563eb", "#10b981"]
    return "".join(
        f'<button class="swatch{" on" if i == 0 else ""}" '
        f'style="background:{c}" data-accent="{c}" onclick="setAccent(this)"></button>'
        for i, c in enumerate(colors)
    )
