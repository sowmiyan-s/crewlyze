# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
PDF export — world-class executive report format.
Premium design with:
  - Cinematic cover page with gradient header band and Crewlyze branding
  - Table of Contents page
  - Numbered section headers with coloured icon chips
  - Three-panel insight cards (Observation | Business Implication | Actionable Strategy)
  - Chart thumbnails embedded inline below each insight
  - Professional correlation tables with alternating bands
  - Data statistics tables with conditional number formatting
  - Styled risk alert boxes
  - Polished chat-log format with role badges and timestamps
  - Two-pass page-number canvas with company footer rule
"""

import html
import io
import os
import re
import urllib.parse
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.fonts import addMapping
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

# Register standard Type 1 font mappings across all case combinations
for family in ("Courier", "courier", "COURIER"):
    addMapping(family, 0, 0, "Courier")
    addMapping(family, 1, 0, "Courier-Bold")
    addMapping(family, 0, 1, "Courier-Oblique")
    addMapping(family, 1, 1, "Courier-BoldOblique")

for family in ("Helvetica", "helvetica", "HELVETICA"):
    addMapping(family, 0, 0, "Helvetica")
    addMapping(family, 1, 0, "Helvetica-Bold")
    addMapping(family, 0, 1, "Helvetica-Oblique")
    addMapping(family, 1, 1, "Helvetica-BoldOblique")

for family in ("Times-Roman", "times-roman", "Times", "times", "TIMES"):
    addMapping(family, 0, 0, "Times-Roman")
    addMapping(family, 1, 0, "Times-Bold")
    addMapping(family, 0, 1, "Times-Italic")
    addMapping(family, 1, 1, "Times-BoldItalic")



# ─────────────────────────────────────────────────────────────────────────────
# Colour palette
# ─────────────────────────────────────────────────────────────────────────────
C_CRIMSON      = colors.HexColor("#c0392b")   # primary accent
C_CRIMSON_DARK = colors.HexColor("#7b1d1d")   # dark crimson for headings
C_CRIMSON_PALE = colors.HexColor("#fff0f0")   # very light rose tint
C_AMBER        = colors.HexColor("#d97706")   # warning amber
C_AMBER_PALE   = colors.HexColor("#fffbeb")
C_EMERALD      = colors.HexColor("#047857")   # strategy green
C_EMERALD_PALE = colors.HexColor("#ecfdf5")
C_SAPPHIRE     = colors.HexColor("#1d4ed8")   # observation blue
C_SAPPHIRE_PALE= colors.HexColor("#eff6ff")
C_INK          = colors.HexColor("#0f172a")   # body text
C_MUTED        = colors.HexColor("#475569")   # secondary text
C_BORDER       = colors.HexColor("#cbd5e1")
C_LIGHT_GRID   = colors.HexColor("#e2e8f0")
C_ROW_ALT      = colors.HexColor("#f8fafc")
C_WHITE        = colors.white
C_COVER_BG     = colors.HexColor("#100608")   # near-black cover bg
C_COVER_BAND   = colors.HexColor("#8b0000")   # deep red band


# ─────────────────────────────────────────────────────────────────────────────
# Two-Pass Canvas — Page X of Y + corporate rules
# ─────────────────────────────────────────────────────────────────────────────

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas that renders running headers, footers, and page numbers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_decorations(total)
            super().showPage()
        super().save()

    def _draw_decorations(self, total_pages: int):
        self.saveState()
        page_num = self._pageNumber

        if page_num == 1:
            # Draw double 4-side executive decorative border around Cover Page
            self.setStrokeColor(C_CRIMSON_DARK)
            self.setLineWidth(2.0)
            self.rect(28, 28, 612 - 56, 792 - 56)

            self.setStrokeColor(C_AMBER)
            self.setLineWidth(0.75)
            self.rect(34, 34, 612 - 68, 792 - 68)

            # Draw 4 decorative corner caps
            for x, y in [(34, 34), (612 - 34, 34), (34, 792 - 34), (612 - 34, 792 - 34)]:
                self.setFillColor(C_CRIMSON_DARK)
                self.circle(x, y, 3.5, fill=1, stroke=0)

            self.restoreState()
            return

        # Crewlyze wordmark — always top-left
        self.setFillColor(C_CRIMSON)
        self.setFont("Helvetica-Bold", 9)
        self.drawString(54, 756, "CREWLYZE")

        # ── Running header ──────────────────────────────────────────────────
        self.setStrokeColor(C_BORDER)
        self.setLineWidth(0.5)
        self.line(54, 748, 558, 748)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(C_MUTED)
        self.drawRightString(558, 753, "EXECUTIVE ANALYSIS REPORT  ·  CONFIDENTIAL")

        # ── Footer rule ─────────────────────────────────────────────────────
        self.line(54, 62, 558, 62)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(C_MUTED)
        self.drawString(54, 50, "Generated by Crewlyze  ·  Powered by CrewAI")
        self.drawRightString(558, 50, f"Page {page_num} of {total_pages}")

        self.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Markdown → ReportLab HTML helpers
# ─────────────────────────────────────────────────────────────────────────────

def _md_to_html(text: str) -> str:
    """Convert minimal markdown (**bold**, *italic*, `code`) to ReportLab-safe HTML."""
    if not text:
        return ""
    # 1. Strip AI reasoning artifacts first
    text = _clean_ai_artifacts(text)
    # 2. Normalize exotic unicode characters (hyphens, smart quotes, spaces)
    charmap = {
        '\u2010': '-', '\u2011': '-', '\u2012': '-', '\u2013': '-', '\u2014': '-',
        '\u2018': "'", '\u2019': "'", '\u201a': "'", '\u201b': "'",
        '\u201c': '"', '\u201d': '"', '\u201e': '"', '\u201f': '"',
        '\u00a0': ' ', '\u202f': ' ', '\u2009': ' ',
    }
    for k, v in charmap.items():
        text = text.replace(k, v)
    # 3. Escape raw HTML entities to prevent ReportLab Expat XML errors
    text = html.escape(str(text))
    # 4. Restore intended markdown formatting into safe ReportLab HTML tags
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.*?)\*",     r"<i>\1</i>", text)
    text = re.sub(r"`(.*?)`",       r'<font name="Courier">\1</font>', text)
    return text.strip()



def _clean_ai_artifacts(text: str) -> str:
    """Strip AI reasoning tags (<think>...</think>) and system prefixes from raw text."""
    if not text:
        return ""
    # Strip full <think>...</think> blocks
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'</?think>', '', cleaned, flags=re.IGNORECASE)
    lines = cleaned.split("\n")
    filtered = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^(thought|action|observation|route|call|api_key|response):\s*", stripped, re.IGNORECASE):
            continue
        filtered.append(line)
    return "\n".join(filtered).strip()


def _escape(text: str) -> str:
    """HTML-escape a plain string for safe inclusion in ReportLab Paragraphs."""
    return html.escape(str(text)) if text else ""


# ─────────────────────────────────────────────────────────────────────────────
# Insight / relation parsers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_insight_fields(text: str) -> dict:
    """Extract Observation, Business Implication, and Actionable Strategy."""
    text_clean = _clean_ai_artifacts(text)
    obs = imp = strat = ""

    obs_m   = re.search(r"\*\*Observation\*\*:\s*(.*?)(?=\*\*Business Implication\*\*|\*\*Actionable Strategy\*\*|$)", text_clean, re.DOTALL | re.IGNORECASE)
    imp_m   = re.search(r"\*\*Business Implication\*\*:\s*(.*?)(?=\*\*Observation\*\*|\*\*Actionable Strategy\*\*|$)", text_clean, re.DOTALL | re.IGNORECASE)
    strat_m = re.search(r"\*\*Actionable Strategy\*\*:\s*(.*?)(?=\*\*Observation\*\*|\*\*Business Implication\*\*|$)", text_clean, re.DOTALL | re.IGNORECASE)

    if obs_m:   obs   = obs_m.group(1).strip()
    if imp_m:   imp   = imp_m.group(1).strip()
    if strat_m: strat = strat_m.group(1).strip()

    # Loose fallbacks without asterisks
    if not obs:
        m = re.search(r"Observation:\s*(.*?)(?=Business Implication|Actionable Strategy|$)", text_clean, re.DOTALL | re.IGNORECASE)
        if m: obs = m.group(1).strip()
    if not imp:
        m = re.search(r"Business Implication:\s*(.*?)(?=Observation|Actionable Strategy|$)", text_clean, re.DOTALL | re.IGNORECASE)
        if m: imp = m.group(1).strip()
    if not strat:
        m = re.search(r"Actionable Strategy:\s*(.*?)(?=Observation|Business Implication|$)", text_clean, re.DOTALL | re.IGNORECASE)
        if m: strat = m.group(1).strip()

    return {
        "observation": obs or text_clean,
        "implication": imp,
        "strategy":    strat,
    }


def _parse_relation_line(line: str) -> dict:
    parts = [p.strip() for p in line.split("|")]
    res   = {"x": "N/A", "y": "N/A", "type": "N/A", "details": "N/A"}
    for part in parts:
        if ":" in part:
            key, val = part.split(":", 1)
            key = key.strip().lower()
            val = val.strip()
            if   key == "x":       res["x"]       = val
            elif key == "y":       res["y"]       = val
            elif key == "type":    res["type"]    = val
            elif key == "details": res["details"] = val
        else:
            pc = part.lstrip("- ").strip()
            if pc:
                res["details"] = pc
    return res


def _find_matching_chart(insight_text: str, png_files: list, placed: set):
    text_lower = insight_text.lower()
    for png in png_files:
        if png in placed:
            continue
        stem = png.stem.lower().replace("_", " ")
        words = [w for w in stem.split()
                 if w not in ("vs", "plot", "chart", "scatter", "bar",
                               "box", "line", "distribution", "correlation", "plotly")]
        if words and all(w in text_lower for w in words):
            return png
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Number formatting
# ─────────────────────────────────────────────────────────────────────────────

def _fmt_num(val) -> str:
    try:
        if pd.isna(val):
            return "—"
        f = float(val)
        if f.is_integer():
            return f"{int(f):,}"
        if abs(f) < 0.0001 and f != 0:
            return f"{f:.4e}"
        s = f"{f:,.2f}".rstrip("0").rstrip(".")
        return s
    except Exception:
        return str(val)


# ─────────────────────────────────────────────────────────────────────────────
# Reusable layout primitives
# ─────────────────────────────────────────────────────────────────────────────

def _section_header(number: str, title: str, body_style) -> Table:
    """Premium numbered section header with left crimson chip + uppercase title."""
    chip_style = ParagraphStyle(
        "ChipNum", fontName="Helvetica-Bold", fontSize=9,
        textColor=C_WHITE, alignment=1, leading=11
    )
    title_style = ParagraphStyle(
        "SectTitle", fontName="Helvetica-Bold", fontSize=13,
        textColor=C_INK, leading=16, leftIndent=0
    )
    chip = Paragraph(number, chip_style)
    heading = Paragraph(title.upper(), title_style)

    tbl = Table([[chip, heading]], colWidths=[24, 476])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), C_CRIMSON),
        ("BACKGROUND",    (1, 0), (1, 0), colors.HexColor("#fafafa")),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (0, 0),  0),
        ("LEFTPADDING",   (1, 0), (1, 0), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("LINEBELOW",     (0, 0), (-1, -1), 1.5, C_CRIMSON),
    ]))
    return tbl


def _kv_chip(label: str, value: str, label_style, value_style) -> Table:
    """Compact key-value pair rendered in two cells."""
    return Table(
        [[Paragraph(f"<b>{label}</b>", label_style), Paragraph(_escape(value), value_style)]],
        colWidths=[130, 370]
    )


def _img_flowable(png_path: Path, max_w: int = 440, max_h: int = 250):
    """Return (img_table, fig_title) for a chart image, or (None, None) on error."""
    try:
        with PILImage.open(png_path) as im:
            ow, oh = im.size
        aspect = oh / ow
        if aspect > (max_h / max_w):
            nh, nw = max_h, max_h / aspect
        else:
            nw, nh = max_w, max_w * aspect

        img_flow  = Image(str(png_path), width=nw, height=nh)
        img_table = Table([[img_flow]], colWidths=[504])
        img_table.setStyle(TableStyle([
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("BOX",           (0, 0), (-1, -1), 0.75, C_BORDER),
            ("BACKGROUND",    (0, 0), (-1, -1), C_WHITE),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        fig_title = Paragraph(
            f"<i>Figure: {png_path.stem.replace('_', ' ').title()}</i>",
            ParagraphStyle("FigCap", fontName="Helvetica-Oblique", fontSize=7.5,
                           textColor=C_MUTED, spaceBefore=3, spaceAfter=2, alignment=1)
        )
        return img_table, fig_title
    except Exception:
        return None, None


# ─────────────────────────────────────────────────────────────────────────────
# Column statistics table
# ─────────────────────────────────────────────────────────────────────────────

def _build_stats_tables(df: pd.DataFrame, body_style) -> list:
    flowables = []

    hdr_style = ParagraphStyle("TblHdr", fontName="Helvetica-Bold", fontSize=8.5,
                               textColor=C_WHITE, leading=11)
    cell_style = ParagraphStyle("TblCell", fontName="Helvetica", fontSize=8.5,
                                textColor=C_INK, leading=12)

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols     = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if numeric_cols:
        header = [
            Paragraph("<b>Column</b>",   hdr_style),
            Paragraph("<b>Min</b>",      hdr_style),
            Paragraph("<b>Max</b>",      hdr_style),
            Paragraph("<b>Mean</b>",     hdr_style),
            Paragraph("<b>Median</b>",   hdr_style),
            Paragraph("<b>Std Dev</b>",  hdr_style),
            Paragraph("<b>Missing%</b>", hdr_style),
        ]
        rows = [header]
        for col in numeric_cols[:22]:
            s   = df[col]
            sn  = s.dropna()
            miss = round(s.isnull().sum() / max(len(df), 1) * 100, 1)
            rows.append([
                Paragraph(_escape(str(col)),                                  cell_style),
                Paragraph(_fmt_num(sn.min())    if not sn.empty else "—",     cell_style),
                Paragraph(_fmt_num(sn.max())    if not sn.empty else "—",     cell_style),
                Paragraph(_fmt_num(sn.mean())   if not sn.empty else "—",     cell_style),
                Paragraph(_fmt_num(sn.median()) if not sn.empty else "—",     cell_style),
                Paragraph(_fmt_num(sn.std())    if len(sn) > 1 else "—",      cell_style),
                Paragraph(f"{miss}%",                                          cell_style),
            ])

        tbl = Table(rows, colWidths=[130, 52, 52, 52, 52, 52, 58])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  C_CRIMSON_DARK),
            ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
            ("INNERGRID",     (0, 0), (-1, -1), 0.25, C_LIGHT_GRID),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_ROW_ALT]),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        flowables.extend([tbl, Spacer(1, 10)])

    if cat_cols:
        cat_hdr = [
            Paragraph("<b>Column</b>",             hdr_style),
            Paragraph("<b>Top Values (count)</b>", hdr_style),
            Paragraph("<b>Unique</b>",             hdr_style),
            Paragraph("<b>Missing%</b>",           hdr_style),
        ]
        cat_rows = [cat_hdr]
        for col in cat_cols[:10]:
            s    = df[col]
            miss = round(s.isnull().sum() / max(len(df), 1) * 100, 1)
            top3 = s.value_counts().head(3)
            raw_items = [f"{str(v)[:25]}({c})" for v, c in top3.items()] if not top3.empty else ["—"]
            top_raw = ", ".join(raw_items)
            if len(top_raw) > 85:
                top_raw = top_raw[:82] + "..."
            top_str = _escape(top_raw)
            cat_rows.append([
                Paragraph(_escape(str(col)), cell_style),
                Paragraph(top_str,           cell_style),
                Paragraph(str(s.nunique()),  cell_style),
                Paragraph(f"{miss}%",        cell_style),
            ])

        cat_tbl = Table(cat_rows, colWidths=[110, 278, 56, 56])
        cat_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  C_CRIMSON_DARK),
            ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
            ("INNERGRID",     (0, 0), (-1, -1), 0.25, C_LIGHT_GRID),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_ROW_ALT]),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        flowables.append(cat_tbl)

    return flowables


# ─────────────────────────────────────────────────────────────────────────────
# 25 Capabilities Manifest Registry for Distinct PDF Reporting
# ─────────────────────────────────────────────────────────────────────────────

REPORT_MANIFESTS: Dict[str, Dict[str, Any]] = {
    # 1. Data Analysis Agents
    "dataset_explorer": {
        "report_type": "dataset_overview_report",
        "title": "Dataset Overview Report",
        "subtitle": "Dimensions, Column Dictionary, Inferred Types & Data Coverage",
        "domain_badge": "DATA PROFILER & EXPLORATION",
        "sections": ["executive_summary", "scorecard", "inventory", "distribution", "caveats"],
        "disclaimer": "Descriptive profiling reflects raw ingestion state. Categorical distributions reflect observed sample frequencies.",
        "chart_keywords": ["distribution", "type", "profile", "overview", "count"],
    },
    "data_cleaner": {
        "report_type": "data_audit_report",
        "title": "Data Audit & Hygiene Report",
        "subtitle": "Missing Values, Duplicate Detection, Schema Conformance & Cleaning Plan",
        "domain_badge": "DATA QUALITY & HYGIENE AUDIT",
        "sections": ["executive_summary", "scorecard", "findings", "cleaning_plan", "caveats"],
        "disclaimer": "Cleaning operations are deterministic. The original raw dataset remains unmodified.",
        "chart_keywords": ["clean", "missing", "duplicate", "null", "hygiene"],
    },
    "statistical_analysis": {
        "report_type": "statistical_summary_report",
        "title": "Statistical Summary & Distribution Report",
        "subtitle": "Descriptive Moments, Quartiles, Continuous Dispersion & Variance",
        "domain_badge": "STATISTICAL ANALYSIS",
        "sections": ["executive_summary", "scorecard", "findings", "distributions", "caveats"],
        "disclaimer": "Statistical moments computed strictly for valid numeric dimensions.",
        "chart_keywords": ["stat", "dist", "hist", "box", "dispersion", "variance"],
    },
    "trend_analysis": {
        "report_type": "trend_growth_report",
        "title": "Trend & Growth Trajectory Report",
        "subtitle": "Temporal Momentum, Period-over-Period Delta & Turning Points",
        "domain_badge": "TEMPORAL TREND INTELLIGENCE",
        "sections": ["executive_summary", "scorecard", "findings", "visuals", "caveats"],
        "disclaimer": "Historical trends evaluate past momentum and do not guarantee future continuation.",
        "chart_keywords": ["trend", "time", "series", "velocity", "momentum", "trajectory"],
    },
    "comparative_analysis": {
        "report_type": "comparative_analysis_report",
        "title": "Comparative Benchmarking Report",
        "subtitle": "Cohort Variance, Group Performance Differentials & Spread Metrics",
        "domain_badge": "COMPARATIVE ANALYSIS",
        "sections": ["executive_summary", "scorecard", "findings", "visuals", "caveats"],
        "disclaimer": "Comparisons should consider group sample sizes and baseline cohort conditions.",
        "chart_keywords": ["comparative", "benchmark", "cohort", "group", "spread"],
    },
    "insight_discovery": {
        "report_type": "autonomous_discovery_report",
        "title": "Autonomous Discovery & Root Cause Report",
        "subtitle": "Empirical Pattern Extraction, High-Leverage Levers & Cross-Dimensional Findings",
        "domain_badge": "INSIGHT DISCOVERY",
        "sections": ["executive_summary", "scorecard", "findings", "actionable_strategy", "caveats"],
        "disclaimer": "Discovered patterns represent observational associations that require business validation.",
        "chart_keywords": ["insight", "discovery", "lever", "root", "cause"],
    },

    # 2. Business Analysis Agents
    "sales_analysis": {
        "report_type": "sales_pareto_report",
        "title": "Commercial Sales & Pareto Decomposition Report",
        "subtitle": "Revenue Concentration, 80/20 Pareto Distribution, Ticket Sizes & Velocity",
        "domain_badge": "SALES INTELLIGENCE",
        "sections": ["executive_summary", "scorecard", "findings", "visuals", "actionable_strategy", "caveats"],
        "disclaimer": "Sales metrics evaluate recorded commercial transactions without presupposing external market adjustments.",
        "chart_keywords": ["sales", "revenue", "pareto", "ticket", "commercial"],
    },
    "profitability_analysis": {
        "report_type": "profitability_report",
        "title": "Profitability & Margin Contribution Report",
        "subtitle": "Gross Margin Decomposition, Unit Economics & Margin Leakage Levers",
        "domain_badge": "PROFITABILITY & UNIT ECONOMICS",
        "sections": ["executive_summary", "scorecard", "findings", "actionable_strategy", "caveats"],
        "disclaimer": "Unit profitability calculations rely upon accurate cost and revenue attribution.",
        "chart_keywords": ["profit", "margin", "cost", "unit", "economics"],
    },
    "expense_optimization": {
        "report_type": "expense_optimization_report",
        "title": "Expense Optimization & Resource Efficiency Report",
        "subtitle": "Spend Categorization, Operational Cost Leaks & Efficiency Levers",
        "domain_badge": "EXPENSE & EFFICIENCY AUDIT",
        "sections": ["executive_summary", "scorecard", "findings", "actionable_strategy", "caveats"],
        "disclaimer": "Efficiency levers must balance operational velocity against cost containment targets.",
        "chart_keywords": ["expense", "spend", "leak", "efficiency", "resource"],
    },
    "customer_intelligence": {
        "report_type": "customer_intelligence_report",
        "title": "Customer Intelligence & Retention Report",
        "subtitle": "Account Concentration, Churn Risk Propensity & High-LTV Cohorts",
        "domain_badge": "CUSTOMER INTELLIGENCE",
        "sections": ["executive_summary", "scorecard", "findings", "actionable_strategy", "caveats"],
        "disclaimer": "Retention signals reflect historical transaction patterns and customer interaction logs.",
        "chart_keywords": ["customer", "retention", "churn", "ltv", "rfm"],
    },
    "decision_support": {
        "report_type": "decision_support_report",
        "title": "Executive Decision Support & Action Plan Report",
        "subtitle": "Multi-Criteria Tradeoff Matrix, Prioritized Initiatives & Strategic Roadmap",
        "domain_badge": "DECISION SUPPORT & STRATEGY",
        "sections": ["executive_summary", "scorecard", "findings", "actionable_strategy", "caveats"],
        "disclaimer": "Decision frameworks serve as advisory decision-support aids for executive leadership.",
        "chart_keywords": ["decision", "matrix", "priority", "roadmap", "tradeoff"],
    },

    # 3. Data Mining Agents
    "pattern_discovery": {
        "report_type": "pattern_discovery_report",
        "title": "Unsupervised Pattern & Latent Clustering Report",
        "subtitle": "High-Dimensional Motif Discovery, Feature Groupings & Behavioral Signatures",
        "domain_badge": "DATA MINING & PATTERNS",
        "sections": ["executive_summary", "scorecard", "findings", "visuals", "caveats"],
        "disclaimer": "Unsupervised clustering identifies mathematical proximity and natural groupings.",
        "chart_keywords": ["pattern", "cluster", "motif", "latent", "mining"],
    },
    "relationship_analysis": {
        "report_type": "relationship_discovery_report",
        "title": "Relationship Discovery & Correlation Matrix Report",
        "subtitle": "Multivariate Dependencies, Pearson Interactions & Co-Dependency Strength",
        "domain_badge": "RELATIONSHIP DISCOVERY",
        "sections": ["executive_summary", "scorecard", "findings", "visuals", "caveats"],
        "disclaimer": "Correlation measures mathematical association, not causal directionality.",
        "chart_keywords": ["correlation", "relation", "matrix", "heatmap", "scatter"],
    },
    "segmentation": {
        "report_type": "segment_profile_report",
        "title": "Cohort & Segment Profile Report",
        "subtitle": "Multi-Dimensional Clustering, Centroid Characterization & Profile Breakdown",
        "domain_badge": "SEGMENTATION & CLUSTERING",
        "sections": ["executive_summary", "scorecard", "findings", "visuals", "actionable_strategy", "caveats"],
        "disclaimer": "Segments represent exploratory cohort clusters to guide differentiated targeting.",
        "chart_keywords": ["segment", "cluster", "cohort", "profile", "centroid"],
    },
    "anomaly_detection": {
        "report_type": "unusual_records_report",
        "title": "Unusual Records & Anomaly Audit Report",
        "subtitle": "Multivariate Outlier Isolation, IQR Dispersion & Review Queue",
        "domain_badge": "ANOMALY & OUTLIER AUDIT",
        "sections": ["executive_summary", "scorecard", "findings", "visuals", "caveats"],
        "disclaimer": "Statistical anomalies highlight atypical records and do not necessarily imply fraud or error.",
        "chart_keywords": ["anomaly", "outlier", "unusual", "isolation", "zscore"],
    },
    "association_mining": {
        "report_type": "association_mining_report",
        "title": "Market Basket & Association Mining Report",
        "subtitle": "Support, Confidence, Lift Metrics & Itemset Co-Occurrence Affinities",
        "domain_badge": "ASSOCIATION MINING",
        "sections": ["executive_summary", "scorecard", "findings", "visuals", "actionable_strategy", "caveats"],
        "disclaimer": "Association rules require adequate transaction frequency to ensure statistical validity.",
        "chart_keywords": ["association", "basket", "lift", "itemset", "affinity"],
    },

    # 4. Predictive Analysis Agents
    "sales_forecasting": {
        "report_type": "forecast_report",
        "title": "Sales Trajectory & Forecast Report",
        "subtitle": "Predictive Run-Rate Horizons, Historical Backtesting & Confidence Intervals",
        "domain_badge": "PREDICTIVE SALES FORECAST",
        "sections": ["executive_summary", "scorecard", "findings", "visuals", "caveats"],
        "disclaimer": "Forecasts are probabilistic projections with statistical confidence bands; market shocks may alter trends.",
        "chart_keywords": ["forecast", "predict", "trajectory", "horizon", "sales"],
    },
    "budget_forecasting": {
        "report_type": "budget_forecast_report",
        "title": "Budget Run-Rate & Variance Forecast Report",
        "subtitle": "Fiscal Trajectory, Burn-Rate Projections & Capital Headroom Modeling",
        "domain_badge": "BUDGET & FISCAL FORECAST",
        "sections": ["executive_summary", "scorecard", "findings", "visuals", "actionable_strategy", "caveats"],
        "disclaimer": "Budget forecasts extrapolate historical burn rates under current operational policy assumptions.",
        "chart_keywords": ["budget", "burn", "fiscal", "headroom", "variance"],
    },
    "demand_forecasting": {
        "report_type": "demand_forecast_report",
        "title": "Demand & Inventory Buffer Forecast Report",
        "subtitle": "Order Volume Trajectory, Safety Stock Buffers & Replenishment Horizons",
        "domain_badge": "DEMAND & INVENTORY PLANNING",
        "sections": ["executive_summary", "scorecard", "findings", "visuals", "actionable_strategy", "caveats"],
        "disclaimer": "Demand planning assumes steady replenishment lead times and unconstrained supplier availability.",
        "chart_keywords": ["demand", "inventory", "stock", "buffer", "replenishment"],
    },
    "risk_prediction": {
        "report_type": "risk_register_report",
        "title": "Risk Prediction & Exposure Register Report",
        "subtitle": "Multi-Factor Vulnerability Scoring, Downside VaR & Mitigation Controls",
        "domain_badge": "RISK PREDICTION & EXPOSURE",
        "sections": ["executive_summary", "scorecard", "findings", "visuals", "caveats"],
        "disclaimer": "Risk scores serve as analytical warning aids and must be accompanied by expert human review.",
        "chart_keywords": ["risk", "exposure", "var", "vulnerability", "mitigation"],
    },
    "whatif_simulation": {
        "report_type": "scenario_planning_report",
        "title": "Scenario Planning & What-If Simulation Report",
        "subtitle": "Sensitivity Frontiers, Parameter Shocks & Baseline Differential Modeling",
        "domain_badge": "WHAT-IF SCENARIO SIMULATION",
        "sections": ["executive_summary", "scorecard", "findings", "actionable_strategy", "caveats"],
        "disclaimer": "Simulations compute outcomes under specified parameter assumptions rather than deterministic forecasts.",
        "chart_keywords": ["simulation", "whatif", "scenario", "sensitivity", "shock"],
    },

    # 5. Exploratory Data Analysis Agents
    "natural_query": {
        "report_type": "natural_query_report",
        "title": "Natural-Language Query & Ad-Hoc Investigation Report",
        "subtitle": "Question-Driven Data Extraction, Verified Answers & Schema Insights",
        "domain_badge": "AD-HOC QUERY INVESTIGATION",
        "sections": ["executive_summary", "scorecard", "findings", "caveats"],
        "disclaimer": "Responses are generated from deterministic queries executed directly against dataset columns.",
        "chart_keywords": ["query", "adhoc", "question", "sql", "answer"],
    },
    "visualization": {
        "report_type": "visual_analytics_report",
        "title": "Visual Analytics & Chart Gallery Report",
        "subtitle": "High-Resolution Statistical Graphics, Multi-Metric Plots & Visual Mappings",
        "domain_badge": "VISUAL ANALYTICS GALLERY",
        "sections": ["executive_summary", "scorecard", "visuals", "findings", "caveats"],
        "disclaimer": "Visual scales and axis bounds are derived directly from verified data limits.",
        "chart_keywords": ["plot", "chart", "scatter", "bar", "heatmap", "gallery"],
    },
    "quality_inspector": {
        "report_type": "quality_scorecard_report",
        "title": "Data Quality Scorecard & Schema Integrity Report",
        "subtitle": "Completeness, Uniqueness, Validity, Consistency & Schema Health Metrics",
        "domain_badge": "DATA QUALITY SCORECARD",
        "sections": ["executive_summary", "scorecard", "findings", "actionable_strategy", "caveats"],
        "disclaimer": "Quality indices evaluate structural compliance and completeness of ingested records.",
        "chart_keywords": ["quality", "scorecard", "health", "completeness", "schema"],
    },
    "storytelling": {
        "report_type": "executive_story_report",
        "title": "Executive Data Story & Narrative Synthesis Report",
        "subtitle": "End-to-End Commercial Storyboard, Turning Points & Strategic Synthesis",
        "domain_badge": "EXECUTIVE DATA STORY",
        "sections": ["executive_summary", "scorecard", "findings", "actionable_strategy", "caveats"],
        "disclaimer": "Executive storyboard synthesizes empirical findings across active intelligence agents.",
        "chart_keywords": ["story", "narrative", "arc", "turning", "executive"],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Flowable Builders for Distinct PDF Reports
# ─────────────────────────────────────────────────────────────────────────────

def _build_distinct_cover(manifest: dict, agent_data: dict, dataset_meta: dict, df: Optional[pd.DataFrame] = None) -> list:
    """Build a cinematic, capability-specific cover page."""
    flowables = []
    agent_name = agent_data.get("name") or agent_data.get("agent_id") or "Specialist Agent"
    exec_time = agent_data.get("execution_time", 0.0)
    timestamp = datetime.now().strftime("%B %d, %Y  ·  %I:%M %p")

    flowables.append(Spacer(1, 45))

    # Domain Badge Pill
    badge_text = manifest.get("domain_badge", "CREWLYZE INTELLIGENCE REPORT")
    flowables.append(Paragraph(
        f"<b>CREWLYZE &nbsp;·&nbsp; {badge_text}</b>",
        ParagraphStyle("DistCoverBadge", fontName="Helvetica-Bold", fontSize=9,
                       leading=12, textColor=C_CRIMSON_DARK, alignment=1)
    ))
    flowables.append(Spacer(1, 20))

    # Distinct Report Title
    title_text = manifest.get("title", agent_name)
    flowables.append(Paragraph(
        f"<b>{_escape(title_text.upper())}</b>",
        ParagraphStyle("DistCoverTitle", fontName="Helvetica-Bold", fontSize=22,
                       leading=28, textColor=C_CRIMSON_DARK, spaceAfter=14, alignment=1)
    ))
    flowables.append(HRFlowable(width="60%", thickness=1.5, color=C_CRIMSON, spaceBefore=4, spaceAfter=16, hAlign='CENTER'))

    # Subtitle
    subtitle_text = manifest.get("subtitle", "")
    flowables.append(Paragraph(
        f"{_escape(subtitle_text)}<br/>"
        f"<font color='#64748b' size=9>Generated on {timestamp}</font>",
        ParagraphStyle("DistCoverSub", fontName="Helvetica", fontSize=10.5,
                       leading=16, textColor=C_INK, alignment=1)
    ))
    flowables.append(Spacer(1, 45))

    # Telemetry and Execution Metadata Card
    ds_name = dataset_meta.get("filename") or dataset_meta.get("name") or "dataset.csv"
    rows_str = str(df.shape[0]) if (df is not None and isinstance(df, pd.DataFrame)) else str(dataset_meta.get("rows_count", "--"))
    cols_str = str(df.shape[1]) if (df is not None and isinstance(df, pd.DataFrame)) else str(dataset_meta.get("cols_count", "--"))

    meta_table_data = [
        [
            Paragraph("<b>DATASET</b>", ParagraphStyle("MKey1", fontName="Helvetica-Bold", fontSize=8, textColor=C_MUTED, leading=10)),
            Paragraph(f"<b>{_escape(ds_name)}</b>", ParagraphStyle("MVal1", fontName="Helvetica", fontSize=8.5, textColor=C_INK, leading=12)),
            Paragraph("<b>EXECUTION STATUS</b>", ParagraphStyle("MKey2", fontName="Helvetica-Bold", fontSize=8, textColor=C_MUTED, leading=10)),
            Paragraph(f"<b>{str(agent_data.get('status', 'completed')).upper()}</b>", ParagraphStyle("MVal2", fontName="Helvetica-Bold", fontSize=8.5, textColor=C_EMERALD if agent_data.get('status') == 'completed' else C_AMBER, leading=12)),
        ],
        [
            Paragraph("<b>RECORDS / COLS</b>", ParagraphStyle("MKey3", fontName="Helvetica-Bold", fontSize=8, textColor=C_MUTED, leading=10)),
            Paragraph(f"{rows_str} rows × {cols_str} cols", ParagraphStyle("MVal3", fontName="Helvetica", fontSize=8.5, textColor=C_INK, leading=12)),
            Paragraph("<b>RUN TIME</b>", ParagraphStyle("MKey4", fontName="Helvetica-Bold", fontSize=8, textColor=C_MUTED, leading=10)),
            Paragraph(f"{float(exec_time):.2f} seconds", ParagraphStyle("MVal4", fontName="Helvetica", fontSize=8.5, textColor=C_INK, leading=12)),
        ]
    ]
    meta_tbl = Table(meta_table_data, colWidths=[110, 142, 110, 142])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_CRIMSON_PALE),
        ("BOX", (0, 0), (-1, -1), 1, C_CRIMSON),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    flowables.append(meta_tbl)
    flowables.append(Spacer(1, 30))
    flowables.append(PageBreak())
    return flowables


def _build_kpi_cards_table(metrics: dict) -> Optional[Table]:
    """Render up to 6 quantitative metrics into an alternating KPI cards grid."""
    if not metrics or not isinstance(metrics, dict):
        return None
    items = list(metrics.items())[:6]
    if not items:
        return None

    cols = 3 if len(items) >= 3 else len(items)
    col_w = int(504 / cols)
    col_widths = [col_w] * cols

    rows = []
    curr_cells = []

    hdr_s = ParagraphStyle("KpiH", fontName="Helvetica-Bold", fontSize=7.5, textColor=C_MUTED, alignment=1, leading=10)
    val_s = ParagraphStyle("KpiV", fontName="Helvetica-Bold", fontSize=12, textColor=C_CRIMSON_DARK, alignment=1, leading=15)

    for k, v in items:
        k_clean = str(k).replace("_", " ").upper()
        if isinstance(v, float):
            v_clean = f"{v:,.2f}".rstrip("0").rstrip(".")
        elif isinstance(v, int):
            v_clean = f"{v:,}"
        else:
            v_clean = str(v)[:26]

        cell = [
            Paragraph(k_clean, hdr_s),
            Spacer(1, 3),
            Paragraph(f"<b>{_escape(v_clean)}</b>", val_s)
        ]
        curr_cells.append(cell)
        if len(curr_cells) == cols:
            rows.append(curr_cells)
            curr_cells = []

    if curr_cells:
        while len(curr_cells) < cols:
            curr_cells.append([Paragraph("", hdr_s)])
        rows.append(curr_cells)

    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_ROW_ALT),
        ("BOX", (0, 0), (-1, -1), 0.75, C_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, C_LIGHT_GRID),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    return t


def _build_findings_list(findings: list, body_style, bullet_style) -> list:
    """Format agent findings with clear panels or structured bullet points."""
    flowables = []
    if not findings:
        return flowables

    card_hdr = ParagraphStyle("CardHdr", fontName="Helvetica-Bold", fontSize=8, textColor=C_SAPPHIRE, leading=11)
    card_bdy = ParagraphStyle("CardBdy", fontName="Helvetica", fontSize=8, textColor=C_INK, leading=12)

    for idx, f in enumerate(findings, start=1):
        if not f:
            continue
        f_clean = _clean_ai_artifacts(str(f))

        if "**Observation**" in f_clean or "Observation:" in f_clean:
            parsed = _parse_insight_fields(f_clean)
            c_data = [
                [Paragraph("<b>OBSERVATION</b>", card_hdr), Paragraph("<b>STRATEGIC IMPLICATION</b>", ParagraphStyle("CImpT", fontName="Helvetica-Bold", fontSize=8, textColor=C_EMERALD, leading=11))],
                [Paragraph(_md_to_html(parsed["observation"]), card_bdy), Paragraph(_md_to_html(parsed["implication"] or parsed["strategy"] or "—"), card_bdy)]
            ]
            t = Table(c_data, colWidths=[246, 258])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), C_SAPPHIRE_PALE),
                ("BACKGROUND", (1, 0), (1, 0), C_EMERALD_PALE),
                ("BACKGROUND", (0, 1), (-1, 1), C_WHITE),
                ("BOX", (0, 0), (-1, -1), 0.75, C_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, C_LIGHT_GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]))
            flowables.append(KeepTogether([t, Spacer(1, 6)]))
        else:
            flowables.append(Paragraph(f"▸  {_md_to_html(f_clean)}", bullet_style))
            flowables.append(Spacer(1, 3))

    flowables.append(Spacer(1, 6))
    return flowables


def _build_agent_visuals(visuals: list, png_files: list, agent_id: str, manifest: dict, placed_charts: set) -> list:
    """Embed matched charts and visuals for the specific capability."""
    flowables = []
    keywords = manifest.get("chart_keywords", [agent_id])

    for v in (visuals or []):
        if isinstance(v, dict):
            chart_path = v.get("path") or v.get("chart_path") or v.get("url")
            if chart_path and Path(chart_path).exists() and Path(chart_path) not in placed_charts:
                img_tbl, fig_cap = _img_flowable(Path(chart_path))
                if img_tbl:
                    flowables.append(KeepTogether([img_tbl, fig_cap, Spacer(1, 8)]))
                    placed_charts.add(Path(chart_path))

    for png in (png_files or []):
        if png in placed_charts:
            continue
        p_name = png.stem.lower()
        if any(kw in p_name for kw in keywords):
            img_tbl, fig_cap = _img_flowable(png)
            if img_tbl:
                flowables.append(KeepTogether([img_tbl, fig_cap, Spacer(1, 8)]))
                placed_charts.add(png)
                if len(flowables) >= 3:
                    break
    return flowables


def _build_limitations_and_recommendations(limitations: list, recommendations: list, disclaimer: str) -> list:
    """Render analytical limitations in an alert box and recommendations in a strategy box."""
    flowables = []
    all_limits = []
    if disclaimer:
        all_limits.append(disclaimer)
    if limitations:
        all_limits.extend([str(l) for l in limitations if l])

    if all_limits:
        warn_content = [
            Paragraph("<b>Analytical Guardrails &amp; Methodological Caveats</b>",
                      ParagraphStyle("LimH", fontName="Helvetica-Bold", fontSize=8.5, textColor=colors.HexColor("#7f1d1d"), leading=11, spaceAfter=3)),
        ]
        for lim in all_limits:
            warn_content.append(Paragraph(f"▸  {_md_to_html(lim)}",
                                         ParagraphStyle("LimB", fontName="Helvetica", fontSize=8, textColor=colors.HexColor("#7f1d1d"), leading=11.5)))
        lim_tbl = Table([[warn_content]], colWidths=[504])
        lim_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_CRIMSON_PALE),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#fecaca")),
            ("LINELEFT", (0, 0), (0, -1), 4, C_CRIMSON),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        flowables.append(KeepTogether([lim_tbl, Spacer(1, 10)]))

    if recommendations:
        rec_content = [
            Paragraph("<b>Recommended Next Steps &amp; Action Plan</b>",
                      ParagraphStyle("RecH", fontName="Helvetica-Bold", fontSize=8.5, textColor=C_EMERALD, leading=11, spaceAfter=3)),
        ]
        for rec in recommendations:
            rec_content.append(Paragraph(f"✓  {_md_to_html(str(rec))}",
                                         ParagraphStyle("RecB", fontName="Helvetica", fontSize=8, textColor=C_INK, leading=11.5)))
        rec_tbl = Table([[rec_content]], colWidths=[504])
        rec_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_EMERALD_PALE),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#a7f3d0")),
            ("LINELEFT", (0, 0), (0, -1), 4, C_EMERALD),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        flowables.append(KeepTogether([rec_tbl, Spacer(1, 10)]))

    return flowables


def export_distinct_agent_pdf(
    agent_data: dict,
    dataset_meta: dict,
    output_dir: Union[Path, str] = "outputs",
    df: Optional[pd.DataFrame] = None
) -> bytes:
    """Build and return a dedicated, capability-specific ReportLab PDF report."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54, leftMargin=54,
        topMargin=82, bottomMargin=82,
    )

    out_dir = Path(output_dir) if isinstance(output_dir, (str, Path)) else Path("outputs")
    png_files = list(out_dir.glob("*.png")) if out_dir.exists() else []
    placed_charts = set()

    agent_id = agent_data.get("agent_id", "data_analysis")
    manifest = REPORT_MANIFESTS.get(agent_id, {
        "report_type": f"{agent_id}_report",
        "title": agent_data.get("name", "Specialist Analysis Report"),
        "subtitle": "Autonomous Agentic Intelligence Analysis",
        "domain_badge": str(agent_data.get("category", "CREWLYZE INTELLIGENCE")).upper(),
        "sections": ["executive_summary", "scorecard", "findings", "visuals", "caveats"],
        "disclaimer": "Analysis performed autonomously based on verified dataset dimensions.",
        "chart_keywords": [agent_id],
    })

    body_style = ParagraphStyle("DistBody", fontName="Helvetica", fontSize=9,
                                leading=14, textColor=C_INK, spaceAfter=5)
    bullet_style = ParagraphStyle("DistBullet", fontName="Helvetica", fontSize=8.5,
                                  leading=13, textColor=C_INK,
                                  leftIndent=12, firstLineIndent=-8, spaceAfter=4)

    story = []

    # 1. Distinct Cover Page
    story.extend(_build_distinct_cover(manifest, agent_data, dataset_meta, df=df))

    # 2. Executive Summary & Narrative
    story.append(KeepTogether([
        _section_header("01", "Executive Summary & Scope", body_style),
        Spacer(1, 10)
    ]))

    narrative = agent_data.get("narrative") or ""
    if not narrative:
        narrative = f"This report delivers tailored empirical findings and verified metrics from the <b>{_escape(agent_data.get('name', agent_id))}</b> capability, analyzing commercial dependencies and operational performance."
    story.append(Paragraph(_md_to_html(narrative), body_style))
    story.append(Spacer(1, 12))

    # 3. Quantitative KPI Scorecard
    metrics = agent_data.get("metrics", {})
    kpi_tbl = _build_kpi_cards_table(metrics)
    if kpi_tbl:
        story.append(KeepTogether([
            _section_header("02", "Quantitative KPI Scorecard", body_style),
            Spacer(1, 10),
            kpi_tbl,
            Spacer(1, 14)
        ]))

    # 4. Verified Findings & Evidence
    findings = agent_data.get("findings", [])
    if findings:
        sec_num = "03" if kpi_tbl else "02"
        story.append(KeepTogether([
            _section_header(sec_num, "Empirical Findings & Evidence", body_style),
            Spacer(1, 10)
        ]))
        story.extend(_build_findings_list(findings, body_style, bullet_style))
        story.append(Spacer(1, 10))

    # 5. Visualizations & Chart Embed
    visuals = _build_agent_visuals(agent_data.get("visuals", []), png_files, agent_id, manifest, placed_charts)
    if visuals:
        story.append(KeepTogether([
            _section_header("04", "Analytical Visualizations", body_style),
            Spacer(1, 10)
        ]))
        story.extend(visuals)
        story.append(Spacer(1, 10))

    # 6. Data Tables / Appendices (for profiler / stats)
    if df is not None and isinstance(df, pd.DataFrame) and agent_id in ("dataset_explorer", "statistical_analysis", "data_cleaner"):
        story.append(KeepTogether([
            _section_header("05", "Column Metrics Breakdown", body_style),
            Spacer(1, 8)
        ]))
        stats_tables = _build_stats_tables(df, body_style)
        if stats_tables:
            story.extend(stats_tables[:2])
        story.append(Spacer(1, 10))

    # 7. Limitations, Caveats & Actionable Next Steps
    limitations = agent_data.get("limitations", [])
    recommendations = agent_data.get("recommendations", [])
    disclaimer = manifest.get("disclaimer", "")
    lim_recs = _build_limitations_and_recommendations(limitations, recommendations, disclaimer)
    if lim_recs:
        story.append(KeepTogether([
            _section_header("06", "Strategic Implications & Guardrails", body_style),
            Spacer(1, 10)
        ]))
        story.extend(lim_recs)

    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# ─────────────────────────────────────────────────────────────────────────────
