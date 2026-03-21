"""
certificate.py — Generate a downloadable PDF training certificate using reportlab.
Now includes unique certificate ID (UUID4).
"""

import io
import uuid
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    Table,
    TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# Brand colours
PURPLE = colors.HexColor("#7C3AED")
EMERALD = colors.HexColor("#10B981")
DARK = colors.HexColor("#0E1117")
LIGHT_GRAY = colors.HexColor("#F3F4F6")
WHITE = colors.white


def analyse_quiz_results(
    quiz: list[dict], user_answers: list[str]
) -> dict:
    """
    Score the quiz and identify knowledge gaps.

    Args:
        quiz: List of quiz question dicts from ai_engine output.
        user_answers: List of user-selected answer letters (e.g. ["A", "C", "B", ...])

    Returns:
        {
            "score": int,          # 0–100
            "correct": int,
            "total": int,
            "passed": bool,        # True if score >= 70
            "gap_questions": [...] # questions answered incorrectly
        }
    """
    total = len(quiz)
    correct = 0
    gap_questions = []

    for i, (q, ans) in enumerate(zip(quiz, user_answers)):
        correct_answer = q.get("answer", "").strip().upper()
        user_answer = (ans or "").strip().upper()
        if user_answer == correct_answer:
            correct += 1
        else:
            gap_questions.append(
                {
                    "question": q.get("question", ""),
                    "user_answer": user_answer,
                    "correct_answer": correct_answer,
                    "explanation": q.get("explanation", ""),
                }
            )

    score = int((correct / total) * 100) if total > 0 else 0
    return {
        "score": score,
        "correct": correct,
        "total": total,
        "passed": score >= 70,
        "gap_questions": gap_questions,
    }


def generate_certificate(
    employee_name: str,
    sop_title: str,
    score: int,
    passed: bool,
    skills_covered: list[str],
) -> tuple[bytes, str]:
    """
    Generate a PDF certificate and return it as bytes along with a unique ID.

    Args:
        employee_name: Name printed on the certificate.
        sop_title: Title of the SOP training completed.
        score: Readiness score 0–100.
        passed: Whether the employee passed (score >= 70).
        skills_covered: List of skill strings from the training module.

    Returns:
        (pdf_bytes, certificate_id) — PDF file content and unique certificate ID.
    """
    cert_id = str(uuid.uuid4()).upper()[:12]  # Short readable ID
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    cert_title_style = ParagraphStyle(
        "CertTitle",
        fontName="Helvetica-Bold",
        fontSize=32,
        textColor=PURPLE,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        fontName="Helvetica",
        fontSize=13,
        textColor=colors.HexColor("#6B7280"),
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    name_style = ParagraphStyle(
        "Name",
        fontName="Helvetica-Bold",
        fontSize=26,
        textColor=DARK,
        alignment=TA_CENTER,
    )
    body_style = ParagraphStyle(
        "Body",
        fontName="Helvetica",
        fontSize=12,
        textColor=colors.HexColor("#374151"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    skills_style = ParagraphStyle(
        "Skills",
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#6B7280"),
        alignment=TA_CENTER,
    )
    stamp_style = ParagraphStyle(
        "Stamp",
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=EMERALD if passed else colors.red,
        alignment=TA_CENTER,
    )

    elements = []

    # ─── Header bar ──────────────────────────────────────────────────────────
    elements.append(
        Paragraph("🏆  Certificate of Training Completion", cert_title_style)
    )
    elements.append(
        Paragraph("Nutrabay — AI-Powered Employee Training System", subtitle_style)
    )
    elements.append(HRFlowable(width="100%", thickness=2, color=PURPLE))
    elements.append(Spacer(1, 8 * mm))

    # ─── Body ─────────────────────────────────────────────────────────────────
    elements.append(Paragraph("This is to certify that", body_style))
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph(employee_name or "Employee", name_style))
    elements.append(Spacer(1, 3 * mm))
    elements.append(
        Paragraph(
            f"has successfully completed the training module for the SOP:", body_style
        )
    )
    elements.append(
        Paragraph(
            f"<b>{sop_title}</b>",
            ParagraphStyle(
                "SopTitle",
                fontName="Helvetica-Bold",
                fontSize=16,
                textColor=PURPLE,
                alignment=TA_CENTER,
            ),
        )
    )
    elements.append(Spacer(1, 5 * mm))

    # ─── Score table ─────────────────────────────────────────────────────────
    score_label = f"Readiness Score: {score}/100"
    status_label = "✅  PASSED" if passed else "❌  NEEDS REVIEW"
    date_label = f"Date: {date.today().strftime('%d %B %Y')}"

    table_data = [[score_label, status_label, date_label]]
    t = Table(table_data, colWidths=[90 * mm, 80 * mm, 80 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
                ("TEXTCOLOR", (0, 0), (0, 0), DARK),
                ("TEXTCOLOR", (1, 0), (1, 0), EMERALD if passed else colors.red),
                ("TEXTCOLOR", (2, 0), (2, 0), colors.HexColor("#6B7280")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 13),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_GRAY]),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("ROUNDEDCORNERS", [6]),
            ]
        )
    )
    elements.append(t)
    elements.append(Spacer(1, 5 * mm))

    # ─── Skills ──────────────────────────────────────────────────────────────
    if skills_covered:
        skills_text = "  •  ".join(skills_covered)
        elements.append(Paragraph(f"<b>Skills Demonstrated:</b>  {skills_text}", skills_style))
        elements.append(Spacer(1, 4 * mm))

    # ─── Certificate ID ──────────────────────────────────────────────────────
    elements.append(
        Paragraph(
            f"<b>Certificate ID:</b> {cert_id}",
            ParagraphStyle(
                "CertId",
                fontName="Helvetica",
                fontSize=9,
                textColor=colors.HexColor("#9CA3AF"),
                alignment=TA_CENTER,
            ),
        )
    )
    elements.append(Spacer(1, 2 * mm))

    # ─── Footer ──────────────────────────────────────────────────────────────
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E5E7EB")))
    elements.append(Spacer(1, 3 * mm))
    elements.append(
        Paragraph(
            "Generated by Nutrabay SOP Training Engine  •  Powered by GPT-4o-mini & Sarvam AI",
            ParagraphStyle(
                "Footer",
                fontName="Helvetica",
                fontSize=9,
                textColor=colors.HexColor("#9CA3AF"),
                alignment=TA_CENTER,
            ),
        )
    )

    doc.build(elements)
    return buffer.getvalue(), cert_id
