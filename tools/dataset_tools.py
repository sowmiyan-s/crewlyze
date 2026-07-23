# Crewlyze
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
from typing import Optional
from crewai.tools import tool



# ---------------------------------------------------------------------------
# Robust CSV Reader Helper
# ---------------------------------------------------------------------------

def read_csv_robust(file_path: str, **kwargs) -> pd.DataFrame:
    """Read a CSV file robustly, handling encoding and tokenization (bad lines) errors.
    
    If standard parsing fails, it falls back to skipping bad lines and prints
    a warning to stdout so it appears in the user-facing logs.
    """
    encodings = ['utf-8', 'latin1', 'utf-8-sig', 'cp1252']
    
    # Try normal reading first with different encodings
    for encoding in encodings:
        try:
            return pd.read_csv(file_path, encoding=encoding, **kwargs)
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                raise e
            continue
            
    # If standard reading fails, try skipping bad lines
    print(f"[Warning] Encountered formatting issues reading {file_path}. Attempting to parse by skipping malformed lines...", file=sys.stdout)
    sys.stdout.flush()
    for encoding in encodings:
        try:
            return pd.read_csv(file_path, encoding=encoding, on_bad_lines='skip', **kwargs)
        except Exception:
            continue
            
    # If all fails, run one final time to let the error bubble up
    return pd.read_csv(file_path, **kwargs)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _strip_markdown_fences(code: str) -> str:
    """Remove leading/trailing markdown code fences from LLM output."""
    # Find any python code blocks: ```python ... ```
    match = re.search(r"```(?:python)?\s*(.*?)\s*```", code, re.DOTALL | re.IGNORECASE)
    if match:
        code = match.group(1)
    else:
        code = code.strip()
        code = re.sub(r"^```(?:python)?\s*\n?", "", code)
        code = re.sub(r"\n?```\s*$", "", code)
    
    import textwrap
    return textwrap.dedent(code).strip()


def _df_to_markdown(df: "pd.DataFrame", index: bool = True) -> str:
    """Convert a pandas DataFrame to a compact GitHub-style markdown table.

    Pure Python fallback — avoids the optional ``tabulate`` dependency.
    Numeric cells are right-aligned; all others are left-aligned.

    Args:
        df    : DataFrame to render.
        index : If True, include the DataFrame index as the first column.

    Returns:
        A multi-line markdown string.
    """
    import pandas as pd

    if df is None or df.empty:
        return "*(empty)*"

    df_display = df.reset_index() if index else df.copy()

    headers = [str(h) for h in list(df_display.columns)]
    rows = []
    for row in df_display.values.tolist():
        formatted_row = []
        for cell in row:
            if cell is None or pd.isna(cell):
                formatted_row.append("")
            else:
                val_str = str(cell)
                if len(val_str) > 50:
                    val_str = val_str[:47] + "..."
                formatted_row.append(val_str)
        rows.append(formatted_row)

    # Column widths — at least as wide as the header
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    def _row_str(cells: list, widths: list) -> str:
        parts = []
        for cell, w in zip(cells, widths):
            parts.append(cell.ljust(w))
        return "| " + " | ".join(parts) + " |"

    sep_parts = ["-" * w for w in col_widths]
    separator = "|" + "|".join(f"-{s}-" for s in sep_parts) + "|"

    lines = [_row_str(headers, col_widths), separator]
    for row in rows:
        lines.append(_row_str(row, col_widths))

    return "\n".join(lines)


def _heal_script_code(script: str, error_output: str) -> str:
    """Use the configured LLM to self-heal/correct a failing python script."""
    try:
        from crewai import LLM
        from config.llm_config import get_llm_params
        
        # Get LLM instance
        llm = LLM(**get_llm_params())
        
        prompt = f"""You are a senior python debugger.
The following python script failed during execution with an error/traceback.

--- FAIL SCRIPT ---
{script}

--- ERROR OUTPUT ---
{error_output}

Task:
Analyze the error carefully. Identify why it failed (e.g., missing imports, undefined variables, incorrect pandas api calls, type mismatches).
Rewrite the script to fix this error, ensuring you preserve the original logic and functional goal.
Do NOT omit the imports, variables, or functions that are set up.
For visualization scripts, make sure 'save_chart(filename)' is called correctly.
For data cleaning scripts, make sure 'df.to_csv(FILE_PATH, index=False)' is kept at the end.

Format:
Return ONLY the corrected, ready-to-run python script inside a markdown python block:
```python
# corrected code here
```
Do not include any other explanations, intros, or markdown outside the code block.
"""
        # Call LLM
        response = llm.call([{"role": "user", "content": prompt}])
        corrected_code = _strip_markdown_fences(response)
        return corrected_code
    except Exception as e:
        # If healing fails, return original script
        print(f"Self-healing error: {e}")
        return script


