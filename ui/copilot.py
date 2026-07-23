# Crewlyze
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
from typing import Optional

import pandas as pd
from crewai import LLM
from config.llm_config import get_llm_params
from tools.dataset_tools import _run_in_subprocess, _strip_markdown_fences, read_csv_robust


# ---------------------------------------------------------------------------
# Column schema builder
# ---------------------------------------------------------------------------

def _build_column_context(csv_path: str, max_rows: int = 100) -> str:
    """
    Load CSV header & dtypes rapidly and build a ultra-compact schema string.
    Optimized for high-speed LLM inference.
    """
    try:
        df = read_csv_robust(csv_path, nrows=max_rows)
    except Exception as exc:
        return f"[Could not load dataset: {exc}]"

    lines = [
        f"Dataset Shape: {len(df)} rows × {len(df.columns)} columns",
        "Columns & Data Types:",
    ]
    for col in df.columns[:35]:
        lines.append(f"  - {col}: {df[col].dtype}")
    
    if len(df.columns) > 35:
        lines.append(f"  ... (+ {len(df.columns) - 35} more columns)")

    lines.append("")
    lines.append("Sample Values:")
    if len(df) > 0:
        sample = {k: str(v)[:30] for k, v in dict(df.iloc[0]).items()}
        lines.append("  " + str(sample))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Specialized Data Analysis Engines (Hypothesis Testing & AutoML)
# ---------------------------------------------------------------------------

def _run_hypothesis_test_engine(query: str, csv_path: str) -> Optional[dict]:
    """Runs scipy statistical hypothesis tests (Pearson, Spearman, Chi-Square, ANOVA, Normality)."""
    q_lower = query.lower()
    if not any(k in q_lower for k in ("hypothesis", "p-value", "significance", "pearson", "spearman", "chi-square", "anova", "normality", "t-test")):
        return None

    try:
        import scipy.stats as stats
        df = read_csv_robust(csv_path)
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

        results_md = []
        results_md.append("### 🧪 **Statistical Hypothesis & Significance Test Report**\n")

        if len(num_cols) >= 2:
            c1, c2 = num_cols[0], num_cols[1]
            p_corr, p_val = stats.pearsonr(df[c1].dropna(), df[c2].dropna())
            sig_text = "Statistically Significant ($p < 0.05$)" if p_val < 0.05 else "Not Statistically Significant ($p \\ge 0.05$)"
            results_md.append(f"#### **1. Pearson Correlation Test ({c1} vs {c2})**")
            results_md.append(f"| Metric | Calculated Value |")
            results_md.append(f"| :--- | :--- |")
            results_md.append(f"| **Pearson $r$ Coefficient** | `{p_corr:.4f}` |")
            results_md.append(f"| **$P$-Value** | `{p_val:.4e}` |")
            results_md.append(f"| **Conclusion** | **{sig_text}** |")

            sample_data = df[c1].dropna().head(100)
            shapiro_stat, shapiro_p = stats.shapiro(sample_data)
            norm_text = "Normal Distribution" if shapiro_p > 0.05 else "Non-Normal Distribution"
            results_md.append(f"\n#### **2. Shapiro-Wilk Normality Test ({c1})**")
            results_md.append(f"- **Test Statistic ($W$)**: `{shapiro_stat:.4f}`")
            results_md.append(f"- **$P$-Value**: `{shapiro_p:.4f}` $\\rightarrow$ **{norm_text}**")

        if cat_cols and num_cols:
            cat_col = cat_cols[0]
            num_col = num_cols[0]
            groups = [group[num_col].dropna().values for _, group in df.groupby(cat_col) if len(group) > 2]
            if len(groups) >= 2:
                f_stat, f_p = stats.f_oneway(*groups[:5])
                anova_sig = "Significant Group Variance ($p < 0.05$)" if f_p < 0.05 else "No Significant Group Variance"
                results_md.append(f"\n#### **3. One-Way ANOVA Test ({num_col} across {cat_col})**")
                results_md.append(f"- **$F$-Statistic**: `{f_stat:.4f}`")
                results_md.append(f"- **$P$-Value**: `{f_p:.4e}` $\\rightarrow$ **{anova_sig}**")

        return {
            "success": True,
            "text": "\n".join(results_md),
            "plot_path": None
        }
    except Exception as e:
        print(f"Hypothesis engine fallback to code generator: {e}")
        return None

