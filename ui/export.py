# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""PDF export logic, extracted from app.py."""

from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image as PILImage


def export_pdf(result: dict) -> bytes:
    """Build and return a PDF report from the analysis result dict."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import (
        Image,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    story = []

    styles = getSampleStyleSheet()

    primary_color   = colors.HexColor("#6366f1")
    secondary_color = colors.HexColor("#06b6d4")
    text_color      = colors.HexColor("#1e293b")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=15,
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=secondary_color,
        spaceAfter=20,
    )
    h1_style = ParagraphStyle(
        "H1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=text_color,
        spaceAfter=8,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=text_color,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=6,
    )

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("Agentic Data Analysis Report", title_style))
    story.append(
        Paragraph(
            "Autonomous Business Intelligence Insights & Visualizations", subtitle_style
        )
    )
    story.append(Spacer(1, 10))

    # ── Dataset summary table ─────────────────────────────────────────────────
    story.append(Paragraph("Dataset Summary", h1_style))
    df = result.get("dataframe")
    if df is not None:
        summary_data = [
            [Paragraph("<b>Metric</b>", body_style), Paragraph("<b>Value</b>", body_style)],
            [Paragraph("Total Rows",    body_style), Paragraph(str(df.shape[0]), body_style)],
            [Paragraph("Total Columns", body_style), Paragraph(str(df.shape[1]), body_style)],
            [
                Paragraph("Columns", body_style),
                Paragraph(
                    f"{', '.join(df.columns[:8])}{'...' if len(df.columns) > 8 else ''}",
                    body_style,
                ),
            ],
        ]
        t = Table(summary_data, colWidths=[130, 370])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING",    (0, 0), (-1, -1), 5),
                    ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(t)
    story.append(Spacer(1, 10))

    # ── Cleaning steps ────────────────────────────────────────────────────────
    story.append(Paragraph("Data Cleaning Steps", h1_style))
    for raw in result.get("cleaning_steps", "").split("\n"):
        line = raw.strip().lstrip("-*• ").strip()
        if line:
            story.append(Paragraph(f"• {line}", bullet_style))
    story.append(Spacer(1, 10))

    # ── Relations ─────────────────────────────────────────────────────────────
    story.append(Paragraph("Identified Relationships", h1_style))
    for raw in result.get("relations", "").split("\n"):
        line = raw.strip().lstrip("-*• ").strip()
        if line:
            story.append(Paragraph(f"🔗 {line}", bullet_style))
    story.append(Spacer(1, 10))

    # ── Key insights ──────────────────────────────────────────────────────────
    story.append(Paragraph("Key Insights", h1_style))
    import re
    for raw in result.get("insights", "").split("\n"):
        line = raw.strip()
        # strip numbered prefix (1. 2. ... N.)
        line = re.sub(r"^[\d]+\.\s+", "", line).lstrip("-*• ").strip()
        if line:
            story.append(Paragraph(f"✨ {line}", bullet_style))

    # ── Visualizations ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Visualizations", h1_style))

    output_dir = result.get("output_dir", Path("outputs"))
    png_files  = list(Path(output_dir).glob("*.png"))

    if png_files:
        for png_file in png_files:
            try:
                with PILImage.open(png_file) as img:
                    orig_w, orig_h = img.size
                max_w, max_h = 460, 300
                aspect = orig_h / orig_w
                if aspect > (max_h / max_w):
                    new_h = max_h
                    new_w = new_h / aspect
                else:
                    new_w = max_w
                    new_h = new_w * aspect
                story.append(Paragraph(f"<b>{png_file.stem}</b>", body_style))
                story.append(Image(str(png_file), width=new_w, height=new_h))
                story.append(Spacer(1, 10))
            except Exception as e:
                story.append(
                    Paragraph(f"Error loading image {png_file.name}: {e}", body_style)
                )
    else:
        story.append(Paragraph("No visualizations generated.", body_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


@st.cache_data(show_spinner=False)
def export_pdf_cached(cache_key: str, result_cleaning: str, result_relations: str,
                      result_insights: str, result_code: str,
                      output_dir_str: str, df_csv: str) -> bytes:
    """Cached wrapper — only rebuilds the PDF when result content actually changes."""
    import pandas as pd
    from io import StringIO
    df = pd.read_csv(StringIO(df_csv))
    result = {
        "dataframe":     df,
        "cleaning_steps": result_cleaning,
        "relations":      result_relations,
        "insights":       result_insights,
        "code":           result_code,
        "output_dir":     output_dir_str,
    }
    return export_pdf(result)
