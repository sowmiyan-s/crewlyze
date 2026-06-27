# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
UI component helpers for the Agentic Data Analyst app.

All functions that render LLM-generated text use html.escape() before
injecting into unsafe_allow_html blocks to prevent XSS.
"""

import html
import re
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path


# ---------------------------------------------------------------------------
# Business Intelligence Renderers
# ---------------------------------------------------------------------------

def display_mckinsey_insights(text: str) -> None:
    """Parse and render McKinsey/BCG-style structured insights into premium visual cards.

    Expects the agent output structure:
    1. **Observation**: ...
       **Business Implication**: ...
       **Actionable Strategy**: ...
    """
    if not text:
        st.info("No business insights available.")
        return

    # Split into separate numbered insight items (matches e.g., "1. " or "\n2. ")
    items = re.split(r'\n\d+\.\s+|\b\d+\.\s+', text)
    count = 0

    for item in items:
        item = item.strip()
        if not item:
            continue
        count += 1

        # Use regex to extract the Observation, Business Implication, and Actionable Strategy sections
        obs_match = re.search(
            r'\*\*(?:Observation)\*\*:\s*(.*?)(?=\*\*(?:Business\s+)?Implication\*\*|\*\*(?:Actionable\s+)?Strategy\*\*|$)',
            item, re.DOTALL | re.IGNORECASE
        )
        imp_match = re.search(
            r'\*\*(?:Business\s+)?Implication\*\*:\s*(.*?)(?=\*\*(?:Actionable\s+)?Strategy\*\*|$)',
            item, re.DOTALL | re.IGNORECASE
        )
        strat_match = re.search(
            r'\*\*(?:Actionable\s+)?Strategy\*\*:\s*(.*?)$',
            item, re.DOTALL | re.IGNORECASE
        )

        obs = obs_match.group(1).strip() if obs_match else ""
        imp = imp_match.group(1).strip() if imp_match else ""
        strat = strat_match.group(1).strip() if strat_match else ""

        # Fallback: if structure is not strictly matched, render the raw item gracefully
        if not obs and not imp and not strat:
            obs = item

        # Build XSS-safe text
        safe_obs = html.escape(obs)
        safe_imp = html.escape(imp)
        safe_strat = html.escape(strat)

        # Style Subsections
        section_html = ""
        if safe_obs:
            section_html += f"""
            <div class="insight-section">
                <span class="insight-label label-obs">🔍 Observation</span>
                <p class="insight-text">{safe_obs}</p>
            </div>
            """
        if safe_imp:
            section_html += f"""
            <div class="insight-section">
                <span class="insight-label label-imp">⚠️ Business Implication</span>
                <p class="insight-text" style="color: #fbbf24;">{safe_imp}</p>
            </div>
            """
        if safe_strat:
            section_html += f"""
            <div class="insight-section">
                <span class="insight-label label-strat">⚡ Actionable Strategy</span>
                <p class="insight-text insight-text-strat">{safe_strat}</p>
            </div>
            """

        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-header">💡 STRATEGIC INSIGHT #{count}</div>
                {section_html}
            </div>
            """,
            unsafe_allow_html=True,
        )


