# ============================================================
# AI Contract Risk Analyzer — PDF Report Generator
# utils/report_generator.py
#
# Uses ReportLab to produce a professional, styled PDF report
# containing the full clause-by-clause risk analysis.
# ============================================================

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


# ── Brand Colors ──────────────────────────────────────────
COLOR_HIGH   = colors.HexColor("#E63939")
COLOR_WARN   = colors.HexColor("#F57C00")
COLOR_SAFE   = colors.HexColor("#2E7D32")
COLOR_BG     = colors.HexColor("#0F1117")
COLOR_CARD   = colors.HexColor("#1A1D2E")
COLOR_TEXT   = colors.HexColor("#1a1a2e")
COLOR_ACCENT = colors.HexColor("#4F8EF7")


def risk_color(level: str):
    """Return the brand color for a given risk level string."""
    mapping = {"HIGH RISK": COLOR_HIGH, "WARNING": COLOR_WARN, "SAFE": COLOR_SAFE}
    return mapping.get(level, colors.grey)


def risk_emoji(level: str) -> str:
    mapping = {"HIGH RISK": "❌ HIGH RISK", "WARNING": "⚠ WARNING", "SAFE": "✅ SAFE"}
    return mapping.get(level, level)


def final_recommendation(results: list[dict]) -> tuple[str, str]:
    """
    Compute the overall recommendation based on risk counts.
    Returns (short_label, detail_message).
    """
    high = sum(1 for r in results if r["risk_level"] == "HIGH RISK")
    warn = sum(1 for r in results if r["risk_level"] == "WARNING")
    total = len(results)

    if high == 0 and warn <= 2:
        return "✅ Safe to Sign", "This contract appears generally fair. Review the warning clauses before signing."
    elif high <= 2:
        return "⚠ Review Carefully Before Signing", f"{high} high-risk clause(s) detected. Negotiate or remove them."
    else:
        return "❌ Do NOT Sign", f"{high} high-risk clauses detected out of {total}. This contract is heavily skewed against you."


