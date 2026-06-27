# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Dataset tools for CrewAI agents.

Security note
-------------
All LLM-generated code is executed in an isolated child process (subprocess),
never via exec() in the parent process. This eliminates RCE risk: the child
has no access to the parent's globals, secrets, or in-memory state.

Performance note
----------------
build_dataset_profile() is a pure Python function (not a CrewAI tool) that
pre-computes a compact dataset summary and returns it as a string. Injecting
this string into task descriptions eliminates 6-8 LLM round-trips per run that
agents would otherwise spend calling read_dataset_head / get_dataset_info /
get_correlation_matrix before they can act.

generate_plotly_charts() parses the relation-agent output and produces
interactive Plotly figures directly in Python — no LLM, no subprocess, no PNG
file I/O. This replaces static matplotlib PNGs with zoomable, hoverable charts.
"""

import os
import re
import sys
import textwrap
import tempfile
import subprocess

import pandas as pd
from crewai.tools import tool


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _strip_markdown_fences(code: str) -> str:
    """Remove leading/trailing markdown code fences from LLM output."""
    code = code.strip()
    code = re.sub(r"^```(?:python)?\s*\n?", "", code)
    code = re.sub(r"\n?```\s*$", "", code)
    return code.strip()


def _run_in_subprocess(script: str, timeout: int = 120) -> tuple[bool, str]:
    """
    Write *script* to a temp file and execute it in an isolated subprocess.

    Returns (success: bool, output: str) where output is stdout+stderr.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(script)
        tmp_path = tmp.name

    try:
        proc = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = (proc.stdout + proc.stderr).strip()
        success = proc.returncode == 0
        return success, output or "(no output)"
    except subprocess.TimeoutExpired:
        return False, f"Execution timed out after {timeout}s."
    except Exception as e:
        return False, f"Failed to launch subprocess: {e}"
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Pure Python helpers — NOT CrewAI tools, called directly from run_crew()
# ---------------------------------------------------------------------------

def build_dataset_profile(csv_path: str, max_rows: int = 5000) -> str:
    """Build a compact, token-efficient dataset profile string.

    Injecting this into task descriptions eliminates the need for agents to
    call read_dataset_head / get_dataset_info / get_correlation_matrix —
    saving 6-8 LLM round-trips per pipeline run.

    Args:
        csv_path : Path to the CSV file.
        max_rows : Row cap for profiling large files (default 5000).

    Returns:
        A markdown-formatted string safe for embedding in task descriptions.
    """
    try:
        df = pd.read_csv(csv_path, nrows=max_rows)
    except Exception as exc:
        return f"[Profile unavailable: {exc}]"

    lines: list[str] = []
    sampled = len(df)

    # Shape
    note = " (sample — file is larger)" if sampled == max_rows else ""
    lines.append(
        f"**Dataset shape**: {sampled} rows × {len(df.columns)} columns{note}"
    )
    lines.append("")

    # Column summary
    lines.append("**Columns** (name | dtype | missing% | stats/top values):")
    for col in df.columns:
        dtype    = df[col].dtype
        miss_pct = round(df[col].isnull().sum() / max(len(df), 1) * 100, 1)
        if pd.api.types.is_numeric_dtype(dtype):
            desc = (
                f"min={df[col].min():.4g}, "
                f"mean={df[col].mean():.4g}, "
                f"max={df[col].max():.4g}"
            )
        else:
            tops = df[col].dropna().value_counts().head(3).index.tolist()
            desc = ", ".join(str(v) for v in tops) or "—"
        lines.append(f"  - {col}: {dtype} | missing={miss_pct}% | {desc}")
    lines.append("")

    # Top correlations (numeric only)
    numeric_df = df.select_dtypes(include=["number"])
    if len(numeric_df.columns) >= 2:
        try:
            corr = numeric_df.corr().unstack().reset_index()
            corr.columns = ["A", "B", "r"]
            corr = corr[corr["A"] < corr["B"]].copy()
            corr["abs_r"] = corr["r"].abs()
            top5 = corr.nlargest(5, "abs_r")[["A", "B", "r"]]
            lines.append("**Top correlations**:")
            for _, row in top5.iterrows():
                lines.append(f"  - {row['A']} ↔ {row['B']}: r={row['r']:.3f}")
            lines.append("")
        except Exception:
            pass  # silently skip if corr fails (e.g. all NaN numeric cols)

    # Sample rows
    lines.append("**Sample rows (first 5)**:")
    lines.append(df.head(5).to_markdown(index=False))

    return "\n".join(lines)


