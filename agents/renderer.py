"""Agent 8a — Matplotlib renderer: full ~37-page valuation PDF."""
import base64
import io
import threading
from datetime import date
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams

A4 = (8.27, 11.69)

_local = threading.local()
_UNSET = object()

_DEFAULT_COLORS = {
    "primary": "#1e3a8a",
    "secondary": "#2563eb",
    "primary_light": "#eff6ff",
}
_NEUTRAL_DEFAULTS = {
    "text_primary": "#1f2937",
    "text_body": "#374151",
    "text_muted": "#6b7280",
    "text_faint": "#9ca3af",
    "border": "#d1d5db",
    "grid": "#e5e7eb",
    "stripe": "#f8fafc",
}
_DEFAULT_GRADE = {"A": "#10b981", "B": "#22c55e", "C": "#f59e0b", "D": "#f97316", "F": "#ef4444"}
_DEFAULT_RATING = {"good": "#10b981", "warning": "#f59e0b", "poor": "#ef4444", "n/a": "#9ca3af"}
_DEFAULT_VCHAIN = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"]
_DEFAULT_SEVERITY = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981"}


def _apply_style(config: dict, brand: dict):
    _local.cfg = config or {}
    _local.theme = brand or {}
    _local._logo_arr = _UNSET
    font_family = (config or {}).get("style", {}).get("font", {}).get("family", "DejaVu Sans")
    rcParams["font.family"] = font_family
    rcParams["mathtext.fontset"] = "cm"
    rcParams["axes.unicode_minus"] = False


def _c(key: str) -> str:
    cfg = getattr(_local, "cfg", {})
    theme = getattr(_local, "theme", {})
    colors = cfg.get("style", {}).get("colors", {})
    if key in colors:
        return colors[key]
    if key in theme:
        return theme[key]
    return _NEUTRAL_DEFAULTS.get(key, _DEFAULT_COLORS.get(key, "#333333"))


def _layout(key: str):
    cfg = getattr(_local, "cfg", {})
    layout = cfg.get("style", {}).get("layout", {})
    defaults = {
        "content_axes": [0.07, 0.055, 0.86, 0.905],
        "header_height": 0.046,
        "accent_height": 0.007,
        "footer_height": 0.022,
        "title_fontsize": 11.5,
    }
    val = layout.get(key, defaults.get(key))
    return val


def _scale() -> float:
    cfg = getattr(_local, "cfg", {})
    return cfg.get("style", {}).get("typography", {}).get("scale", 1.0)


def _bw_scale() -> float:
    cfg = getattr(_local, "cfg", {})
    return cfg.get("style", {}).get("components", {}).get("border_width_scale", 1.0)


def _figure_postprocess(fig):
    s = _scale()
    bw = _bw_scale()
    for ax in fig.get_axes():
        for item in ax.get_xticklabels() + ax.get_yticklabels():
            item.set_fontsize(item.get_fontsize() * s)
        for item in [ax.title, ax.xaxis.label, ax.yaxis.label]:
            if item:
                item.set_fontsize(item.get_fontsize() * s)
        for spine in ax.spines.values():
            spine.set_linewidth(spine.get_linewidth() * bw)
        for line in ax.get_lines():
            line.set_linewidth(line.get_linewidth() * bw)


def _draw_page_frame(fig, title: str = "", page_num: int = 0, total: int = 0):
    header_h = _layout("header_height")
    accent_h = _layout("accent_height")
    footer_h = _layout("footer_height")
    cfg = getattr(_local, "cfg", {})

    ax_h = fig.add_axes([0, 1 - header_h, 1, header_h])
    ax_h.set_facecolor(_c("primary"))
    ax_h.axis("off")
    if title:
        ax_h.text(0.04, 0.5, title, color="white",
                  fontsize=_layout("title_fontsize") * _scale(),
                  fontweight="bold", va="center", ha="left",
                  transform=ax_h.transAxes)

    company_name = ""
    ax_a = fig.add_axes([0, 1 - header_h - accent_h, 1, accent_h])
    ax_a.set_facecolor(_c("secondary"))
    ax_a.axis("off")

    ax_f = fig.add_axes([0, 0, 1, footer_h])
    ax_f.set_facecolor(_c("primary"))
    ax_f.axis("off")
    footer_text = cfg.get("content", {}).get("footer_prefix", "Báo cáo tạo ngày")
    today = date.today().strftime("%d/%m/%Y")
    page_info = f"Trang {page_num}/{total}" if total else ""
    ax_f.text(0.04, 0.5, f"{footer_text} {today}", color="white",
              fontsize=7 * _scale(), va="center", transform=ax_f.transAxes)
    if page_info:
        ax_f.text(0.96, 0.5, page_info, color="white",
                  fontsize=7 * _scale(), va="center", ha="right",
                  transform=ax_f.transAxes)


def _new_content_ax(fig) -> plt.Axes:
    ca = _layout("content_axes")
    ax = fig.add_axes(ca)
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return ax


def _fmt(v, unit="", decimals=1) -> str:
    if v is None:
        return "N/A"
    try:
        v = float(v)
        if abs(v) >= 1e9:
            return f"{v/1e9:.{decimals}f}T {unit}".strip()
        if abs(v) >= 1e6:
            return f"{v/1e6:.{decimals}f}M {unit}".strip()
        if abs(v) >= 1e3:
            return f"{v/1e3:.{decimals}f}K {unit}".strip()
        return f"{v:,.{decimals}f} {unit}".strip()
    except Exception:
        return str(v)


def _get_logo_arr():
    if not hasattr(_local, "_logo_arr") or _local._logo_arr is _UNSET:
        theme = getattr(_local, "theme", {})
        cfg = getattr(_local, "cfg", {})
        b64 = theme.get("logo_b64") or cfg.get("images", {}).get("logo", {}).get("file")
        if b64:
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(base64.b64decode(b64)))
                _local._logo_arr = np.array(img.convert("RGBA"))
            except Exception:
                _local._logo_arr = None
        else:
            _local._logo_arr = None
    return _local._logo_arr


# ── Section renderers ─────────────────────────────────────────────────────────

