"""
PDF Report Generator using fpdf2.
Produces a branded valuation report with all key sections.
"""

import logging
import os
import tempfile
from datetime import datetime
from typing import Optional

from app.db.models import Valuation, Company

logger = logging.getLogger(__name__)


def _fmt_vnd(value: Optional[float]) -> str:
    """Format a VND value in tỷ đồng (billions)."""
    if value is None or value == 0:
        return "N/A"
    billions = value / 1_000_000_000 if value > 1_000_000 else value
    return f"{billions:,.1f} tỷ VND"


async def generate_pdf_report(valuation: Valuation, company: Optional[Company]) -> str:
    """
    Generate a PDF valuation report and save to a temp file.
    Returns the file path.
    """
    logger.info(f"[REPORT] generating PDF for valuation={valuation.id}")

    try:
        from fpdf import FPDF
    except ImportError:
        raise RuntimeError("fpdf2 not installed. Run: pip install fpdf2")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    company_name = company.name if company else "Company"
    today = datetime.now().strftime("%B %d, %Y")

    # ── Cover ──────────────────────────────────────────────────────────
    pdf.set_fill_color(30, 58, 138)  # dark blue
    pdf.rect(0, 0, 210, 50, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_xy(10, 12)
    pdf.cell(0, 10, "ValuAI Valuation Report", align="C")
    pdf.set_font("Helvetica", "", 14)
    pdf.set_xy(10, 28)
    pdf.cell(0, 10, company_name, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(10, 40)
    pdf.cell(0, 8, f"Generated: {today}", align="C")

    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(10, 60)

    # ── Valuation Summary ─────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Valuation Summary", ln=True)
    pdf.set_draw_color(30, 58, 138)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_fill_color(239, 246, 255)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(190, 10, f"Final Valuation Range", fill=True, ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)

    ranges = [
        ("Minimum", valuation.final_range_min),
        ("Mid-point", valuation.final_range_mid),
        ("Maximum", valuation.final_range_max),
    ]
    for label, val in ranges:
        pdf.cell(95, 8, f"  {label}:", border="LB")
        pdf.cell(95, 8, _fmt_vnd(float(val) if val else None), border="RB", align="R")
        pdf.ln()
    pdf.ln(6)

    # ── Method Breakdown ──────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Method Breakdown", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    methods = [
        ("DCF (Discounted Cash Flow)", valuation.dcf_value, valuation.dcf_confidence),
        ("Comparable Companies", valuation.comparable_value, valuation.comparable_confidence),
        ("Scorecard", valuation.scorecard_value, valuation.scorecard_confidence),
    ]
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(80, 8, "Method", border=1)
    pdf.cell(60, 8, "Implied Value", border=1, align="C")
    pdf.cell(50, 8, "Confidence", border=1, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 10)
    for method_name, method_val, method_conf in methods:
        pdf.cell(80, 8, method_name, border=1)
        pdf.cell(60, 8, _fmt_vnd(float(method_val) if method_val else None), border=1, align="C")
        pdf.cell(50, 8, f"{float(method_conf or 0):.0%}", border=1, align="C")
        pdf.ln()
    pdf.ln(6)

    # ── Scorecard ─────────────────────────────────────────────────────
    if valuation.scorecard_breakdown:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"Scorecard Detail (Total: {float(valuation.scorecard_total or 0):.1f}/10)", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(90, 7, "Criterion", border=1)
        pdf.cell(20, 7, "Score", border=1, align="C")
        pdf.cell(80, 7, "Reason", border=1)
        pdf.ln()
        pdf.set_font("Helvetica", "", 9)
        for criterion, detail in valuation.scorecard_breakdown.items():
            if isinstance(detail, dict):
                name = criterion.replace("_", " ").title()
                score = detail.get("score", 0)
                reason = str(detail.get("reason", ""))[:60]
                pdf.cell(90, 7, name, border=1)
                pdf.cell(20, 7, str(score), border=1, align="C")
                pdf.cell(80, 7, reason, border=1)
                pdf.ln()
        pdf.ln(6)

    # ── SWOT ──────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "SWOT Analysis", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    def _swot_section(title: str, items: list, color: tuple):
        pdf.set_fill_color(*color)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(190, 8, f"  {title}", fill=True, ln=True)
        pdf.set_font("Helvetica", "", 10)
        for item in (items or []):
            pdf.cell(10, 7, "•")
            pdf.multi_cell(180, 7, str(item))
        pdf.ln(2)

    _swot_section("Strengths", list(valuation.strengths or []), (209, 250, 229))
    _swot_section("Weaknesses", list(valuation.weaknesses or []), (254, 226, 226))
    _swot_section("Opportunities", list(valuation.opportunities or []), (219, 234, 254))
    _swot_section("Threats", list(valuation.threats or []), (255, 237, 213))

    # ── Recommendations ───────────────────────────────────────────────
    if valuation.recommendations:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Strategic Recommendations", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Helvetica", "", 10)
        for i, rec in enumerate(valuation.recommendations or [], 1):
            pdf.cell(10, 7, f"{i}.")
            pdf.multi_cell(180, 7, str(rec))
            pdf.ln(1)

    # ── Executive Summary ─────────────────────────────────────────────
    if valuation.report_text:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Executive Summary", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Helvetica", "", 10)
        # fpdf2 handles multi-line text
        pdf.multi_cell(190, 6, valuation.report_text)

    # ── Footer ────────────────────────────────────────────────────────
    pdf.set_y(-20)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 10, f"ValuAI — Confidential Valuation Report — {today}", align="C")

    # Save to temp file
    tmp_dir = os.environ.get("REPORT_OUTPUT_DIR", tempfile.gettempdir())
    os.makedirs(tmp_dir, exist_ok=True)
    pdf_path = os.path.join(tmp_dir, f"valuation_{valuation.id}.pdf")
    pdf.output(pdf_path)

    logger.info(f"[REPORT] PDF saved to {pdf_path}")
    return pdf_path