# Main Executive PDF generator
# ─────────────────────────────────────────────────────────────────────────────

def export_pdf(result: dict, filename: str = "", analysis_id: Optional[str] = None) -> bytes:
    """Build and return a premium world-class executive PDF report.
    Dispatches to export_distinct_agent_pdf when analysis_id is provided.
    """
    df = result.get("dataframe")
    output_dir = result.get("output_dir", Path("outputs"))

    # Check if a specific distinct report was requested
    if analysis_id and str(analysis_id).lower() not in ("consolidated", "all", "none"):
        aid = str(analysis_id).strip().lower()
        target_agent = None

        if result.get("agent_id") == aid:
            target_agent = result
        else:
            categories_data = result.get("categories", {})
            for cat_id, agent_list in categories_data.items():
                if isinstance(agent_list, list):
                    for a in agent_list:
                        if isinstance(a, dict) and a.get("agent_id") == aid:
                            target_agent = a
                            break
                elif isinstance(agent_list, dict) and agent_list.get("agent_id") == aid:
                    target_agent = agent_list
                    break
                if target_agent:
                    break

            if not target_agent and aid in categories_data:
                cat_agents = categories_data[aid]
                if isinstance(cat_agents, list) and cat_agents:
                    completed_agents = [a for a in cat_agents if isinstance(a, dict) and a.get("status") == "completed"]
                    target_agent = completed_agents[0] if completed_agents else cat_agents[0]

        if target_agent:
            dataset_meta = {
                "name": result.get("report_title") or filename or "dataset.csv",
                "filename": filename or result.get("report_title") or "dataset.csv",
                "goal": result.get("goal", ""),
                "rows_count": df.shape[0] if (df is not None and isinstance(df, pd.DataFrame)) else result.get("rows_count"),
                "cols_count": df.shape[1] if (df is not None and isinstance(df, pd.DataFrame)) else result.get("cols_count"),
            }
            return export_distinct_agent_pdf(target_agent, dataset_meta, output_dir=output_dir, df=df)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54, leftMargin=54,
        topMargin=82, bottomMargin=82,
    )

    story  = []
    styles = getSampleStyleSheet()

    # Shared paragraph styles
    body_style = ParagraphStyle("Body", fontName="Helvetica", fontSize=9.5,
                                leading=14.5, textColor=C_INK, spaceAfter=5)
    small_style = ParagraphStyle("Small", fontName="Helvetica", fontSize=8.5,
                                 leading=13, textColor=C_MUTED)
    h2_style = ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=10.5,
                               leading=14, textColor=C_CRIMSON_DARK,
                               spaceBefore=10, spaceAfter=4, keepWithNext=True)
    bullet_style = ParagraphStyle("Bullet", fontName="Helvetica", fontSize=9.5,
                                  leading=14.5, textColor=C_INK,
                                  leftIndent=14, firstLineIndent=-10, spaceAfter=5)
    label_style = ParagraphStyle("MetaKey", fontName="Helvetica-Bold", fontSize=8,
                                 textColor=C_MUTED, leading=11)
    value_style = ParagraphStyle("MetaVal", fontName="Helvetica", fontSize=9,
                                 textColor=C_INK, leading=13)

    # ── Pull result data ──────────────────────────────────────────────────────
    raw_insights    = _clean_ai_artifacts(result.get("insights", "")).strip()
    cleaning_text   = _clean_ai_artifacts(result.get("cleaning_steps", "")).strip()
    relations_text  = _clean_ai_artifacts(result.get("relations", "")).strip()
    predictive_text     = _clean_ai_artifacts(result.get("predictive", "")).strip()
    anomaly_text        = _clean_ai_artifacts(result.get("anomaly", "")).strip()
    trend_text          = _clean_ai_artifacts(result.get("trend", "")).strip()
    executive_narrative = _clean_ai_artifacts(result.get("executive_narrative", "")).strip()
    categories_data     = result.get("categories", {})
    executive_findings  = result.get("executive_findings", [])
    report_title        = _clean_ai_artifacts(result.get("report_title") or result.get("name") or filename or "Executive Analysis").strip()
    report_goal         = _clean_ai_artifacts(result.get("goal", "")).strip()
    timestamp           = datetime.now().strftime("%B %d, %Y  ·  %I:%M %p")
    df                  = result.get("dataframe")
    output_dir          = result.get("output_dir", Path("outputs"))
    png_files           = list(Path(output_dir).glob("*.png"))
    placed_charts       = set()

    # ── Parse insight subsections ─────────────────────────────────────────────
    objectives_text = stats_text = strategic_text = warnings_text = ""
    if raw_insights:
        for sec in re.split(r"###\s+", raw_insights):
            lines = sec.split("\n")
            if not lines or not lines[0].strip():
                continue
            hdr     = lines[0].strip().lower()
            content = "\n".join(lines[1:]).strip()
            if   "objective" in hdr or "goal" in hdr: objectives_text = content
            elif "stat"      in hdr:                   stats_text      = content
            elif "insight"   in hdr:                   strategic_text  = content
            elif "warning"   in hdr or "alert" in hdr: warnings_text   = content
        if not strategic_text and not objectives_text:
            strategic_text = raw_insights

    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE 1 — COVER
    # ═══════════════════════════════════════════════════════════════════════════

    # Top Header Pill / Brand Tag
    story.append(Spacer(1, 50))
    story.append(Paragraph(
        "CREWLYZE EXECUTIVE GROWTH INTELLIGENCE",
        ParagraphStyle("CoverBadge", fontName="Helvetica-Bold", fontSize=9,
                       leading=12, textColor=C_CRIMSON_DARK, alignment=1)
    ))
    story.append(Spacer(1, 25))

    # Title (dynamic, generated by LLM)
    story.append(Paragraph(
        f"<b>{_escape(report_title.upper())}</b>",
        ParagraphStyle("CoverTitle", fontName="Helvetica-Bold", fontSize=26,
                       leading=34, textColor=C_CRIMSON_DARK, spaceAfter=15, alignment=1)
    ))
    story.append(Spacer(1, 10))

    story.append(HRFlowable(width="60%", thickness=1.5, color=C_CRIMSON, spaceBefore=10, spaceAfter=20, hAlign='CENTER'))

    # Subtitle / Generation timestamp (dynamic)
    story.append(Paragraph(
        f"Autonomous Agentic Business Intelligence &amp; Growth Strategy Report<br/>"
        f"<font color='#64748b' size=9.5>Generated on {timestamp}</font>",
        ParagraphStyle("CoverDate", fontName="Helvetica", fontSize=11,
                       leading=18, textColor=C_INK, alignment=1)
    ))

    story.append(Spacer(1, 60))

    # Dataset Summary Card on Cover Page
    if df is not None and isinstance(df, pd.DataFrame):
        cover_meta_data = [
            [Paragraph("<b>TOTAL RECORDS</b>", label_style), Paragraph(f"<b>{df.shape[0]:,}</b>", value_style),
             Paragraph("<b>TOTAL COLUMNS</b>", label_style), Paragraph(f"<b>{df.shape[1]}</b>", value_style)],
            [Paragraph("<b>NUMERIC COLS</b>", label_style), Paragraph(f"<b>{len(df.select_dtypes(include=['number']).columns)}</b>", value_style),
             Paragraph("<b>CATEGORICAL COLS</b>", label_style), Paragraph(f"<b>{len(df.select_dtypes(include=['object', 'category']).columns)}</b>", value_style)]
        ]
        t_cover = Table(cover_meta_data, colWidths=[110, 110, 110, 110])
        t_cover.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_CRIMSON_PALE),
            ("BOX", (0, 0), (-1, -1), 1, C_CRIMSON),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, C_BORDER),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(t_cover)

    story.append(Spacer(1, 40))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE 2 — EXECUTIVE SUMMARY & DATASET OVERVIEW
    # ═══════════════════════════════════════════════════════════════════════════

    story.append(KeepTogether([
        _section_header("01", "Executive Summary & Commercial KPI Overview", body_style),
        Spacer(1, 12)
    ]))

    story.append(Paragraph(
        "This report delivers high-impact growth levers, revenue drivers, commercial opportunity mappings, "
        "and chart-backed executive intelligence generated autonomously from the active business dataset.",
        body_style
    ))
    story.append(Spacer(1, 10))

    if df is not None and isinstance(df, pd.DataFrame):
        ncol = len(df.select_dtypes(include=["number"]).columns)
        ccol = len(df.select_dtypes(include=["object", "category"]).columns)
        cols_preview = ", ".join(str(c) for c in df.columns[:7])
        if len(df.columns) > 7:
            cols_preview += "  …"

        kv_rows = [
            [Paragraph("<b>Total Records</b>",    label_style), Paragraph(f"<b>{df.shape[0]:,}</b>", value_style),
             Paragraph("<b>Total Columns</b>",    label_style), Paragraph(f"<b>{df.shape[1]}</b>",   value_style)],
            [Paragraph("<b>Numeric Columns</b>",  label_style), Paragraph(f"<b>{ncol}</b>",           value_style),
             Paragraph("<b>Categorical Cols</b>", label_style), Paragraph(f"<b>{ccol}</b>",           value_style)],
            [Paragraph("<b>Column Preview</b>",   label_style), Paragraph(_escape(cols_preview),      value_style),
             Paragraph("", label_style), Paragraph("", value_style)],
        ]
        kv_tbl = Table(kv_rows, colWidths=[100, 152, 100, 152])
        kv_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), C_ROW_ALT),
            ("BOX",           (0, 0), (-1, -1), 1, C_BORDER),
            ("LINEBELOW",     (0, 0), (-1, 0),  1.5, C_CRIMSON),
            ("INNERGRID",     (0, 0), (-1, -1), 0.25, C_LIGHT_GRID),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(kv_tbl)
        story.append(Spacer(1, 14))

    # Executive Strategic Narrative (from 25-Agent System)
    if executive_narrative:
        narrative_p = Paragraph(
            f"<b>Strategic Intelligence Narrative:</b><br/>{_md_to_html(executive_narrative)}",
            ParagraphStyle("ExecNarrative", fontName="Helvetica", fontSize=9.5, leading=15, textColor=C_INK)
        )
        narrative_box = Table([[narrative_p]], colWidths=[504])
        narrative_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("LINELEFT", (0, 0), (0, -1), 4, colors.HexColor("#8b5cf6")),
            ("PADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(KeepTogether([narrative_box, Spacer(1, 16)]))

    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE 3+ — STRATEGIC BUSINESS INSIGHTS
    # ═══════════════════════════════════════════════════════════════════════════

    if strategic_text:
        story.append(KeepTogether([
            _section_header("02", "Strategic Business Intelligence & Growth Levers", body_style),
            Spacer(1, 12)
        ]))
        story.append(Paragraph(
            "Each strategic growth card below evaluates commercial performance across three dimensions: "
            "the data <b>Observation</b>, the commercial <b>Business Implication</b>, and a decision-ready <b>Actionable Strategy</b>.",
            body_style
        ))
        story.append(Spacer(1, 10))

        hdr_obs   = ParagraphStyle("HObs",   fontName="Helvetica-Bold", fontSize=8.5, textColor=C_SAPPHIRE, leading=12)
        hdr_imp   = ParagraphStyle("HImp",   fontName="Helvetica-Bold", fontSize=8.5, textColor=colors.HexColor("#6d28d9"), leading=12)
        hdr_strat = ParagraphStyle("HStrat", fontName="Helvetica-Bold", fontSize=8.5, textColor=C_EMERALD,  leading=12)
        cell_obs   = ParagraphStyle("CObs",  fontName="Helvetica", fontSize=8.5, textColor=C_INK, leading=13)
        cell_imp   = ParagraphStyle("CImp",  fontName="Helvetica", fontSize=8.5, textColor=C_INK, leading=13)
        cell_strat = ParagraphStyle("CStrt", fontName="Helvetica", fontSize=8.5, textColor=C_INK, leading=13)

        insight_items = re.split(r"\d+\.\s+", strategic_text)
        insight_count = 0

        for raw_item in insight_items:
            item = raw_item.strip()
            if not item:
                continue
            insight_count += 1
            fields = _parse_insight_fields(item)

            # Extract title from first bold token
            title = ""
            first = item.split("\n")[0].strip()
            if first and not any(k in first for k in ("Observation", "Implication", "Strategy")):
                title = first.replace("**", "").replace("<b>", "").replace("</b>", "").strip()

            # ── Insight label ──────────────────────────────────────────────
            lbl_text = f"<b>#{insight_count}  {_escape(title)}</b>" if title else f"<b>Insight #{insight_count}</b>"
            lbl = Paragraph(
                lbl_text,
                ParagraphStyle("InsLbl", fontName="Helvetica-Bold", fontSize=10.5,
                               textColor=C_CRIMSON_DARK, spaceBefore=12,
                               spaceAfter=5, keepWithNext=True)
            )

            # ── Three-panel card ───────────────────────────────────────────
            card_data = [
                [
                    Paragraph("<b>📊  Observation</b>",        hdr_obs),
                    Paragraph("<b>💡  Business Implication</b>", hdr_imp),
                    Paragraph("<b>🎯  Actionable Strategy</b>",  hdr_strat),
                ],
                [
                    Paragraph(_md_to_html(fields["observation"]),              cell_obs),
                    Paragraph(_md_to_html(fields["implication"] or "—"),       cell_imp),
                    Paragraph(_md_to_html(fields["strategy"]    or "—"),       cell_strat),
                ],
            ]
            card = Table(card_data, colWidths=[160, 172, 172])
            card.setStyle(TableStyle([
                # Header row backgrounds
                ("BACKGROUND",    (0, 0), (0, 0), C_SAPPHIRE_PALE),
                ("BACKGROUND",    (1, 0), (1, 0), colors.HexColor("#f5f3ff")),
                ("BACKGROUND",    (2, 0), (2, 0), C_EMERALD_PALE),
                # Data row backgrounds
                ("BACKGROUND",    (0, 1), (0, 1), colors.HexColor("#f0f8ff")),
                ("BACKGROUND",    (1, 1), (1, 1), colors.HexColor("#fdfaff")),
                ("BACKGROUND",    (2, 1), (2, 1), colors.HexColor("#f0fff8")),
                # Borders
                ("BOX",           (0, 0), (-1, -1), 0.75, C_BORDER),
                ("INNERGRID",     (0, 0), (-1, -1), 0.4,  C_LIGHT_GRID),
                ("LINEBELOW",     (0, 0), (-1, 0),  1.2,  C_BORDER),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING",    (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING",   (0, 0), (-1, -1), 9),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 9),
            ]))

            story.append(KeepTogether([lbl, card]))

            # ── Paired chart ───────────────────────────────────────────────
            matched = _find_matching_chart(item, png_files, placed_charts)
            if matched:
                img_tbl, fig_cap = _img_flowable(matched)
                if img_tbl:
                    story.append(Spacer(1, 5))
                    story.append(KeepTogether([img_tbl, fig_cap]))
                    placed_charts.add(matched)
            story.append(Spacer(1, 14))

        story.append(Spacer(1, 8))

    # ── Risk alerts ────────────────────────────────────────────────────────────
    if warnings_text and "no warnings" not in warnings_text.lower() and "none" not in warnings_text.lower():
        story.append(KeepTogether([
            _section_header("03", "Business Risks & Critical Alerts", body_style),
            Spacer(1, 10)
        ]))
        warn_content = [Paragraph(
            _md_to_html(warnings_text).replace("\n", "<br/>"),
            ParagraphStyle("WarnBody", fontName="Helvetica", fontSize=9.5,
                           textColor=colors.HexColor("#7f1d1d"), leading=14)
        )]
        warn_tbl = Table([warn_content], colWidths=[504])
        warn_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), C_CRIMSON_PALE),
            ("LINELEFT",      (0, 0), (0, -1),  5, C_CRIMSON),
            ("BOX",           (0, 0), (-1, -1), 0.75, colors.HexColor("#fecaca")),
            ("LEFTPADDING",   (0, 0), (-1, -1), 14),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(KeepTogether([warn_tbl, Spacer(1, 14)]))
        story.append(Spacer(1, 8))

    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE 4+ — DATA SUMMARY & METHODOLOGY
    # ═══════════════════════════════════════════════════════════════════════════

    sec_num = "04" if (strategic_text or warnings_text) else "03"
    story.append(KeepTogether([
        _section_header(sec_num, "Opportunity Drivers & Methodology", body_style),
        Spacer(1, 12)
    ]))

    if objectives_text:
        story.append(Paragraph("Strategic Growth Objectives &amp; Scope", h2_style))
        story.append(Paragraph(
            _md_to_html(objectives_text).replace("\n", "<br/>"), body_style
        ))
        story.append(Spacer(1, 10))

    if cleaning_text:
        story.append(Paragraph("Dataset Integrity &amp; Ingestion Profile", h2_style))
        story.append(Paragraph(
            "Commercial dataset verification and baseline integrity audit:", body_style
        ))
        for raw in cleaning_text.split("\n"):
            line = raw.strip().lstrip("-*• ").strip()
            if line:
                story.append(Paragraph(f"▸  {_md_to_html(line)}", bullet_style))
        story.append(Spacer(1, 10))

    if relations_text:
        story.append(Paragraph("Key Growth Drivers &amp; Commercial Relationship Map", h2_style))

        hdr_style_tbl = ParagraphStyle("RelHdr", fontName="Helvetica-Bold", fontSize=8.5,
                                       textColor=C_WHITE, leading=11)
        cell_r = ParagraphStyle("RelCell", fontName="Helvetica", fontSize=8.5,
                                textColor=C_INK, leading=12)

        desc_lines = []
        tbl_data = [[
            Paragraph("<b>Variable X</b>",             hdr_style_tbl),
            Paragraph("<b>Variable Y</b>",             hdr_style_tbl),
            Paragraph("<b>Chart Type</b>",             hdr_style_tbl),
            Paragraph("<b>Business Context</b>",       hdr_style_tbl),
        ]]

        for raw in relations_text.split("\n"):
            line = raw.strip().lstrip("-*• ").strip()
            if not line:
                continue
            if "|" in line or ("x:" in line.lower() and "y:" in line.lower()):
                parsed = _parse_relation_line(line)
                if parsed["x"] != "N/A" or parsed["y"] != "N/A":
                    # Filter out placeholders or templates
                    if "[" in parsed["x"] or "]" in parsed["x"] or "Column" in parsed["x"] or "Column" in parsed["y"]:
                        continue
                    tbl_data.append([
                        Paragraph(f"<b>{_escape(parsed['x'])}</b>", cell_r),
                        Paragraph(f"<b>{_escape(parsed['y'])}</b>", cell_r),
                        Paragraph(_escape(parsed["type"]),           cell_r),
                        Paragraph(_escape(parsed["details"]),        cell_r),
                    ])
                    continue
            if not any(line.lower().startswith(k) for k in ("strictly", "output nothing")):
                desc_lines.append(line)

        if desc_lines:
            story.append(Paragraph(
                "<br/>".join(_md_to_html(l) for l in desc_lines), body_style
            ))
            story.append(Spacer(1, 6))
        else:
            story.append(Paragraph(
                "The following variable pairs were identified for targeted visualization:", body_style
            ))
            story.append(Spacer(1, 4))

        if len(tbl_data) > 1:
            rel_tbl = Table(tbl_data, colWidths=[100, 100, 90, 214])
            rel_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0),  C_CRIMSON_DARK),
                ("BOX",           (0, 0), (-1, -1), 0.75, C_BORDER),
                ("INNERGRID",     (0, 0), (-1, -1), 0.3,  C_LIGHT_GRID),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_ROW_ALT]),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING",    (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ]))
            story.append(KeepTogether([rel_tbl]))
            
        # Search for and render correlation mapping chart/heatmap directly inside Section 4
        corr_chart = None
        for png in png_files:
            p_name = png.name.lower()
            if "correlation" in p_name or "relation" in p_name or "matrix" in p_name:
                corr_chart = png
                break
        
        if corr_chart:
            img_tbl, fig_cap = _img_flowable(corr_chart)
            if img_tbl:
                story.append(Spacer(1, 10))
                story.append(KeepTogether([img_tbl, fig_cap]))
                placed_charts.add(corr_chart)
                
        story.append(Spacer(1, 14))

    # ═══════════════════════════════════════════════════════════════════════════
    # SPECIALIZED ANALYSES — PREDICTIVE ML, RISK AUDIT & TREND FORECAST
    # ═══════════════════════════════════════════════════════════════════════════
    curr_sec_idx = int(sec_num)

    if predictive_text and "skipped" not in predictive_text.lower():
        curr_sec_idx += 1
        sec_str = str(curr_sec_idx).zfill(2)
        story.append(KeepTogether([
            _section_header(sec_str, "Predictive Auto-ML & Feature Drivers", body_style),
            Spacer(1, 12)
        ]))
        story.append(Paragraph(
            "Multi-algorithm machine learning benchmarks and quantitative feature driver rankings:", body_style
        ))
        story.append(Spacer(1, 8))
        for raw_l in predictive_text.split("\n"):
            l_str = raw_l.strip()
            if not l_str:
                continue
            if l_str.startswith("#"):
                story.append(Paragraph(f"<b>{_escape(l_str.lstrip('#').strip())}</b>", h2_style))
            elif l_str.startswith("-") or l_str.startswith("*"):
                story.append(Paragraph(f"▸  {_md_to_html(l_str.lstrip('-*• ').strip())}", bullet_style))
            elif "|" in l_str:
                # Format table lines cleanly
                story.append(Paragraph(f"<font color='#475569'>{_md_to_html(l_str)}</font>", small_style))
            else:
                story.append(Paragraph(_md_to_html(l_str), body_style))
        story.append(Spacer(1, 14))

    if anomaly_text and "skipped" not in anomaly_text.lower():
        curr_sec_idx += 1
        sec_str = str(curr_sec_idx).zfill(2)
        story.append(KeepTogether([
            _section_header(sec_str, "Quantitative Anomaly & Risk Audit", body_style),
            Spacer(1, 12)
        ]))
        story.append(Paragraph(
            "Statistical distribution variance, IQR/Z-score outlier audit, and compliance risk flags:", body_style
        ))
        story.append(Spacer(1, 8))
        for raw_l in anomaly_text.split("\n"):
            l_str = raw_l.strip()
            if not l_str:
                continue
            if l_str.startswith("#"):
                story.append(Paragraph(f"<b>{_escape(l_str.lstrip('#').strip())}</b>", h2_style))
            elif l_str.startswith("-") or l_str.startswith("*"):
                story.append(Paragraph(f"▸  {_md_to_html(l_str.lstrip('-*• ').strip())}", bullet_style))
            else:
                story.append(Paragraph(_md_to_html(l_str), body_style))
        story.append(Spacer(1, 14))

    if trend_text and "skipped" not in trend_text.lower():
        curr_sec_idx += 1
        sec_str = str(curr_sec_idx).zfill(2)
        story.append(KeepTogether([
            _section_header(sec_str, "Time-Series Trajectory & Trend Projections", body_style),
            Spacer(1, 12)
        ]))
        story.append(Paragraph(
            "Temporal momentum tracking, growth delta trajectories, and forward-looking outlook:", body_style
        ))
        story.append(Spacer(1, 8))
        for raw_l in trend_text.split("\n"):
            l_str = raw_l.strip()
            if not l_str:
                continue
            if l_str.startswith("#"):
                story.append(Paragraph(f"<b>{_escape(l_str.lstrip('#').strip())}</b>", h2_style))
            elif l_str.startswith("-") or l_str.startswith("*"):
                story.append(Paragraph(f"▸  {_md_to_html(l_str.lstrip('-*• ').strip())}", bullet_style))
            else:
                story.append(Paragraph(_md_to_html(l_str), body_style))
        story.append(Spacer(1, 14))

    # ═══════════════════════════════════════════════════════════════════════════
    # MULTI-AGENT DOMAIN BREAKDOWN (25 AGENTS INTELLIGENCE SYSTEM)
    # ═══════════════════════════════════════════════════════════════════════════
    has_cat_data = any(len(agents) > 0 for agents in categories_data.values() if isinstance(agents, list))
    if has_cat_data:
        curr_sec_idx += 1
        sec_str = str(curr_sec_idx).zfill(2)
        story.append(KeepTogether([
            _section_header(sec_str, "Multi-Agent Domain Intelligence Breakdown", body_style),
            Spacer(1, 10)
        ]))
        story.append(Paragraph(
            "Empirical findings and verified performance metrics from active intelligence agents:", body_style
        ))
        story.append(Spacer(1, 8))

        cat_titles = {
            "data_analysis": "1. Data Analysis Domain",
            "business_analysis": "2. Business Analysis Domain",
            "data_mining": "3. Data Mining Domain",
            "predictive_analysis": "4. Predictive Analysis Domain",
            "eda": "5. Exploratory Data Analysis & Visuals",
        }

        for cat_id, cat_title in cat_titles.items():
            cat_agents = categories_data.get(cat_id, [])
            active_agents = [a for a in cat_agents if a.get("status") == "completed"]
            if not active_agents:
                continue

            story.append(Paragraph(f"<b>{cat_title}</b>", h2_style))
            for agent in active_agents:
                a_name = agent.get("name", agent.get("agent_id", "Agent"))
                a_findings = agent.get("findings", [])
                a_metrics = agent.get("metrics", {})

                metrics_summary = ", ".join(
                    f"{k.replace('_', ' ').title()}: {v:,.2f}" if isinstance(v, (int, float)) else f"{k.replace('_', ' ').title()}: {v}"
                    for k, v in a_metrics.items()
                )
                metric_label = f" <font color='#64748b' size=8>({_escape(metrics_summary)})</font>" if metrics_summary else ""
                story.append(Paragraph(f"<b>{_escape(a_name)}</b>{metric_label}", bullet_style))
                for f in a_findings[:3]:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;▸  {_md_to_html(f)}", small_style))
            story.append(Spacer(1, 8))
        story.append(Spacer(1, 10))

    app_num = str(curr_sec_idx + 1).zfill(2)
    story.append(KeepTogether([
        _section_header(app_num, "Appendix", body_style),
        Spacer(1, 12)
    ]))

    if df is not None and isinstance(df, pd.DataFrame):
        story.append(Paragraph("Per-Column Statistical Summary", h2_style))
        story.append(Paragraph(
            "Numeric distributions and categorical frequency breakdowns for all dataset columns:",
            body_style
        ))
        story.append(Spacer(1, 5))
        stat_flowables = _build_stats_tables(df, body_style)
        if stat_flowables:
            story.extend(stat_flowables)
        story.append(Spacer(1, 12))

    unplaced = [p for p in png_files if p not in placed_charts]
    if unplaced:
        story.append(Paragraph("Additional Analytical Visualizations", h2_style))
        story.append(Paragraph(
            "Supplementary visual mappings of auxiliary data relationships:", body_style
        ))
        story.append(Spacer(1, 8))
        for png_file in unplaced:
            img_tbl, fig_cap = _img_flowable(png_file)
            if img_tbl:
                fig_lbl = Paragraph(
                    f"<b>Figure: {_escape(png_file.stem.replace('_', ' ').title())}</b>",
                    ParagraphStyle("FigLbl", fontName="Helvetica-Bold", fontSize=9,
                                   textColor=C_CRIMSON_DARK, spaceBefore=8, spaceAfter=4, keepWithNext=True)
                )
                story.append(KeepTogether([fig_lbl, img_tbl, fig_cap, Spacer(1, 12)]))
            else:
                story.append(Paragraph(f"(Could not load: {png_file.name})", small_style))

    # ── Conclusion box ─────────────────────────────────────────────────────────
    conclusion_items = [
        Paragraph(
            "<b>Executive Conclusion &amp; Recommended Next Steps</b>",
            ParagraphStyle("ConclHdr", fontName="Helvetica-Bold", fontSize=11,
                           textColor=C_CRIMSON_DARK, spaceAfter=6, leading=14)
        ),
        Paragraph(
            (
                "Based on the analysis conducted on the dataset, the data pipeline has successfully validated "
                "and evaluated the provided records. "
                "The findings point towards the strategic recommendations detailed in the Insights section. "
                "To maximize value from these insights, it is highly recommended to prioritize the outlined "
                "Actionable Strategies, actively mitigate any Business Risks surfaced in this report, and leverage "
                "the key visualizations to communicate findings with stakeholders."
            ) if not strategic_text else (
                "Based on the autonomous data analysis, several critical patterns were uncovered. "
                f"Most notably, the primary insight reveals: {_escape(strategic_text.split('**Observation**:')[1].split('**Business Implication**:')[0].strip()[:250] if '**Observation**:' in strategic_text else strategic_text[:250])}... "
                "To maximize business value, stakeholders must prioritize the Actionable Strategies detailed in the Insights section, "
                "address the highlighted Business Risks, and use the provided data visualizations to drive informed decision-making."
            ),
            ParagraphStyle("ConclBody", fontName="Helvetica", fontSize=9.5,
                           textColor=C_INK, leading=14.5)
        ),
    ]
    concl_tbl = Table([[conclusion_items]], colWidths=[504])
    concl_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_ROW_ALT),
        ("BOX",           (0, 0), (-1, -1), 1,  C_BORDER),
        ("LINELEFT",      (0, 0), (0, -1),  5,  C_CRIMSON_DARK),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(Spacer(1, 18))
    story.append(KeepTogether([concl_tbl]))

    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# ─────────────────────────────────────────────────────────────────────────────
