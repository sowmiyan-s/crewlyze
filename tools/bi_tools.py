# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Business Intelligence & Growth Analytics Tools for CrewAI agents.

Equips agents with safe, read-only Pandas analytical tools to query real dataset
numbers, slice segments, calculate correlations, audit margin leakage, run
predictive feature importance, and measure growth velocity.
"""

import os
import sys
import numpy as np
import pandas as pd
from typing import Optional, Union
from crewai.tools import tool

from tools.dataset_tools import read_csv_robust, _df_to_markdown


def _resolve_csv_path(file_path: Optional[str] = None) -> str:
    """Resolve active session CSV path."""
    fp = file_path
    if not fp or not isinstance(fp, str) or fp.lower() == "none" or "properties" in str(fp) or not os.path.exists(fp):
        from config.context import current_session_csv
        fp = current_session_csv.get() or os.getenv("CURRENT_SESSION_CSV", "")
    return fp


def query_segment_performance(
    dimension: str,
    metric: str,
    agg: str = "sum",
    top_n: int = 10,
    file_path: Optional[str] = None
) -> str:
    """
    Group dataset by a categorical/dimension column and aggregate a numeric metric.
    Useful for identifying top revenue drivers, high-performing cohorts, or underperforming categories.

    Args:
        dimension: Categorical column name to group by (e.g., 'Category', 'Region', 'Plan_Tier', 'Customer_Segment')
        metric: Numeric column name to aggregate (e.g., 'Revenue', 'Sales', 'Profit', 'Units_Sold', 'Churn_Count')
        agg: Aggregation function ('sum', 'mean', 'median', 'count', 'std'). Default is 'sum'.
        top_n: Number of top groups to return (default: 10).
        file_path: Optional path to CSV file.
    """
    try:
        fp = _resolve_csv_path(file_path)
        if not fp or not os.path.exists(fp):
            return "Error: Active dataset file not found."

        df = read_csv_robust(fp)
        if dimension not in df.columns:
            available = ", ".join(df.columns[:10])
            return f"Error: Dimension '{dimension}' not found in dataset. Available columns: {available}"
        if metric not in df.columns:
            available_num = ", ".join(df.select_dtypes(include=["number"]).columns[:10])
            return f"Error: Metric '{metric}' not found in dataset. Available numeric columns: {available_num}"

        num_series = pd.to_numeric(df[metric], errors="coerce")
        temp_df = pd.DataFrame({dimension: df[dimension].astype(str), metric: num_series}).dropna()

        agg_map = {
            "sum": "sum",
            "mean": "mean",
            "avg": "mean",
            "median": "median",
            "count": "count",
            "std": "std",
        }
        func = agg_map.get(str(agg).lower().strip(), "sum")

        grouped = temp_df.groupby(dimension)[metric].agg(func).reset_index()
        grouped = grouped.sort_values(by=metric, ascending=False).head(int(top_n))

        total_val = temp_df[metric].sum() if func == "sum" else None
        if total_val and total_val > 0:
            grouped["Share_Pct"] = (grouped[metric] / total_val * 100).round(2).astype(str) + "%"

        grouped[metric] = grouped[metric].round(2)
        md_table = _df_to_markdown(grouped, index=False)
        return f"### Segment Breakdown: '{metric}' by '{dimension}' (agg: {func})\n\n{md_table}"
    except Exception as e:
        return f"Error querying segment performance: {e}"


def calculate_driver_correlations(
    target_metric: Optional[str] = None,
    file_path: Optional[str] = None
) -> str:
    """
    Compute correlation matrix against a primary target commercial metric (or overall top-10 drivers).
    Identifies positive growth accelerators and negative friction factors.

    Args:
        target_metric: The primary target metric column (e.g., 'Revenue', 'Profit', 'Churn', 'Conversion_Rate').
                       If not specified, returns the top correlation pairs in the dataset.
        file_path: Optional path to CSV file.
    """
    try:
        fp = _resolve_csv_path(file_path)
        if not fp or not os.path.exists(fp):
            return "Error: Active dataset file not found."

        df = read_csv_robust(fp)
        num_df = df.select_dtypes(include=["number"])
        if num_df.empty or num_df.shape[1] < 2:
            return "Insufficient numeric columns to calculate correlations."

        if target_metric and target_metric in num_df.columns:
            target_corr = num_df.corr()[target_metric].drop(target_metric, errors="ignore").dropna()
            ranked = target_corr.abs().sort_values(ascending=False).head(8)
            rows = []
            for col in ranked.index:
                coeff = target_corr[col]
                direction = "Positive Accelerator" if coeff > 0 else "Negative Friction/Drag"
                strength = "Strong" if abs(coeff) > 0.6 else ("Moderate" if abs(coeff) > 0.3 else "Weak")
                rows.append({
                    "Driver_Column": col,
                    "Correlation_Coefficient": round(coeff, 3),
                    "Impact_Type": direction,
                    "Strength": strength
                })
            res_df = pd.DataFrame(rows)
            return f"### Primary Drivers of '{target_metric}':\n\n{_df_to_markdown(res_df, index=False)}"

        # General top pairs
        corr = num_df.corr().abs()
        np.fill_diagonal(corr.values, 0)
        unstacked = corr.unstack().reset_index()
        unstacked.columns = ["Variable_A", "Variable_B", "Absolute_Correlation"]
        unstacked["Pair"] = unstacked.apply(lambda r: "-".join(sorted([r["Variable_A"], r["Variable_B"]])), axis=1)
        deduped = unstacked.drop_duplicates(subset=["Pair"]).sort_values(by="Absolute_Correlation", ascending=False).head(10)
        deduped["Absolute_Correlation"] = deduped["Absolute_Correlation"].round(3)
        deduped = deduped[["Variable_A", "Variable_B", "Absolute_Correlation"]]
        return f"### Top Discovered Variable Connections:\n\n{_df_to_markdown(deduped, index=False)}"
    except Exception as e:
        return f"Error calculating driver correlations: {e}"


def audit_margin_leakage(
    metric: Optional[str] = None,
    dimension: Optional[str] = None,
    file_path: Optional[str] = None
) -> str:
    """
    Audit dataset for operational risks, extreme cost/margin leakage, IQR outliers, and loss points.
    Useful for answering 'Problem in Y likely' operational questions.

    Args:
        metric: Numeric metric to audit (e.g. 'Discount', 'Refund_Amount', 'Cost', 'Days_To_Close', 'Error_Count').
                If None, auto-selects high-variance numeric columns.
        dimension: Optional category to pinpoint which segment contains the most anomalies.
        file_path: Optional path to CSV file.
    """
    try:
        fp = _resolve_csv_path(file_path)
        if not fp or not os.path.exists(fp):
            return "Error: Active dataset file not found."

        df = read_csv_robust(fp)
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not num_cols:
            return "No numeric metrics available to audit."

        target_metric = metric if (metric and metric in num_cols) else num_cols[0]
        series = pd.to_numeric(df[target_metric], errors="coerce").dropna()
        if series.empty:
            return f"Metric '{target_metric}' contains no valid numeric records."

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = series[(series < lower_bound) | (series > upper_bound)]
        outlier_pct = round(len(outliers) / len(series) * 100, 2)

        res = [
            f"### Risk & Anomaly Audit for '{target_metric}'",
            f"- Total Records: {len(series):,}",
            f"- Normal Range [Q1-1.5*IQR to Q3+1.5*IQR]: {lower_bound:.2f} to {upper_bound:.2f}",
            f"- Outlier Count: {len(outliers):,} ({outlier_pct}% of total records)",
            f"- Median: {series.median():.2f} | Mean: {series.mean():.2f} | Max: {series.max():.2f} | Min: {series.min():.2f}"
        ]

        if dimension and dimension in df.columns:
            outlier_indices = outliers.index
            seg_outliers = df.loc[outlier_indices, dimension].value_counts().head(5).reset_index()
            seg_outliers.columns = [dimension, "Anomaly_Count"]
            res.append(f"\n#### Segments with Highest Outlier Concentration:\n{_df_to_markdown(seg_outliers, index=False)}")

        return "\n".join(res)
    except Exception as e:
        return f"Error auditing anomalies: {e}"


def train_predictive_driver_model(
    target_metric: Optional[str] = None,
    file_path: Optional[str] = None
) -> str:
    """
    Train a Random Forest model on the dataset to extract quantitative feature importance rankings.
    Proves exactly which features have the strongest mathematical power in predicting the target metric.

    Args:
        target_metric: The target column to predict (e.g., 'Revenue', 'Retention', 'Deal_Size', 'Donated').
        file_path: Optional path to CSV file.
    """
    try:
        fp = _resolve_csv_path(file_path)
        if not fp or not os.path.exists(fp):
            return "Error: Active dataset file not found."

        from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
        df = read_csv_robust(fp)
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if len(num_cols) < 2:
            return "Need at least 2 numeric columns for predictive driver modeling."

        target = target_metric if (target_metric and target_metric in df.columns) else num_cols[-1]
        features = [c for c in num_cols if c != target]

        clean_df = df[features + [target]].dropna()
        if len(clean_df) < 10:
            return "Insufficient clean rows for predictive modeling."

        X = clean_df[features]
        y = clean_df[target]

        is_classification = y.nunique() <= 10 or y.dtype == "object"
        if is_classification:
            model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=6)
        else:
            model = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=6)

        model.fit(X, y)
        importances = model.feature_importances_

        fi_df = pd.DataFrame({
            "Feature_Column": features,
            "Predictive_Importance_Pct": (importances * 100).round(2)
        }).sort_values(by="Predictive_Importance_Pct", ascending=False).head(8)

        fi_df["Predictive_Importance_Pct"] = fi_df["Predictive_Importance_Pct"].astype(str) + "%"
        md = _df_to_markdown(fi_df, index=False)
        model_type = "RandomForest Classifier" if is_classification else "RandomForest Regressor"
        return f"### Predictive Drivers for Target: '{target}' ({model_type})\n\n{md}"
    except Exception as e:
        return f"Error training predictive driver model: {e}"


def calculate_velocity_and_growth(
    time_column: Optional[str] = None,
    metric: Optional[str] = None,
    file_path: Optional[str] = None
) -> str:
    """
    Detect temporal progression and calculate historical velocity, growth rates, and run-rate momentum.

    Args:
        time_column: Date, Year, or Period column name (e.g., 'Date', 'Year', 'Month', 'Quarter').
        metric: Numeric commercial metric to track over time (e.g., 'Revenue', 'Orders', 'Volume').
        file_path: Optional path to CSV file.
    """
    try:
        fp = _resolve_csv_path(file_path)
        if not fp or not os.path.exists(fp):
            return "Error: Active dataset file not found."

        df = read_csv_robust(fp)
        
        # Find candidate time column if not supplied
        candidate_time = time_column
        if not candidate_time or candidate_time not in df.columns:
            for col in df.columns:
                col_l = col.lower()
                if any(t in col_l for t in ["date", "year", "time", "month", "quarter", "period", "timestamp"]):
                    candidate_time = col
                    break

        if not candidate_time or candidate_time not in df.columns:
            return "No temporal (Date/Year/Period) column found in this dataset."

        # Find candidate numeric metric
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if candidate_time in num_cols:
            num_cols.remove(candidate_time)

        candidate_metric = metric if (metric and metric in df.columns) else (num_cols[0] if num_cols else None)
        if not candidate_metric:
            return f"No numeric metric available to evaluate velocity over time column '{candidate_time}'."

        # Aggregate
        temp_df = df[[candidate_time, candidate_metric]].dropna()
        try:
            temp_df["dt"] = pd.to_datetime(temp_df[candidate_time], errors="coerce")
            if temp_df["dt"].notnull().sum() > len(temp_df) * 0.5:
                temp_df = temp_df.sort_values(by="dt")
                temp_df["Period_Str"] = temp_df["dt"].dt.to_period("M").astype(str)
            else:
                temp_df = temp_df.sort_values(by=candidate_time)
                temp_df["Period_Str"] = temp_df[candidate_time].astype(str)
        except Exception:
            temp_df = temp_df.sort_values(by=candidate_time)
            temp_df["Period_Str"] = temp_df[candidate_time].astype(str)

        velocity = temp_df.groupby("Period_Str")[candidate_metric].sum().reset_index()
        velocity["Period_Over_Period_Growth"] = velocity[candidate_metric].pct_change().multiply(100).round(2)
        velocity[candidate_metric] = velocity[candidate_metric].round(2)

        velocity["Growth_Pct"] = velocity["Period_Over_Period_Growth"].apply(
            lambda x: f"{x:+.2f}%" if pd.notnull(x) else "Baseline (Base Period)"
        )
        out_df = velocity[["Period_Str", candidate_metric, "Growth_Pct"]].tail(10)
        md = _df_to_markdown(out_df, index=False)
        return f"### Growth Velocity & Trajectory ('{candidate_metric}' by '{candidate_time}'):\n\n{md}"
    except Exception as e:
        return f"Error computing growth velocity: {e}"


class BusinessIntelligenceTools:
    """CrewAI tool registry for Autonomous BI agents."""
    query_segment_performance = tool("Query Segment Breakdown")(query_segment_performance)
    calculate_driver_correlations = tool("Calculate Driver Correlations")(calculate_driver_correlations)
    audit_margin_leakage = tool("Audit Margin Leakage and Risk Outliers")(audit_margin_leakage)
    train_predictive_driver_model = tool("Train Predictive Driver Model")(train_predictive_driver_model)
    calculate_velocity_and_growth = tool("Calculate Growth Velocity and Momentum")(calculate_velocity_and_growth)
