import os
import pytest
import pandas as pd
from pathlib import Path
from tools.bi_tools import (
    BusinessIntelligenceTools,
    query_segment_performance,
    calculate_driver_correlations,
    audit_margin_leakage,
    train_predictive_driver_model,
    calculate_velocity_and_growth,
)


@pytest.fixture
def sample_csv(tmp_path):
    csv_file = tmp_path / "sample_business_data.csv"
    data = {
        "Date": pd.date_range("2024-01-01", periods=12, freq="ME").astype(str),
        "Region": ["North", "South", "East", "West"] * 3,
        "Plan_Tier": ["Enterprise", "Pro", "Starter"] * 4,
        "Revenue": [12000, 4500, 1500, 14000, 5000, 1800, 16000, 5200, 2000, 19000, 5500, 2200],
        "Units_Sold": [120, 90, 50, 140, 95, 55, 160, 100, 60, 180, 105, 65],
        "Refund_Amount": [200, 50, 10, 250, 60, 15, 300, 70, 20, 350, 80, 25],
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_file, index=False)
    return str(csv_file)


def test_query_segment_performance(sample_csv):
    res = query_segment_performance(
        dimension="Plan_Tier",
        metric="Revenue",
        agg="sum",
        file_path=sample_csv
    )
    assert "Enterprise" in res
    assert "Revenue" in res
    assert "Share_Pct" in res


def test_calculate_driver_correlations(sample_csv):
    res = calculate_driver_correlations(
        target_metric="Revenue",
        file_path=sample_csv
    )
    assert "Revenue" in res
    assert "Units_Sold" in res
    assert "Positive Accelerator" in res


def test_audit_margin_leakage(sample_csv):
    res = audit_margin_leakage(
        metric="Refund_Amount",
        dimension="Region",
        file_path=sample_csv
    )
    assert "Refund_Amount" in res
    assert "Outlier Count" in res
    assert "Normal Range" in res


def test_train_predictive_driver_model(sample_csv):
    res = train_predictive_driver_model(
        target_metric="Revenue",
        file_path=sample_csv
    )
    assert "Predictive Drivers for Target" in res
    assert "Predictive_Importance_Pct" in res


def test_calculate_velocity_and_growth(sample_csv):
    res = calculate_velocity_and_growth(
        time_column="Date",
        metric="Revenue",
        file_path=sample_csv
    )
    assert "Growth Velocity & Trajectory" in res
    assert "Growth_Pct" in res


def test_crewai_tool_registry():
    assert hasattr(BusinessIntelligenceTools, "query_segment_performance")
    assert hasattr(BusinessIntelligenceTools, "calculate_driver_correlations")
    assert hasattr(BusinessIntelligenceTools, "audit_margin_leakage")
    assert hasattr(BusinessIntelligenceTools, "train_predictive_driver_model")
    assert hasattr(BusinessIntelligenceTools, "calculate_velocity_and_growth")
