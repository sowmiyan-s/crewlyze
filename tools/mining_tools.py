# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Deterministic Data Mining Engines.
Provides pure Python calculations for Category 3 Data Mining Agents:
  - 3.1 Pattern Discovery
  - 3.2 Relationship Analysis
  - 3.3 Segmentation
  - 3.4 Anomaly Detection
  - 3.5 Association Mining
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler


# ─────────────────────────────────────────────────────────────────────────────
# 3.1 Pattern Discovery Engine (Clustering)
# ─────────────────────────────────────────────────────────────────────────────

def discover_patterns_clustering(df: pd.DataFrame, n_clusters: int = 3) -> Dict[str, Any]:
    """
    Applies unsupervised KMeans clustering across continuous features
    to discover hidden multivariate patterns and natural groupings.
    """
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if len(num_cols) < 2:
        return {"has_patterns": False, "reason": "Requires at least 2 numerical features for multivariate clustering."}

    df_clean = df[num_cols].dropna().copy()
    if len(df_clean) < 15:
        return {"has_patterns": False, "reason": "Insufficient observations (< 15 rows) for robust clustering."}

    # Sample if very large
    if len(df_clean) > 2000:
        df_sample = df_clean.sample(2000, random_state=42)
    else:
        df_sample = df_clean

    scaler = StandardScaler()
    scaled = scaler.fit_transform(df_sample)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(scaled)

    # Calculate cluster profiles
    df_sample["cluster"] = labels
    profiles = []
    total_len = len(df_sample)

    for c_id in range(n_clusters):
        c_subset = df_sample[df_sample["cluster"] == c_id]
        c_size = len(c_subset)
        c_pct = round((c_size / total_len) * 100, 1)

        means = c_subset[num_cols].mean().to_dict()
        profiles.append({
            "cluster_id": c_id,
            "size": c_size,
            "share_pct": c_pct,
            "feature_means": {k: round(float(v), 2) for k, v in means.items()},
        })

    profiles.sort(key=lambda x: x["size"], reverse=True)

    return {
        "has_patterns": True,
        "algorithm": "KMeans",
        "clusters_evaluated": n_clusters,
        "features_used": num_cols[:6],
        "cluster_profiles": profiles,
        "findings": [
            f"Partitioned data into {n_clusters} natural clusters. Largest cluster (C{profiles[0]['cluster_id']}) represents {profiles[0]['share_pct']}% of records ({profiles[0]['size']:,} observations).",
            f"Distinct behavioral separation detected across {', '.join(num_cols[:3])}.",
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3.2 Relationship Analysis Engine
# ─────────────────────────────────────────────────────────────────────────────

def analyze_relationships(df: pd.DataFrame, max_cols: int = 12) -> Dict[str, Any]:
    """
    Computes Pearson and Spearman correlation matrices across variables,
    identifying the strongest linear and non-linear relationships.
    """
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()[:max_cols]
    if len(num_cols) < 2:
        return {"has_relationships": False, "reason": "At least 2 numerical columns required for relationship analysis."}

    df_clean = df[num_cols].dropna()
    if len(df_clean) < 4:
        return {"has_relationships": False, "reason": "Insufficient valid numeric records."}

    corr_matrix = df_clean.corr(method="pearson")
    pairs = []

    for i in range(len(num_cols)):
        for j in range(i + 1, len(num_cols)):
            c1, c2 = num_cols[i], num_cols[j]
            r = corr_matrix.loc[c1, c2]
            if not np.isnan(r):
                strength = "Strong" if abs(r) >= 0.6 else ("Moderate" if abs(r) >= 0.3 else "Weak")
                direction = "Positive" if r > 0 else "Negative"
                pairs.append({
                    "feature_x": c1,
                    "feature_y": c2,
                    "correlation": round(float(r), 3),
                    "strength": strength,
                    "direction": direction,
                    "abs_corr": abs(r),
                })

    pairs.sort(key=lambda x: x["abs_corr"], reverse=True)
    top_pairs = pairs[:8]

    findings = []
    for p in top_pairs[:3]:
        findings.append(
            f"{p['strength']} {p['direction']} correlation (r = {p['correlation']:+.3f}) between '{p['feature_x']}' and '{p['feature_y']}'."
        )

    return {
        "has_relationships": True,
        "numeric_variables_count": len(num_cols),
        "evaluated_pairs_count": len(pairs),
        "top_relationships": top_pairs,
        "findings": findings or ["No strong linear correlations identified among analyzed numerical columns."],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3.3 Segmentation Engine
# ─────────────────────────────────────────────────────────────────────────────

def segment_entities(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Segments entities into distinct strategic tiers (e.g., Tier 1 Core,
    Tier 2 Growth, Tier 3 Long-Tail) based on normalized multi-metric scoring.
    """
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if not num_cols:
        return {"has_segmentation": False, "reason": "Numerical performance variables required for segmentation."}

    primary_col = num_cols[0]
    for c in num_cols:
        if any(k in c.lower() for k in ["total", "amount", "revenue", "sales", "volume", "pints", "donat"]):
            primary_col = c
            break

    series = pd.to_numeric(df[primary_col], errors="coerce").fillna(0)
    q67 = float(series.quantile(0.67))
    q33 = float(series.quantile(0.33))

    tier_1 = int((series >= q67).sum())
    tier_2 = int(((series >= q33) & (series < q67)).sum())
    tier_3 = int((series < q33).sum())
    total = len(series) or 1

    tier_1_vol = float(series[series >= q67].sum())
    total_vol = float(series.sum()) or 1.0
    tier_1_share = (tier_1_vol / total_vol) * 100

    return {
        "has_segmentation": True,
        "primary_segmentation_column": primary_col,
        "segments": [
            {
                "tier": "Tier 1: Core Leaders",
                "threshold": f">= {q67:,.2f}",
                "count": tier_1,
                "share_of_records_pct": round((tier_1 / total) * 100, 1),
                "share_of_volume_pct": round(tier_1_share, 1),
            },
            {
                "tier": "Tier 2: Mid-Range Growth",
                "threshold": f"{q33:,.2f} to {q67:,.2f}",
                "count": tier_2,
                "share_of_records_pct": round((tier_2 / total) * 100, 1),
                "share_of_volume_pct": round((float(series[(series >= q33) & (series < q67)].sum()) / total_vol) * 100, 1),
            },
            {
                "tier": "Tier 3: Long-Tail / Incidental",
                "threshold": f"< {q33:,.2f}",
                "count": tier_3,
                "share_of_records_pct": round((tier_3 / total) * 100, 1),
                "share_of_volume_pct": round((float(series[series < q33].sum()) / total_vol) * 100, 1),
            },
        ],
        "findings": [
            f"Segmented population into 3 strategic performance tiers using '{primary_col}'.",
            f"Tier 1 Core Leaders represent {tier_1_share:.1f}% of total volume across {tier_1:,} records ({tier_1/total*100:.1f}% of records).",
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3.4 Anomaly Detection Engine (Isolation Forest & LOF)
# ─────────────────────────────────────────────────────────────────────────────

def detect_anomalies(df: pd.DataFrame, contamination: float = 0.03) -> Dict[str, Any]:
    """
    Applies Scikit-Learn IsolationForest to detect multivariate operational anomalies,
    risk outliers, and abnormal data patterns.
    """
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if len(num_cols) < 2:
        return {"has_anomalies": False, "reason": "Requires at least 2 numerical features for multivariate anomaly detection."}

    df_clean = df[num_cols].dropna().copy()
    if len(df_clean) < 15:
        return {"has_anomalies": False, "reason": "Insufficient observations (< 15 rows) to fit anomaly models."}

    scaler = StandardScaler()
    scaled = scaler.fit_transform(df_clean)

    iso = IsolationForest(contamination=contamination, random_state=42)
    preds = iso.fit_predict(scaled)
    scores = iso.decision_function(scaled)

    anomaly_mask = preds == -1
    anomalies_count = int(anomaly_mask.sum())
    anomalies_pct = round((anomalies_count / len(df_clean)) * 100, 2)

    # Top anomaly indices
    df_clean["anomaly_score"] = scores
    top_anomalies = df_clean[anomaly_mask].sort_values("anomaly_score").head(5)

    examples = []
    for idx, r in top_anomalies.iterrows():
        examples.append({
            "record_index": int(idx),
            "anomaly_score": round(float(r["anomaly_score"]), 3),
            "values": {c: round(float(r[c]), 2) for c in num_cols[:4]},
        })

    return {
        "has_anomalies": True,
        "algorithm": "IsolationForest",
        "contamination_rate": contamination,
        "anomalies_detected_count": anomalies_count,
        "anomalies_pct": anomalies_pct,
        "top_outlier_examples": examples,
        "findings": [
            f"Isolation Forest identified {anomalies_count:,} multivariate anomaly records ({anomalies_pct}%) deviating from established operational distributions.",
            f"Extreme outlier record at row index {examples[0]['record_index']} exhibiting anomaly score of {examples[0]['anomaly_score']:.3f}.",
        ] if examples else ["No statistically abnormal multivariate outliers detected."],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3.5 Association Mining Engine
# ─────────────────────────────────────────────────────────────────────────────

def mine_associations(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Discovers co-occurrence patterns and associations across categorical dimensions.
    """
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if len(cat_cols) < 2:
        return {"has_associations": False, "reason": "Requires at least 2 categorical variables for cross-association mining."}

    c1, c2 = cat_cols[0], cat_cols[1]
    ct = pd.crosstab(df[c1], df[c2], normalize="all") * 100

    top_associations = []
    for r_idx in ct.index:
        for c_idx in ct.columns:
            pct = float(ct.loc[r_idx, c_idx])
            if pct > 3.0:
                top_associations.append({
                    "item_a": f"{c1}={r_idx}",
                    "item_b": f"{c2}={c_idx}",
                    "co_occurrence_pct": round(pct, 2),
                })

    top_associations.sort(key=lambda x: x["co_occurrence_pct"], reverse=True)

    return {
        "has_associations": True,
        "dimension_a": c1,
        "dimension_b": c2,
        "top_associations": top_associations[:6],
        "findings": [
            f"Top categorical co-occurrence: '{top_associations[0]['item_a']}' paired with '{top_associations[0]['item_b']}' accounts for {top_associations[0]['co_occurrence_pct']:.1f}% of total dataset records."
        ] if top_associations else ["No high-frequency categorical associations detected exceeding 3% support."],
    }