def generate_plotly_charts(csv_path: str, relations_text: str, max_rows: int = 5000) -> list:
    """Parse agent relation output and generate interactive Plotly figures.

    Replaces static matplotlib PNGs with zoomable, hoverable charts rendered
    natively by st.plotly_chart(). No LLM calls, no subprocess, no file I/O.

    Args:
        csv_path       : Path to the cleaned CSV file.
        relations_text : Raw text output from the relation agent.
        max_rows       : Row cap for chart data (default 5000 for rendering speed).

    Returns:
        List of dicts: [{"title": str, "fig": plotly.graph_objs.Figure}, ...]
        Returns an empty list if plotly is unavailable or no valid relations found.
    """
    try:
        import plotly.express as px
    except ImportError:
        return []

    try:
        df = pd.read_csv(csv_path, nrows=max_rows)
    except Exception:
        return []

    # Dark-theme layout matching the app's "Obsidian & Electric Violet" aesthetic
    _dark = dict(
        paper_bgcolor="rgba(9,9,11,0.0)",
        plot_bgcolor="rgba(15,23,42,0.4)",
        font_color="#e2e8f0",
        title_font_color="#a78bfa",
        title_font_size=15,
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.07)",
            zerolinecolor="rgba(255,255,255,0.1)",
            title_font_color="#94a3b8",
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.07)",
            zerolinecolor="rgba(255,255,255,0.1)",
            title_font_color="#94a3b8",
        ),
        margin=dict(l=50, r=20, t=55, b=50),
        hoverlabel=dict(bgcolor="rgba(15,23,42,0.95)", font_color="#e2e8f0"),
    )
    _colors = ["#a78bfa", "#6366f1", "#22d3ee", "#e879f9", "#34d399"]

    figures = []

    for line in relations_text.split("\n"):
        line = line.strip()
        if not (line and "|" in line and "X:" in line):
            continue
        try:
            parts = [p.strip() for p in line.lstrip("- ").split("|")]
            x_col = parts[0].split(":", 1)[1].strip()
            y_col = parts[1].split(":", 1)[1].strip()
            ptype = parts[2].split(":", 1)[1].strip().lower()
        except (IndexError, ValueError):
            continue

        if x_col not in df.columns or y_col not in df.columns:
            continue

        title = f"{x_col} vs {y_col}"
        color = _colors[len(figures) % len(_colors)]

        try:
            sample = df[[x_col, y_col]].dropna().head(2000)

            if "scatter" in ptype:
                fig = px.scatter(
                    sample, x=x_col, y=y_col, title=title,
                    color_discrete_sequence=[color],
                    opacity=0.75,
                )
            elif "bar" in ptype:
                agg = sample.groupby(x_col)[y_col].mean().reset_index()
                fig = px.bar(
                    agg.head(20), x=x_col, y=y_col, title=title,
                    color_discrete_sequence=[color],
                )
            elif "line" in ptype:
                fig = px.line(
                    sample, x=x_col, y=y_col, title=title,
                    color_discrete_sequence=[color],
                )
            elif "box" in ptype:
                fig = px.box(
                    sample, x=x_col, y=y_col, title=title,
                    color_discrete_sequence=[color],
                )
            elif "hist" in ptype:
                fig = px.histogram(
                    sample, x=x_col, nbins=30,
                    title=f"Distribution of {x_col}",
                    color_discrete_sequence=[color],
                )
            else:
                # Default: scatter
                fig = px.scatter(
                    sample, x=x_col, y=y_col, title=title,
                    color_discrete_sequence=[color],
                    opacity=0.75,
                )

            fig.update_layout(**_dark)
            figures.append({"title": title, "fig": fig})

        except Exception:
            continue  # skip un-plottable pairs silently

    return figures


# ---------------------------------------------------------------------------
# CrewAI tools — used by agents at runtime as fallback / code generation aid
# ---------------------------------------------------------------------------