def _render_cover(pdf: PdfPages, payload: dict, page_num: int, total: int):
    financials = payload.get("financials", {})
    company = financials.get("company", {})
    thesis = payload.get("thesis", {})
    val = payload.get("valuation", {})
    cfg = getattr(_local, "cfg", {})
    content = cfg.get("content", {})

    fig = plt.figure(figsize=A4)
    ax = _new_content_ax(fig)

    y = 0.88
    logo_arr = _get_logo_arr()
    if logo_arr is not None:
        ax_logo = fig.add_axes([0.07, 0.80, 0.20, 0.10])
        ax_logo.imshow(logo_arr)
        ax_logo.axis("off")
        y = 0.78

    ax.text(0.5, y, content.get("report_title", "BÁO CÁO ĐỊNH GIÁ DOANH NGHIỆP"),
            color=_c("primary"), fontsize=20 * _scale(), fontweight="bold",
            ha="center", va="top", transform=ax.transAxes)
    ax.text(0.5, y - 0.07, content.get("report_subtitle", "SME Valuation Report"),
            color=_c("text_muted"), fontsize=13 * _scale(),
            ha="center", va="top", transform=ax.transAxes)

    y -= 0.14
    ax.text(0.5, y, company.get("name", ""), color=_c("text_primary"),
            fontsize=16 * _scale(), fontweight="bold",
            ha="center", va="top", transform=ax.transAxes)

    y -= 0.06
    meta_rows = [
        ("Ngành", company.get("industry", "N/A")),
        ("Mã số thuế", company.get("tax_code", "N/A")),
        ("Địa chỉ", company.get("address", "N/A")),
        ("Kỳ báo cáo", financials.get("period", {}).get("current", {}).get("label", "N/A")),
        ("Đơn vị tiền tệ", f"{financials.get('currency', 'VND')} ({financials.get('unit', 'triệu đồng')})"),
    ]

    val_data = val.get("summary", {})
    fv_mid = val_data.get("fair_value_mid")
    if fv_mid:
        meta_rows.append(("Fair Value (Mid)", f"{fv_mid:,.0f} {financials.get('unit', '')}"))

    rec = thesis.get("executive_summary", {}).get("recommendation", "N/A")
    meta_rows.append(("Khuyến nghị", rec))

    row_h = 0.045
    for i, (label, value) in enumerate(meta_rows):
        bg = _c("stripe") if i % 2 == 0 else "white"
        rect = mpatches.FancyBboxPatch(
            (0.05, y - i * row_h - row_h), 0.90, row_h,
            boxstyle="round,pad=0.001", facecolor=bg, edgecolor=_c("border"),
            linewidth=0.5 * _bw_scale()
        )
        ax.add_patch(rect)
        ax.text(0.10, y - i * row_h - row_h / 2, label,
                color=_c("text_muted"), fontsize=8.5 * _scale(), va="center",
                transform=ax.transAxes)
        ax.text(0.55, y - i * row_h - row_h / 2, str(value),
                color=_c("text_primary"), fontsize=8.5 * _scale(), va="center",
                fontweight="bold", transform=ax.transAxes)

    disc_y = y - len(meta_rows) * row_h - 0.06
    disc_text = content.get("disclaimer_default", "")[:300]
    ax.text(0.05, disc_y, "DISCLAIMER:", color=_c("text_muted"),
            fontsize=7.5 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)
    ax.text(0.05, disc_y - 0.03, disc_text, color=_c("text_faint"),
            fontsize=6.5 * _scale(), va="top", wrap=True,
            transform=ax.transAxes)

    ax.text(0.95, 0.03, content.get("cover_generated_by", "ValuAI"),
            color=_c("text_faint"), fontsize=6.5 * _scale(), va="bottom",
            ha="right", transform=ax.transAxes)

    _draw_page_frame(fig, "", page_num, total)
    _figure_postprocess(fig)
    pdf.savefig(fig, bbox_inches="tight", dpi=150)
    plt.close(fig)


def _render_executive_summary(pdf: PdfPages, payload: dict, page_num: int, total: int):
    thesis = payload.get("thesis", {})
    es = thesis.get("executive_summary", {})
    drivers = thesis.get("key_value_drivers_ranked", [])

    fig = plt.figure(figsize=A4)
    ax = _new_content_ax(fig)
    _draw_page_frame(fig, "01 — EXECUTIVE SUMMARY", page_num, total)

    y = 0.94
    headline = es.get("headline", "")
    ax.text(0.0, y, headline, color=_c("primary"), fontsize=13 * _scale(),
            fontweight="bold", va="top", wrap=True, transform=ax.transAxes)

    y -= 0.08
    rec_color = {"BUY": "#10b981", "HOLD": "#f59e0b", "SELL": "#ef4444"}.get(
        es.get("recommendation", ""), _c("primary")
    )
    rec_text = f"Khuyến nghị: {es.get('recommendation', 'N/A')}"
    ax.text(0.0, y, rec_text, color=rec_color, fontsize=12 * _scale(),
            fontweight="bold", va="top", transform=ax.transAxes)

    y -= 0.06
    briefs = [
        ("Công ty", es.get("company_brief", "")),
        ("Ngành", es.get("industry_brief", "")),
        ("Quy mô", es.get("scale_brief", "")),
        ("Định giá", es.get("valuation_result", "")),
    ]
    row_h = 0.048
    for i, (label, text) in enumerate(briefs):
        bg = _c("stripe") if i % 2 == 0 else "white"
        rect = mpatches.FancyBboxPatch(
            (0.0, y - i * row_h - row_h), 1.0, row_h,
            boxstyle="round,pad=0.001", facecolor=bg, edgecolor=_c("border"),
            linewidth=0.4 * _bw_scale()
        )
        ax.add_patch(rect)
        ax.text(0.01, y - i * row_h - row_h / 2, label,
                color=_c("text_muted"), fontsize=8 * _scale(), va="center",
                transform=ax.transAxes)
        ax.text(0.22, y - i * row_h - row_h / 2, text,
                color=_c("text_body"), fontsize=8.5 * _scale(), va="center",
                transform=ax.transAxes)

    y -= len(briefs) * row_h + 0.06
    ax.text(0.0, y, "KEY VALUE DRIVERS", color=_c("primary"),
            fontsize=10 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)
    y -= 0.04
    for driver in drivers[:5]:
        rank = driver.get("rank", "")
        name = driver.get("driver", "")
        rat = driver.get("rationale", "")
        ax.add_patch(mpatches.Circle((0.02, y - 0.015), 0.015,
                                      color=_c("primary"), transform=ax.transAxes))
        ax.text(0.02, y - 0.015, str(rank), color="white",
                fontsize=7.5 * _scale(), fontweight="bold", ha="center", va="center",
                transform=ax.transAxes)
        ax.text(0.06, y, f"{name}", color=_c("text_primary"),
                fontsize=9 * _scale(), fontweight="bold", va="top",
                transform=ax.transAxes)
        ax.text(0.06, y - 0.03, rat, color=_c("text_muted"),
                fontsize=7.5 * _scale(), va="top", transform=ax.transAxes)
        y -= 0.06

    _figure_postprocess(fig)
    pdf.savefig(fig, bbox_inches="tight", dpi=150)
    plt.close(fig)


