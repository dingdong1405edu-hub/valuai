"""Explainer matplotlib renderer — fallback for explainer PDF."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages

from agents.renderer import (
    A4, _apply_style, _new_content_ax, _draw_page_frame,
    _c, _layout, _scale, _bw_scale, _figure_postprocess,
)
from explanations_default import EXPLANATIONS_DEFAULT


def render_explainer(config: dict = None, brand: dict = None,
                     out_path: str = None) -> str:
    _apply_style(config or {}, brand or {})
    content = (config or {}).get("content", {})
    explanations = content.get("explanations") or EXPLANATIONS_DEFAULT
    title = content.get("explainer_title", "GIẢI THÍCH PHƯƠNG PHÁP ĐỊNH GIÁ")

    items_per_page = 2
    total_pages = 1 + (len(explanations) + items_per_page - 1) // items_per_page

    with PdfPages(str(out_path)) as pdf:
        # Cover page
        fig = plt.figure(figsize=A4)
        ax = _new_content_ax(fig)
        _draw_page_frame(fig, title, 1, total_pages)
        y = 0.90
        ax.text(0.5, y, content.get("explainer_subtitle", "Hướng dẫn đọc báo cáo"),
                color=_c("primary"), fontsize=14 * _scale(), fontweight="bold",
                ha="center", va="top", transform=ax.transAxes)
        y -= 0.08
        intro = content.get("explainer_intro", "")[:300]
        ax.text(0.0, y, intro, color=_c("text_body"), fontsize=8.5 * _scale(),
                va="top", wrap=True, transform=ax.transAxes)
        y -= 0.10
        ax.text(0.0, y, "MỤC LỤC:", color=_c("primary"),
                fontsize=9.5 * _scale(), fontweight="bold", va="top",
                transform=ax.transAxes)
        y -= 0.03
        for i, expl in enumerate(explanations, 1):
            ax.text(0.04, y, f"{i}. {expl.get('title', '')}",
                    color=_c("text_body"), fontsize=8.5 * _scale(),
                    va="top", transform=ax.transAxes)
            y -= 0.033
        _figure_postprocess(fig)
        pdf.savefig(fig, bbox_inches="tight", dpi=150)
        plt.close(fig)

        # Content pages
        page_num = 2
        for i in range(0, len(explanations), items_per_page):
            batch = explanations[i:i + items_per_page]
            fig = plt.figure(figsize=A4)
            ax = _new_content_ax(fig)
            _draw_page_frame(fig, title, page_num, total_pages)
            y = 0.94

            for expl in batch:
                # Card title
                rect = mpatches.FancyBboxPatch(
                    (0.0, y - 0.04), 1.0, 0.04,
                    boxstyle="round,pad=0.001",
                    facecolor=_c("primary_light") if hasattr(_c, "__call__") else "#eff6ff",
                    edgecolor=_c("primary"), linewidth=0.8 * _bw_scale()
                )
                try:
                    rect.set_facecolor(_c("primary_light"))
                except Exception:
                    pass
                ax.add_patch(rect)
                ax.text(0.01, y - 0.02, expl.get("title", ""),
                        color=_c("primary"), fontsize=10 * _scale(),
                        fontweight="bold", va="center", transform=ax.transAxes)
                y -= 0.04

                # Formula
                formula = expl.get("formula", "")
                if formula:
                    rect2 = mpatches.FancyBboxPatch(
                        (0.0, y - 0.035), 1.0, 0.035,
                        boxstyle="round,pad=0.001",
                        facecolor=_c("primary"), edgecolor="none"
                    )
                    ax.add_patch(rect2)
                    ax.text(0.01, y - 0.018, formula,
                            color="white", fontsize=8 * _scale(),
                            fontfamily="monospace", va="center",
                            transform=ax.transAxes)
                    y -= 0.035

                # Body text
                body = expl.get("body", "")[:350]
                ax.text(0.01, y - 0.01, body,
                        color=_c("text_body"), fontsize=8 * _scale(),
                        va="top", wrap=True, transform=ax.transAxes)
                y -= 0.07

                # Variables
                variables = expl.get("variables", [])
                if variables:
                    row_h = 0.028
                    ax.text(0.01, y, "Biến số:",
                            color=_c("text_muted"), fontsize=7.5 * _scale(),
                            fontweight="bold", va="top", transform=ax.transAxes)
                    y -= 0.03
                    for j, v in enumerate(variables[:4]):
                        bg = _c("stripe") if j % 2 == 0 else "white"
                        rect3 = mpatches.FancyBboxPatch(
                            (0.01, y - row_h), 0.98, row_h,
                            boxstyle="round,pad=0.001", facecolor=bg,
                            edgecolor=_c("border"), linewidth=0.3 * _bw_scale()
                        )
                        ax.add_patch(rect3)
                        ax.text(0.02, y - row_h / 2, v.get("name", ""),
                                color=_c("primary"), fontsize=7 * _scale(),
                                fontweight="bold", va="center", transform=ax.transAxes)
                        ax.text(0.20, y - row_h / 2, v.get("desc", ""),
                                color=_c("text_muted"), fontsize=6.5 * _scale(),
                                va="center", transform=ax.transAxes)
                        y -= row_h
                    y -= 0.02

                y -= 0.04

            _figure_postprocess(fig)
            pdf.savefig(fig, bbox_inches="tight", dpi=150)
            plt.close(fig)
            page_num += 1

    return out_path