class DatasetTools:

    @tool("Read Dataset Head")
    def read_dataset_head(file_path: str) -> str:
        """Reads the first 10 rows of the dataset to understand its structure.
        Uses nrows=10 so the entire file is never loaded into memory.
        """
        try:
            df = pd.read_csv(file_path, nrows=10)
            return df.to_markdown(index=False)
        except Exception as e:
            return f"Error reading file: {e}"

    @tool("Get Dataset Info")
    def get_dataset_info(file_path: str) -> str:
        """Returns basic information about the dataset: shape, columns, data types,
        and missing-value counts.
        """
        try:
            df = pd.read_csv(file_path)
            lines = [f"Shape: {df.shape}", "\nColumns and Types:"]
            for col, dtype in df.dtypes.items():
                missing = df[col].isnull().sum()
                lines.append(f"  - {col}: {dtype} (Missing: {missing})")
            return "\n".join(lines)
        except Exception as e:
            return f"Error analyzing file: {e}"

    @tool("Get Correlation Matrix")
    def get_correlation_matrix(file_path: str) -> str:
        """Returns the top-20 strongest column-pair correlations (by absolute value).

        Sending a full N×N matrix to the LLM wastes tokens and may exceed context
        limits for wide datasets. Only the most informative pairs are returned.
        """
        try:
            df = pd.read_csv(file_path)
            numeric_df = df.select_dtypes(include=["number"])
            if numeric_df.empty:
                return "No numeric columns found."

            corr = numeric_df.corr()
            unstacked = (
                corr.unstack()
                .reset_index()
                .rename(columns={"level_0": "Col_A", "level_1": "Col_B", 0: "Correlation"})
            )
            unstacked = unstacked[unstacked["Col_A"] < unstacked["Col_B"]]
            unstacked["AbsCorr"] = unstacked["Correlation"].abs()
            top = (
                unstacked.sort_values("AbsCorr", ascending=False)
                .head(20)
                .drop(columns=["AbsCorr"])
                .reset_index(drop=True)
            )
            return top.to_markdown(index=False)
        except Exception as e:
            return f"Error calculating correlation: {e}"

    @tool("Clean Dataset with Python Code")
    def clean_dataset_with_python(file_path: str, python_code: str) -> str:
        """Cleans the dataset at *file_path* by executing *python_code* in an
        isolated subprocess.

        Your code must:
          1. Read the CSV:  df = pd.read_csv(FILE_PATH)   # FILE_PATH is pre-set
          2. Perform cleaning on df
          3. Save:          df.to_csv(FILE_PATH, index=False)

        Do NOT include markdown code fences. Do NOT use any other file paths.
        """
        clean_code = _strip_markdown_fences(python_code)

        script = textwrap.dedent(f"""\
            import os
            import pandas as pd

            FILE_PATH = {repr(str(file_path))}
            df = pd.read_csv(FILE_PATH)

            # ---- LLM-generated cleaning code ----
            {textwrap.indent(clean_code, "            ").lstrip()}
            # ---- end LLM code ----

            df.to_csv(FILE_PATH, index=False)
            print("Dataset cleaned and saved successfully.")
        """)

        success, output = _run_in_subprocess(script)
        if success:
            return f"Dataset cleaned successfully.\n{output}"
        return f"Error executing cleaning code:\n{output}"

    @tool("Execute Visualization Code")
    def execute_visualization_code(python_code: str) -> str:
        """Executes Python code to generate and save visualizations as PNG files.

        The code runs in an isolated subprocess — it MUST import all libraries
        it needs (pandas, matplotlib, seaborn, etc.) and use the session-specific
        file paths given in the task description.

        Always call matplotlib.use('Agg') before importing pyplot.
        Save each plot with plt.savefig(..., bbox_inches='tight', dpi=150).
        Always call plt.close() after saving each figure.
        """
        clean_code = _strip_markdown_fences(python_code)

        # NOTE: The session-specific output directory is created by run_crew()
        # before agents are invoked. Do NOT create a root-level "outputs/" here
        # as it would bypass per-session file isolation.
        success, output = _run_in_subprocess(clean_code)
        if success:
            return f"Visualization code executed successfully. Plots saved.\n{output}"
        return f"Error executing visualization code:\n{output}"