def _render_investment_thesis(pdf: PdfPages, payload: dict, page_num: int, total: int):
    thesis = payload.get("thesis", {})
    it = thesis.get("investment_thesis", {})
    risk_matrix = thesis.get("risk_matrix", [])

    fig = plt.figure(figsize=A4)
    ax = _new_content_ax(fig)
    _draw_page_frame(fig, "02 — LUẬN ĐIỂM ĐẦU TƯ", page_num, total)

    y = 0.94
    ax.text(0.0, y, "THESIS POINTS", color=_c("primary"),
            fontsize=10 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)
    y -= 0.03
    for pt in it.get("thesis_points", [])[:3]:
        ax.text(0.0, y, f"▶  {pt.get('title', '')}", color=_c("text_primary"),
                fontsize=9 * _scale(), fontweight="bold", va="top",
                transform=ax.transAxes)
        ax.text(0.04, y - 0.03, pt.get("thesis", ""),
                color=_c("text_body"), fontsize=8 * _scale(), va="top",
                transform=ax.transAxes)
        ax.text(0.04, y - 0.06, f"Bằng chứng: {pt.get('evidence', '')}",
                color=_c("text_muted"), fontsize=7.5 * _scale(), va="top",
                transform=ax.transAxes, style="italic")
        y -= 0.10

    y -= 0.02
    ax.text(0.0, y, "RISK MATRIX", color=_c("primary"),
            fontsize=10 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)
    y -= 0.04
    headers = ["Rủi ro", "P", "I", "Score", "Biện pháp"]
    col_x = [0.0, 0.45, 0.52, 0.60, 0.70]
    row_h = 0.04

    for j, h in enumerate(headers):
        rect = mpatches.FancyBboxPatch(
            (col_x[j], y), (col_x[j+1] if j+1 < len(col_x) else 1.0) - col_x[j] - 0.01, row_h,
            boxstyle="round,pad=0.001",
            facecolor=_c("primary"), edgecolor=_c("primary"),
        )
        ax.add_patch(rect)
        ax.text(col_x[j] + 0.005, y + row_h / 2, h, color="white",
                fontsize=7.5 * _scale(), fontweight="bold", va="center",
                transform=ax.transAxes)
    y -= row_h

    for i, risk in enumerate(risk_matrix[:6]):
        bg = _c("stripe") if i % 2 == 0 else "white"
        score = risk.get("score", 0)
        score_color = _DEFAULT_SEVERITY.get(
            "HIGH" if score >= 6 else ("MEDIUM" if score >= 3 else "LOW"), _c("text_muted")
        )
        vals = [
            risk.get("risk", "")[:35],
            str(risk.get("probability", "")),
            str(risk.get("impact", "")),
            str(score),
            risk.get("mitigation", "")[:30],
        ]
        for j, (x, txt) in enumerate(zip(col_x, vals)):
            rect = mpatches.FancyBboxPatch(
                (x, y), (col_x[j+1] if j+1 < len(col_x) else 1.0) - x - 0.01, row_h,
                boxstyle="round,pad=0.001", facecolor=bg, edgecolor=_c("border"),
                linewidth=0.3 * _bw_scale(),
            )
            ax.add_patch(rect)
            color = score_color if j == 3 else _c("text_body")
            ax.text(x + 0.005, y + row_h / 2, txt, color=color,
                    fontsize=7 * _scale(), va="center", transform=ax.transAxes)
        y -= row_h

    _figure_postprocess(fig)
    pdf.savefig(fig, bbox_inches="tight", dpi=150)
    plt.close(fig)


def _render_company_overview(pdf: PdfPages, payload: dict, page_num: int, total: int):
    business = payload.get("business", {})
    fig = plt.figure(figsize=A4)
    ax = _new_content_ax(fig)
    _draw_page_frame(fig, "03 — TỔNG QUAN DOANH NGHIỆP", page_num, total)

    y = 0.94
    bm = business.get("business_model", {})
    ax.text(0.0, y, "MÔ HÌNH KINH DOANH", color=_c("primary"),
            fontsize=10 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)
    ax.text(0.0, y - 0.04, bm.get("summary", ""),
            color=_c("text_body"), fontsize=8.5 * _scale(), va="top",
            transform=ax.transAxes)
    y -= 0.12

    vchain = business.get("value_chain", {})
    steps = ["input", "production", "distribution", "customer"]
    labels = ["Đầu vào", "Sản xuất", "Phân phối", "Khách hàng"]
    if vchain:
        ax.text(0.0, y, "CHUỖI GIÁ TRỊ", color=_c("primary"),
                fontsize=10 * _scale(), fontweight="bold", va="top",
                transform=ax.transAxes)
        y -= 0.04
        for i, (step, label) in enumerate(zip(steps, labels)):
            x = i * 0.25
            rect = mpatches.FancyBboxPatch(
                (x, y - 0.08), 0.23, 0.07,
                boxstyle="round,pad=0.005", facecolor=_DEFAULT_VCHAIN[i],
                edgecolor="none"
            )
            ax.add_patch(rect)
            ax.text(x + 0.115, y - 0.045, label, color="white",
                    fontsize=8 * _scale(), fontweight="bold", ha="center", va="center",
                    transform=ax.transAxes)
            desc = vchain.get(step, "")[:50]
            ax.text(x + 0.115, y - 0.09, desc, color=_c("text_body"),
                    fontsize=6.5 * _scale(), ha="center", va="top",
                    transform=ax.transAxes)
        y -= 0.18

    milestones = business.get("founding_milestones", [])
    if milestones:
        ax.text(0.0, y, "MILESTONES", color=_c("primary"),
                fontsize=10 * _scale(), fontweight="bold", va="top",
                transform=ax.transAxes)
        y -= 0.04
        for m in milestones[:5]:
            ax.text(0.03, y, f"• {m.get('year', '')}: {m.get('event', '')}",
                    color=_c("text_body"), fontsize=8 * _scale(), va="top",
                    transform=ax.transAxes)
            y -= 0.03

    y -= 0.02
    si = business.get("scale_indicators", {})
    ax.text(0.0, y, f"Quy mô: {si.get('revenue_size_class', '')}  |  "
                    f"Nhân lực: {si.get('employee_estimate', '')}  |  "
                    f"Vị thế: {business.get('competitive_position', '')}  |  "
                    f"Giai đoạn: {business.get('growth_stage', '')}",
            color=_c("text_muted"), fontsize=8 * _scale(), va="top",
            transform=ax.transAxes)

    _figure_postprocess(fig)
    pdf.savefig(fig, bbox_inches="tight", dpi=150)
    plt.close(fig)


