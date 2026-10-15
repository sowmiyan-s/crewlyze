# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Category 3: Data Mining Agents.
Provides 5 specialized data mining agents:
  3.1 PatternDiscoveryAgent
  3.2 RelationshipAnalysisAgent
  3.3 SegmentationAgent
  3.4 AnomalyDetectionAgent
  3.5 AssociationMiningAgent
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from agents.base_agent import BaseIntelligenceAgent, InspectionResult
from tools.mining_tools import (
    discover_patterns_clustering,
    analyze_relationships,
    segment_entities,
    detect_anomalies,
    mine_associations,
)


class PatternDiscoveryAgent(BaseIntelligenceAgent):
    agent_id = "pattern_discovery"
    name = "Pattern Discovery Agent"
    category = "data_mining"
    description = "Discovers hidden clusters, multivariate groupings, and behavioral centroids."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if len(num_cols) < 2:
            return InspectionResult(is_eligible=False, reason="Requires at least 2 numeric features for clustering pattern discovery.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = discover_patterns_clustering(df)
        if not res.get("has_patterns"):
            return {"metrics": {}, "findings": [res.get("reason", "Pattern discovery unavailable.")]}

        top_c = res.get("cluster_profiles", [{}])[0]
        return {
            "metrics": {
                "clusters_count": res.get("clusters_evaluated", 0),
                "dominant_cluster_id": top_c.get("cluster_id"),
                "dominant_cluster_share_pct": top_c.get("share_pct"),
            },
            "findings": res.get("findings", []),
            "tables": [{"title": "Multivariate Cluster Profiles", "rows": res.get("cluster_profiles", [])}],
            "provenance": {"method": "discover_patterns_clustering", "algorithm": "KMeans"},
        }


class RelationshipAnalysisAgent(BaseIntelligenceAgent):
    agent_id = "relationship_analysis"
    name = "Relationship Analysis Agent"
    category = "data_mining"
    description = "Computes correlation coefficients and cross-variable dependencies."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if len(num_cols) < 2:
            return InspectionResult(is_eligible=False, reason="At least 2 numeric variables required for relationship correlation.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = analyze_relationships(df)
        if not res.get("has_relationships"):
            return {"metrics": {}, "findings": [res.get("reason", "Relationship analysis unavailable.")]}

        top_rel = res.get("top_relationships", [{}])[0]
        return {
            "metrics": {
                "strongest_pair": f"{top_rel.get('feature_x')} vs {top_rel.get('feature_y')}",
                "max_correlation": top_rel.get("correlation", 0.0),
                "evaluated_pairs": res.get("evaluated_pairs_count", 0),
            },
            "findings": res.get("findings", []),
            "tables": [{"title": "Strongest Variable Relationships", "rows": res.get("top_relationships", [])}],
            "provenance": {"method": "analyze_relationships", "metric": "Pearson Correlation"},
        }


class SegmentationAgent(BaseIntelligenceAgent):
    agent_id = "segmentation"
    name = "Segmentation Agent"
    category = "data_mining"
    description = "Partitions observations into distinct strategic performance tiers."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not num_cols:
            return InspectionResult(is_eligible=False, reason="Numeric metric required to segment tiers.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = segment_entities(df)
        if not res.get("has_segmentation"):
            return {"metrics": {}, "findings": [res.get("reason", "Segmentation unavailable.")]}

        segments = res.get("segments", [])
        return {
            "metrics": {
                "tier_1_volume_share_pct": segments[0].get("share_of_volume_pct", 0.0) if segments else 0.0,
                "tier_1_count": segments[0].get("count", 0) if segments else 0,
            },
            "findings": res.get("findings", []),
            "tables": [{"title": "Strategic Tier Segmentation", "rows": segments}],
            "provenance": {"method": "segment_entities", "column": res.get("primary_segmentation_column")},
        }


class AnomalyDetectionAgent(BaseIntelligenceAgent):
    agent_id = "anomaly_detection"
    name = "Anomaly Detection Agent"
    category = "data_mining"
    description = "Executes Isolation Forest to score operational outliers and risk deviations."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if len(num_cols) < 2:
            return InspectionResult(is_eligible=False, reason="Requires at least 2 numerical features for multivariate anomaly detection.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = detect_anomalies(df)
        if not res.get("has_anomalies"):
            return {"metrics": {}, "findings": [res.get("reason", "Anomaly detection unavailable.")]}

        return {
            "metrics": {
                "anomalies_detected": res.get("anomalies_detected_count", 0),
                "anomaly_rate_pct": res.get("anomalies_pct", 0.0),
            },
            "findings": res.get("findings", []),
            "tables": [{"title": "Top Anomaly Records", "rows": res.get("top_outlier_examples", [])}],
            "provenance": {"method": "detect_anomalies", "algorithm": "IsolationForest"},
        }


class AssociationMiningAgent(BaseIntelligenceAgent):
    agent_id = "association_mining"
    name = "Association Mining Agent"
    category = "data_mining"
    description = "Discovers high-frequency co-occurrences and cross-attribute combinations."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if len(cat_cols) < 2:
            return InspectionResult(is_eligible=False, reason="Requires at least 2 categorical variables for association mining.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = mine_associations(df)
        if not res.get("has_associations"):
            return {"metrics": {}, "findings": [res.get("reason", "Association mining unavailable.")]}

        return {
            "metrics": {"associations_found": len(res.get("top_associations", []))},
            "findings": res.get("findings", []),
            "tables": [{"title": "Frequent Association Pairs", "rows": res.get("top_associations", [])}],
            "provenance": {"method": "mine_associations"},
        }
