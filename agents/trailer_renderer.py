"""Trailer renderer — matplotlib fallback for 4-page free preview PDF."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages

from agents.renderer import (
    A4, _apply_style, _new_content_ax, _draw_page_frame,
    _c, _layout, _scale, _bw_scale, _figure_postprocess,
)


def _estimate_valuation(financials: dict, ratios: dict) -> dict:
    income_cur = financials.get("income_statement", {}).get("current", {})
    derived = ratios.get("_derived", {})
    ebitda = derived.get("ebitda", 0) or 0
    net_debt = derived.get("net_debt", 0) or 0

    multiple = 8.0
    ev = ebitda * multiple
    equity = ev - net_debt

    net_income = income_cur.get("net_profit_after_tax", 0) or 0
    pe_eq = net_income * 12

    mid = (equity + pe_eq) / 2 if equity and pe_eq else (equity or pe_eq)
    return {
        "equity_low": round(mid * 0.85, 0),
        "equity_mid": round(mid, 0),
        "equity_high": round(mid * 1.18, 0),
    }


def render_trailer(payload: dict, out_path: str,
                   brand: dict = None, config: dict = None) -> str:
    _apply_style(config or {}, brand or {})
    financials = payload.get("financials", {})
    ratios = payload.get("ratios", {})
    industry = payload.get("industry", {})
    company = financials.get("company", {})
    unit = financials.get("unit", "")
    content = (config or {}).get("content", {})

    est = _estimate_valuation(financials, ratios)
    ind = industry.get("industry", industry) if isinstance(industry, dict) else {}

    with PdfPages(str(out_path)) as pdf:
        # ── Page 1: Cover ────────────────────────────────────────────────────
        fig = plt.figure(figsize=A4)
        ax = _new_content_ax(fig)
        _draw_page_frame(fig, content.get("trailer_brand_name", "ValuAI"), 1, 4)

        badge = content.get("trailer_preview_badge", "XEM TRƯỚC")
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.35, 0.75), 0.30, 0.05,
            boxstyle="round,pad=0.01", facecolor=_c("secondary"), edgecolor="none"
        ))
        ax.text(0.5, 0.775, badge, color="white", fontsize=10 * _scale(),
                fontweight="bold", ha="center", va="center", transform=ax.transAxes)

        ax.text(0.5, 0.68, company.get("name", "Doanh nghiệp"),
                color=_c("primary"), fontsize=16 * _scale(), fontweight="bold",
                ha="center", va="center", transform=ax.transAxes)
        ax.text(0.5, 0.62, f"Ngành: {company.get('industry', 'N/A')}",
                color=_c("text_muted"), fontsize=10 * _scale(),
                ha="center", va="center", transform=ax.transAxes)

        ax.add_patch(mpatches.FancyBboxPatch(
            (0.1, 0.44), 0.80, 0.13,
            boxstyle="round,pad=0.01", facecolor=_c("primary_light"),
            edgecolor=_c("primary"), linewidth=1.5 * _bw_scale()
        ))
        ax.text(0.5, 0.535, "ĐỊNH GIÁ ƯỚC TÍNH",
                color=_c("primary"), fontsize=9 * _scale(), fontweight="bold",
                ha="center", va="center", transform=ax.transAxes)
        ax.text(0.5, 0.49,
                f"███████ – ███████ {unit}",
                color=_c("text_faint"), fontsize=14 * _scale(),
                ha="center", va="center", transform=ax.transAxes)
        ax.text(0.5, 0.455, "Mua báo cáo đầy đủ để xem con số thực",
                color=_c("text_muted"), fontsize=8 * _scale(),
                ha="center", va="center", transform=ax.transAxes)

        ax.text(0.5, 0.30, content.get("trailer_tagline", "Định giá thông minh"),
                color=_c("text_muted"), fontsize=10 * _scale(),
                ha="center", va="center", transform=ax.transAxes)

        _figure_postprocess(fig)
        pdf.savefig(fig, bbox_inches="tight", dpi=150)
        plt.close(fig)

        # ── Page 2: Financial Snapshot ────────────────────────────────────────
        fig = plt.figure(figsize=A4)
        ax = _new_content_ax(fig)
        _draw_page_frame(fig, "SNAPSHOT TÀI CHÍNH", 2, 4)

        income_cur = financials.get("income_statement", {}).get("current", {})
        income_prev = financials.get("income_statement", {}).get("previous", {})
        bs_cur = (financials.get("balance_sheet", {}).get("current") or {})
        cur_a = bs_cur.get("assets", {}) or {}
        cur_e = bs_cur.get("equity", {}) or {}

        period_cur = financials.get("period", {}).get("current", {}).get("label", "Hiện tại")
        period_prev = financials.get("period", {}).get("previous", {}).get("label", "Trước")

        kpis = [
            ("Doanh thu thuần", income_cur.get("net_revenue") or income_cur.get("revenue"),
             income_prev.get("net_revenue") or income_prev.get("revenue")),
            ("Lợi nhuận gộp", income_cur.get("gross_profit"), income_prev.get("gross_profit")),
            ("EBIT", income_cur.get("operating_profit"), income_prev.get("operating_profit")),
            ("Lợi nhuận ròng", income_cur.get("net_profit_after_tax"), income_prev.get("net_profit_after_tax")),
            ("Tổng tài sản", cur_a.get("total_assets"), None),
            ("Vốn chủ sở hữu", cur_e.get("total_equity"), None),
        ]

        y = 0.88
        ax.text(0.0, y + 0.04, f"Đơn vị: {unit}", color=_c("text_muted"),
                fontsize=8 * _scale(), va="top", transform=ax.transAxes)

        row_h = 0.07
        for i, (label, cur, prev) in enumerate(kpis):
            bg = _c("stripe") if i % 2 == 0 else "white"
            rect = mpatches.FancyBboxPatch(
                (0, y - row_h), 1.0, row_h,
                boxstyle="round,pad=0.001", facecolor=bg, edgecolor=_c("border"),
                linewidth=0.4 * _bw_scale()
            )
            ax.add_patch(rect)
            ax.text(0.02, y - row_h / 2, label, color=_c("text_body"),
                    fontsize=9.5 * _scale(), va="center", transform=ax.transAxes)
            if cur is not None:
                ax.text(0.55, y - row_h / 2, f"{cur:,.0f}",
                        color=_c("text_primary"), fontsize=9.5 * _scale(),
                        fontweight="bold", va="center", transform=ax.transAxes)
            if prev is not None and cur is not None and prev != 0:
                growth = (cur - prev) / abs(prev) * 100
                g_color = "#10b981" if growth >= 0 else "#ef4444"
                ax.text(0.80, y - row_h / 2, f"{growth:+.1f}%",
                        color=g_color, fontsize=9 * _scale(),
                        fontweight="bold", va="center", transform=ax.transAxes)
            y -= row_h

        _figure_postprocess(fig)
        pdf.savefig(fig, bbox_inches="tight", dpi=150)
        plt.close(fig)

        # ── Page 3: Industry + Key Ratios ─────────────────────────────────────
        fig = plt.figure(figsize=A4)
        ax = _new_content_ax(fig)
        _draw_page_frame(fig, "NGÀNH & TỶ SỐ NỔI BẬT", 3, 4)

        y = 0.92
        ax.text(0.0, y, "NGÀNH", color=_c("primary"),
                fontsize=11 * _scale(), fontweight="bold", va="top",
                transform=ax.transAxes)
        ax.text(0.0, y - 0.04, f"{ind.get('industry_name', 'N/A')}",
                color=_c("text_body"), fontsize=9.5 * _scale(), va="top",
                transform=ax.transAxes)
        ax.text(0.0, y - 0.08, f"CAGR 5Y: {ind.get('industry_cagr_5y_pct', 'N/A')}%  |  "
                                f"Triển vọng: {ind.get('industry_outlook_3y', 'N/A')[:50]}",
                color=_c("text_muted"), fontsize=8.5 * _scale(), va="top",
                transform=ax.transAxes)

        y -= 0.16
        ax.text(0.0, y, "TỶ SỐ TÀI CHÍNH NỔI BẬT", color=_c("primary"),
                fontsize=11 * _scale(), fontweight="bold", va="top",
                transform=ax.transAxes)
        y -= 0.04

        r = ratios.get("ratios", {})
        key_ratios = [
            ("Gross Margin", r.get("profitability", {}).get("gross_margin", {})),
            ("Net Margin", r.get("profitability", {}).get("net_margin", {})),
            ("ROE", r.get("profitability", {}).get("roe", {})),
            ("Current Ratio", r.get("liquidity", {}).get("current_ratio", {})),
            ("D/E Ratio", r.get("leverage", {}).get("debt_to_equity", {})),
        ]
        from agents.renderer import _DEFAULT_RATING
        row_h = 0.065
        for i, (label, rd) in enumerate(key_ratios):
            val = rd.get("value")
            rating = rd.get("rating", "n/a")
            color = _DEFAULT_RATING.get(rating, _c("text_muted"))
            bg = _c("stripe") if i % 2 == 0 else "white"
            rect = mpatches.FancyBboxPatch(
                (0, y - row_h), 1.0, row_h,
                boxstyle="round,pad=0.001", facecolor=bg, edgecolor=_c("border"),
                linewidth=0.4 * _bw_scale()
            )
            ax.add_patch(rect)
            ax.text(0.02, y - row_h / 2, label, color=_c("text_body"),
                    fontsize=9.5 * _scale(), va="center", transform=ax.transAxes)
            ax.text(0.65, y - row_h / 2,
                    f"{val:.2f}" if val is not None else "N/A",
                    color=color, fontsize=9.5 * _scale(),
                    fontweight="bold", va="center", transform=ax.transAxes)
            ax.text(0.82, y - row_h / 2, rating, color=color,
                    fontsize=8.5 * _scale(), va="center", transform=ax.transAxes)
            y -= row_h

        _figure_postprocess(fig)
        pdf.savefig(fig, bbox_inches="tight", dpi=150)
        plt.close(fig)

        # ── Page 4: CTA ───────────────────────────────────────────────────────
        fig = plt.figure(figsize=A4)
        ax = _new_content_ax(fig)
        _draw_page_frame(fig, "MUA BÁO CÁO ĐẦY ĐỦ", 4, 4)

        ax.add_patch(mpatches.FancyBboxPatch(
            (0.05, 0.60), 0.90, 0.30,
            boxstyle="round,pad=0.02", facecolor=_c("primary_light"),
            edgecolor=_c("primary"), linewidth=1.5 * _bw_scale()
        ))
        ax.text(0.5, 0.84, "BÁO CÁO ĐẦY ĐỦ BAO GỒM:",
                color=_c("primary"), fontsize=12 * _scale(), fontweight="bold",
                ha="center", va="center", transform=ax.transAxes)
        items = [
            "✓ Định giá đầy đủ DCF + Multiples (~37 trang)",
            "✓ Football Field & Sensitivity Analysis",
            "✓ Dự phóng tài chính 5 năm chi tiết",
            "✓ Investment Thesis & Risk Matrix",
            "✓ Deal Recommendation & Exit Strategy",
        ]
        for i, item in enumerate(items):
            ax.text(0.15, 0.78 - i * 0.04, item, color=_c("text_body"),
                    fontsize=9 * _scale(), va="center", transform=ax.transAxes)

        footer = content.get("trailer_footer", "Mua báo cáo để xem chi tiết")
        ax.text(0.5, 0.48, footer, color=_c("text_muted"),
                fontsize=9.5 * _scale(), ha="center", va="center",
                transform=ax.transAxes)

        _figure_postprocess(fig)
        pdf.savefig(fig, bbox_inches="tight", dpi=150)
        plt.close(fig)

    return out_path