def _render_industry(pdf: PdfPages, payload: dict, page_num: int, total: int):
    industry = payload.get("industry", {})
    fig = plt.figure(figsize=A4)
    _draw_page_frame(fig, "04 — PHÂN TÍCH NGÀNH", page_num, total)

    header_h = _layout("header_height")
    accent_h = _layout("accent_height")
    footer_h = _layout("footer_height")
    ca = _layout("content_axes")

    ax = fig.add_axes(ca)
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    y = 0.94
    ax.text(0.0, y, f"Ngành: {industry.get('industry_name', 'N/A')}",
            color=_c("primary"), fontsize=11 * _scale(), fontweight="bold",
            va="top", transform=ax.transAxes)
    ax.text(0.0, y - 0.04, industry.get("industry_overview", "")[:200],
            color=_c("text_body"), fontsize=8 * _scale(), va="top",
            transform=ax.transAxes)

    y -= 0.12
    ms = industry.get("market_size", {})
    ax.text(0.0, y, "MARKET SIZE", color=_c("primary"),
            fontsize=10 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)
    y -= 0.04
    for label, key in [("TAM", "tam_vnd_billion"), ("SAM", "sam_vnd_billion"), ("SOM", "som_vnd_billion")]:
        val = ms.get(key, 0)
        ax.text(0.05, y, f"{label}: {val:,.0f} tỷ VND" if val else f"{label}: N/A",
                color=_c("text_body"), fontsize=8.5 * _scale(), va="top",
                transform=ax.transAxes)
        y -= 0.035

    y -= 0.02
    p5 = industry.get("porters_5_forces", {})
    forces = ["buyer_power", "supplier_power", "threat_of_substitutes",
              "threat_of_new_entrants", "competitive_rivalry"]
    labels_f = ["Buyer Power", "Supplier Power", "Threat Subs.", "New Entrants", "Rivalry"]
    ax.text(0.0, y, "PORTER'S 5 FORCES", color=_c("primary"),
            fontsize=10 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)
    y -= 0.04

    ax_inner = fig.add_axes([ca[0], ca[1] + ca[3] * (y - 0.25), ca[2], ca[3] * 0.22])
    scores = [p5.get(f, {}).get("score", 3) for f in forces]
    colors_bar = [_DEFAULT_RATING["poor"] if s >= 4 else
                  (_DEFAULT_RATING["warning"] if s >= 3 else _DEFAULT_RATING["good"]) for s in scores]
    bars = ax_inner.barh(labels_f, scores, color=colors_bar, edgecolor=_c("border"),
                          linewidth=0.5 * _bw_scale())
    ax_inner.set_xlim(0, 5)
    ax_inner.set_xlabel("Score (1-5)", fontsize=7 * _scale())
    ax_inner.tick_params(labelsize=7 * _scale())
    ax_inner.set_facecolor(_c("stripe"))
    ax_inner.grid(axis="x", color=_c("grid"), linewidth=0.5 * _bw_scale())
    ax_inner.spines["top"].set_visible(False)
    ax_inner.spines["right"].set_visible(False)

    _figure_postprocess(fig)
    pdf.savefig(fig, bbox_inches="tight", dpi=150)
    plt.close(fig)


def _render_operations(pdf: PdfPages, payload: dict, page_num: int, total: int):
    thesis = payload.get("thesis", {})
    ops = thesis.get("operations_analysis", {})
    ratios = payload.get("ratios", {})
    common_size = ratios.get("common_size", {})
    financials = payload.get("financials", {})
    income_cur = financials.get("income_statement", {}).get("current", {})
    unit = financials.get("unit", "triệu đồng")

    fig = plt.figure(figsize=A4)
    _draw_page_frame(fig, "05 — HOẠT ĐỘNG KINH DOANH", page_num, total)
    ca = _layout("content_axes")

    ax = fig.add_axes(ca)
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    y = 0.94

    for label, key in [("Revenue Drivers", "revenue_drivers"),
                        ("Margin Analysis", "margin_analysis"),
                        ("Key Observations", "key_metrics_observations")]:
        ax.text(0.0, y, label, color=_c("primary"),
                fontsize=9.5 * _scale(), fontweight="bold", va="top",
                transform=ax.transAxes)
        ax.text(0.0, y - 0.035, ops.get(key, "N/A")[:200],
                color=_c("text_body"), fontsize=8 * _scale(), va="top",
                transform=ax.transAxes)
        y -= 0.09

    y -= 0.02
    ax.text(0.0, y, "COMMON-SIZE P&L (% doanh thu)", color=_c("primary"),
            fontsize=9.5 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)
    y -= 0.04

    cs_items = [
        ("Doanh thu thuần", "net_revenue"),
        ("COGS", "cogs"),
        ("Lợi nhuận gộp", "gross_profit"),
        ("Chi phí bán hàng", "selling_expense"),
        ("Chi phí QLDN", "admin_expense"),
        ("EBIT", "operating_profit"),
        ("Lợi nhuận ròng", "net_profit_after_tax"),
    ]
    row_h = 0.038
    for i, (label, key) in enumerate(cs_items):
        pct = common_size.get(key)
        val = income_cur.get(key)
        bg = _c("stripe") if i % 2 == 0 else "white"
        rect = mpatches.FancyBboxPatch(
            (0, y - row_h), 1.0, row_h,
            boxstyle="round,pad=0.001", facecolor=bg, edgecolor=_c("border"),
            linewidth=0.3 * _bw_scale()
        )
        ax.add_patch(rect)
        ax.text(0.01, y - row_h / 2, label, color=_c("text_body"),
                fontsize=7.5 * _scale(), va="center", transform=ax.transAxes)
        ax.text(0.65, y - row_h / 2, f"{val:,.0f}" if val is not None else "N/A",
                color=_c("text_primary"), fontsize=7.5 * _scale(), va="center",
                transform=ax.transAxes)
        ax.text(0.85, y - row_h / 2, f"{pct:.1f}%" if pct is not None else "N/A",
                color=_c("text_muted"), fontsize=7.5 * _scale(), va="center",
                transform=ax.transAxes)
        y -= row_h

    _figure_postprocess(fig)
    pdf.savefig(fig, bbox_inches="tight", dpi=150)
    plt.close(fig)