def generate_pdf_report(results: list[dict], user_role: str) -> bytes:
    """
    Generate a complete professional PDF report.

    Returns raw PDF bytes that can be sent as a Streamlit download.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
    )

    # ── Styles ──────────────────────────────────────────────
    base_styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title", parent=base_styles["Title"],
        fontSize=22, textColor=COLOR_ACCENT,
        spaceAfter=4, alignment=TA_CENTER, fontName="Helvetica-Bold"
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=base_styles["Normal"],
        fontSize=11, textColor=colors.grey,
        spaceAfter=2, alignment=TA_CENTER
    )
    section_header_style = ParagraphStyle(
        "SectionHeader", parent=base_styles["Normal"],
        fontSize=13, textColor=COLOR_ACCENT,
        spaceBefore=12, spaceAfter=4, fontName="Helvetica-Bold"
    )
    body_style = ParagraphStyle(
        "Body", parent=base_styles["Normal"],
        fontSize=9, leading=13, textColor=COLOR_TEXT,
        alignment=TA_JUSTIFY
    )
    label_style = ParagraphStyle(
        "Label", parent=base_styles["Normal"],
        fontSize=8, textColor=colors.grey, fontName="Helvetica-Bold"
    )
    clause_style = ParagraphStyle(
        "ClauseText", parent=base_styles["Normal"],
        fontSize=8, leading=12, textColor=colors.HexColor("#444444"),
        alignment=TA_JUSTIFY, leftIndent=8
    )

    # ── Story (content) ─────────────────────────────────────
    story = []
    now = datetime.now().strftime("%d %B %Y, %I:%M %p")

    # Header
    story.append(Paragraph("AI Contract Risk Analyzer", title_style))
    story.append(Paragraph("Powered by Groq LLaMA-3.1 · Indian Contract Act 1872", subtitle_style))
    story.append(Paragraph(f"Generated: {now}   |   User Role: {user_role}", subtitle_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT))
    story.append(Spacer(1, 0.3*cm))

    # Privacy Notice
    notice_style = ParagraphStyle(
        "Notice", parent=base_styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#555555"),
        borderPad=6, backColor=colors.HexColor("#FFF9C4"),
        borderColor=colors.HexColor("#F57C00"), borderWidth=1,
        alignment=TA_CENTER
    )
    story.append(Paragraph(
        "🔒 Privacy Notice: Your documents were processed only for this analysis. They are never stored or shared.",
        notice_style
    ))
    story.append(Spacer(1, 0.4*cm))

    # Dashboard Summary Table
    high  = sum(1 for r in results if r["risk_level"] == "HIGH RISK")
    warn  = sum(1 for r in results if r["risk_level"] == "WARNING")
    safe  = sum(1 for r in results if r["risk_level"] == "SAFE")
    total = len(results)
    rec_label, rec_detail = final_recommendation(results)

    story.append(Paragraph("📊 Analysis Dashboard", section_header_style))

    summary_data = [
        ["Total Clauses", "✅ Safe", "⚠ Warning", "❌ High Risk"],
        [str(total), str(safe), str(warn), str(high)],
    ]
    summary_table = Table(summary_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 10),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F5F5F5")]),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*cm))

    # Final Recommendation Box
    rec_style = ParagraphStyle(
        "Rec", parent=base_styles["Normal"],
        fontSize=12, fontName="Helvetica-Bold",
        textColor=colors.white,
        backColor=risk_color(
            "HIGH RISK" if high > 2 else ("WARNING" if high > 0 else "SAFE")
        ),
        borderPad=10, alignment=TA_CENTER
    )
    story.append(Paragraph(f"Overall Recommendation: {rec_label}", rec_style))
    story.append(Paragraph(rec_detail, ParagraphStyle(
        "RecDetail", parent=base_styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER, spaceBefore=4
    )))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))

    # ── Per-Clause Analysis ──────────────────────────────────
    story.append(Paragraph("📋 Clause-by-Clause Analysis", section_header_style))

    for r in results:
        level = r["risk_level"]
        c_color = risk_color(level)

        # Clause header row
        header_data = [[
            Paragraph(f"Clause {r['clause_number']}", ParagraphStyle(
                "CH", parent=base_styles["Normal"],
                fontSize=10, fontName="Helvetica-Bold", textColor=colors.white
            )),
            Paragraph(risk_emoji(level), ParagraphStyle(
                "RL", parent=base_styles["Normal"],
                fontSize=10, fontName="Helvetica-Bold",
                textColor=colors.white, alignment=TA_CENTER
            )),
        ]]
        header_table = Table(header_data, colWidths=[13*cm, 3*cm])
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), c_color),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (0, 0), 8),
        ]))

        # Detail rows
        detail_data = [
            [Paragraph("Original Clause:", label_style),
             Paragraph(r["clause_text"][:400], clause_style)],
            [Paragraph("📌 Explanation:", label_style),
             Paragraph(r["explanation"], body_style)],
            [Paragraph("⚡ Consequence:", label_style),
             Paragraph(r["consequence"], body_style)],
            [Paragraph("🔧 Action:", label_style),
             Paragraph(r["action"], body_style)],
            [Paragraph("✏️ Safer Rewrite:", label_style),
             Paragraph(r["rewrite"], body_style)],
        ]
        detail_table = Table(detail_data, colWidths=[3.5*cm, 12.5*cm])
        detail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
            ("VALIGN",     (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#E0E0E0")),
        ]))

        # Group header + detail to keep them together on one page
        story.append(KeepTogether([header_table, detail_table]))
        story.append(Spacer(1, 0.4*cm))

    # Footer disclaimer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Paragraph(
        "⚠️ Disclaimer: This report is generated by an AI system for informational purposes only. "
        "It does not constitute legal advice. Please consult a qualified legal professional before "
        "signing any contract.",
        ParagraphStyle("Footer", parent=base_styles["Normal"],
                       fontSize=7, textColor=colors.grey, alignment=TA_CENTER, spaceBefore=6)
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
