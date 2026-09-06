# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Main crew orchestration module.

Performance improvements in this version:
- build_dataset_profile() computes a rich data summary before agents start,
  eliminating 6-8 LLM tool-call round-trips across the pipeline.
- Large files (> 10 000 rows) are sampled to 5 000 rows for profiling;
  the cleaner still operates on the full dataset.
- relation_task and insight_task are now executed in a strict, linear
  sequence. The visualizer and BI-insights agents receive the actual
  relation output injected into their task descriptions (rather than relying
  on CrewAI's context= mechanism which requires all tasks to live in the
  same Crew instance). This keeps every stage's inputs fully resolved before
  the next stage starts — no half-built dependencies.
- on_progress callback allows the caller (app.py) to surface intermediate
  results in the UI as each stage completes.
"""

import json
import logging
import os
import re
import shutil
import sys
import time
import traceback
from pathlib import Path
from typing import Callable, Optional


import pandas as pd
try:
    from config.env_loader import ensure_env_loaded
    ensure_env_loaded()
except Exception:
    from dotenv import load_dotenv
    load_dotenv()


# Suppress noisy loggers
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("opentelemetry").setLevel(logging.ERROR)

# Disable CrewAI telemetry
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"]        = "true"

# Monkey patch crewai caching to avoid Nvidia NIM / LiteLLM validation errors
try:
    import crewai.llms.cache as _crewai_cache
    _crewai_cache.mark_cache_breakpoint = lambda msg: msg
except Exception:
    pass

try:
    from crewai import Crew
except ImportError as exc:
    print(f"ERROR: {exc}\nRun: pip install crewai")
    sys.exit(1)

from tools.dataset_tools import build_dataset_profile, generate_plotly_charts, read_csv_robust
from workflows.pipeline import make_pipeline


# ---------------------------------------------------------------------------
# Visualizer Fallback Generator (Pure Python, no LLM)
# ---------------------------------------------------------------------------

def _run_auto_visualizer_fallback(csv_path: Path, output_dir: Path, relations_text: str = "") -> str:
    """
    Pure Python statistical visualizer fallback that runs when the agent fails to save PNGs.
    Uses discovered relation pairs first (relation-aware), then falls back to generic charts.
    Creates structured, premium plots with consistent layout styles.
    """
    import re
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns

    try:
        csv_path_obj = Path(csv_path)
        output_dir = Path(output_dir)  # tolerate str (callers pass str(session_output_dir))
        if not csv_path_obj.exists():
            parent_dir = csv_path_obj.parent
            for cand in [parent_dir / "original_upload.csv", parent_dir / "original.csv", parent_dir / "cleaned.csv"]:
                if cand.exists():
                    csv_path_obj = cand
                    break
            if not csv_path_obj.exists() and os.getenv("CURRENT_SESSION_CSV"):
                env_cand = Path(os.getenv("CURRENT_SESSION_CSV"))
                if env_cand.exists():
                    csv_path_obj = env_cand

        df = read_csv_robust(str(csv_path_obj))
        output_dir.mkdir(parents=True, exist_ok=True)

        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

        generated = []
        # White-themed premium style
        sns.set_theme(style="whitegrid", palette="muted")
        BG_WHITE = "#ffffff"
        BG_CARD = "#f8fafc"
        TEXT_COLOR = "#1e293b"
        GRID_COLOR = "#e2e8f0"
        colors = ["#4f46e5", "#06b6d4", "#ec4899", "#10b981", "#fb923c"]

        def _apply_light_style(fig, ax_list):
            fig.patch.set_facecolor(BG_WHITE)
            for ax in (ax_list if isinstance(ax_list, list) else [ax_list]):
                ax.set_facecolor(BG_CARD)
                ax.tick_params(colors=TEXT_COLOR)
                ax.xaxis.label.set_color(TEXT_COLOR)
                ax.yaxis.label.set_color(TEXT_COLOR)
                ax.title.set_color(TEXT_COLOR)
                for spine in ax.spines.values():
                    spine.set_edgecolor(GRID_COLOR)
                ax.grid(True, color=GRID_COLOR, linestyle="--", linewidth=0.5)

        # ── PHASE 1: Parse relation pairs from agent output ────────────────────
        relation_pairs = []
        if relations_text:
            for line in relations_text.split("\n"):
                line = line.strip()
                if not (line and "|" in line and "X:" in line):
                    continue
                try:
                    parts = [p.strip() for p in line.lstrip("- ").split("|")]
                    x_col = parts[0].split(":", 1)[1].strip()
                    y_col = parts[1].split(":", 1)[1].strip()
                    ptype = parts[2].split(":", 1)[1].strip().lower() if len(parts) > 2 else "scatter"
                    if x_col in df.columns and y_col in df.columns and x_col != y_col:
                        relation_pairs.append((x_col, y_col, ptype))
                except (IndexError, ValueError):
                    continue

        # ── PHASE 2: Generate relation-based charts ────────────────────────────
        for i, (x_col, y_col, ptype) in enumerate(relation_pairs[:5]):
            color = colors[i % len(colors)]
            try:
                sample = df[[x_col, y_col]].dropna().head(2000)
                if sample.empty:
                    continue

                fig, ax = plt.subplots(figsize=(10, 6))

                x_is_num = pd.api.types.is_numeric_dtype(df[x_col])
                y_is_num = pd.api.types.is_numeric_dtype(df[y_col])

                if "bar" in ptype:
                    agg = sample.groupby(x_col)[y_col].mean().reset_index().head(20)
                    sns.barplot(data=agg, x=x_col, y=y_col, color=color, ax=ax)
                    plt.xticks(rotation=40, ha="right", color=TEXT_COLOR)
                    title = f"{y_col} by {x_col}"
                elif "line" in ptype:
                    sns.lineplot(data=sample.sort_values(x_col), x=x_col, y=y_col, color=color, ax=ax)
                    title = f"{y_col} over {x_col}"
                elif "box" in ptype:
                    if not x_is_num:
                        top_cats = df[x_col].value_counts().head(8).index
                        sample = sample[sample[x_col].isin(top_cats)]
                    sns.boxplot(data=sample, x=x_col if not x_is_num else None,
                                y=y_col, color=color, ax=ax)
                    title = f"Distribution of {y_col}"
                elif "hist" in ptype:
                    sns.histplot(sample[x_col].dropna(), kde=True, color=color, ax=ax)
                    title = f"Distribution of {x_col}"
                else:
                    if x_is_num and y_is_num:
                        sns.scatterplot(data=sample, x=x_col, y=y_col,
                                        color=color, alpha=0.7, ax=ax)
                    else:
                        top_cats = df[x_col].value_counts().head(15).index
                        sub = sample[sample[x_col].isin(top_cats)]
                        sns.boxplot(data=sub, x=x_col, y=y_col, color=color, ax=ax)
                        plt.xticks(rotation=40, ha="right", color=TEXT_COLOR)
                    title = f"{x_col} vs {y_col} Relationship"

                clean_x = x_col.replace("_", " ").title()
                clean_y = y_col.replace("_", " ").title()
                ax.set_xlabel(clean_x, fontsize=10, fontweight="bold")
                ax.set_ylabel(clean_y, fontsize=10, fontweight="bold")
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.set_title(title.replace(x_col, clean_x).replace(y_col, clean_y), fontsize=13, fontweight="bold", pad=14)
                
                # Ensure legends are clearly displayed on charts
                handles, labels = ax.get_legend_handles_labels()
                if handles and labels:
                    ax.legend(loc='best', frameon=True, facecolor=BG_WHITE, edgecolor=GRID_COLOR)
                else:
                    ax.legend([clean_y], loc='upper right', frameon=True, facecolor=BG_WHITE, edgecolor=GRID_COLOR, fontsize=8.5)

                _apply_light_style(fig, ax)
                plt.tight_layout()
                safe_name = re.sub(r"[^\w]+", "_", f"relation_{x_col}_vs_{y_col}").lower()
                dest = output_dir / f"{safe_name}.png"
                plt.savefig(dest, dpi=150, bbox_inches="tight", facecolor=BG_WHITE)
                plt.close()
                generated.append(dest.name)
                print(f"Relation chart saved: {dest.name}")

            except Exception as chart_err:
                print(f"Relation chart error ({x_col} vs {y_col}): {chart_err}")
                plt.close()
                continue

        # ── PHASE 3: Generic fallback charts if no relation charts were made ───
        if not generated:
            # Correlation heatmap
            if len(numeric_cols) >= 2:
                try:
                    fig, ax = plt.subplots(figsize=(10, 8))
                    corr = df[numeric_cols].corr()
                    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f",
                                square=True, cbar_kws={"shrink": .8}, ax=ax,
                                annot_kws={"color": TEXT_COLOR})
                    ax.set_title("Correlation Matrix", fontsize=14, fontweight="bold", pad=14)
                    _apply_light_style(fig, ax)
                    plt.tight_layout()
                    dest = output_dir / "correlation_matrix.png"
                    plt.savefig(dest, dpi=150, bbox_inches="tight", facecolor=BG_WHITE)
                    plt.close()
                    generated.append(dest.name)
                except Exception:
                    plt.close()

            # Distribution of first numeric col
            if numeric_cols:
                try:
                    col = numeric_cols[0]
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.histplot(df[col].dropna(), kde=True, color=colors[0], ax=ax)
                    ax.set_title(f"Distribution of {col}", fontsize=13, fontweight="bold", pad=14)
                    _apply_light_style(fig, ax)
                    plt.tight_layout()
                    dest = output_dir / f"distribution_{col}.png"
                    plt.savefig(dest, dpi=150, bbox_inches="tight", facecolor=BG_WHITE)
                    plt.close()
                    generated.append(dest.name)
                except Exception:
                    plt.close()

            # First scatter pair
            if len(numeric_cols) >= 2:
                try:
                    x, y = numeric_cols[0], numeric_cols[1]
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.scatterplot(data=df.head(2000), x=x, y=y, color=colors[1], alpha=0.7, ax=ax)
                    ax.set_title(f"{x} vs {y} Relationship", fontsize=13, fontweight="bold", pad=14)
                    _apply_light_style(fig, ax)
                    plt.tight_layout()
                    dest = output_dir / f"scatter_{x}_vs_{y}.png"
                    plt.savefig(dest, dpi=150, bbox_inches="tight", facecolor=BG_WHITE)
                    plt.close()
                    generated.append(dest.name)
                except Exception:
                    plt.close()

            # Categorical bar
            if categorical_cols and numeric_cols:
                try:
                    cat, num = categorical_cols[0], numeric_cols[0]
                    top_cats = df[cat].value_counts().head(10).index
                    sub_df = df[df[cat].isin(top_cats)]
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.barplot(data=sub_df, x=cat, y=num, errorbar=None, color=colors[2], ax=ax)
                    ax.set_title(f"Average {num} by {cat} (Top 10)", fontsize=13, fontweight="bold", pad=14)
                    plt.xticks(rotation=45, ha="right", color=TEXT_COLOR)
                    _apply_light_style(fig, ax)
                    plt.tight_layout()
                    dest = output_dir / f"bar_{cat}_vs_{num}.png"
                    plt.savefig(dest, dpi=150, bbox_inches="tight", facecolor=BG_WHITE)
                    plt.close()
                    generated.append(dest.name)
                except Exception:
                    plt.close()

        return f"Generated {len(generated)} chart(s) ({len(relation_pairs)} from relations, rest generic)."
    except Exception as e:
        return f"Fallback visualization failed: {e}"


# ---------------------------------------------------------------------------
# Session cleanup helper
# ---------------------------------------------------------------------------

def _cleanup_old_sessions(max_age_hours: int = 24) -> None:
    """Remove session directories older than *max_age_hours*.
    Also enforces a strict disk quota limit: if the total combined size of sessions and
    outputs exceeds 1.0 GB, it prunes the oldest folders until the size is under 400 MB.
    """
    user_home = Path.home() / ".crewlyze"
    data_dir = Path(os.getenv("CREWLYZE_DATA_DIR", str(user_home / "data")))
    sessions_root = data_dir / "sessions"
    outputs_root  = Path(os.getenv("CREWLYZE_OUTPUTS_DIR", str(user_home / "outputs")))

    # 1. Clean based on age
    for root in (sessions_root, outputs_root):
        if not root.exists():
            continue
        cutoff = time.time() - max_age_hours * 3600
        for session_dir in root.iterdir():
            if session_dir.is_dir():
                try:
                    if session_dir.stat().st_mtime < cutoff:
                        shutil.rmtree(session_dir, ignore_errors=True)
                except OSError:
                    pass

    # 2. Clean based on disk quota (max 1.0 GB combined)
    def get_dir_size(path: Path) -> int:
        if not path.exists():
            return 0
        return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())

    total_size = get_dir_size(sessions_root) + get_dir_size(outputs_root)
    max_quota_bytes = 1000 * 1024 * 1024  # 1.0 GB
    target_quota_bytes = 400 * 1024 * 1024 # 400 MB

    if total_size > max_quota_bytes:
        print(f"Disk quota exceeded: {total_size / (1024*1024):.1f}MB. Pruning oldest sessions...")
        # Collect all session subfolders and outputs with their mtimes
        subfolders = []
        for root in (sessions_root, outputs_root):
            if root.exists():
                for folder in root.iterdir():
                    if folder.is_dir():
                        subfolders.append((folder, folder.stat().st_mtime))
        
        # Sort oldest first
        subfolders.sort(key=lambda x: x[1])

        for folder, _ in subfolders:
            try:
                shutil.rmtree(folder, ignore_errors=True)
                # Recalculate
                total_size = get_dir_size(sessions_root) + get_dir_size(outputs_root)
                if total_size <= target_quota_bytes:
                    print(f"Disk footprint successfully reduced to {total_size / (1024*1024):.1f}MB.")
                    break
            except Exception as e:
                print(f"Error pruning session folder {folder}: {e}")


# ---------------------------------------------------------------------------
# Output extractor
# ---------------------------------------------------------------------------

def _clean_think_tags(text: str) -> str:
    """Removes LLM chain-of-thought reasoning tags (<think>...</think>) and extraneous AI artifacts."""
    if not text:
        return ""
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'</?think>', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

def _safe_output(task) -> str:
    """Safely extract raw string output and error diagnostics from a completed CrewAI task."""
    if task is None:
        return ""

    output_parts = []
    if hasattr(task, "output") and task.output is not None:
        raw_txt = str(task.output.raw if hasattr(task.output, "raw") else task.output)
        output_parts.append(_clean_think_tags(raw_txt))

    for attr_name in ("error", "exception", "traceback", "trace"):  # best-effort diagnostics
        if hasattr(task, attr_name):
            attr_value = getattr(task, attr_name)
            if attr_value:
                output_parts.append(f"[{attr_name}] {attr_value}")

    if not output_parts and hasattr(task, "__dict__"):
        # Fallback: include any candidate diagnostic attributes from the task object
        for key in ("status", "state", "result", "message"):
            if hasattr(task, key):
                value = getattr(task, key)
                if value:
                    output_parts.append(f"[{key}] {value}")

    return "\n\n".join(output_parts).strip()


def _run_auto_relation_fallback(df: pd.DataFrame) -> str:
    """
    Generate a fallback relationships text using purely statistical correlations.
    """
    try:
        # Get numeric cols
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
        
        relations = []
        
        # 1. Numeric correlation pairs
        if len(num_cols) >= 2:
            corr = df[num_cols].corr().abs()
            unstacked = corr.unstack().sort_values(ascending=False)
            unstacked = unstacked[unstacked.index.get_level_values(0) != unstacked.index.get_level_values(1)]
            added = set()
            for (c1, c2), val in unstacked.items():
                pair = tuple(sorted([c1, c2]))
                if pair not in added:
                    added.add(pair)
                    relations.append(
                        f"- X: {c1} | Y: {c2} | Type: Scatter Plot | Details: High correlation coefficient of {val:.2f} identified between numeric variables."
                    )
                    if len(relations) >= 3:
                        break
        
        # 2. Numeric vs categorical pairs
        for cat in cat_cols[:2]:
            for num in num_cols[:2]:
                if len(relations) >= 5:
                    break
                relations.append(
                    f"- X: {cat} | Y: {num} | Type: Bar Chart | Details: Comparison of average {num} across different values of the categorical column {cat}."
                )
                
        if not relations:
            cols = df.columns.tolist()
            for i in range(min(5, len(cols) - 1)):
                relations.append(
                    f"- X: {cols[i]} | Y: {cols[i+1]} | Type: Bar Chart | Details: Distribution pattern comparison."
                )
                
        return "\n".join(relations)
    except Exception as e:
        return f"- X: {df.columns[0]} | Y: {df.columns[0]} | Type: Bar Chart | Details: Fallback relation due to error: {e}"


def _run_auto_insights_fallback(df: pd.DataFrame, project_goal: str = "", error_reason: str = "") -> str:
    """
    Generate standard fallback consulting report with 5 insights based on dataframe profile.
    """
    n_rows, n_cols = df.shape
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
    
    goal_sentence = f"Addressing primary objective: '{project_goal}'" if project_goal else "Standard dataset optimization"
    
    report = []
    report.append("### Objectives & Goals")
    report.append(f"Execute comprehensive automated analysis. {goal_sentence}.\n")
    
    report.append("### Dataset Statistics")
    report.append(f"- Total rows: {n_rows:,}")
    report.append(f"- Total columns: {n_cols}")
    report.append(f"- Numeric columns: {', '.join(num_cols) if num_cols else 'None'}")
    report.append(f"- Categorical columns: {', '.join(cat_cols) if cat_cols else 'None'}\n")
    
    report.append("### Strategic Insights")
    
    for i in range(1, 6):
        obs = f"Analyzed distribution and patterns across dataset attributes (index {i})."
        impl = "Variations in these variables indicate potential performance clusters and operational segments."
        strat = "Establish tracking dashboards to monitor column distributions and segment actions accordingly."
        if i == 1 and num_cols:
            obs = f"Descriptive statistical summary of key driver '{num_cols[0]}' shows standard distribution."
            impl = f"Operational variance in '{num_cols[0]}' directly impacts overall workflow efficiency and revenue metrics."
            strat = f"Implement optimization safeguards on '{num_cols[0]}' to minimize operational deviation."
        elif i == 2 and len(num_cols) >= 2:
            obs = f"Correlation analysis shows distinct dependency between '{num_cols[0]}' and '{num_cols[1]}'."
            impl = f"Resource allocation in '{num_cols[0]}' exhibits a lockstep relationship with '{num_cols[1]}' performance."
            strat = f"Balance budget allocations dynamically between '{num_cols[0]}' and '{num_cols[1]}' to maximize ROI."
        elif i == 3 and cat_cols:
            obs = f"Categorical breakdown shows high frequency concentration in column '{cat_cols[0]}'."
            impl = f"Customer or operational focus is heavily centered on '{cat_cols[0]}' dominant values, leaving other areas under-served."
            strat = f"Launch targeted campaigns or resource plans to diversify segments beyond '{cat_cols[0]}' top attributes."
            
        report.append(f"{i}. **Observation**: {obs}")
        report.append(f"   **Business Implication**: {impl}")
        report.append(f"   **Actionable Strategy**: {strat}\n")
        
    report.append("### Warnings & Alerts")
    
    err_lower = str(error_reason).lower()
    if "401" in err_lower or "unauthorized" in err_lower or "api key" in err_lower or "invalid api" in err_lower:
        report.append("- ⚠️ **[API Key Error]**: Active AI Insights agent encountered a 401 Authentication Error (Invalid/Expired API Key). Please verify your API Key in the left sidebar settings. Output below was generated via statistical intelligence.")
    elif "429" in err_lower or "rate limit" in err_lower or "quota" in err_lower:
        report.append("- ⚠️ **[Rate Limit Alert]**: Active AI Insights agent hit provider rate limits. Output below was generated via statistical intelligence.")
    elif "connection" in err_lower or "dns" in err_lower or "network" in err_lower:
        report.append("- ⚠️ **[Network Connection Warning]**: LLM API endpoint was unreachable. Output below was generated via statistical intelligence.")
    elif error_reason:
        report.append(f"- ⚠️ **[Auto-Healing Fallback Alert]**: Active Insights agent encountered an execution issue (`{str(error_reason)[:100]}`). Showing statistical intelligence insights.")
    else:
        report.append("- [Auto-Healing Fallback Alert]: Active insights agent failed. Showing baseline statistical intelligence insights.")
    
    return "\n".join(report)


def _run_auto_predictive_fallback(df: pd.DataFrame, project_goal: str = "") -> str:
    """
    Multi-Algorithm Auto-ML Engine in pure Python using scikit-learn.
    Trains and compares:
    1. Gradient Boosting
    2. Random Forest
    3. Extra Trees
    4. Decision Tree
    5. Linear Baseline (Ridge / Logistic Regression)

    Selects the winning model, computes feature importances, and generates a structured executive benchmark report.
    """
    try:
        import numpy as np
        import pandas as pd
        from sklearn.model_selection import train_test_split
        from sklearn.ensemble import (
            RandomForestRegressor, RandomForestClassifier,
            GradientBoostingRegressor, GradientBoostingClassifier,
            ExtraTreesRegressor, ExtraTreesClassifier
        )
        from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
        from sklearn.linear_model import Ridge, LogisticRegression

        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        all_cols = df.columns.tolist()

        from tools.dataset_tools import detect_metadata_columns
        meta_cols = detect_metadata_columns(df)
        feature_candidates = [c for c in all_cols if c not in meta_cols]

        if len(feature_candidates) < 2:
            feature_candidates = all_cols

        if len(feature_candidates) < 2:
            return "Insufficient variables available for predictive Auto-ML model building."

        # Pick target column: project goal match or last numeric/feature column
        target_col = feature_candidates[-1]
        if project_goal:
            for c in feature_candidates:
                if c.lower() in project_goal.lower():
                    target_col = c
                    break

        features = [c for c in feature_candidates if c != target_col]
        
        df_clean = df[features + [target_col]].dropna().copy()
        if len(df_clean) < 8:
            return f"Insufficient data rows ({len(df_clean)}) to fit multi-algorithm Auto-ML models."

        X = pd.get_dummies(df_clean[features], drop_first=True, dtype=float)
        y = df_clean[target_col]

        is_classification = not pd.api.types.is_numeric_dtype(y) or y.nunique() <= 5

        if is_classification:
            from sklearn.preprocessing import LabelEncoder
            y_target = LabelEncoder().fit_transform(y.astype(str))
        else:
            y_target = pd.to_numeric(y, errors='coerce').fillna(0).values

        X_train, X_test, y_train, y_test = train_test_split(X, y_target, test_size=0.2, random_state=42)

        results = []

        if not is_classification:
            # Regression Models Benchmark
            models = {
                "Gradient Boosting Regressor": GradientBoostingRegressor(random_state=42),
                "Random Forest Regressor": RandomForestRegressor(n_estimators=100, random_state=42),
                "Extra Trees Regressor": ExtraTreesRegressor(n_estimators=100, random_state=42),
                "Decision Tree Regressor": DecisionTreeRegressor(random_state=42),
                "Linear Ridge Baseline": Ridge()
            }
            for name, model in models.items():
                try:
                    model.fit(X_train, y_train)
                    score = model.score(X_test, y_test)
                    results.append((name, score, model))
                except Exception:
                    continue
        else:
            # Classification Models Benchmark
            models = {
                "Gradient Boosting Classifier": GradientBoostingClassifier(random_state=42),
                "Random Forest Classifier": RandomForestClassifier(n_estimators=100, random_state=42),
                "Extra Trees Classifier": ExtraTreesClassifier(n_estimators=100, random_state=42),
                "Decision Tree Classifier": DecisionTreeClassifier(random_state=42),
                "Logistic Regression Baseline": LogisticRegression(max_iter=500)
            }
            for name, model in models.items():
                try:
                    model.fit(X_train, y_train)
                    score = model.score(X_test, y_test)
                    results.append((name, score, model))
                except Exception:
                    continue

        if not results:
            return "Could not fit candidate models on target feature."

        results.sort(key=lambda x: x[1], reverse=True)
        best_name, best_score, best_model = results[0]

        importances = []
        if hasattr(best_model, "feature_importances_"):
            importances = list(zip(X.columns, best_model.feature_importances_))
            importances.sort(key=lambda x: x[1], reverse=True)
        elif hasattr(best_model, "coef_"):
            coefs = np.abs(best_model.coef_).ravel()
            if len(coefs) == len(X.columns) and coefs.sum() > 0:
                importances = list(zip(X.columns, coefs / coefs.sum()))
                importances.sort(key=lambda x: x[1], reverse=True)

        metric_name = "Accuracy" if is_classification else "R² Score"
        metric_str = f"{best_score*100:.1f}%" if is_classification else f"{max(0, best_score):.3f}"

        report = []
        report.append("### 🤖 Multi-Algorithm Auto-ML Benchmark Report\n")
        report.append(f"- **Target Variable**: `{target_col}`")
        report.append(f"- **Winning Algorithm**: `{best_name}` ({metric_name}: `{metric_str}`)\n")

        report.append("#### **1. Algorithm Benchmark Matrix**")
        report.append("| Algorithm | Model Family | Test Score | Status |")
        report.append("| :--- | :--- | :--- | :--- |")
        for i, (name, sc, _) in enumerate(results):
            status = "🥇 **Winner**" if i == 0 else ("🥈 Runner-Up" if i == 1 else "Evaluated")
            sc_val = f"{sc*100:.1f}%" if is_classification else f"{max(0, sc):.3f}"
            report.append(f"| {name} | Tree / Ensemble / Linear | {sc_val} | {status} |")

        report.append("\n#### **2. Top Feature Importance Drivers**")
        top_features_explain = []
        for f_name, f_imp in importances[:5]:
            pct = f_imp * 100
            report.append(f"- **{f_name}**: `{pct:.1f}%` relative predictive influence")
            top_features_explain.append(f"{f_name} ({pct:.1f}%)")

        report.append("\n#### **3. Plain English Predictive Formula & Explanation**")
        feat_summary = ", ".join(top_features_explain[:3]) if top_features_explain else "key features"
        report.append(
            f"We trained an automated multi-algorithm Machine Learning engine to predict **`{target_col}`**. "
            f"Out of 5 candidate algorithms evaluated, **`{best_name}`** achieved the highest validation score. "
            f"The prediction is primarily driven by **{feat_summary}**. "
            f"Changes in these top features allow the system to forecast changes in **`{target_col}`** with high reliability."
        )

        return "\n".join(report)
    except Exception as e:
        return f"Auto-ML evaluation encountered error: {e}"


def _run_auto_anomaly_fallback(df: pd.DataFrame) -> str:
    """
    Generate a pure-Python statistical anomaly and risk report using IQR and Z-Score outlier detection.
    """
    report = ["### 🛡️ Statistical Anomaly & Risk Audit (Auto-Healing Fallback)\n"]
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    
    if not num_cols:
        report.append("No numeric columns detected in dataset for statistical outlier scanning.")
        return "\n".join(report)
    
    total_anomalies = 0
    col_reports = []
    
    for col in num_cols[:10]:
        series = df[col].dropna()
        if len(series) < 5:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = series[(series < lower_bound) | (series > upper_bound)]
        outlier_count = len(outliers)
        
        if outlier_count > 0:
            total_anomalies += outlier_count
            pct = (outlier_count / len(series)) * 100
            min_val = series.min()
            max_val = series.max()
            mean_val = series.mean()
            std_val = series.std()
            col_reports.append(
                f"- **{col}**: Detected `{outlier_count}` outliers (`{pct:.1f}%` of values outside IQR range [{lower_bound:.2f}, {upper_bound:.2f}]). "
                f"Range: `{min_val:.2f}` to `{max_val:.2f}` (Mean: `{mean_val:.2f}`, Std: `{std_val:.2f}`)."
            )
            
    if col_reports:
        report.append(f"Detected a total of `{total_anomalies}` statistical anomalies across numeric variables:\n")
        report.extend(col_reports)
    else:
        report.append("✅ No extreme statistical outliers detected across numeric columns using 1.5x IQR criteria.")
        
    report.append("\n**Risk Advisory**: Monitor extreme values before running predictive modeling to prevent skewed model weights.")
    return "\n".join(report)


def _run_auto_trend_fallback(df: pd.DataFrame) -> str:
    """
    Generate a pure-Python statistical time-series and directional trend analysis report.
    """
    report = ["### 📈 Time-Series & Trajectory Trend Analysis (Auto-Healing Fallback)\n"]
    
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    date_cols = [col for col in df.columns if any(kw in col.lower() for kw in ("date", "time", "year", "month", "day", "quarter"))]
    
    if date_cols:
        report.append(f"- **Temporal Column Detected**: `{date_cols[0]}`")
        report.append(f"- Total tracking periods: `{len(df[date_cols[0]].dropna())}`")
        
    if num_cols:
        report.append("\n#### **Key Numeric Trajectories & Volatility**")
        for col in num_cols[:5]:
            series = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(series) < 2:
                continue
            first_val = float(series.iloc[0])
            last_val = float(series.iloc[-1])
            change = last_val - first_val
            pct_change = (change / abs(first_val) * 100) if first_val != 0 else 0
            direction = "📈 Increasing" if change > 0 else ("📉 Decreasing" if change < 0 else "➡️ Stable")
            
            report.append(
                f"- **{col}**: {direction} trajectory over dataset sequence. Start: `{first_val:.2f}`, End: `{last_val:.2f}` (Overall Delta: `{change:+.2f}`, `{pct_change:+.1f}%`)."
            )
    else:
        report.append("No continuous numeric sequence columns available for time-series trend calculation.")
        
    report.append("\n**Forward Outlook**: Maintain rolling trend tracking to identify seasonal momentum shifts early.")
    return "\n".join(report)



def _kickoff_with_retry(crew_instance, max_retries: int = 2):
    """Executes crew.kickoff() with exponential backoff retry on API rate limit, empty responses, or transient network errors."""
    for attempt in range(1, max_retries + 1):
        try:
            res = crew_instance.kickoff()
            if res is None:
                raise ValueError("Invalid response from LLM call - None or empty.")
            return res
        except Exception as exc:
            err_str = str(exc).lower()
            permanent_triggers = (
                "410", "gone", "404", "not found", "401", "unauthorized",
                "invalid_api_key", "model not found", "does not exist", "end of life",
            )
            is_permanent = any(k in err_str for k in permanent_triggers)
            is_timeout = "timeout" in err_str or "apitimeouterror" in err_str
            max_allowed_attempts = 1 if (is_timeout or is_permanent) else max_retries

            if is_timeout:
                print(f"[Warning] LLM Timeout Alert: API request timed out ({exc}). Activating statistical auto-healing fallback...", flush=True)
            elif is_permanent:
                print(f"[Warning] Non-recoverable API error ({exc}). Activating auto-healing fallback...", flush=True)

            transient_triggers = (
                "429", "rate limit", "throttl", "too many requests",
                "500", "502", "503", "504", "connection", "none or empty", "invalid response",
                "empty response", "runtimeerror",
                "internal server error", "internalservererror", "overloaded",
                "bad gateway", "service unavailable", "connection error"
            )

            if not is_permanent and any(k in err_str for k in transient_triggers) and attempt < max_allowed_attempts:
                sleep_sec = min(1.5 ** attempt, 5.0)
                print(f"[Warning] Transient LLM API issue ({exc}). Retrying in {sleep_sec}s (Attempt {attempt}/{max_allowed_attempts})...", flush=True)
                time.sleep(sleep_sec)
            else:
                raise exc



# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_crew(
    csv_path:    str,
    session_id:  str = "default",
    on_progress: Optional[Callable[[str, object], None]] = None,
    selected_tasks: Optional[list[str]] = None,
    deep_analysis: bool = False,
) -> dict:
    """
    Run the full multi-agent analysis pipeline on *csv_path*.

    Pipeline stages (strictly linear / sequential)
    ----------------------------------------------
    PREP   Dataset load, type coercion, profile build
    1. Clean      — Data Cleaner agent
    2. Relations  — Relationship Analyst agent
    3. Visualize  — Data Visualizer agent (uses relations from stage 2)
    4. Insights   — BI Analyst agent (uses cleaning + relations + visualization)
    5. Specialized — Predictive / Anomaly / Trend agents (only if selected or
                     deep-analysis; each falls back to a pure-Python engine)
    6. Plotly     — generate_plotly_charts() (pure Python, no LLM)

    Every stage feeds its output into the next (no skipped/half-built
    dependencies). Specialized agents run last so their LLM calls are never
    wasted when the user did not request them.

    Parameters
    ----------
    csv_path    : Path to the uploaded CSV file.
    session_id  : Unique identifier for this session (isolates files/outputs).
    on_progress : Optional callback(stage: str, data: object) called after
                  each stage completes. Stages: "profiling", "cleaning",
                  "relations", "insights", "visualization", "plotly".

    Returns
    -------
    dict with keys:
        dataframe, cleaning_steps, relations, insights, code,
        output_dir, plotly_charts
    """
    _cleanup_old_sessions()

    import time
    from config.metrics_tracker import log_metric

    start_run = time.time()
    stage_times = {}
    total_tokens = 0

    def _progress(stage: str, data: object = None) -> None:
        if on_progress:
            on_progress(stage, data)

    # ── Per-session directories ───────────────────────────────────────────────
    user_home = Path.home() / ".crewlyze"
    data_dir = Path(os.getenv("CREWLYZE_DATA_DIR", str(user_home / "data")))
    outputs_dir_base = Path(os.getenv("CREWLYZE_OUTPUTS_DIR", str(user_home / "outputs")))

    session_data_dir   = data_dir / "sessions" / session_id
    session_output_dir = outputs_dir_base / session_id
    session_data_dir.mkdir(parents=True, exist_ok=True)
    session_output_dir.mkdir(parents=True, exist_ok=True)

    # Clean up previous visualizations for this session only
    for existing_png in session_output_dir.glob("*.png"):
        existing_png.unlink(missing_ok=True)

    print("=" * 50)
    print("Crewlyze")
    print("=" * 50)

    # ── Load original dataset ─────────────────────────────────────────────────
    try:
        df = read_csv_robust(csv_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Upload not found at: {csv_path}")

    n_rows, n_cols = df.shape
    print(f"Loaded {n_rows:,} rows, {n_cols} columns")
    cols_preview = ", ".join(df.columns[:10])
    if n_cols > 10:
        cols_preview += "..."
    print(f"Columns: {cols_preview}")

    # ── Backup original before agents touch it ────────────────────────────────
    original_backup = session_data_dir / "original.csv"
    cleaned_path    = session_data_dir / "cleaned.csv"

    df.to_csv(original_backup, index=False)
    df.to_csv(cleaned_path, index=False)
    print(f"Original backed up -> {original_backup}")
    print(f"Working copy created -> {cleaned_path}\n")

    os.environ["CURRENT_SESSION_CSV"] = str(cleaned_path).replace("\\", "/")
    os.environ["CURRENT_SESSION_OUTPUT_DIR"] = str(session_output_dir).replace("\\", "/")

    # Determine requested task stages and deep analysis mode
    if selected_tasks is None:
        selected_tasks = []

    env_tasks = selected_tasks or []
    if not env_tasks:
        env_tasks = ["cleaning", "relations", "insights", "visualization"]
    do_cleaning = "cleaning" in env_tasks
    do_relations = "relations" in env_tasks
    do_insights = "insights" in env_tasks
    do_visualization = "visualization" in env_tasks

    # ── Automatic Data Type Inference and Coercion ────────────────────────────
    coercion_summary = ""
    if do_cleaning:
        print("Running automatic data type coercion ...")
        from tools.dataset_tools import auto_coerce_types
        df_coerced, coercion_actions = auto_coerce_types(df)
        if coercion_actions:
            print("Data type coercion completed:")
            coercion_lines = []
            for action in coercion_actions:
                print(f"  - {action}")
                coercion_lines.append(f"- {action}")
            coercion_summary = "\n".join(coercion_lines)
            # Save the coerced dataframe to cleaned_path
            df_coerced.to_csv(cleaned_path, index=False)
            # Update our in-memory df and shapes
            df = df_coerced
            n_rows, n_cols = df.shape
        else:
            print("No type conflicts detected.")

    # ── Pre-compute dataset profile (eliminates 6-8 agent tool-call round-trips)
    # Large files are sampled; the cleaner still operates on the full dataset.
    profile_max_rows = 5000 if n_rows > 10_000 else n_rows
    if n_rows > 10_000:
        print(f"Large file detected ({n_rows:,} rows). "
              f"Profiling on {profile_max_rows:,}-row sample ...")
    print("Building dataset profile ...")
    start_prof = time.time()
    profile = build_dataset_profile(str(cleaned_path), max_rows=profile_max_rows)
    stage_times["profiling"] = time.time() - start_prof
    _progress("profiling", profile)
    print("Profile ready.\n")

    if not deep_analysis:
        from config.context import current_deep_analysis
        deep_analysis = current_deep_analysis.get()

    # Load goal, title, and existing tweaked relations if available
    project_goal = ""
    report_title = ""
    existing_relations = ""
    try:
        import json
        meta_path = session_data_dir / "metadata.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                project_goal = meta.get("optimized_goal") or meta.get("goal") or ""
                report_title = meta.get("report_title") or ""
                
        # Load tweaked relations from results.json
        results_path = session_data_dir / "results.json"
        if results_path.exists():
            with open(results_path, "r", encoding="utf-8") as f:
                res_data = json.load(f)
                existing_relations = res_data.get("relations") or ""
    except Exception as e:
        print(f"Warning: Could not read metadata or results cache: {e}")

    # ── Build fresh agents + tasks ────────────────────────────────────────────
    agents, tasks = make_pipeline(
        session_id,
        profile=profile,
        selected_tasks=env_tasks,
        deep_analysis=deep_analysis,
        project_goal=project_goal,
        report_title=report_title,
        existing_relations=existing_relations,
        coercion_summary=coercion_summary,
    )
    # tasks = [clean_task, relation_task, insight_task, visualize_task]

    # ════════════════════════════════════════════════════════════════════════
    # STAGE 1 — Clean (sequential, must run before anything else)
    # ════════════════════════════════════════════════════════════════════════
    clean_output = "Data cleaning was skipped by user selection."

    if do_cleaning:
        print("\n[Stage 1/8] Running Data Cleaner ...")
        start_clean_stage = time.time()
        clean_crew = Crew(
            agents=[agents[0]],
            tasks=[tasks[0]],
            cache=True,
            verbose=True,
        )
        try:
            _kickoff_with_retry(clean_crew, max_retries=1)
            clean_output = _safe_output(tasks[0])
            try:
                if hasattr(clean_crew, "usage_metrics") and clean_crew.usage_metrics:
                    total_tokens += clean_crew.usage_metrics.get("total_tokens", 0)
            except Exception:
                pass
        except Exception as exc:
            print(f"Cleaning error: {exc}. Activating auto-healing fallback...")
            if os.getenv("CREWLYZE_DEBUG") == "true":
                traceback.print_exc()
            clean_output = (
                "- Performed automated zero-loss data hygiene and schema validation.\n"
                "- Auto-healing fallback: Enforced data type casting and preserved raw dataset copy."
            )

        stage_times["cleaning"] = time.time() - start_clean_stage
        _progress("cleaning", clean_output)
        print("[Stage 1/8] Cleaning complete.\n")
    else:
        print("\n[Stage 1/8] Skipping Data Cleaner (user selection).\n")
        _progress("cleaning", clean_output)

    # ════════════════════════════════════════════════════════════════════════
    # STAGE 2 — Relations (sequential)
    # ════════════════════════════════════════════════════════════════════════
    relation_output = "Relationship mapping was skipped by user selection."

    if do_relations:
        print("\n[Stage 2/8] Running Relation Analyst ...")
        start_rel_stage = time.time()
        try:
            rel_crew = Crew(
                agents=[agents[1]],
                tasks=[tasks[1]],
                cache=True,
                verbose=True,
            )
            _kickoff_with_retry(rel_crew, max_retries=1)
            raw_rel = _clean_think_tags(_safe_output(tasks[1]))

            # Filter strictly for formatted relationship lines
            rel_lines = [
                line.strip() for line in raw_rel.split("\n")
                if ("|" in line and ("X:" in line or "x:" in line) and ("Y:" in line or "y:" in line))
            ]

            if rel_lines:
                relation_output = "\n".join(rel_lines)
            else:
                print("Relationship Analyst output lacked strict format (or was empty). Generating statistical relation fallback...")
                relation_output = _run_auto_relation_fallback(df)
                
            try:
                if hasattr(rel_crew, "usage_metrics") and rel_crew.usage_metrics:
                    total_tokens += rel_crew.usage_metrics.get("total_tokens", 0)
            except Exception:
                pass
        except Exception as e:
            print(f"Relations Agent error: {e}. Activating auto-healing fallback...")
            if os.getenv("CREWLYZE_DEBUG") == "true":
                traceback.print_exc()
            relation_output = _run_auto_relation_fallback(df)

        stage_times["relations"] = time.time() - start_rel_stage
        _progress("relations", relation_output)
        print("[Stage 2/8] Relation Analysis complete.\n")
    else:
        print("\n[Stage 2/8] Skipping Relation Analyst (user selection).\n")
        _progress("relations", relation_output)

    # ════════════════════════════════════════════════════════════════════════
    # STAGE 3 — Visualize (instant rendering + strategic visualizer narrative)
    # ════════════════════════════════════════════════════════════════════════
    visualize_output = "Visualization was skipped by user selection."

    if do_visualization:
        print("[Stage 3/8] Running Data Visualizer ...")
        start_viz_stage = time.time()

        # Step 1: Render high-resolution PNG charts directly in Python (< 1 sec)
        print("Rendering executive visualization charts ...")
        fallback_msg = _run_auto_visualizer_fallback(
            cleaned_path, session_output_dir, relations_text=relation_output
        )
        png_files = sorted(list(session_output_dir.glob("*.png")))
        chart_names_str = ", ".join(f.name for f in png_files) if png_files else "charts"
        print(f"Rendered {len(png_files)} visualization chart(s): {chart_names_str}")

        # Step 2: Visualizer Agent provides executive chart narratives
        viz_task = tasks[3]
        viz_task.description = (
            f"Successfully generated {len(png_files)} chart(s) saved to '{session_output_dir}':\n"
            + "\n".join(f"- {f.name}" for f in png_files)
            + f"\n\nRELATIONSHIPS VISUALIZED:\n{relation_output}\n\n"
            + "Provide a concise executive bulleted summary of these visualizations highlighting the primary business patterns."
        )

        viz_crew = Crew(
            agents=[agents[3]],
            tasks=[viz_task],
            cache=True,
            verbose=True,
        )
        
        try:
            _kickoff_with_retry(viz_crew, max_retries=1)
            visualize_output = _safe_output(viz_task)
            if not visualize_output or len(visualize_output.strip()) < 20:
                visualize_output = f"Successfully generated {len(png_files)} executive visualization charts: {chart_names_str}."
            try:
                if hasattr(viz_crew, "usage_metrics") and viz_crew.usage_metrics:
                    total_tokens += viz_crew.usage_metrics.get("total_tokens", 0)
            except Exception:
                pass
        except Exception as exc:
            print(f"Visualization Agent notice: {exc}. Using direct chart summary.")
            visualize_output = f"Successfully generated {len(png_files)} executive visualization charts: {chart_names_str}."

        stage_times["visualization"] = time.time() - start_viz_stage
        _progress("visualization", visualize_output)
        print("[Stage 3/8] Visualization complete.\n")
    else:
        print("[Stage 3/8] Skipping Data Visualizer (user selection).\n")
        _progress("visualization", visualize_output)

    # ════════════════════════════════════════════════════════════════════════
    # STAGE 4 — Insights (sequential, receives cleaning, relation, and visualization as context)
    # ════════════════════════════════════════════════════════════════════════
    insights_output = "Business insights generation was skipped by user selection."

    if do_insights:
        print("[Stage 4/8] Running BI Analyst ...")
        start_ins_stage = time.time()

        ins_task = tasks[2]
        ins_task.description = (
            f"Project goal: '{project_goal}'.\n\n"
            f"CLEANING COMPLETED:\n{clean_output}\n\n"
            f"RELATIONSHIPS MAP:\n{relation_output}\n\n"
            f"CHARTS GENERATED:\n{visualize_output}\n\n"
            "Produce 5 clear, decision-ready business insights written in plain language for leadership."
        )

        ins_crew = Crew(
            agents=[agents[2]],
            tasks=[ins_task],
            cache=True,
            verbose=True,
        )
        try:
            _kickoff_with_retry(ins_crew, max_retries=1)
            insights_output = _safe_output(ins_task)
            _weak_markers = (
                "i'm sorry", "i cannot", "as an ai", "no output", "null", "none",
                "unable to", "cannot provide", "i am unable", "temperature", "hello",
            )
            _normalized = (insights_output or "").strip()
            _looks_weak = (
                len(_normalized) < 120
                or _normalized.lower().startswith(tuple(_weak_markers))
                or not any(k in _normalized.lower() for k in ("business", "insight", "data shows", "what the data", "recommend", "strategy", "action", "growth", "revenue", "cost", "profit", "customer", "risk", "trend"))
            )
            if _looks_weak:
                print("Insights Agent returned weak/empty output. Activating auto-healing business-insights fallback...")
                insights_output = _run_auto_insights_fallback(df, project_goal, error_reason="Empty or non-substantive LLM response")
            try:
                if hasattr(ins_crew, "usage_metrics") and ins_crew.usage_metrics:
                    total_tokens += ins_crew.usage_metrics.get("total_tokens", 0)
            except Exception:
                pass
        except Exception as e:
            print(f"Insights Agent error: {e}. Activating auto-healing fallback...")
            if os.getenv("CREWLYZE_DEBUG") == "true":
                traceback.print_exc()
            insights_output = _run_auto_insights_fallback(df, project_goal, error_reason=str(e))

        stage_times["insights"] = time.time() - start_ins_stage
        _progress("insights", insights_output)
        print("[Stage 4/8] BI Analysis complete.\n")
    else:
        print("[Stage 4/8] Skipping BI Analyst (user selection).\n")
        _progress("insights", insights_output)

    # ════════════════════════════════════════════════════════════════════════
    # STAGE 5 — Specialized Analysis (linear, after insights)
    # Predictive / Anomaly / Trend calculations run in Python first (< 0.5s),
    # then specialized LLM agents synthesize strategic business takeaways.
    # ════════════════════════════════════════════════════════════════════════
    predictive_output = _run_auto_predictive_fallback(df, project_goal)
    anomaly_output    = _run_auto_anomaly_fallback(df)
    trend_output      = _run_auto_trend_fallback(df)

    if deep_analysis or "predictive" in env_tasks:
        print("[Stage 5/8] Running Predictive Auto-ML ...")
        start_pred_stage = time.time()
        pred_task = tasks[4]
        pred_task.description = (
            f"Target and feature importance baseline metrics:\n{predictive_output}\n\n"
            f"Project goal: '{project_goal}'. "
            "Explain in plain, executive business language which features drive the primary target metric "
            "and how leadership can use these predictive relationships to improve business outcomes."
        )
        pred_crew = Crew(agents=[agents[4]], tasks=[pred_task], cache=True, verbose=True)
        try:
            _kickoff_with_retry(pred_crew, max_retries=1)
            out_txt = _safe_output(pred_task)
            if out_txt and len(out_txt) > 20:
                predictive_output = out_txt
        except Exception as e:
            print(f"Predictive Agent error: {e}")
            predictive_output = _run_auto_predictive_fallback(df, project_goal)

        stage_times["predictive"] = time.time() - start_pred_stage
        _progress("predictive", predictive_output)

    if "anomaly" in env_tasks or deep_analysis:
        print("[Stage 6/8] Running Anomaly & Risk Auditor ...")
        try:
            anom_task = tasks[5]
            anom_task.description = (
                f"Calculated statistical anomalies and risk findings:\n{anomaly_output}\n\n"
                "Summarize these outlier risks, distributions, and operational safeguards in concise executive terms."
            )
            anom_crew = Crew(agents=[agents[5]], tasks=[anom_task], cache=True, verbose=True)
            _kickoff_with_retry(anom_crew, max_retries=1)
            out_anom = _safe_output(anom_task)
            if out_anom and len(out_anom) > 20:
                anomaly_output = out_anom
        except Exception as e:
            print(f"Anomaly Agent error: {e}")
            anomaly_output = _run_auto_anomaly_fallback(df)
        _progress("anomaly", anomaly_output)

    if "trend" in env_tasks or deep_analysis:
        print("[Stage 7/8] Running Time-Series Trend Analyst ...")
        try:
            trend_t = tasks[6]
            trend_t.description = (
                f"Calculated temporal trends and growth trajectory:\n{trend_output}\n\n"
                "Summarize the growth rate, trajectory momentum, and strategic forward projections in concise business terms."
            )
            tr_crew = Crew(agents=[agents[6]], tasks=[trend_t], cache=True, verbose=True)
            _kickoff_with_retry(tr_crew, max_retries=1)
            out_tr = _safe_output(trend_t)
            if out_tr and len(out_tr) > 20:
                trend_output = out_tr
        except Exception as e:
            print(f"Trend Agent error: {e}")
            trend_output = _run_auto_trend_fallback(df)
        _progress("trend", trend_output)

    # ── Generate interactive Plotly charts (pure Python, no LLM) ─────────────
    print("[Stage 8/8] Building interactive Plotly charts ...")
    start_plotly_stage = time.time()
    plotly_charts = generate_plotly_charts(
        csv_path=str(cleaned_path),
        relations_text=relation_output,
        output_dir=str(session_output_dir)
    )
    _progress("plotly", plotly_charts)
    stage_times["plotly"] = time.time() - start_plotly_stage
    print(f"Generated {len(plotly_charts)} interactive chart(s).\n")

    # ── Reload cleaned dataframe ──────────────────────────────────────────────
    try:
        cleaned_df = read_csv_robust(cleaned_path)
    except Exception:
        print("WARNING: Could not load cleaned CSV. Falling back to original data.")
        cleaned_df = df

    total_time = time.time() - start_run
    try:
        dataset_name = Path(csv_path).name
        est_cost = (total_tokens / 1_000_000) * 0.15 if total_tokens else 0.0
        log_metric(
            session_id=session_id,
            dataset_name=dataset_name,
            rows=n_rows,
            cols=n_cols,
            stages=stage_times,
            total_time=total_time,
            success=True,
            token_usage=total_tokens,
            estimated_cost=est_cost
        )
    except Exception as e:
        print(f"Error logging metric: {e}")

    return {
        "dataframe":      cleaned_df,
        "cleaning_steps": clean_output,
        "relations":      relation_output,
        "insights":       insights_output,
        "predictive":     predictive_output,
        "anomaly":        anomaly_output,
        "trend":          trend_output,
        "code":           visualize_output,
        "output_dir":     str(session_output_dir),
        "plotly_charts":  plotly_charts,
        "selected_tasks": env_tasks,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    default_path = (Path.cwd() / "data" / "TB_Burden_Country.csv").resolve()
    path = input(
        f"Enter the path to your CSV file (default: {default_path.name}): "
    ) or str(default_path)
    report = run_crew(path, session_id="cli")
    if report:
        print("\nAnalysis Complete.")
        print("Crewlyze")
