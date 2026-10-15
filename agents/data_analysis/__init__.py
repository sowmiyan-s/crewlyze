# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Category 1: Data Analysis Agents.
Provides 5 specialized analytical agents:
  1.1 DataCleanerAgent
  1.2 StatisticalAnalysisAgent
  1.3 TrendAnalysisAgent
  1.4 ComparativeAnalysisAgent
  1.5 InsightDiscoveryAgent
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from agents.base_agent import BaseIntelligenceAgent, InspectionResult
from tools.stats_tools import (
    clean_dataset_safely,
    calculate_descriptive_stats,
    calculate_temporal_trends,
    calculate_comparative_benchmarks,
    synthesize_empirical_insights,
)


class DataCleanerAgent(BaseIntelligenceAgent):
    agent_id = "data_cleaner"
    name = "Data Cleaner Agent"
    category = "data_analysis"
    description = "Detects missing values, duplicates, whitespace anomalies, and standardizes data types."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        if df is None or df.empty:
            return InspectionResult(is_eligible=False, reason="Dataset is empty.")
        return InspectionResult(is_eligible=True, reason="Dataset schema ready for cleaning inspection.")

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cleaned_df, report = clean_dataset_safely(df)
        if context and "context_bus" in context:
            context["context_bus"].set_shared("cleaned_df", cleaned_df)

        return {
            "metrics": {
                "initial_rows": report["initial_shape"][0],
                "cleaned_rows": report["cleaned_shape"][0],
                "duplicates_removed": report["duplicates_removed"],
                "missing_columns_count": len(report["null_counts"]),
            },
            "findings": report["changelog"] or ["Dataset conforms to hygiene standards; no destructive edits required."],
            "tables": [{"title": "Data Hygiene Changelog", "rows": [{"action": c} for c in report["changelog"]]}],
            "provenance": {"method": "clean_dataset_safely", "deduplication": "exact_match"},
        }


class StatisticalAnalysisAgent(BaseIntelligenceAgent):
    agent_id = "statistical_analysis"
    name = "Statistical Analysis Agent"
    category = "data_analysis"
    description = "Computes distributions, mean, median, IQR, skewness, and identifies statistical outliers."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not num_cols:
            return InspectionResult(is_eligible=False, reason="No numerical variables available for statistical analysis.")
        return InspectionResult(is_eligible=True, target_columns=num_cols)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = calculate_descriptive_stats(df)
        metrics = {}
        first_col = plan["target_columns"][0] if plan.get("target_columns") else None
        if first_col and first_col in res["statistics"]:
            s = res["statistics"][first_col]
            metrics = {
                f"{first_col}_mean": s["mean"],
                f"{first_col}_median": s["median"],
                f"{first_col}_iqr": s["iqr"],
                f"{first_col}_skew": s["skewness"],
            }

        return {
            "metrics": metrics,
            "findings": res["observations"] or ["All continuous features follow balanced distribution profiles."],
            "tables": [{"title": "Descriptive Statistics Matrix", "rows": [{"column": k, **v} for k, v in res["statistics"].items()]}],
            "provenance": {"method": "calculate_descriptive_stats", "engine": "scipy.stats"},
        }


class TrendAnalysisAgent(BaseIntelligenceAgent):
    agent_id = "trend_analysis"
    name = "Trend Analysis Agent"
    category = "data_analysis"
    description = "Detects temporal velocity, directional momentum, period-over-period growth, and peaks."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not num_cols:
            return InspectionResult(is_eligible=False, reason="Requires numeric metrics to analyze trend velocity.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = calculate_temporal_trends(df)
        if not res.get("has_temporal_data"):
            return {
                "metrics": {},
                "findings": [res.get("reason", "Temporal analysis unavailable.")],
            }

        metrics = {
            "trajectory": res.get("direction", "neutral"),
            "net_growth_pct": res.get("net_growth_pct", res.get("net_percentage_change", 0.0)),
            "r_squared": res.get("r_squared", 0.0),
        }
        return {
            "metrics": metrics,
            "findings": res.get("findings", []),
            "provenance": {"method": "calculate_temporal_trends", "temporal_key": res.get("temporal_key", res.get("date_column"))},
        }


class ComparativeAnalysisAgent(BaseIntelligenceAgent):
    agent_id = "comparative_analysis"
    name = "Comparative Analysis Agent"
    category = "data_analysis"
    description = "Benchmarks categories, ranks cohorts, and isolates the largest segment performance gaps."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not cat_cols or not num_cols:
            return InspectionResult(is_eligible=False, reason="Requires both categorical groups and numerical columns.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = calculate_comparative_benchmarks(df)
        if not res.get("has_comparative_data"):
            return {"metrics": {}, "findings": [res.get("reason", "Comparative data unavailable.")]}

        return {
            "metrics": {
                "top_segment": res["top_segment"],
                "top_share_pct": res["top_share_pct"],
                "gap_multiple": res["gap_multiple"],
            },
            "findings": res.get("findings", []),
            "tables": [{"title": f"Cohort Benchmarks ({res['group_column']} vs {res['metric_column']})", "rows": res.get("benchmarks", [])}],
            "provenance": {"method": "calculate_comparative_benchmarks"},
        }


class InsightDiscoveryAgent(BaseIntelligenceAgent):
    agent_id = "insight_discovery"
    name = "Insight Discovery Agent"
    category = "data_analysis"
    description = "Synthesizes observations across multi-agent findings and ranks discoveries by commercial impact."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        if df is None or len(df) < 2:
            return InspectionResult(is_eligible=False, reason="Insufficient records for insight synthesis.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = synthesize_empirical_insights(df, plan.get("goal", ""))
        findings = [f"[{i['title']}]: {i['evidence']}" for i in res.get("insights", [])]

        return {
            "metrics": {"discovered_insights_count": res.get("discovered_insights_count", 0)},
            "findings": findings or ["Dataset displays homogeneous behavior with no extreme variance anomalies."],
            "tables": [{"title": "Ranked Empirical Insights", "rows": res.get("insights", [])}],
            "provenance": {"method": "synthesize_empirical_insights"},
        }
