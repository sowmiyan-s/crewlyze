# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Interactive AI Data Copilot module.

Accepts a natural language query from the user, generates Python code via LLM,
executes it securely in an isolated subprocess, and returns text results and
new dynamically generated visualizations.

Key improvements:
- Column names, dtypes, and per-column statistics are injected into the prompt
  so the LLM generates accurate, runnable code without guessing column names.
- Supports /column slash command prefix for column-aware queries.
"""

import os
import re
import sys
import textwrap
import uuid
from pathlib import Path

import pandas as pd
from crewai import LLM
from config.llm_config import get_llm_params
from tools.dataset_tools import _run_in_subprocess, _strip_markdown_fences, read_csv_robust


# ---------------------------------------------------------------------------
# Column schema builder
# ---------------------------------------------------------------------------

def _build_column_context(csv_path: str, max_rows: int = 500) -> str:
    """
    Load the CSV and build a compact column schema string for injection into
    the LLM prompt.  Includes dtypes, missing%, and key statistics so the LLM
    can write correct, runnable pandas code without hallucinating column names.
    """
    try:
        df = read_csv_robust(csv_path, nrows=max_rows)
    except Exception as exc:
        return f"[Could not load dataset: {exc}]"

    lines = [
        f"Dataset: {max_rows if len(df) == max_rows else len(df)} rows × {len(df.columns)} columns",
        "",
        "Columns (name | dtype | missing% | stats):",
    ]
    for col in df.columns:
        dtype    = df[col].dtype
        miss_pct = round(df[col].isnull().sum() / max(len(df), 1) * 100, 1)
        if pd.api.types.is_numeric_dtype(dtype):
            stats = (
                f"min={df[col].min():.4g}, "
                f"mean={df[col].mean():.4g}, "
                f"max={df[col].max():.4g}, "
                f"std={df[col].std():.4g}"
            )
        else:
            top3 = df[col].dropna().value_counts().head(3).index.tolist()
            stats = "top: " + ", ".join(str(v) for v in top3) if top3 else "—"
        lines.append(f"  - {col!r}: {dtype} | missing={miss_pct}% | {stats}")

    lines.append("")
    lines.append("Sample rows (first 3):")
    for _, row in df.head(3).iterrows():
        lines.append("  " + str(dict(row)))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main copilot entry point
# ---------------------------------------------------------------------------

def run_copilot_query(query: str, csv_path: str, output_dir_str: str) -> dict:
    """
    Accepts a user query, generates Python code using the current LLM,
    runs the code in a sandbox subprocess, and returns {text, plot_path}.

    The column schema (names, dtypes, stats) is injected into the prompt to
    prevent NameError / KeyError in LLM-generated code.
    """
    # 1. Initialise LLM from current session env vars
    try:
        llm_params = get_llm_params()
        llm = LLM(**llm_params)
    except Exception as exc:
        return {
            "success": False,
            "text": f"LLM not configured: {exc}\nSet your API key in the sidebar.",
            "plot_path": None,
        }

    # 2. Build column context (prevents wrong-column NameErrors)
    column_context = _build_column_context(csv_path)

    # 3. Prepare plot output path
    output_dir = Path(output_dir_str)
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_name = f"copilot_plot_{_uuid_short()}.png"
    plot_path = output_dir / plot_name

    # Clean up previous copilot plots
    for prev in output_dir.glob("copilot_plot_*.png"):
        try:
            prev.unlink(missing_ok=True)
        except OSError:
            pass

    # 4. Build LLM prompt with full column context
    prompt = textwrap.dedent(f"""
    You are an expert AI Data Analyst. You have access to a CSV dataset at:
      FILE_PATH = '{csv_path}'

    === DATASET SCHEMA ===
    {column_context}
    =====================

    USER QUERY: "{query}"

    INSTRUCTIONS:
    1. Read the dataset: df = pd.read_csv(FILE_PATH)
    2. Use ONLY the column names listed above (exact spelling, case-sensitive).
    3. Perform any required analysis, aggregation, or computation.
    4. Print a clear, formatted answer to stdout.
    5. If the query asks for a chart/plot/graph:
       - Call `import matplotlib; matplotlib.use('Agg')` BEFORE importing pyplot.
       - Generate a professional chart and save it to: '{plot_path.as_posix()}'
       - Call `plt.tight_layout()` then `plt.savefig(...)` then `plt.close()`.

    Return ONLY valid Python code inside a ```python ... ``` block.
    Do NOT include explanations or text outside the code block.
    """).strip()

    try:
        # 5. Generate code
        response  = llm.call([{"role": "user", "content": prompt}])
        raw_code  = response if isinstance(response, str) else str(response)
        code      = _strip_markdown_fences(raw_code)

        if not code.strip():
            return {
                "success": False,
                "text": "The model returned empty code. Try rephrasing your query.",
                "plot_path": None,
            }

        # 6. Execute in sandboxed subprocess
        success, exec_output = _run_in_subprocess(code)

        plot_saved      = plot_path.exists() and plot_path.stat().st_size > 0
        final_plot_path = str(plot_path) if plot_saved else None

        if success:
            answer_text = exec_output.strip() if exec_output.strip() not in ("", "(no output)") \
                          else "✅ Query executed successfully (no text output)."
            return {"success": True, "text": answer_text, "plot_path": final_plot_path}
        else:
            return {
                "success": False,
                "text": f"⚠️ Execution error:\n```\n{exec_output}\n```",
                "plot_path": None,
            }

    except Exception as exc:
        return {
            "success": False,
            "text": f"Copilot error: {exc}",
            "plot_path": None,
        }


def _uuid_short() -> str:
    return uuid.uuid4().hex[:6]


# ---------------------------------------------------------------------------
# Column list helper (used by the /column slash picker in app.py)
# ---------------------------------------------------------------------------

def get_column_names(csv_path: str) -> list[str]:
    """Return column names from the CSV, or empty list on error."""
    try:
        return list(read_csv_robust(csv_path, nrows=0).columns)
    except Exception:
        return []