def _run_automl_engine(query: str, csv_path: str, output_dir: Path) -> Optional[dict]:
    """Trains a Scikit-Learn predictive model and generates feature importance charts."""
    q_lower = query.lower()
    if not any(k in q_lower for k in ("predict", "automl", "model", "feature importance", "classify", "train")):
        return None

    try:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import train_test_split
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        df = read_csv_robust(csv_path)
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        
        if len(num_cols) < 2:
            return None

        target_col = num_cols[-1]
        feature_cols = [c for c in num_cols if c != target_col][:6]

        if not feature_cols:
            return None

        X = df[feature_cols].fillna(df[feature_cols].median())
        y = df[target_col].fillna(df[target_col].median())

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        score = model.score(X_test, y_test)

        importances = model.feature_importances_
        feat_df = pd.DataFrame({"Feature": feature_cols, "Importance": importances}).sort_values("Importance", ascending=True)

        plot_path = output_dir / f"automl_importance_{_uuid_short()}.png"
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.barh(feat_df["Feature"], feat_df["Importance"], color="#7c3aed")
        ax.set_title(f"Feature Importance Ranking for Target: '{target_col}'", fontsize=11, fontweight="bold", pad=12)
        ax.set_xlabel("Relative Importance Score", fontsize=9)
        plt.tight_layout()
        plt.savefig(str(plot_path), dpi=150)
        plt.close()

        res_md = [
            f"### 🤖 **AutoML Predictive Model & Feature Importance Report**",
            f"- **Target Predictor Variable**: `{target_col}`",
            f"- **Algorithm**: `RandomForestRegressor (n_estimators=50)`",
            f"- **Model $R^2$ Variance Score**: `{score:.4f}` ({score*100:.1f}% explained variance)",
            f"\n#### **Feature Importance Ranking Table**",
            f"| Feature Name | Importance Weight | Rank |",
            f"| :--- | :--- | :--- |"
        ]
        for rank, (_, r) in enumerate(feat_df.iloc[::-1].iterrows(), 1):
            res_md.append(f"| `{r['Feature']}` | `{r['Importance']:.4f}` | **#{rank}** |")

        return {
            "success": True,
            "text": "\n".join(res_md),
            "plot_path": str(plot_path) if plot_path.exists() else None
        }
    except Exception as e:
        print(f"AutoML engine fallback to code generator: {e}")
        return None

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

    # Check for specialized Data Analysis Engines (Hypothesis Testing & AutoML)
    hypo_res = _run_hypothesis_test_engine(query, csv_path)
    if hypo_res:
        return hypo_res

    automl_res = _run_automl_engine(query, csv_path, output_dir)
    if automl_res:
        return automl_res

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
      FILE_PATH = '{Path(csv_path).as_posix()}'

    === DATASET SCHEMA ===
    {column_context}
    =====================

    USER QUERY: "{query}"

    INSTRUCTIONS:
    1. Read the dataset: df = pd.read_csv(FILE_PATH)
    2. Use ONLY the column names listed in the dataset schema (exact spelling, case-sensitive).
    3. Perform any required analysis, aggregation, computation, or modifications.
    4. Print a clear, detailed, and nicely formatted answer to stdout detailing the results or actions taken.
       - Use rich Markdown formatting (e.g. Markdown tables, bulleted lists, bold text, headers) to structure the output like a professional report.
       - If the user asks for a table or for N values, print a Markdown table.
    5. If the query asks to modify, clean, fix, rename, delete columns, drop rows, replace missing values, or update values in the dataset:
       - Perform the operation on the DataFrame `df`.
       - Save the modified DataFrame back to the CSV file at the end of the script: `df.to_csv(FILE_PATH, index=False)`.
       - Print a confirmation message to stdout using Markdown (e.g., bulleted list) explaining exactly what dataset modifications were made.
    6. IF THE QUERY ASKS FOR A CHART/VISUALIZATION/GRAPH:
       - You have full capability to generate ANY type of visualization requested by the user:
         distribution histograms, box/violin plots, scatter plots, correlation heatmaps, stacked/grouped bar charts, time-series line plots, pie/donut charts, pair plots, subplots, 3D scatter plots, radar charts, and custom color themes.
       - Always include at the top of your code:
         ```python
         import matplotlib
         matplotlib.use('Agg')
         import matplotlib.pyplot as plt
         import seaborn as sns
         import numpy as np
         ```
       - Create a visually stunning, professional visualization with a clear title, custom color palette, grid lines, and properly labeled axes.
       - Save the figure to: `plt.savefig('{plot_path.as_posix()}', dpi=150, bbox_inches='tight')`
       - Clean up memory with: `plt.close('all')`
       - CRITICAL OUTPUT RULE: When generating a visualization, print ONLY 1 short concise sentence introducing the chart (e.g., `print("Generated distribution histogram for column X.")`). Do NOT print long bullet points or unasked dataset summary notes alongside the plot.

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

        # 6. Execute in sandboxed subprocess with Auto-Healing Loop (up to 2 retry attempts)
        success, exec_output = _run_in_subprocess(code)
        auto_healed = False

        max_heals = 2
        heal_count = 0

        while not success and heal_count < max_heals:
            heal_count += 1
            print(f"[AI Chat Auto-Heal] Code execution failed (Attempt {heal_count}/{max_heals}). Auto-fixing code...")
            
            heal_prompt = textwrap.dedent(f"""
            The previous Python code generated for the user query produced a runtime execution error.

            USER QUERY: "{query}"
            
            FAILED CODE:
            ```python
            {code}
            ```

            EXECUTION ERROR TRACE:
            ```
            {exec_output}
            ```

            === DATASET SCHEMA ===
            {column_context}
            =====================

            INSTRUCTIONS TO FIX:
            1. Analyze the execution error trace (e.g. KeyError, NameError, SyntaxError, AttributeError).
            2. Correct the code to use exact column names from the dataset schema.
            3. Ensure all required imports (pandas, matplotlib, seaborn, plotly) are included.
            4. Return ONLY the corrected, self-contained Python code inside a ```python ... ``` block.
            """).strip()

            try:
                heal_res = llm.call([{"role": "user", "content": heal_prompt}])
                heal_raw = heal_res if isinstance(heal_res, str) else str(heal_res)
                healed_code = _strip_markdown_fences(heal_raw)
                if healed_code.strip():
                    code = healed_code
                    success, exec_output = _run_in_subprocess(code)
                    if success:
                        auto_healed = True
                        break
            except Exception as heal_err:
                print(f"[AI Chat Auto-Heal] Failed during heal attempt {heal_count}: {heal_err}")

        plot_saved      = plot_path.exists() and plot_path.stat().st_size > 0
        final_plot_path = str(plot_path) if plot_saved else None

        if success:
            answer_text = exec_output.strip() if exec_output.strip() not in ("", "(no output)") \
                          else "Query executed successfully (no text output)."
            if auto_healed:
                answer_text = f"✨ **[AI Chat Auto-Healed]** *Code fixed automatically after resolving runtime execution error.*\n\n{answer_text}"
            return {"success": True, "text": answer_text, "plot_path": final_plot_path}
        else:
            return {
                "success": False,
                "text": f"⚠️ **Execution error after auto-healing attempts:**\n```\n{exec_output}\n```",
                "plot_path": None,
            }

    except Exception as exc:
        return {
            "success": False,
            "text": f"Copilot error: {exc}",
            "plot_path": None,
        }