def _render_financial_statements(pdf: PdfPages, payload: dict, page_num: int, total: int):
    financials = payload.get("financials", {})
    income = financials.get("income_statement", {})
    bs = financials.get("balance_sheet", {})
    cf = financials.get("cash_flow", {})
    unit = financials.get("unit", "")
    period_cur = financials.get("period", {}).get("current", {}).get("label", "Hiện tại")
    period_prev = financials.get("period", {}).get("previous", {}).get("label", "Trước")

    fig = plt.figure(figsize=A4)
    _draw_page_frame(fig, "06 — BÁO CÁO TÀI CHÍNH", page_num, total)
    ca = _layout("content_axes")
    ax = fig.add_axes(ca)
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    def _draw_table(title, rows, y_start, col_labels):
        ax.text(0.0, y_start, title, color=_c("primary"),
                fontsize=9.5 * _scale(), fontweight="bold", va="top",
                transform=ax.transAxes)
        y = y_start - 0.035
        row_h = 0.036
        cols_x = [0.0, 0.55, 0.78]
        header_row = ["Chỉ tiêu"] + col_labels
        for j, h in enumerate(header_row):
            ax.text(cols_x[j] + 0.01, y, h, color="white",
                    fontsize=7.5 * _scale(), fontweight="bold", va="center",
                    transform=ax.transAxes)
        rect = mpatches.FancyBboxPatch(
            (0, y - row_h / 2), 1.0, row_h,
            boxstyle="round,pad=0.001", facecolor=_c("primary"), edgecolor=_c("primary"),
        )
        ax.add_patch(rect)
        for j, h in enumerate(header_row):
            ax.text(cols_x[j] + 0.01, y, h, color="white",
                    fontsize=7.5 * _scale(), fontweight="bold", va="center",
                    transform=ax.transAxes)
        y -= row_h
        for i, (label, cur, prev) in enumerate(rows):
            bg = _c("stripe") if i % 2 == 0 else "white"
            rect = mpatches.FancyBboxPatch(
                (0, y - row_h), 1.0, row_h,
                boxstyle="round,pad=0.001", facecolor=bg, edgecolor=_c("border"),
                linewidth=0.3 * _bw_scale()
            )
            ax.add_patch(rect)
            ax.text(0.01, y - row_h / 2, label[:40], color=_c("text_body"),
                    fontsize=7 * _scale(), va="center", transform=ax.transAxes)
            ax.text(0.56, y - row_h / 2,
                    f"{cur:,.0f}" if isinstance(cur, (int, float)) and cur is not None else "N/A",
                    color=_c("text_primary"), fontsize=7 * _scale(), va="center",
                    transform=ax.transAxes)
            ax.text(0.79, y - row_h / 2,
                    f"{prev:,.0f}" if isinstance(prev, (int, float)) and prev is not None else "N/A",
                    color=_c("text_muted"), fontsize=7 * _scale(), va="center",
                    transform=ax.transAxes)
            y -= row_h
        return y

    income_cur = income.get("current", {})
    income_prev = income.get("previous", {})
    income_rows = [
        ("Doanh thu thuần", income_cur.get("net_revenue"), income_prev.get("net_revenue")),
        ("COGS", income_cur.get("cogs"), income_prev.get("cogs")),
        ("Lợi nhuận gộp", income_cur.get("gross_profit"), income_prev.get("gross_profit")),
        ("EBIT", income_cur.get("operating_profit"), income_prev.get("operating_profit")),
        ("Lợi nhuận ròng", income_cur.get("net_profit_after_tax"), income_prev.get("net_profit_after_tax")),
    ]
    y = 0.94
    y = _draw_table("KẾT QUẢ KINH DOANH", income_rows, y, [period_cur, period_prev])

    y -= 0.04
    bs_cur = bs.get("current", {})
    bs_prev = bs.get("previous", {})
    cur_a = bs_cur.get("assets", {})
    prev_a = bs_prev.get("assets", {})
    cur_l = bs_cur.get("liabilities", {})
    bs_rows = [
        ("Tổng tài sản", cur_a.get("total_assets"), prev_a.get("total_assets")),
        ("Tài sản ngắn hạn", cur_a.get("current_assets_total"), prev_a.get("current_assets_total")),
        ("Tài sản dài hạn", cur_a.get("non_current_assets_total"), prev_a.get("non_current_assets_total")),
        ("Tổng nợ", cur_l.get("total_liabilities"), bs_prev.get("liabilities", {}).get("total_liabilities")),
        ("Vốn chủ sở hữu", bs_cur.get("equity", {}).get("total_equity"), bs_prev.get("equity", {}).get("total_equity")),
    ]
    y = _draw_table("BẢNG CÂN ĐỐI KẾ TOÁN", bs_rows, y, [period_cur, period_prev])

    y -= 0.04
    cf_cur = cf.get("current", {})
    cf_prev = cf.get("previous", {})
    cf_rows = [
        ("CF Hoạt động", cf_cur.get("cf_operating"), cf_prev.get("cf_operating")),
        ("CF Đầu tư", cf_cur.get("cf_investing"), cf_prev.get("cf_investing")),
        ("CF Tài chính", cf_cur.get("cf_financing"), cf_prev.get("cf_financing")),
        ("Tiền cuối kỳ", cf_cur.get("ending_cash"), cf_prev.get("ending_cash")),
    ]
    _draw_table("LƯU CHUYỂN TIỀN TỆ", cf_rows, y, [period_cur, period_prev])

    _figure_postprocess(fig)
    pdf.savefig(fig, bbox_inches="tight", dpi=150)
    plt.close(fig)


def _render_ratios(pdf: PdfPages, payload: dict, page_num: int, total: int):
    ratios = payload.get("ratios", {})
    all_ratios = ratios.get("ratios", {})
    dupont = ratios.get("dupont", {})
    wcd = ratios.get("working_capital_days", {})
    qoe = ratios.get("quality_of_earnings", {})

    fig = plt.figure(figsize=A4)
    _draw_page_frame(fig, "07 — TỶ SỐ TÀI CHÍNH", page_num, total)
    ca = _layout("content_axes")
    ax = fig.add_axes(ca)
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    y = 0.94
    groups = [
        ("Thanh khoản", "liquidity", ["current_ratio", "quick_ratio", "cash_ratio"]),
        ("Đòn bẩy", "leverage", ["debt_ratio", "debt_to_equity", "interest_coverage"]),
        ("Lợi nhuận", "profitability", ["gross_margin", "operating_margin", "net_margin", "roa", "roe"]),
        ("Hiệu quả", "efficiency", ["asset_turnover", "inventory_turnover", "receivables_turnover"]),
    ]

    label_map = {
        "current_ratio": "Current Ratio", "quick_ratio": "Quick Ratio",
        "cash_ratio": "Cash Ratio", "debt_ratio": "Debt Ratio",
        "debt_to_equity": "D/E", "interest_coverage": "Interest Coverage",
        "gross_margin": "Gross Margin %", "operating_margin": "Op. Margin %",
        "net_margin": "Net Margin %", "roa": "ROA %", "roe": "ROE %",
        "asset_turnover": "Asset Turnover", "inventory_turnover": "Inv. Turnover",
        "receivables_turnover": "Rec. Turnover",
    }

    for group_name, group_key, keys in groups:
        ax.text(0.0, y, group_name, color=_c("primary"),
                fontsize=9 * _scale(), fontweight="bold", va="top",
                transform=ax.transAxes)
        y -= 0.03
        group_data = all_ratios.get(group_key, {})
        row_h = 0.035
        for i, k in enumerate(keys):
            r = group_data.get(k, {})
            val = r.get("value")
            rating = r.get("rating", "n/a")
            color = _DEFAULT_RATING.get(rating, _c("text_muted"))
            label = label_map.get(k, k)
            bg = _c("stripe") if i % 2 == 0 else "white"
            rect = mpatches.FancyBboxPatch(
                (0.02, y - row_h), 0.96, row_h,
                boxstyle="round,pad=0.001", facecolor=bg, edgecolor=_c("border"),
                linewidth=0.3 * _bw_scale()
            )
            ax.add_patch(rect)
            ax.text(0.04, y - row_h / 2, label, color=_c("text_body"),
                    fontsize=7.5 * _scale(), va="center", transform=ax.transAxes)
            val_str = f"{val:.2f}" if val is not None else "N/A"
            ax.text(0.7, y - row_h / 2, val_str, color=color,
                    fontsize=7.5 * _scale(), fontweight="bold", va="center",
                    transform=ax.transAxes)
            ax.text(0.85, y - row_h / 2, rating, color=color,
                    fontsize=7 * _scale(), va="center", transform=ax.transAxes)
            y -= row_h
        y -= 0.015

    ax.text(0.0, y, f"DuPont: NM={dupont.get('net_margin', 0):.1f}% × "
                    f"AT={dupont.get('asset_turnover', 0):.2f}x × "
                    f"EM={dupont.get('equity_multiplier', 0):.2f}x = "
                    f"ROE {dupont.get('roe', 0):.1f}%",
            color=_c("text_body"), fontsize=7.5 * _scale(), va="top",
            transform=ax.transAxes)
    y -= 0.04
    ax.text(0.0, y, f"CCC: DSO={wcd.get('dso', 0):.0f}d + "
                    f"DIO={wcd.get('dio', 0):.0f}d - "
                    f"DPO={wcd.get('dpo', 0):.0f}d = "
                    f"{wcd.get('ccc', 0):.0f}d",
            color=_c("text_body"), fontsize=7.5 * _scale(), va="top",
            transform=ax.transAxes)

    _figure_postprocess(fig)
    pdf.savefig(fig, bbox_inches="tight", dpi=150)
    plt.close(fig)