# Cached wrapper
# ─────────────────────────────────────────────────────────────────────────────

_pdf_cache: dict = {}


def export_pdf_cached(
    cache_key:       str,
    filename:        str = "",
    result_cleaning: str = "",
    result_relations:str = "",
    result_insights: str = "",
    result_code:     str = "",
    output_dir_str:  str = "outputs",
    df_csv:          str = "",
) -> bytes:
    if cache_key in _pdf_cache:
        return _pdf_cache[cache_key]

    df = None
    if df_csv:
        try:
            df = pd.read_csv(io.StringIO(df_csv))
        except Exception:
            df = None

    result = {
        "dataframe":      df,
        "cleaning_steps": result_cleaning,
        "relations":      result_relations,
        "insights":       result_insights,
        "code":           result_code,
        "output_dir":     output_dir_str,
    }
    pdf_bytes = export_pdf(result, filename=filename)
    _pdf_cache[cache_key] = pdf_bytes
    return pdf_bytes


# ─────────────────────────────────────────────────────────────────────────────
# Chat log helpers
# ─────────────────────────────────────────────────────────────────────────────

def _clean_chat_content(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r'\[Auto-Healing system resolved a code error!\][\s\S]*?(?:Successful Execution Output:\s*(?:\(no output\)|\S+)?\s*)', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[Auto-Healing system installed missing package[\s\S]*?(?:Output:\s*\S*\s*)?', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Original Error:[\s\S]*?(?=(?:Successful Execution Output|$))', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Successful Execution Output:\s*\(no output\)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Successful Execution Output:', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Chat PDF generator — premium format
# ─────────────────────────────────────────────────────────────────────────────

def export_chat_pdf(messages: list, session_id: str) -> bytes:
    """Generate a premium styled PDF from a Crew Chat conversation."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=54, leftMargin=54,
        topMargin=82, bottomMargin=82,
    )
    styles = getSampleStyleSheet()

    P_RED      = colors.HexColor("#c0392b")
    P_DARK     = colors.HexColor("#7b1d1d")
    P_BLUE     = colors.HexColor("#1d4ed8")
    P_MUTED    = colors.HexColor("#475569")
    P_INK      = colors.HexColor("#0f172a")
    P_PALE_U   = colors.HexColor("#f0f4ff")
    P_PALE_A   = colors.HexColor("#fff5f5")
    P_BORDER   = colors.HexColor("#cbd5e1")

    title_style = ParagraphStyle("ChatTitle", fontName="Helvetica-Bold", fontSize=22,
                                  leading=26, textColor=P_DARK, spaceAfter=4)
    meta_style  = ParagraphStyle("ChatMeta",  fontName="Helvetica", fontSize=8.5,
                                  leading=12, textColor=P_MUTED, spaceAfter=8)
    user_style  = ParagraphStyle("UserMsg",   fontName="Helvetica", fontSize=9.5,
                                  leading=14.5, textColor=P_INK)
    asst_style  = ParagraphStyle("AsstMsg",   fontName="Helvetica", fontSize=9.5,
                                  leading=14.5, textColor=P_INK)
    role_u_style= ParagraphStyle("RoleU", fontName="Helvetica-Bold", fontSize=8,
                                  textColor=P_BLUE, leading=11)
    role_a_style= ParagraphStyle("RoleA", fontName="Helvetica-Bold", fontSize=8,
                                  textColor=P_RED,  leading=11)

    # Cover strip
    def _band(text, bg, fg):
        t = Table([[Paragraph(text, ParagraphStyle("B", fontName="Helvetica-Bold",
                               fontSize=8.5, textColor=fg, alignment=1, leading=11))]],
                  colWidths=[504], rowHeights=[20])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), bg),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0),(-1,-1), 2),
            ("BOTTOMPADDING", (0,0),(-1,-1), 2),
        ]))
        return t

    def _divider_c(thick=2, color=P_RED):
        t = Table([[""]], colWidths=[504], rowHeights=[thick])
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),color),
                                ("TOPPADDING",(0,0),(-1,-1),0),
                                ("BOTTOMPADDING",(0,0),(-1,-1),0)]))
        return t

    story = [
        Spacer(1, 30),
        _band("CREW CHAT  ·  CONVERSATION EXPORT", P_DARK, colors.white),
        Spacer(1, 5),
        _divider_c(3),
        Spacer(1, 14),
        Paragraph("<b>Crew Chat Log</b>", title_style),
        Paragraph(
            f"Session ID: {session_id}  ·  Exported on {datetime.now().strftime('%d %B %Y at %I:%M %p')}",
            meta_style
        ),
        Spacer(1, 4),
        _divider_c(1, colors.HexColor("#e2e8f0")),
        Spacer(1, 16),
    ]

    for idx, msg in enumerate(messages, start=1):
        role      = msg.get("role", "user")
        content   = _clean_chat_content(msg.get("content", ""))
        plot_url  = msg.get("plot_url")
        is_user   = (role == "user")

        formatted = _md_to_html(content).replace("\n", "<br/>")

        if is_user:
            role_label = Paragraph("YOU", role_u_style)
            msg_para   = Paragraph(formatted, user_style)
            msg_tbl    = Table([[msg_para]], colWidths=[450])
            msg_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), P_PALE_U),
                ("BOX",           (0,0),(-1,-1), 0.5, P_BORDER),
                ("LINERIGHT",     (0,0),(-1,-1), 3,  P_BLUE),
                ("LEFTPADDING",   (0,0),(-1,-1), 12),
                ("RIGHTPADDING",  (0,0),(-1,-1), 12),
                ("TOPPADDING",    (0,0),(-1,-1), 9),
                ("BOTTOMPADDING", (0,0),(-1,-1), 9),
            ]))
            wrapper = Table([[role_label, ""], [msg_tbl, ""]], colWidths=[450, 54])
        else:
            role_label = Paragraph("CREW CHAT", role_a_style)
            msg_para   = Paragraph(formatted, asst_style)
            msg_tbl    = Table([[msg_para]], colWidths=[450])
            msg_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), P_PALE_A),
                ("BOX",           (0,0),(-1,-1), 0.5, P_BORDER),
                ("LINELEFT",      (0,0),(0,-1),  3,  P_RED),
                ("LEFTPADDING",   (0,0),(-1,-1), 12),
                ("RIGHTPADDING",  (0,0),(-1,-1), 12),
                ("TOPPADDING",    (0,0),(-1,-1), 9),
                ("BOTTOMPADDING", (0,0),(-1,-1), 9),
            ]))
            wrapper = Table([["", role_label], ["", msg_tbl]], colWidths=[54, 450])

        story.append(KeepTogether([wrapper]))

        # Embedded chart
        if plot_url:
            try:
                fname = urllib.parse.unquote(plot_url.split("/")[-1])
                user_home   = Path.home() / ".crewlyze"
                outputs_base = Path(os.getenv("CREWLYZE_OUTPUTS_DIR", str(user_home / "outputs")))
                png_file = outputs_base / session_id / fname

                if png_file.exists():
                    img_tbl, fig_cap = _img_flowable(png_file, max_w=380, max_h=260)
                    if img_tbl:
                        story.append(Spacer(1, 4))
                        story.append(KeepTogether([img_tbl, fig_cap]))
            except Exception as exc:
                print(f"Chat PDF image embed failed: {exc}")

        story.append(Spacer(1, 10))

    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
