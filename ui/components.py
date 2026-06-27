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
# Bullet / list renderers
# ---------------------------------------------------------------------------

def display_text_as_bullets(text: str, emoji: str = "🔹") -> None:
    """Parse text lines and display them as styled bullet points.

    Handles:
    - Markdown list prefixes (-, *, •)
    - Numbered lists (1. 2. 3. ... N.) via regex — not just 1–3
    - HTML-escapes all LLM output before injection
    """
    if not text:
        return

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        # Strip any leading list marker (bullet or numbered)
        line = re.sub(r"^[\d]+\.\s+", "", line)          # numbered: "4. foo" → "foo"
        line = re.sub(r"^[-*•]\s*", "", line)             # bullets:  "- foo"  → "foo"
        line = line.strip()

        if not line:
            continue

        safe_line = html.escape(line)
        safe_emoji = html.escape(emoji)
        st.markdown(
            f"""
            <div class="styled-bullet">
                <span style="color: #e879f9; font-size: 1.2em; margin-right: 10px;">{safe_emoji}</span>
                <span style="font-size: 1.05em; color: #d1d5db;">{safe_line}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def display_relations(text: str) -> None:
    """Parse relations text and display as styled X vs Y (Type) items.

    All dynamic content is HTML-escaped before injection (XSS fix).
    """
    if not text:
        return

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        rendered = False
        if "|" in line and "X:" in line:
            try:
                parts = [p.strip() for p in line.replace("- ", "").split("|")]
                x_col    = html.escape(parts[0].split(":", 1)[1].strip())
                y_col    = html.escape(parts[1].split(":", 1)[1].strip())
                plot_type = html.escape(parts[2].split(":", 1)[1].strip())

                display_text = (
                    f"<span style='color: #e0e0e0; font-weight: 600;'>{x_col}</span>"
                    f"<span style='color: #6b7280; margin: 0 5px;'>vs</span>"
                    f"<span style='color: #e0e0e0; font-weight: 600;'>{y_col}</span>"
                    f"<span style='color: #e879f9; font-size: 0.85em; margin-left: 10px; "
                    f"background: rgba(232,121,249,0.1); padding: 2px 8px; border-radius: 12px;'>"
                    f"{plot_type}</span>"
                )
                st.markdown(
                    f"""
                    <div class="relation-item">
                        <span style="margin-right: 10px; font-size: 1.2em;">🔗</span>
                        {display_text}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                rendered = True
            except (IndexError, KeyError, ValueError):
                pass  # fall through to plain rendering below

        if not rendered:
            safe_line = html.escape(line.lstrip("- "))
            st.markdown(
                f"""
                <div class="relation-item">
                    <span style="margin-right: 10px; font-size: 1.2em;">🔗</span>
                    {safe_line}
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Interactive visualizations (Streamlit-native charts)
# ---------------------------------------------------------------------------

def render_visualizations(df: pd.DataFrame, key_prefix: str = "") -> None:
    """Render interactive Streamlit-native visualizations for a dataframe."""
    st.markdown("### 📈 Visualizations")

    numeric_cols     = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # 1. Distribution plots
    if numeric_cols:
        st.markdown("#### Distribution of Numeric Variables")
        col_to_plot = st.selectbox(
            "Select column for distribution", numeric_cols, key=f"{key_prefix}_dist_col"
        )
        hist_values, bin_edges = np.histogram(df[col_to_plot].dropna(), bins=20)
        hist_df = pd.DataFrame({"Frequency": hist_values}, index=bin_edges[:-1])
        st.bar_chart(hist_df)

    # 2. Correlation heatmap (as styled dataframe)
    if len(numeric_cols) >= 2:
        st.markdown("#### Correlation Heatmap")
        corr = df[numeric_cols].corr()
        st.dataframe(corr.style.background_gradient(cmap="coolwarm"))

    # 3. Scatter plot
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

    # 4. Categorical vs Numeric
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
# Stdout logger widget (moved from inner class to module level)
# ---------------------------------------------------------------------------

class StreamlitLogger:
    """Redirects stdout to a scrollable terminal-style Streamlit widget."""

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
                'border:1px solid rgba(139,92,246,0.4);box-shadow:0 0 20px rgba(139,92,246,0.15),'
                'inset 0 0 15px rgba(0,0,0,0.6);">'
                '<span style="color:#a78bfa;font-weight:bold;">$ agentic_terminal_output</span><br/>'
                + "".join(self._logs)
                + "</div>"
            )
            self._container.markdown(log_html, unsafe_allow_html=True)

        # Safely write to the real stdout — re-encode through the terminal's
        # actual encoding with errors='replace' so non-cp1252 chars (arrows,
        # emojis, etc.) become '?' instead of raising UnicodeEncodeError.
        try:
            enc = getattr(sys.__stdout__, "encoding", "utf-8") or "utf-8"
            safe = message.encode(enc, errors="replace").decode(enc)
            sys.__stdout__.write(safe)
        except Exception:
            pass  # never crash the UI over a terminal encoding issue

    def flush(self) -> None:
        import sys
        sys.__stdout__.flush()