def _render_projections(pdf: PdfPages, payload: dict, page_num: int, total: int):
    proj_data = payload.get("projection", {})
    proj = proj_data.get("projection", proj_data) if isinstance(proj_data, dict) else {}
    projections = proj.get("projections", [])
    summary = proj.get("summary_5y", {})
    unit = payload.get("financials", {}).get("unit", "")

    fig = plt.figure(figsize=A4)
    _draw_page_frame(fig, "08 — DỰ PHÓNG 5 NĂM", page_num, total)
    ca = _layout("content_axes")

    ax = fig.add_axes(ca)
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    y = 0.94
    ax.text(0.0, y, "BẢNG DỰ PHÓNG 5 NĂM", color=_c("primary"),
            fontsize=10 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)
    y -= 0.04

    cols = ["Chỉ tiêu"] + [p.get("year_label", f"Y{p.get('year_index',i+1)}") for i, p in enumerate(projections)]
    col_w = 0.18
    row_h = 0.038
    header_x = [0.0] + [0.22 + i * col_w for i in range(len(projections))]

    rect = mpatches.FancyBboxPatch(
        (0, y - row_h), 1.0, row_h,
        boxstyle="round,pad=0.001", facecolor=_c("primary"), edgecolor=_c("primary")
    )
    ax.add_patch(rect)
    for j, h in enumerate(cols):
        x = header_x[j] if j < len(header_x) else 0.8
        ax.text(x + 0.01, y - row_h / 2, h, color="white",
                fontsize=7.5 * _scale(), fontweight="bold", va="center",
                transform=ax.transAxes)
    y -= row_h

    metrics = [
        ("Doanh thu", "revenue"),
        ("Tăng trưởng %", "growth_pct"),
        ("Lợi nhuận gộp", "gross_profit"),
        ("EBITDA", "ebitda"),
        ("EBITDA Margin %", "ebitda_margin_pct"),
        ("EBIT", "ebit"),
        ("Lợi nhuận ròng", "net_income"),
        ("Net Margin %", "net_margin_pct"),
        ("FCFF", "fcff"),
    ]
    for i, (label, key) in enumerate(metrics):
        bg = _c("stripe") if i % 2 == 0 else "white"
        rect = mpatches.FancyBboxPatch(
            (0, y - row_h), 1.0, row_h,
            boxstyle="round,pad=0.001", facecolor=bg, edgecolor=_c("border"),
            linewidth=0.3 * _bw_scale()
        )
        ax.add_patch(rect)
        ax.text(0.01, y - row_h / 2, label, color=_c("text_body"),
                fontsize=7 * _scale(), va="center", transform=ax.transAxes)
        for j, p in enumerate(projections):
            val = p.get(key)
            x = header_x[j + 1] if j + 1 < len(header_x) else 0.8
            if val is not None:
                if "pct" in key or key == "growth_pct":
                    txt = f"{val:.1f}%"
                else:
                    txt = f"{val:,.0f}"
            else:
                txt = "N/A"
            ax.text(x + 0.01, y - row_h / 2, txt, color=_c("text_primary"),
                    fontsize=7 * _scale(), va="center", transform=ax.transAxes)
        y -= row_h

    y -= 0.04
    ax.text(0.0, y, f"Revenue CAGR: {summary.get('revenue_cagr_pct', 0):.1f}%  |  "
                    f"EBITDA CAGR: {summary.get('ebitda_cagr_pct', 0):.1f}%  |  "
                    f"FCFF tích lũy: {summary.get('fcff_cumulative', 0):,.0f} {unit}",
            color=_c("text_body"), fontsize=8 * _scale(), va="top",
            transform=ax.transAxes)

    if projections:
        years = [p.get("year_label", "") for p in projections]
        revenues = [p.get("revenue", 0) or 0 for p in projections]
        ebitdas = [p.get("ebitda", 0) or 0 for p in projections]

        chart_h = 0.22
        chart_y_bottom = ca[1] + ca[3] * (y - 0.04 - chart_h) / 1.0

        ax2 = fig.add_axes([ca[0], ca[1] + ca[3] * max(0.05, y - 0.28), ca[2] * 0.47, chart_h])
        x = np.arange(len(years))
        ax2.bar(x, revenues, color=_c("primary"), edgecolor="none")
        ax2.set_xticks(x)
        ax2.set_xticklabels(years, fontsize=6 * _scale())
        ax2.set_title("Doanh thu", fontsize=7 * _scale())
        ax2.set_facecolor(_c("stripe"))
        ax2.grid(axis="y", color=_c("grid"), linewidth=0.5 * _bw_scale())
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)

        ax3 = fig.add_axes([ca[0] + ca[2] * 0.53, ca[1] + ca[3] * max(0.05, y - 0.28),
                             ca[2] * 0.47, chart_h])
        ax3.plot(years, ebitdas, color=_c("secondary"), marker="o",
                 linewidth=1.5 * _bw_scale(), markersize=4)
        ax3.set_title("EBITDA", fontsize=7 * _scale())
        ax3.set_facecolor(_c("stripe"))
        ax3.grid(axis="y", color=_c("grid"), linewidth=0.5 * _bw_scale())
        ax3.tick_params(labelsize=6 * _scale())
        ax3.spines["top"].set_visible(False)
        ax3.spines["right"].set_visible(False)

    _figure_postprocess(fig)
    pdf.savefig(fig, bbox_inches="tight", dpi=150)
    plt.close(fig)


