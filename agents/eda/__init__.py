# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Category 5: Exploratory Data Analysis (EDA) Agents.
Provides 5 specialized exploration and visualization agents:
  5.1 DatasetExplorerAgent
  5.2 NaturalLanguageDataQueryAgent
  5.3 VisualizationAgent
  5.4 DataQualityInspectorAgent
  5.5 DataStorytellingAgent
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from agents.base_agent import BaseIntelligenceAgent, InspectionResult
from tools.artifact_manager import ArtifactManager
from tools.eda_tools import (
    explore_dataset_schema,
    execute_natural_query,
    generate_executive_visualizations,
    inspect_data_quality,
    compose_data_story,
)


class DatasetExplorerAgent(BaseIntelligenceAgent):
    agent_id = "dataset_explorer"
    name = "Dataset Explorer Agent"
    category = "eda"
    description = "Inspects schema, cardinality, missingness, memory usage, and candidate roles."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        if df is None or df.empty:
            return InspectionResult(is_eligible=False, reason="Dataset is empty.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = explore_dataset_schema(df)
        dims = res.get("dimensions", {})
        artifacts = []
        sid = context.get("session_id") if context else None
        if sid and res.get("columns_dictionary"):
            art = ArtifactManager.save_rows_csv(
                sid,
                "column_dictionary.csv",
                res["columns_dictionary"],
                "Dataset Schema & Column Dictionary",
            )
            if art:
                artifacts.append(art)

        return {
            "metrics": {
                "rows_count": dims.get("rows", 0),
                "cols_count": dims.get("columns", 0),
                "memory_mb": res.get("memory_usage_mb", 0.0),
            },
            "findings": res.get("findings", []),
            "tables": [{"title": "Dataset Schema & Column Dictionary", "rows": res.get("columns_dictionary", [])}],
            "artifacts": artifacts,
            "provenance": {"method": "explore_dataset_schema"},
        }


class NaturalLanguageDataQueryAgent(BaseIntelligenceAgent):
    agent_id = "natural_query"
    name = "Natural-Language Data Query Agent"
    category = "eda"
    description = "Executes validated numerical queries, aggregations, and filters in response to natural-language questions."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        if df is None or df.empty:
            return InspectionResult(is_eligible=False, reason="Dataset is empty.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        goal = plan.get("goal") or "What are the primary metrics across this dataset?"
        res = execute_natural_query(df, goal)
        return {
            "metrics": {"queried_value": res.get("direct_value")},
            "findings": [res.get("answer", "Query processed.")],
            "provenance": {"method": "execute_natural_query", "question": goal},
        }


class VisualizationAgent(BaseIntelligenceAgent):
    agent_id = "visualization"
    name = "Visualization Agent"
    category = "eda"
    description = "Generates decoupled interactive Plotly charts and high-resolution visuals without blocking execution."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not num_cols:
            return InspectionResult(is_eligible=False, reason="No numeric metrics available to plot.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        output_dir = None
        if context and "context_bus" in context:
            output_dir = context["context_bus"].get_shared("output_dir")

        res = generate_executive_visualizations(df, output_dir=output_dir)
        charts = res.get("charts", [])
        findings = [f"Generated {c['title']}: {c['insight']}" for c in charts]

        return {
            "metrics": {
                "charts_count": res.get("charts_generated", 0),
                "png_saved_count": len(res.get("saved_pngs", [])),
            },
            "findings": findings or ["Rendered baseline visual figures for key variables."],
            "visuals": charts,
            "provenance": {"method": "generate_executive_visualizations", "engine": "pure_python_decoupled"},
        }


class DataQualityInspectorAgent(BaseIntelligenceAgent):
    agent_id = "quality_inspector"
    name = "Data Quality Inspector Agent"
    category = "eda"
    description = "Calculates objective Data Health Score (0-100), duplicate rates, null violations, and outlier counts."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        if df is None or df.empty:
            return InspectionResult(is_eligible=False, reason="Dataset is empty.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = inspect_data_quality(df)
        return {
            "metrics": {
                "health_score": res.get("data_health_score", 100),
                "grade": res.get("grade", "Excellent"),
                "null_pct": res.get("null_cells_percentage", 0.0),
                "duplicate_rows": res.get("duplicate_rows", 0),
            },
            "findings": res.get("findings", []) + res.get("deductions", []),
            "provenance": {"method": "inspect_data_quality"},
        }


class DataStorytellingAgent(BaseIntelligenceAgent):
    agent_id = "storytelling"
    name = "Data Storytelling Agent"
    category = "eda"
    description = "Synthesizes multi-agent findings into a clear, boardroom-ready narrative report."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        summary_points = []
        if context and "context_bus" in context:
            summary = context["context_bus"].get_context_summary(max_length=1500)
            if summary:
                summary_points = [line.strip("- ") for line in summary.split("\n") if line.strip().startswith("-")]

        res = compose_data_story(df, findings=summary_points)
        return {
            "metrics": {"narrative_paragraphs": len(res.get("narrative", "").split("\n\n"))},
            "findings": res.get("key_takeaways", []),
            "narrative": res.get("narrative", ""),
            "provenance": {"method": "compose_data_story"},
        }
