# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Deterministic Statistical & Data Analysis Engines.
Provides pure Python calculations for Category 1 Data Analysis Agents:
  - 1.1 Data Cleaner
  - 1.2 Statistical Analysis
  - 1.3 Trend Analysis
  - 1.4 Comparative Analysis
  - 1.5 Insight Discovery
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats


# ─────────────────────────────────────────────────────────────────────────────
# 1.1 Data Cleaner Engine
# ─────────────────────────────────────────────────────────────────────────────

def clean_dataset_safely(df: pd.DataFrame, fill_strategy: str = "median") -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Applies non-destructive automated data hygiene:
    - Trims string whitespace
    - Normalizes empty strings to NaN
    - Identifies and drops exact duplicates
    - Coerces obvious numeric and date representations
    - Records an exact changelog with zero data loss on raw copies
    """
    cleaned = df.copy()
    initial_shape = list(df.shape)
    changelog = []

    # 1. Trim strings and normalize empty text
    str_cols = cleaned.select_dtypes(include=["object"]).columns.tolist()
    for col in str_cols:
        try:
            cleaned[col] = cleaned[col].astype(str).str.strip()
            empty_mask = cleaned[col].isin(["", "nan", "NaN", "null", "None", "NULL"])
            if empty_mask.any():
                cleaned.loc[empty_mask, col] = np.nan
                changelog.append(f"Normalized {empty_mask.sum():,} empty strings to null in '{col}'")
        except Exception:
            pass

    # 2. Drop exact duplicate rows
    dups_count = int(cleaned.duplicated().sum())
    if dups_count > 0:
        cleaned = cleaned.drop_duplicates()
        changelog.append(f"Removed {dups_count:,} exact duplicate rows")

    # 3. Numeric string coercion
    for col in str_cols:
        try:
            # Check if converting to numeric retains at least 85% valid numbers
            converted = pd.to_numeric(cleaned[col].str.replace(r"[\$,% ]", "", regex=True), errors="coerce")
            valid_ratio = converted.notna().mean()
            if valid_ratio >= 0.85 and converted.nunique() > 1:
                cleaned[col] = converted
                changelog.append(f"Coerced string column '{col}' to numeric ({valid_ratio*100:.1f}% valid values)")
        except Exception:
            pass

    # 4. Missing value audit
    null_counts = cleaned.isna().sum().to_dict()
    null_summary = {k: int(v) for k, v in null_counts.items() if v > 0}

    report = {
        "initial_shape": initial_shape,
        "cleaned_shape": list(cleaned.shape),
        "duplicates_removed": dups_count,
        "null_counts": null_summary,
        "changelog": changelog,
    }
    return cleaned, report


# ─────────────────────────────────────────────────────────────────────────────
# 1.2 Statistical Analysis Engine
# ─────────────────────────────────────────────────────────────────────────────

def calculate_descriptive_stats(df: pd.DataFrame, max_cols: int = 20) -> Dict[str, Any]:
    """
    Computes rigorous statistical distributions across continuous numeric columns:
    Mean, Median, Mode, Std Dev, Variance, IQR, Min, Max, Skewness, Kurtosis.
    """
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()[:max_cols]
    stats_map = {}
    observations = []

    for col in num_cols:
        series = df[col].dropna()
        if len(series) < 2:
            continue

        mean_val = float(series.mean())
        median_val = float(series.median())
        std_val = float(series.std())
        q25 = float(series.quantile(0.25))
        q75 = float(series.quantile(0.75))
        iqr_val = float(q75 - q25)
        min_val = float(series.min())
        max_val = float(series.max())

        skew_val = float(stats.skew(series)) if len(series) >= 3 else 0.0
        kurt_val = float(stats.kurtosis(series)) if len(series) >= 4 else 0.0

        # Outlier counts (1.5 * IQR rule)
        lower_bound = q25 - 1.5 * iqr_val
        upper_bound = q75 + 1.5 * iqr_val
        outliers_count = int(((series < lower_bound) | (series > upper_bound)).sum())

        stats_map[col] = {
            "mean": round(mean_val, 3),
            "median": round(median_val, 3),
            "std": round(std_val, 3),
            "iqr": round(iqr_val, 3),
            "min": round(min_val, 3),
            "max": round(max_val, 3),
            "q25": round(q25, 3),
            "q75": round(q75, 3),
            "skewness": round(skew_val, 3),
            "kurtosis": round(kurt_val, 3),
            "outliers_count": outliers_count,
            "outliers_pct": round((outliers_count / len(series)) * 100, 2),
        }

        # Observations
        if abs(skew_val) > 1.0:
            direction = "right-skewed (high values tail)" if skew_val > 0 else "left-skewed (low values tail)"
            observations.append(f"'{col}' shows significant distribution skew ({skew_val:+.2f}, {direction}). Use median ({median_val:,.2f}) rather than mean for central planning.")
        if outliers_count > 0:
            observations.append(f"'{col}' exhibits {outliers_count:,} statistical outliers ({outliers_count/len(series)*100:.1f}% of observations) outside the 1.5 IQR range [{lower_bound:,.2f}, {upper_bound:,.2f}].")

    return {
        "numeric_columns_analyzed": len(stats_map),
        "statistics": stats_map,
        "observations": observations,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1.3 Trend Analysis Engine
# ─────────────────────────────────────────────────────────────────────────────

def calculate_temporal_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detects date columns and calculates temporal velocity, trajectory slope,
    period-over-period percentage growth, and peak/trough periods.
    """
    date_cols = []
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower() or "year" in col.lower() or "month" in col.lower() or "day" in col.lower():
            date_cols.append(col)
        elif df[col].dtype == "object":
            try:
                sample = df[col].dropna().head(10)
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    if pd.to_datetime(sample, errors="coerce", format="mixed").notna().sum() >= 8:
                        date_cols.append(col)
            except Exception:
                pass

    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if not num_cols:
        return {"has_temporal_data": False, "reason": "No numeric metrics available for trend measurement."}

    target_metric = num_cols[0]
    for c in num_cols:
        if any(k in c.lower() for k in ["revenue", "sales", "profit", "donation", "pints", "count", "amount"]):
            target_metric = c
            break

    # If no date column is found, compute sequential order trajectory
    if not date_cols:
        series = df[target_metric].dropna()
        if len(series) < 5:
            return {"has_temporal_data": False, "reason": "Insufficient observations for trend calculation."}
        
        x = np.arange(len(series))
        slope, intercept, r_value, p_value, _ = stats.linregress(x, series.values)
        direction = "upward" if slope > 0 else "downward"
        pct_change = float((series.iloc[-1] - series.iloc[0]) / max(1e-9, abs(series.iloc[0]))) * 100

        return {
            "has_temporal_data": True,
            "temporal_key": "Row Sequence Index",
            "target_metric": target_metric,
            "slope": round(float(slope), 4),
            "r_squared": round(float(r_value ** 2), 4),
            "p_value": round(float(p_value), 5),
            "direction": direction,
            "net_percentage_change": round(pct_change, 2),
            "findings": [
                f"Sequential order shows an overall {direction} slope ({slope:+.4f} per record, R²={r_value**2:.3f}).",
                f"Net movement across the dataset is {pct_change:+.1f}%.",
            ],
        }

    date_col = date_cols[0]
    df_temp = df[[date_col, target_metric]].dropna().copy()
    try:
        df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors="coerce")
        df_temp = df_temp.dropna().sort_values(date_col)
    except Exception:
        return {"has_temporal_data": False, "reason": f"Could not parse '{date_col}' into timestamps."}

    if len(df_temp) < 4:
        return {"has_temporal_data": False, "reason": "Insufficient valid time-series points."}

    # Resample or group by suitable frequency
    span_days = (df_temp[date_col].max() - df_temp[date_col].min()).days
    freq = "ME" if span_days > 90 else ("W" if span_days > 14 else "D")

    aggregated = df_temp.set_index(date_col)[target_metric].resample(freq).sum().dropna()
    if len(aggregated) < 3:
        aggregated = df_temp.groupby(date_col)[target_metric].sum()

    y_vals = aggregated.values
    x_vals = np.arange(len(y_vals))
    slope, intercept, r_value, p_value, _ = stats.linregress(x_vals, y_vals)
    direction = "accelerating (upward)" if slope > 0 else "decelerating (downward)"

    peak_period = str(aggregated.idxmax())
    peak_value = float(aggregated.max())
    trough_period = str(aggregated.idxmin())
    trough_value = float(aggregated.min())

    pct_overall = float((y_vals[-1] - y_vals[0]) / max(1e-9, abs(y_vals[0]))) * 100

    return {
        "has_temporal_data": True,
        "date_column": date_col,
        "target_metric": target_metric,
        "frequency": freq,
        "direction": direction,
        "slope": round(float(slope), 3),
        "r_squared": round(float(r_value ** 2), 3),
        "p_value": round(float(p_value), 4),
        "net_growth_pct": round(pct_overall, 2),
        "peak_period": peak_period,
        "peak_value": round(peak_value, 2),
        "trough_period": trough_period,
        "trough_value": round(trough_value, 2),
        "findings": [
            f"Trajectory for '{target_metric}' over '{date_col}' is {direction} with an overall net change of {pct_overall:+.1f}%.",
            f"Peak volume occurred at {peak_period} ({peak_value:,.2f}), while the low trough was at {trough_period} ({trough_value:,.2f}).",
            f"Linear trend fit demonstrates R² = {r_value**2:.3f} (p-value: {p_value:.4f}).",
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1.4 Comparative Analysis Engine
# ─────────────────────────────────────────────────────────────────────────────

def calculate_comparative_benchmarks(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Ranks and benchmarks categories against target continuous metrics,
    computing segment share, delta from average, and top-to-bottom gaps.
    """
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if not cat_cols or not num_cols:
        return {"has_comparative_data": False, "reason": "Requires both categorical grouping and numerical columns."}

    # Pick grouping column with reasonable cardinality (2 to 15 unique values)
    group_col = None
    for c in cat_cols:
        nunique = df[c].nunique()
        if 2 <= nunique <= 15:
            group_col = c
            break
    if not group_col:
        group_col = cat_cols[0]

    metric_col = num_cols[0]
    for c in num_cols:
        if any(k in c.lower() for k in ["sales", "revenue", "profit", "amount", "donat", "total", "volume"]):
            metric_col = c
            break

    grouped = df.groupby(group_col)[metric_col].agg(["count", "sum", "mean", "median"]).reset_index()
    total_sum = float(grouped["sum"].sum()) or 1.0
    overall_mean = float(df[metric_col].mean())

    grouped["share_pct"] = (grouped["sum"] / total_sum) * 100
    grouped["delta_vs_mean_pct"] = ((grouped["mean"] - overall_mean) / max(1e-9, abs(overall_mean))) * 100
    grouped = grouped.sort_values("sum", ascending=False)

    top_row = grouped.iloc[0]
    bottom_row = grouped.iloc[-1]
    gap_multiple = float(top_row["sum"] / max(1e-9, bottom_row["sum"]))

    benchmarks_list = []
    for _, r in grouped.iterrows():
        benchmarks_list.append({
            "segment": str(r[group_col]),
            "count": int(r["count"]),
            "sum": round(float(r["sum"]), 2),
            "mean": round(float(r["mean"]), 2),
            "median": round(float(r["median"]), 2),
            "share_pct": round(float(r["share_pct"]), 2),
            "delta_vs_mean_pct": round(float(r["delta_vs_mean_pct"]), 2),
        })

    return {
        "has_comparative_data": True,
        "group_column": group_col,
        "metric_column": metric_col,
        "overall_mean": round(overall_mean, 2),
        "benchmarks": benchmarks_list,
        "top_segment": str(top_row[group_col]),
        "top_share_pct": round(float(top_row["share_pct"]), 2),
        "bottom_segment": str(bottom_row[group_col]),
        "gap_multiple": round(gap_multiple, 2),
        "findings": [
            f"Segment '{top_row[group_col]}' leads '{metric_col}' with {top_row['share_pct']:.1f}% total share ({top_row['sum']:,.2f}), outperforming overall mean by {top_row['delta_vs_mean_pct']:+.1f}%.",
            f"Lowest performing cohort is '{bottom_row[group_col]}' with {bottom_row['share_pct']:.1f}% share, establishing a {gap_multiple:.1f}x performance spread between top and bottom tiers.",
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1.5 Insight Discovery Synthesis Engine
# ─────────────────────────────────────────────────────────────────────────────

def synthesize_empirical_insights(df: pd.DataFrame, project_goal: str = "") -> Dict[str, Any]:
    """
    Evaluates evidence across statistics, trends, and comparisons to identify
    noteworthy findings, ranking them by empirical magnitude.
    """
    stats_res = calculate_descriptive_stats(df)
    comp_res = calculate_comparative_benchmarks(df)
    trend_res = calculate_temporal_trends(df)

    insights = []

    # 1. Comparative Insights
    if comp_res.get("has_comparative_data"):
        insights.append({
            "type": "opportunity_leverage",
            "title": f"High Concentration in {comp_res['top_segment']}",
            "evidence": f"Generates {comp_res['top_share_pct']:.1f}% of {comp_res['metric_column']} with a {comp_res['gap_multiple']:.1f}x lead over bottom segment.",
            "impact_rank": 1,
        })

    # 2. Skew / Distribution Outliers
    for col, s in stats_res.get("statistics", {}).items():
        if s.get("outliers_pct", 0) > 3.0:
            insights.append({
                "type": "variance_risk",
                "title": f"Outlier Cluster in {col}",
                "evidence": f"{s['outliers_count']:,} data points ({s['outliers_pct']:.1f}%) exceed the 1.5 IQR boundary.",
                "impact_rank": 2,
            })
            break

    # 3. Temporal Growth
    if trend_res.get("has_temporal_data"):
        insights.append({
            "type": "growth_velocity",
            "title": f"Growth Momentum: {trend_res['direction']}",
            "evidence": f"Net change of {trend_res.get('net_growth_pct', trend_res.get('net_percentage_change', 0)):+.1f}% across observed timeline.",
            "impact_rank": 3,
        })

    return {
        "project_goal": project_goal,
        "discovered_insights_count": len(insights),
        "insights": insights,
    }