def _render_valuation(pdf: PdfPages, payload: dict, page_num: int, total: int):
    val = payload.get("valuation", {})
    vd = val.get("valuation", val) if "valuation" in val else val
    dcf = vd.get("dcf", {})
    multiples = vd.get("multiples", {})
    ff = vd.get("football_field", [])
    waterfall = vd.get("waterfall", {})
    summary = vd.get("summary", {})
    assumptions = vd.get("assumptions", {})
    unit = payload.get("financials", {}).get("unit", "")

    fig = plt.figure(figsize=A4)
    _draw_page_frame(fig, "09 — ĐỊNH GIÁ", page_num, total)
    ca = _layout("content_axes")
    ax = fig.add_axes(ca)
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    y = 0.94
    ax.text(0.0, y, f"WACC: {assumptions.get('wacc_pct', 0):.1f}%  |  "
                    f"Terminal Growth: {assumptions.get('terminal_growth_pct', 0):.1f}%",
            color=_c("primary"), fontsize=9 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)
    y -= 0.05

    ax.text(0.0, y, "DCF VALUATION", color=_c("primary"),
            fontsize=9.5 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)
    y -= 0.03
    for label, key in [("PV FCFF", "pv_fcff"), ("Terminal Value PV", "pv_terminal_value"),
                        ("Enterprise Value", "enterprise_value"), ("Net Debt", "net_debt"),
                        ("Equity Value", "equity_value")]:
        val_n = dcf.get(key, 0)
        ax.text(0.03, y, label, color=_c("text_body"), fontsize=8 * _scale(), va="top",
                transform=ax.transAxes)
        ax.text(0.55, y, f"{val_n:,.0f} {unit}", color=_c("text_primary"),
                fontsize=8 * _scale(), fontweight="bold", va="top",
                transform=ax.transAxes)
        y -= 0.033

    y -= 0.02
    ax.text(0.0, y, "FOOTBALL FIELD", color=_c("primary"),
            fontsize=9.5 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)
    y -= 0.03

    if ff:
        all_vals = [r.get("low", 0) for r in ff] + [r.get("high", 0) for r in ff]
        all_vals = [v for v in all_vals if v]
        min_v = min(all_vals) * 0.9 if all_vals else 0
        max_v = max(all_vals) * 1.05 if all_vals else 1

        bar_h = 0.03
        bar_colors = [_c("primary"), _c("secondary"), "#10b981", "#f59e0b"]
        for i, row in enumerate(ff):
            low, high = row.get("low", 0), row.get("high", 0)
            if max_v > min_v:
                x_low = (low - min_v) / (max_v - min_v) * 0.65
                x_high = (high - min_v) / (max_v - min_v) * 0.65
            else:
                x_low, x_high = 0, 0.65
            color = bar_colors[i % len(bar_colors)]
            ax.add_patch(mpatches.FancyBboxPatch(
                (0.3 + x_low, y - bar_h), x_high - x_low, bar_h * 0.7,
                boxstyle="round,pad=0.002", facecolor=color, edgecolor="none", alpha=0.8
            ))
            ax.text(0.28, y - bar_h / 2, row.get("method", ""), color=_c("text_body"),
                    fontsize=7.5 * _scale(), ha="right", va="center",
                    transform=ax.transAxes)
            ax.text(0.3 + x_low - 0.01, y - bar_h / 2,
                    f"{low:,.0f}", color=_c("text_muted"),
                    fontsize=6.5 * _scale(), ha="right", va="center",
                    transform=ax.transAxes)
            ax.text(0.3 + x_high + 0.01, y - bar_h / 2,
                    f"{high:,.0f}", color=_c("text_muted"),
                    fontsize=6.5 * _scale(), va="center",
                    transform=ax.transAxes)
            y -= bar_h + 0.01

    y -= 0.03
    fv = summary
    ax.text(0.0, y, f"Fair Value: {fv.get('fair_value_low', 0):,.0f} – "
                    f"{fv.get('fair_value_mid', 0):,.0f} – "
                    f"{fv.get('fair_value_high', 0):,.0f} {unit}",
            color=_c("primary"), fontsize=9 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)

    _figure_postprocess(fig)
    pdf.savefig(fig, bbox_inches="tight", dpi=150)
    plt.close(fig)


def _render_sensitivity(pdf: PdfPages, payload: dict, page_num: int, total: int):
    val = payload.get("valuation", {})
    vd = val.get("valuation", val) if "valuation" in val else val
    sens = vd.get("sensitivity", {})
    scenarios = vd.get("scenarios", {})
    unit = payload.get("financials", {}).get("unit", "")

    fig = plt.figure(figsize=A4)
    _draw_page_frame(fig, "10 — SENSITIVITY & SCENARIOS", page_num, total)
    ca = _layout("content_axes")
    ax = fig.add_axes(ca)
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    y = 0.94
    ax.text(0.0, y, "SENSITIVITY MATRIX (WACC × Terminal Growth → Equity Value)",
            color=_c("primary"), fontsize=9.5 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)
    y -= 0.04

    wacc_range = sens.get("wacc_range", [])
    g_range = sens.get("g_range", [])
    matrix = sens.get("matrix", [])

    if matrix and wacc_range and g_range:
        cell_w = 0.14
        cell_h = 0.038
        col_offset = 0.16

        ax.text(0.0, y, "WACC \\ g →", color=_c("text_muted"),
                fontsize=6.5 * _scale(), va="top", transform=ax.transAxes)
        for j, g in enumerate(g_range):
            ax.text(col_offset + j * cell_w + cell_w / 2, y,
                    f"{g:.1f}%", color=_c("text_muted"),
                    fontsize=7 * _scale(), ha="center", va="top",
                    transform=ax.transAxes)
        y -= cell_h

        flat = [v for row in matrix for v in row if v]
        vmin = min(flat) if flat else 1
        vmax = max(flat) if flat else 1

        for i, row in enumerate(matrix):
            ax.text(0.0, y - cell_h / 2, f"{wacc_range[i]:.1f}%",
                    color=_c("text_muted"), fontsize=7 * _scale(),
                    va="center", transform=ax.transAxes)
            for j, val_n in enumerate(row):
                intensity = (val_n - vmin) / (vmax - vmin) if vmax != vmin else 0.5
                bg = plt.cm.RdYlGn(intensity)
                rect = mpatches.FancyBboxPatch(
                    (col_offset + j * cell_w, y - cell_h), cell_w - 0.005, cell_h - 0.003,
                    boxstyle="round,pad=0.002", facecolor=bg, edgecolor="white",
                    linewidth=0.5 * _bw_scale()
                )
                ax.add_patch(rect)
                ax.text(col_offset + j * cell_w + cell_w / 2, y - cell_h / 2,
                        f"{val_n:,.0f}", color="black" if intensity > 0.3 else "white",
                        fontsize=6 * _scale(), ha="center", va="center",
                        transform=ax.transAxes)
            y -= cell_h

    y -= 0.05
    ax.text(0.0, y, "SCENARIO ANALYSIS", color=_c("primary"),
            fontsize=9.5 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)
    y -= 0.04

    for scen_key, label, color in [
        ("bull", "Bull", _DEFAULT_SEVERITY["LOW"]),
        ("base", "Base", _DEFAULT_SEVERITY["MEDIUM"]),
        ("bear", "Bear", _DEFAULT_SEVERITY["HIGH"]),
    ]:
        scen = scenarios.get(scen_key, {})
        eq = scen.get("equity_value", 0)
        desc = scen.get("description", "")
        rect = mpatches.FancyBboxPatch(
            (0.0, y - 0.05), 0.98, 0.045,
            boxstyle="round,pad=0.005", facecolor=color + "30",
            edgecolor=color, linewidth=1.0 * _bw_scale()
        )
        ax.add_patch(rect)
        ax.text(0.02, y - 0.025, label, color=color, fontsize=9 * _scale(),
                fontweight="bold", va="center", transform=ax.transAxes)
        ax.text(0.15, y - 0.025, f"Equity: {eq:,.0f} {unit}",
                color=_c("text_primary"), fontsize=8.5 * _scale(), va="center",
                transform=ax.transAxes)
        ax.text(0.55, y - 0.025, desc, color=_c("text_muted"),
                fontsize=7.5 * _scale(), va="center", transform=ax.transAxes)
        y -= 0.06

    _figure_postprocess(fig)
    pdf.savefig(fig, bbox_inches="tight", dpi=150)
    plt.close(fig)