def _generate_suggestions(query: str, csv_path: str) -> list[str]:
    """Generates 3 contextual next-step suggestion prompt chips based on dataset columns."""
    try:
        df = read_csv_robust(csv_path, nrows=5)
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
        
        suggestions = []
        if num_cols and cat_cols:
            suggestions.append(f"📊 Breakdown {num_cols[0]} by {cat_cols[0]}")
        elif len(num_cols) >= 2:
            suggestions.append(f"📈 Scatter plot of {num_cols[0]} vs {num_cols[1]}")
        else:
            suggestions.append("📈 Plot top correlation trends")
            
        if num_cols:
            suggestions.append(f"⚠️ Check for outliers in {num_cols[0]}")
        else:
            suggestions.append("🔍 Show summary of null/missing values")
            
        suggestions.append("💼 Summarize 3 key executive takeaways")
        return suggestions[:3]
    except Exception:
        return ["📊 Breakdown top metrics", "⚠️ Check for data outliers", "💼 Summarize executive takeaways"]


def stream_copilot_query(
    query: str,
    session_id: str,
    provider: str,
    model: str,
    api_key: Optional[str] = None,
    env_key_name: Optional[str] = None,
    csv_path: Optional[str] = None,
    output_dir: Optional[str] = None,
):
    """
    Generator yielding Server-Sent Events (SSE) for real-time dataset analysis streaming,
    live reasoning thought badges, and dynamic chart rendering.
    """
    import json
    import time

    def sse(event_type: str, data: dict) -> str:
        payload = {"type": event_type, **data}
        return f"data: {json.dumps(payload)}\n\n"

    # Step 1: Yield reasoning phase
    yield sse("thought", {"text": "Thinking..."})

    if not csv_path or not Path(csv_path).exists():
        yield sse("token", {"text": "Error: Session dataset file not found."})
        yield sse("done", {})
        return

    # Check hypothesis engine first
    hypo = _run_hypothesis_test_engine(query, csv_path)
    if hypo and hypo.get("text"):
        for line in hypo["text"].split("\n"):
            yield sse("token", {"text": line + "\n"})
        suggestions = _generate_suggestions(query, csv_path)
        yield sse("suggestions", {"items": suggestions})
        yield sse("done", {})
        return

    # Step 2: Processing dataset with Python code engine
    yield sse("thought", {"text": "Thinking..."})

    # Execute standard copilot dataset query engine (Correct 3-argument signature)
    res = run_copilot_query(
        query=query,
        csv_path=csv_path,
        output_dir_str=output_dir
    )

    text_content = res.get("text", "")

    lines = text_content.split("\n")
    for idx, line in enumerate(lines):
        yield sse("token", {"text": line + ("\n" if idx < len(lines) - 1 else "")})

    if res.get("plot_path"):
        plot_name = Path(res["plot_path"]).name
        import urllib.parse
        plot_url = f"/api/charts/{session_id}/{urllib.parse.quote(plot_name)}"
        yield sse("chart", {"plot_url": plot_url})

    # Step 3: Yield smart contextual suggestion chips
    suggestions = _generate_suggestions(query, csv_path)
    yield sse("suggestions", {"items": suggestions})

    yield sse("done", {})


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
