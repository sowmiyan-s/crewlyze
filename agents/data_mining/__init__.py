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
from tools.artifact_manager import ArtifactManager
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

        artifacts = []
        sid = context.get("session_id") if context else None
        if sid and res.get("cluster_profiles"):
            art = ArtifactManager.save_rows_csv(
                sid,
                "cluster_profiles.csv",
                res["cluster_profiles"],
                "Multivariate Cluster Centroids & Profiles",
            )
            if art:
                artifacts.append(art)

        top_c = res.get("cluster_profiles", [{}])[0]
        return {
            "metrics": {
                "clusters_count": res.get("clusters_evaluated", 0),
                "dominant_cluster_id": top_c.get("cluster_id"),
                "dominant_cluster_share_pct": top_c.get("share_pct"),
            },
            "findings": res.get("findings", []),
            "tables": [{"title": "Multivariate Cluster Profiles", "rows": res.get("cluster_profiles", [])}],
            "artifacts": artifacts,
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

        artifacts = []
        sid = context.get("session_id") if context else None
        if sid and res.get("top_relationships"):
            art = ArtifactManager.save_rows_csv(
                sid,
                "correlation_matrix.csv",
                res["top_relationships"],
                "Cross-Feature Correlation Matrix",
            )
            if art:
                artifacts.append(art)

        top_rel = res.get("top_relationships", [{}])[0]
        return {
            "metrics": {
                "strongest_pair": f"{top_rel.get('feature_x')} vs {top_rel.get('feature_y')}",
                "max_correlation": top_rel.get("correlation", 0.0),
                "evaluated_pairs": res.get("evaluated_pairs_count", 0),
            },
            "findings": res.get("findings", []),
            "tables": [{"title": "Strongest Variable Relationships", "rows": res.get("top_relationships", [])}],
            "artifacts": artifacts,
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
        artifacts = []
        sid = context.get("session_id") if context else None
        if sid and segments:
            art = ArtifactManager.save_rows_csv(
                sid,
                "strategic_segments.csv",
                segments,
                "Strategic Tier Segmentation Breakdown",
            )
            if art:
                artifacts.append(art)

        return {
            "metrics": {
                "tier_1_volume_share_pct": segments[0].get("share_of_volume_pct", 0.0) if segments else 0.0,
                "tier_1_count": segments[0].get("count", 0) if segments else 0,
            },
            "findings": res.get("findings", []),
            "tables": [{"title": "Strategic Tier Segmentation", "rows": segments}],
            "artifacts": artifacts,
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

        artifacts = []
        sid = context.get("session_id") if context else None
        if sid and res.get("top_outlier_examples"):
            art = ArtifactManager.save_rows_csv(
                sid,
                "flagged_anomalies.csv",
                res["top_outlier_examples"],
                "Flagged Statistical Outliers",
            )
            if art:
                artifacts.append(art)

        return {
            "metrics": {
                "anomalies_detected": res.get("anomalies_detected_count", 0),
                "anomaly_rate_pct": res.get("anomalies_pct", 0.0),
            },
            "findings": res.get("findings", []),
            "tables": [{"title": "Top Anomaly Records", "rows": res.get("top_outlier_examples", [])}],
            "artifacts": artifacts,
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

        artifacts = []
        sid = context.get("session_id") if context else None
        top_assocs = res.get("top_associations", [])
        if sid and top_assocs:
            art = ArtifactManager.save_rows_csv(
                sid,
                "association_rules.csv",
                top_assocs,
                "Frequent Association Co-occurrences",
            )
            if art:
                artifacts.append(art)

        return {
            "metrics": {"associations_found": len(top_assocs)},
            "findings": res.get("findings", []),
            "tables": [{"title": "Frequent Association Pairs", "rows": top_assocs}],
            "artifacts": artifacts,
            "provenance": {"method": "mine_associations"},
        }