def _render_conclusion(pdf: PdfPages, payload: dict, page_num: int, total: int):
    thesis = payload.get("thesis", {})
    deal = thesis.get("deal_recommendation", {})
    returns = thesis.get("return_scenarios", [])
    exit_st = thesis.get("exit_strategy", {})
    unit = payload.get("financials", {}).get("unit", "")

    fig = plt.figure(figsize=A4)
    _draw_page_frame(fig, "11 — KẾT LUẬN & ĐỀ XUẤT", page_num, total)
    ca = _layout("content_axes")
    ax = fig.add_axes(ca)
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    y = 0.94
    ax.text(0.0, y, "DEAL RECOMMENDATION", color=_c("primary"),
            fontsize=10 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)
    y -= 0.04

    deal_rows = [
        ("Mục tiêu chính", deal.get("primary_objective", "")),
        ("Khoảng Fair Value", deal.get("fair_value_range_text", "")),
        ("Giá vào khuyến nghị", deal.get("entry_price_recommendation", "")),
        ("Cấu trúc deal", deal.get("deal_structure", "")),
        ("Pre-money Valuation", f"{deal.get('pre_money_valuation', 0):,.0f} {unit}"),
        ("Vốn đề xuất đầu tư", f"{deal.get('investment_amount_suggested', 0):,.0f} {unit}"),
        ("Post-money Valuation", f"{deal.get('post_money_valuation', 0):,.0f} {unit}"),
    ]
    row_h = 0.04
    for i, (label, value) in enumerate(deal_rows):
        bg = _c("stripe") if i % 2 == 0 else "white"
        rect = mpatches.FancyBboxPatch(
            (0, y - row_h), 1.0, row_h,
            boxstyle="round,pad=0.001", facecolor=bg, edgecolor=_c("border"),
            linewidth=0.3 * _bw_scale()
        )
        ax.add_patch(rect)
        ax.text(0.01, y - row_h / 2, label, color=_c("text_muted"),
                fontsize=7.5 * _scale(), va="center", transform=ax.transAxes)
        ax.text(0.38, y - row_h / 2, str(value)[:60], color=_c("text_primary"),
                fontsize=7.5 * _scale(), fontweight="bold", va="center",
                transform=ax.transAxes)
        y -= row_h

    y -= 0.04
    ax.text(0.0, y, "RETURN SCENARIOS", color=_c("primary"),
            fontsize=10 * _scale(), fontweight="bold", va="top",
            transform=ax.transAxes)
    y -= 0.035

    headers = ["Scenario", "IRR", "MOIC", "Horizon", "Exit EV", "Description"]
    col_x = [0.0, 0.15, 0.25, 0.35, 0.45, 0.60]
    rect = mpatches.FancyBboxPatch(
        (0, y - 0.035), 1.0, 0.035,
        boxstyle="round,pad=0.001", facecolor=_c("primary"), edgecolor=_c("primary")
    )
    ax.add_patch(rect)
    for j, h in enumerate(headers):
        ax.text(col_x[j] + 0.005, y - 0.018, h, color="white",
                fontsize=7 * _scale(), fontweight="bold", va="center",
                transform=ax.transAxes)
    y -= 0.035

    for i, scen in enumerate(returns[:3]):
        sname = scen.get("scenario", "")
        color = {"Bull": "#10b981", "Base": "#f59e0b", "Bear": "#ef4444"}.get(sname, _c("text_body"))
        bg = _c("stripe") if i % 2 == 0 else "white"
        vals = [
            sname,
            f"{scen.get('irr_pct', 0):.0f}%",
            f"{scen.get('moic', 0):.1f}x",
            f"{scen.get('horizon_years', 5)}Y",
            f"{scen.get('exit_ev', 0):,.0f}",
            scen.get("description", "")[:30],
        ]
        rect = mpatches.FancyBboxPatch(
            (0, y - 0.035), 1.0, 0.035,
            boxstyle="round,pad=0.001", facecolor=bg, edgecolor=_c("border"),
            linewidth=0.3 * _bw_scale()
        )
        ax.add_patch(rect)
        for j, v in enumerate(vals):
            c = color if j == 0 else _c("text_body")
            ax.text(col_x[j] + 0.005, y - 0.018, v, color=c,
                    fontsize=7 * _scale(), fontweight=(j == 0 and "bold" or "normal"),
                    va="center", transform=ax.transAxes)
        y -= 0.035

    y -= 0.04
    ax.text(0.0, y, f"EXIT STRATEGY: {exit_st.get('primary_exit', '')} "
                    f"(Target EV: {exit_st.get('target_ev_at_exit', 0):,.0f} {unit}, "
                    f"{exit_st.get('target_timeline_years', 5)}Y, "
                    f"{exit_st.get('exit_multiple_assumption', 0):.1f}x multiple)",
            color=_c("text_body"), fontsize=8 * _scale(), va="top",
            transform=ax.transAxes)

    _figure_postprocess(fig)
    pdf.savefig(fig, bbox_inches="tight", dpi=150)
    plt.close(fig)


# ── Main render function ──────────────────────────────────────────────────────

_SECTION_RENDERERS = {
    "00_cover_disclaimer": _render_cover,
    "01_executive_summary": _render_executive_summary,
    "02_investment_thesis": _render_investment_thesis,
    "03_company_overview": _render_company_overview,
    "04_industry": _render_industry,
    "05_operations": _render_operations,
    "06_financial_statements": _render_financial_statements,
    "07_ratios": _render_ratios,
    "08_projections": _render_projections,
    "09_valuation": _render_valuation,
    "10_sensitivity": _render_sensitivity,
    "11_conclusion_appendix": _render_conclusion,
}


def render_valuation_report(payload: dict, out_path: str,
                             brand: dict = None, config: dict = None) -> str:
    _apply_style(config or {}, brand or {})

    sections_cfg = (config or {}).get("sections", [])
    enabled = sorted(
        [s for s in sections_cfg if s.get("enabled", True)],
        key=lambda s: s.get("order", 99)
    )
    if not enabled:
        enabled = [{"slug": k} for k in _SECTION_RENDERERS]

    total_pages = len(enabled)

    with PdfPages(str(out_path)) as pdf:
        for i, section in enumerate(enabled, start=1):
            slug = section.get("slug", "")
            renderer = _SECTION_RENDERERS.get(slug)
            if renderer:
                try:
                    renderer(pdf, payload, i, total_pages)
                except Exception as e:
                    fig = plt.figure(figsize=A4)
                    _draw_page_frame(fig, f"ERROR: {slug}", i, total_pages)
                    ax = _new_content_ax(fig)
                    ax.text(0.5, 0.5, f"Lỗi render section:\n{str(e)[:200]}",
                            color="red", fontsize=9, ha="center", va="center",
                            transform=ax.transAxes)
                    pdf.savefig(fig, bbox_inches="tight", dpi=100)
                    plt.close(fig)

    return out_path