def _run_in_subprocess(script: str, timeout: int = 120, is_healed_attempt: bool = False) -> tuple[bool, str]:
    """
    Write *script* to a temp file and execute it in an isolated subprocess.
    Includes auto-dependency healing to download missing packages if needed.
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
        
        # If execution failed and we haven't already tried to self-heal:
        if not success and not is_healed_attempt:
            # 1. Package dependency healing (ModuleNotFoundError)
            match_module = re.search(r"ModuleNotFoundError:\s*No module named\s*['\"]([^'\"]+)['\"]", output)
            if match_module:
                module_name = match_module.group(1)
                print(f"\n[Auto-Healing System] Missing module '{module_name}'. Attempting pip install...\n")
                sys.stdout.flush()
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", module_name], capture_output=True)
                    # Retry execution after package install
                    success_pkg, output_pkg = _run_in_subprocess(script, timeout=timeout, is_healed_attempt=True)
                    if success_pkg:
                        print(f"[Auto-Healing System] Installed '{module_name}' and executed successfully!")
                        sys.stdout.flush()
                        return True, f"[Auto-Healing system installed missing package '{module_name}']\n\nOutput:\n{output_pkg}"
                except Exception as pkg_err:
                    print(f"[Auto-Healing System] Failed to install package: {pkg_err}")
                    sys.stdout.flush()

            # 2. Logic/Code healing (LLM repair)
            print(f"\n[Auto-Healing System] Executing python script failed with error. Attempting self-healing...\nError details:\n{output}\n")
            sys.stdout.flush()
            healed_script = _heal_script_code(script, output)
            if healed_script and healed_script != script:
                success_h, output_h = _run_in_subprocess(healed_script, timeout=timeout, is_healed_attempt=True)
                if success_h:
                    print("[Auto-Healing System] Code repaired and executed successfully!")
                    sys.stdout.flush()
                    return True, f"[Auto-Healing system resolved a code error!]\nOriginal Error:\n{output}\n\nSuccessful Execution Output:\n{output_h}"
                else:
                    print("[Auto-Healing System] Attempted repair but healed script still failed.")
                    sys.stdout.flush()
                    
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

def _mask_pii_column(col_name: str) -> str:
    """Detect potential PII columns to redact them from LLM context."""
    sensitive = ["email", "ssn", "password", "credit", "card", "phone", "address", "name"]
    if any(s in col_name.lower() for s in sensitive):
        return f"{col_name} [PII_MASKED]"
    return col_name

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
        try:
            import duckdb
            total_rows = duckdb.execute("SELECT COUNT(*) FROM read_csv_auto(?)", [csv_path]).fetchone()[0]
            df = duckdb.execute("SELECT * FROM read_csv_auto(?) LIMIT ?", [csv_path, max_rows]).df()
            sampled = total_rows
        except Exception:
            df = read_csv_robust(csv_path, nrows=max_rows)
            sampled = len(df)
    except Exception as exc:
        return f"[Profile unavailable: {exc}]"

    lines: list[str] = []

    # Shape
    note = " (sample — file is larger)" if sampled > max_rows else ""
    lines.append(
        f"**Dataset shape**: {sampled} rows × {len(df.columns)} columns{note}"
    )
    lines.append("")

    # Column summary
    lines.append("**Columns** (name | dtype | missing% | stats/top values):")
    for col in df.columns:
        masked_col = _mask_pii_column(col)
        dtype    = df[col].dtype
        miss_pct = round(df[col].isnull().sum() / max(len(df), 1) * 100, 1)
        
        if "[PII_MASKED]" in masked_col:
            desc = "[SENSITIVE DATA REDACTED]"
        elif pd.api.types.is_numeric_dtype(dtype):
            desc = (
                f"min={df[col].min():.4g}, "
                f"mean={df[col].mean():.4g}, "
                f"max={df[col].max():.4g}"
            )
        else:
            tops = df[col].dropna().value_counts().head(3).index.tolist()
            desc = ", ".join(str(v) for v in tops) or "—"
        lines.append(f"  - {masked_col}: {dtype} | missing={miss_pct}% | {desc}")
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
    sample_cols = df.columns[:12].tolist()
    note_cols = f" (first 12 of {len(df.columns)} columns)" if len(df.columns) > 12 else ""
    lines.append(f"**Sample rows (first 5 rows){note_cols}**:")
    lines.append(_df_to_markdown(df[sample_cols].head(5), index=False))
    if len(df.columns) > 12:
        lines.append(f"*(Note: only the first 12 columns are shown in this preview to conserve token limits)*")

    return "\n".join(lines)


def generate_plotly_charts(csv_path: str, relations_text: str, max_rows: int = 5000, output_dir: str = "") -> list:
    """Parse agent relation output and generate interactive Plotly figures.

    Replaces static matplotlib PNGs with zoomable, hoverable charts rendered
    natively by st.plotly_chart(). No LLM calls, no subprocess, no file I/O.

    Args:
        csv_path       : Path to the cleaned CSV file.
        relations_text : Raw text output from the relation agent.
        max_rows       : Row cap for chart data (default 5000 for rendering speed).
        output_dir     : Directory where PNG snapshots are saved for PDF embedding.

    Returns:
        List of dicts: [{"title": str, "fig": plotly.graph_objs.Figure}, ...]
        Returns an empty list if plotly is unavailable or no valid relations found.
    """
    try:
        import plotly.express as px
    except ImportError:
        return []

    try:
        df = read_csv_robust(csv_path, nrows=max_rows)
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
            ptype = parts[2].split(":", 1)[1].strip().lower() if len(parts) > 2 else "scatter"
        except (IndexError, ValueError):
            continue

        if x_col not in df.columns or y_col not in df.columns:
            continue

        # Guard: skip trivial same-column pairs
        if x_col == y_col:
            continue

        def clean_label(s: str) -> str:
            return s.replace("_", " ").replace("-", " ").title()
            
        clean_x = clean_label(x_col)
        clean_y = clean_label(y_col)
        title = f"{clean_x} vs {clean_y}"
        color = _colors[len(figures) % len(_colors)]
        
        # We define labels for all px charts
        lbls = {x_col: clean_x, y_col: clean_y}

        try:
            sample = df[[x_col, y_col]].dropna().head(2000)

            if sample.empty:
                continue

            if "scatter" in ptype or "plot" in ptype:
                fig = px.scatter(
                    sample, x=x_col, y=y_col, title=title,
                    color_discrete_sequence=[color], opacity=0.75,
                    labels=lbls
                )
                fig.update_traces(marker=dict(size=6, line=dict(width=0.5, color="rgba(255,255,255,0.3)")))
            elif "bar" in ptype:
                if pd.api.types.is_numeric_dtype(df[x_col]):
                    # numeric x → bin it, then aggregate
                    agg = sample.groupby(x_col)[y_col].mean().reset_index()
                else:
                    agg = sample.groupby(x_col)[y_col].mean().reset_index()
                fig = px.bar(
                    agg.head(25), x=x_col, y=y_col, title=title,
                    color_discrete_sequence=[color], labels=lbls
                )
            elif "line" in ptype:
                fig = px.line(
                    sample.sort_values(x_col), x=x_col, y=y_col, title=title,
                    color_discrete_sequence=[color], labels=lbls
                )
            elif "box" in ptype:
                fig = px.box(
                    sample, x=x_col if not pd.api.types.is_numeric_dtype(df[x_col]) else None,
                    y=y_col, title=title,
                    color_discrete_sequence=[color], labels=lbls
                )
            elif "hist" in ptype:
                fig = px.histogram(
                    sample, x=x_col, nbins=30,
                    title=f"Distribution of {clean_x}",
                    color_discrete_sequence=[color], labels=lbls
                )
            else:
                # Default: scatter
                fig = px.scatter(
                    sample, x=x_col, y=y_col, title=title,
                    color_discrete_sequence=[color], opacity=0.75, labels=lbls
                )
                
            # Center title
            fig.update_layout(title_x=0.5)

            fig.update_layout(**_dark)
            figures.append({"title": title, "fig": fig, "x": x_col, "y": y_col, "type": ptype})
            
            # Export to PNG for PDF (white theme)
            if output_dir:
                try:
                    import copy
                    fig_white = copy.deepcopy(fig)
                    fig_white.update_layout(template="plotly_white", paper_bgcolor="white", plot_bgcolor="white", font=dict(color="black"))
                    png_path = os.path.join(output_dir, f"plotly_{x_col}_vs_{y_col}.png".replace("/", "_"))
                    fig_white.write_image(png_path, width=800, height=500)
                except Exception as e:
                    print(f"[Plotly] Could not save PNG for {title}: {e}")

        except Exception as _chart_err:  # log but continue
            print(f"[Plotly] Skipping {title!r}: {_chart_err}")
            continue

    # Fallback: if no relation lines were parseable, auto-generate charts
    # from the first few numeric column pairs in the dataset.
    if not figures:
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        cat_cols     = df.select_dtypes(include=["object", "category"]).columns.tolist()

        pair_count = 0
        for i, col in enumerate(numeric_cols[:3]):
            color = _colors[i % len(_colors)]
            # Histogram for each numeric col
            try:
                fig = px.histogram(df[[col]].dropna().head(3000), x=col,
                                   nbins=30, title=f"Distribution of {col}",
                                   color_discrete_sequence=[color])
                fig.update_layout(**_dark)
                figures.append({"title": f"Distribution of {col}", "fig": fig, "x": col, "y": col, "type": "histogram"})
                pair_count += 1
            except Exception:
                continue

        # Scatter for first 2 numeric pairs
        for i in range(min(len(numeric_cols) - 1, 2)):
            xc, yc = numeric_cols[i], numeric_cols[i + 1]
            color = _colors[(pair_count + i) % len(_colors)]
            try:
                sample = df[[xc, yc]].dropna().head(2000)
                fig = px.scatter(sample, x=xc, y=yc, title=f"{xc} vs {yc}",
                                 color_discrete_sequence=[color], opacity=0.75)
                fig.update_layout(**_dark)
                figures.append({"title": f"{xc} vs {yc}", "fig": fig, "x": xc, "y": yc, "type": "scatter"})
            except Exception:
                continue

        # Bar for first categorical × numeric
        if cat_cols and numeric_cols:
            cc, nc = cat_cols[0], numeric_cols[0]
            try:
                agg = df[[cc, nc]].dropna().groupby(cc)[nc].mean().reset_index()
                fig = px.bar(agg.head(20), x=cc, y=nc, title=f"{nc} by {cc}",
                             color_discrete_sequence=[_colors[0]])
                fig.update_layout(**_dark)
                figures.append({"title": f"{nc} by {cc}", "fig": fig, "x": cc, "y": nc, "type": "bar"})
            except Exception:
                pass

    return figures


# ---------------------------------------------------------------------------
# CrewAI tools — used by agents at runtime as fallback / code generation aid
# ---------------------------------------------------------------------------

class DatasetTools:

    @tool("Read Dataset Head")
    def read_dataset_head(file_path: Optional[str] = None) -> str:
        """Reads the first 10 rows of the dataset to understand its structure.
        Uses nrows=10 so the entire file is never loaded into memory.
        If file_path is not specified or is invalid, the active session's CSV will be used.
        """
        try:
            from config.context import current_session_csv
            fp = file_path
            if not fp or not isinstance(fp, str) or fp.lower() == "none" or "properties" in str(fp):
                fp = current_session_csv.get() or os.getenv("CURRENT_SESSION_CSV", "")
            df = read_csv_robust(fp, nrows=10)
            return _df_to_markdown(df, index=False)
        except Exception as e:
            return f"Error reading file: {e}"

    @tool("Get Dataset Info")
    def get_dataset_info(file_path: Optional[str] = None) -> str:
        """Returns basic information about the dataset: shape, columns, data types,
        and missing-value counts.
        If file_path is not specified or is invalid, the active session's CSV will be used.
        """
        try:
            from config.context import current_session_csv
            fp = file_path
            if not fp or not isinstance(fp, str) or fp.lower() == "none" or "properties" in str(fp):
                fp = current_session_csv.get() or os.getenv("CURRENT_SESSION_CSV", "")
            df = read_csv_robust(fp)
            lines = [f"Shape: {df.shape}", "\nColumns and Types:"]
            for col, dtype in df.dtypes.items():
                missing = df[col].isnull().sum()
                lines.append(f"  - {col}: {dtype} (Missing: {missing})")
            return "\n".join(lines)
        except Exception as e:
            return f"Error analyzing file: {e}"

    @tool("Get Correlation Matrix")
    def get_correlation_matrix(file_path: Optional[str] = None) -> str:
        """Returns the top-20 strongest column-pair correlations (by absolute value).
        If file_path is not specified or is invalid, the active session's CSV will be used.
        """
        try:
            from config.context import current_session_csv
            fp = file_path
            if not fp or not isinstance(fp, str) or fp.lower() == "none" or "properties" in str(fp):
                fp = current_session_csv.get() or os.getenv("CURRENT_SESSION_CSV", "")
            df = read_csv_robust(fp)
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
            return _df_to_markdown(top, index=False)
        except Exception as e:
            return f"Error calculating correlation: {e}"

    @tool("Clean Dataset with Python Code")
    def clean_dataset_with_python(file_path: Optional[str] = None, python_code: Optional[str] = None) -> str:
        """Cleans the dataset by executing *python_code* in an isolated subprocess.
        The file_path parameter is optional and defaults to the active session's dataset CSV.

        Your code must:
          1. Read the CSV:  df = pd.read_csv(FILE_PATH)   # FILE_PATH is pre-set
          2. Perform cleaning on df
          3. Save:          df.to_csv(FILE_PATH, index=False)

        Do NOT include markdown code fences. Do NOT use any other file paths.
        """
        # Swap if python_code is not specified but file_path contains code
        if not python_code:
            if file_path and ("import " in file_path or "df[" in file_path or "\n" in file_path):
                python_code = file_path
                file_path = None
            else:
                return "Error: python_code is required."

        from config.context import current_session_csv
        fp = file_path
        if not fp or not isinstance(fp, str) or fp.lower() == "none" or "properties" in str(fp):
            fp = current_session_csv.get() or os.getenv("CURRENT_SESSION_CSV", "")

        clean_code = _strip_markdown_fences(python_code)

        script = textwrap.dedent(f"""\
            import os
            import pandas as pd

            FILE_PATH = {repr(str(fp))}
            df = pd.read_csv(FILE_PATH)

            # Safeguard: redirect all read_csv calls to FILE_PATH
            _orig_read_csv = pd.read_csv
            def custom_read_csv(*args, **kwargs):
                return _orig_read_csv(FILE_PATH)
            pd.read_csv = custom_read_csv
        """) + "\n" + clean_code + "\n" + textwrap.dedent(f"""\
            df.to_csv(FILE_PATH, index=False)
            print("Dataset cleaned and saved successfully.")
        """)

        success, output = _run_in_subprocess(script)
        if success:
            return f"Dataset cleaned successfully.\n{output}"
        return f"Error executing cleaning code:\n{output}"

    @tool("Execute Visualization Code")
    def execute_visualization_code(python_code: Optional[str] = None, **kwargs) -> str:
        """Executes Python plotting code to generate and save PNG visual charts.

        The code runs in a pre-configured Python environment where:
          - 'df' is a pre-loaded pandas DataFrame containing the cleaned dataset.
          - 'OUTPUT_DIR' is a pre-defined string representing the output folder path.
          - 'save_chart(filename)' is a helper function to save the current plot into OUTPUT_DIR.
          - Libraries 'pandas', 'matplotlib.pyplot as plt', and 'seaborn as sns' are already imported.

        Example usage:
          plt.figure(figsize=(10, 6))
          sns.scatterplot(data=df, x='column_x', y='column_y')
          plt.title('Relationship Title')
          save_chart('chart_name.png')
          plt.close()
        """
        if not python_code:
            for k, v in kwargs.items():
                if v and isinstance(v, str) and ("plt." in v or "sns." in v or "import " in v or "\n" in v):
                    python_code = v
                    break
            if not python_code:
                return "Error: python_code is required."

        clean_code = _strip_markdown_fences(python_code)
        from config.context import current_session_csv, current_session_output_dir
        csv_path = current_session_csv.get() or os.getenv("CURRENT_SESSION_CSV", "")
        output_dir = current_session_output_dir.get() or os.getenv("CURRENT_SESSION_OUTPUT_DIR", "")

        # Fallbacks if env vars are missing
        if not csv_path:
            csv_path = "data/sessions/default/cleaned.csv"
        if not output_dir:
            output_dir = "outputs/default"

        script = textwrap.dedent(f"""\
            import os
            import pandas as pd
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import seaborn as sns
            import textwrap

            CSV_PATH = {repr(csv_path)}
            OUTPUT_DIR = {repr(output_dir)}

            os.makedirs(OUTPUT_DIR, exist_ok=True)
            df = pd.read_csv(CSV_PATH)

            # Safeguard: redirect all read_csv calls to the cleaned CSV path
            _orig_read_csv = pd.read_csv
            def custom_read_csv(*args, **kwargs):
                return _orig_read_csv(CSV_PATH)
            pd.read_csv = custom_read_csv

            def save_chart(filename):
                if not filename.endswith('.png'):
                    filename += '.png'
                path = os.path.join(OUTPUT_DIR, filename)
                plt.savefig(path, bbox_inches='tight', dpi=180)
                print(f"Saved chart: {{filename}}")
        """) + "\n" + clean_code

        success, output = _run_in_subprocess(script)
        if success:
            return f"Visualization executed successfully. Output:\n{output}"
        return f"Error executing visualization code:\n{output}"

    @tool("Run Python Script")
    def run_python_script(python_code: Optional[str] = None, **kwargs) -> str:
        """Executes arbitrary Python code in a sandboxed subprocess for data analysis tasks.

        The code runs in a pre-configured environment where:
          - 'df' is a pre-loaded pandas DataFrame containing the cleaned dataset.
          - 'FILE_PATH' is the path to the active session's CSV file.
          - Libraries 'pandas', 'numpy', and 'sklearn' are available.

        Use this tool to:
          - Train machine-learning models (e.g. RandomForest) for feature importance.
          - Compute advanced statistics or aggregations.
          - Any general-purpose Python data analysis that isn't visualization.

        Return your results via print() statements.
        """
        if not python_code:
            for k, v in kwargs.items():
                if v and isinstance(v, str) and ("import " in v or "df[" in v or "\n" in v):
                    python_code = v
                    break
            if not python_code:
                return "Error: python_code is required."

        clean_code = _strip_markdown_fences(python_code)
        from config.context import current_session_csv
        csv_path = current_session_csv.get() or os.getenv("CURRENT_SESSION_CSV", "")

        if not csv_path:
            csv_path = "data/sessions/default/cleaned.csv"

        script = textwrap.dedent(f"""\
            import os
            import pandas as pd
            import numpy as np

            FILE_PATH = {repr(csv_path)}
            df = pd.read_csv(FILE_PATH)

            # Safeguard: redirect all read_csv calls to the session CSV
            _orig_read_csv = pd.read_csv
            def custom_read_csv(*args, **kwargs):
                return _orig_read_csv(FILE_PATH)
            pd.read_csv = custom_read_csv
        """) + "\n" + clean_code

        success, output = _run_in_subprocess(script, timeout=180)
        if success:
            return f"Script executed successfully. Output:\n{output}"
        return f"Error executing script:\n{output}"


def auto_coerce_types(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Analyze columns in the DataFrame, detect type mismatches/conflicts,
    and convert them to their appropriate types (e.g., object to numeric or datetime).
    Returns (converted_df, list_of_actions).
    """
    actions = []
    df = df.copy()
    
    for col in df.columns:
        # Skip empty columns
        if df[col].isnull().all():
            continue
            
        dtype = df[col].dtype
        
        # We only need to coerce object/string columns
        if dtype == 'object':
            sample_non_null = df[col].dropna().head(200).astype(str)
            if sample_non_null.empty:
                continue
                
            # 1. Heuristic for Date: check if strings contain date patterns
            date_like_count = 0
            for val in sample_non_null:
                val_clean = val.strip()
                # Skip 4-digit years (e.g. 1990) to prevent converting them to date objects
                if val_clean.isdigit() and len(val_clean) == 4:
                    continue
                # matches YYYY-MM-DD, DD/MM/YYYY, or wordy dates like "01 Jul 2026"
                if re.match(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}', val_clean) or \
                   re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{4}', val_clean) or \
                   re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', val_clean, re.IGNORECASE):
                    date_like_count += 1
            
            if date_like_count > len(sample_non_null) * 0.5:
                try:
                    try:
                        converted = pd.to_datetime(df[col], errors='coerce', format='mixed')
                    except (ValueError, TypeError):
                        converted = pd.to_datetime(df[col], errors='coerce')
                    # If conversion didn't result in all NaTs
                    if not converted.isnull().all() and converted.notnull().sum() > len(df[col].dropna()) * 0.7:
                        df[col] = converted
                        actions.append(f"Converted column '{col}' to Datetime (detected date-like patterns)")
                        continue
                except Exception:
                    pass

            # 2. Heuristic for Numeric: check if it could be a numeric column stored as string
            # (e.g., currency "$1,000", percentage "95%", or numbers with commas/spaces/missing placeholders)
            numeric_like_count = 0
            for val in sample_non_null:
                val_clean = val.strip().lower()
                if not val_clean or val_clean in {'nan', 'null', 'n/a', 'na', '?', 'none', '-', '.', 'missing', 'empty'}:
                    numeric_like_count += 1
                    continue
                # Clean currency symbols, percentage signs, commas, and whitespace
                cleaned_val = re.sub(r'[\$,%\s]', '', val_clean).replace(',', '')
                if re.match(r'^-?\d+(?:\.\d+)?$', cleaned_val):
                    numeric_like_count += 1
                    
            if numeric_like_count > len(sample_non_null) * 0.8:
                try:
                    # Clean currency symbols, commas, percent signs, and spaces
                    # Replace common string placeholders with empty strings so pd.to_numeric turns them to NaN
                    cleaned_col = df[col].astype(str).str.strip()
                    # Strip any surrounding quotes first
                    cleaned_col = cleaned_col.str.replace(r'^["\']|["\']$', '', regex=True)
                    # Replace placeholders (exact whole-string match only, case-insensitive)
                    for ph in ['nan', 'null', 'n/a', 'na', '?', 'none', '-', 'missing', 'empty']:
                        cleaned_col = cleaned_col.str.replace(re.compile(rf'^\s*{re.escape(ph)}\s*$', re.IGNORECASE), '', regex=True)
                    cleaned_col = cleaned_col.str.replace(r'[\$,%\s]', '', regex=True).str.replace(',', '', regex=False)
                    # Convert to numeric
                    converted = pd.to_numeric(cleaned_col, errors='coerce')
                    if not converted.isnull().all():
                        non_null_converted = converted.dropna()
                        if not non_null_converted.empty and (non_null_converted % 1 == 0).all():
                            if converted.isnull().any():
                                df[col] = converted.astype('Int64')
                                actions.append(f"Converted column '{col}' to Nullable Integer (cleaned currency/delimiters/nulls)")
                            else:
                                df[col] = converted.astype(int)
                                actions.append(f"Converted column '{col}' to Integer (cleaned currency/delimiters/nulls)")
                        else:
                            df[col] = converted
                            actions.append(f"Converted column '{col}' to Float (cleaned currency/delimiters/nulls)")
                        continue
                except Exception:
                    pass
                    
            # 3. Heuristic for Boolean: check for binary values (Yes/No, True/False, Y/N, 1/0)
            unique_vals = set(sample_non_null.str.lower().str.strip())
            if unique_vals.issubset({'yes', 'no', 'y', 'n', 'true', 'false', 't', 'f', '1', '0'}):
                # Ensure we have both binary parts represented, not just a single constant value column
                if len(unique_vals) >= 2:
                    try:
                        bool_map = {
                            'yes': True, 'no': False, 'y': True, 'n': False,
                            'true': True, 'false': False, 't': True, 'f': False,
                            '1': True, '0': False
                        }
                        df[col] = df[col].astype(str).str.lower().str.strip().map(bool_map)
                        actions.append(f"Converted column '{col}' to Boolean (detected binary labels)")
                        continue
                    except Exception:
                        pass

    return df, actions