def display_cleaning_timeline(text: str) -> None:
    """Parse cleaning steps and render them as a step-by-step audit timeline."""
    if not text:
        st.info("No cleaning operations recorded.")
        return

    steps = []
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        # Strip list tokens
        line = re.sub(r"^[\d]+\.\s+", "", line)  # numbered lists
        line = re.sub(r"^[-*•]\s*", "", line)    # bullet symbols
        line = line.strip()
        if line:
            steps.append(html.escape(line))

    if not steps:
        st.info("No cleaning operations recorded.")
        return

    timeline_items_html = ""
    for idx, step in enumerate(steps):
        timeline_items_html += f"""
        <div class="timeline-item">
            <div class="timeline-step">Step {idx + 1}</div>
            <p class="timeline-desc">{step}</p>
        </div>
        """

    st.markdown(
        f"""
        <div class="timeline-container">
            {timeline_items_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Relations Renderers
# ---------------------------------------------------------------------------

def display_relations(text: str) -> None:
    """Parse relations text and display as styled X vs Y (Type) items."""
    if not text:
        st.info("No relationships recorded.")
        return

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        rendered = False
        if "|" in line and "X:" in line:
            try:
                parts = [p.strip() for p in line.replace("- ", "").split("|")]
                x_col     = html.escape(parts[0].split(":", 1)[1].strip())
                y_col     = html.escape(parts[1].split(":", 1)[1].strip())
                plot_type = html.escape(parts[2].split(":", 1)[1].strip())

                # Pick colors for different plot types
                pt_lower = plot_type.lower()
                badge_bg = "rgba(139,92,246,0.15)"
                badge_color = "#c084fc"
                if "bar" in pt_lower:
                    badge_bg = "rgba(6,182,212,0.15)"
                    badge_color = "#22d3ee"
                elif "line" in pt_lower:
                    badge_bg = "rgba(16,185,129,0.15)"
                    badge_color = "#34d399"
                elif "scatter" in pt_lower:
                    badge_bg = "rgba(232,121,249,0.15)"
                    badge_color = "#e879f9"

                display_text = (
                    f"<span style='color: #e2e8f0; font-weight: 600;'>{x_col}</span>"
                    f"<span style='color: #64748b; margin: 0 8px; font-size: 0.9em;'>vs</span>"
                    f"<span style='color: #e2e8f0; font-weight: 600;'>{y_col}</span>"
                    f"<span style='color: {badge_color}; font-size: 0.8em; margin-left: 12px; "
                    f"background: {badge_bg}; padding: 3px 10px; border-radius: 12px; font-weight: 600;'>"
                    f"{plot_type}</span>"
                )
                st.markdown(
                    f"""
                    <div class="relation-item">
                        <span style="margin-right: 12px; font-size: 1.1em; color: #a78bfa;">🔗</span>
                        {display_text}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                rendered = True
            except (IndexError, KeyError, ValueError):
                pass

        if not rendered:
            safe_line = html.escape(line.lstrip("- "))
            st.markdown(
                f"""
                <div class="relation-item">
                    <span style="margin-right: 12px; font-size: 1.1em; color: #a78bfa;">🔗</span>
                    <span style="color: #e2e8f0;">{safe_line}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Interactive visualizations (Streamlit-native charts)
# ---------------------------------------------------------------------------

def render_visualizations(df: pd.DataFrame, key_prefix: str = "") -> None:
    """Render interactive Streamlit-native visualizations for a dataframe.

    Currently acts as an optional local fallback.
    """
    st.markdown("### 📈 Visualizations")

    numeric_cols     = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if numeric_cols:
        st.markdown("#### Distribution of Numeric Variables")
        col_to_plot = st.selectbox(
            "Select column for distribution", numeric_cols, key=f"{key_prefix}_dist_col"
        )
        hist_values, bin_edges = np.histogram(df[col_to_plot].dropna(), bins=20)
        hist_df = pd.DataFrame({"Frequency": hist_values}, index=bin_edges[:-1])
        st.bar_chart(hist_df)

    if len(numeric_cols) >= 2:
        st.markdown("#### Correlation Heatmap")
        corr = df[numeric_cols].corr()
        st.dataframe(corr.style.background_gradient(cmap="coolwarm"))

    if len(numeric_cols) >= 2:
        st.markdown("#### Scatter Plot")
        c1, c2 = st.columns(2)
        with c1:
            x_col = st.selectbox(
                "X Axis", numeric_cols, index=0, key=f"{key_prefix}_scatter_x"
            )
        with c2:
            y_col = st.selectbox(
                "Y Axis",
                numeric_cols,
                index=1 if len(numeric_cols) > 1 else 0,
                key=f"{key_prefix}_scatter_y",
            )
        st.scatter_chart(df, x=x_col, y=y_col)

    if categorical_cols and numeric_cols:
        st.markdown("#### Categorical vs Numeric")
        c1, c2 = st.columns(2)
        with c1:
            cat_col = st.selectbox(
                "Category", categorical_cols, index=0, key=f"{key_prefix}_cat_col"
            )
        with c2:
            num_col = st.selectbox(
                "Numeric", numeric_cols, index=0, key=f"{key_prefix}_num_col"
            )
        chart_data = (
            df.groupby(cat_col)[num_col].mean().sort_values(ascending=False).head(10)
        )
        st.bar_chart(chart_data)
        st.caption(f"Average {num_col} by Top 10 {cat_col}")


# ---------------------------------------------------------------------------
# Stdout logger widget
# ---------------------------------------------------------------------------

class StreamlitLogger:
    """Redirects stdout to a scrollable terminal-style Streamlit widget.

    Fixed to wrap long lines and prevent horizontal clipping.
    """
    def __init__(self, container, logs: list):
        self._container = container
        self._logs = logs

    def write(self, message: str) -> None:
        import sys

        if message.strip():
            try:
                clean = message.encode("utf-8", "ignore").decode("utf-8")
            except Exception:
                clean = message

            self._logs.append(html.escape(clean))
            log_html = (
                '<div style="height:300px;overflow-y:scroll;background-color:rgba(9,9,11,0.85);'
                "backdrop-filter:blur(12px);color:#22d3ee;padding:18px;border-radius:12px;"
                "font-family:'JetBrains Mono',monospace;font-size:0.85rem;white-space:pre-wrap;"
                "word-break:break-all;word-wrap:break-word;overflow-x:hidden;"
                'border:1px solid rgba(139,92,246,0.4);box-shadow:0 0 20px rgba(139,92,246,0.15),'
                'inset 0 0 15px rgba(0,0,0,0.6);">'
                '<span style="color:#a78bfa;font-weight:bold;">$ agentic_terminal_output</span><br/>'
                + "".join(self._logs)
                + "</div>"
            )
            self._container.markdown(log_html, unsafe_allow_html=True)

        try:
            enc = getattr(sys.__stdout__, "encoding", "utf-8") or "utf-8"
            safe = message.encode(enc, errors="replace").decode(enc)
            sys.__stdout__.write(safe)
        except Exception:
            pass

    def flush(self) -> None:
        import sys
        sys.__stdout__.flush()
