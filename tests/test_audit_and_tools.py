import os
import inspect
import tempfile
import pandas as pd
import pytest

from tools.dataset_tools import auto_coerce_types, DatasetTools
from config.context import current_session_csv
from crew import _run_auto_visualizer_fallback


def test_auto_coerce_types_edge_cases():
    df = pd.DataFrame({
        "int_str": ["1", "2", "3", "4", "5"],
        "int_str_null": ["1", "2", "", "4", "5"],
        "currency": ["$1,000", "$2,500", "$3,200", "$4,100", "$5,000"],
        "pct": ["95%", "88%", "92%", "100%", "76%"],
        "year_only": ["1990", "1991", "1992", "1993", "1994"],
        "real_date": ["2021-01-01", "2021-02-01", "2021-03-01", "2021-04-01", "2021-05-01"],
        "label": ["Yes", "No", "Yes", "No", "Yes"],
        "text": ["apple", "banana", "cherry", "date", "elder"],
    })
    df = pd.concat([df, df.iloc[[0, 2]]], ignore_index=True)
    out, actions = auto_coerce_types(df)

    assert len(out) == 5
    assert str(out["int_str"].dtype) == "int64"
    assert str(out["int_str_null"].dtype) == "Int64"
    assert str(out["currency"].dtype) == "int64" and out["currency"].iloc[0] == 1000
    assert str(out["pct"].dtype) == "int64" and out["pct"].iloc[0] == 95
    assert str(out["year_only"].dtype).startswith("int")
    assert str(out["real_date"].dtype).startswith("datetime")
    assert str(out["label"].dtype) == "bool"
    assert str(out["text"].dtype) == "object"
    assert any("duplicated" in a.lower() for a in actions)


def test_no_dummy_data_in_source():
    src_clean = inspect.getsource(DatasetTools.clean_dataset_with_python.func)
    src_viz = inspect.getsource(DatasetTools.execute_visualization_code.func)

    assert "feature_a" not in src_clean
    assert "no active dataset is loaded" in src_clean
    assert "feature_a" not in src_viz
    assert "No active dataset is loaded" in src_viz


def test_clean_tool_runs_real_csv():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as tmp:
        pd.DataFrame({"a": [1, 2, 3]}).to_csv(tmp.name, index=False)
        tmp_path = tmp.name

    token = current_session_csv.set(tmp_path)
    try:
        res = DatasetTools.clean_dataset_with_python.func(python_code="print(df.shape)")
        assert "Error" not in res
    finally:
        current_session_csv.reset(token)


def test_visualizer_fallback_generates_real_charts():
    out_dir = tempfile.mkdtemp()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as tmp:
        pd.DataFrame({
            "sales": [10, 20, 30, 40, 50],
            "cost": [5, 12, 18, 25, 30],
            "region": ["A", "B", "A", "B", "A"]
        }).to_csv(tmp.name, index=False)
        real_csv = tmp.name

    msg = _run_auto_visualizer_fallback(
        real_csv,
        out_dir,
        relations_text="- X: sales | Y: cost | Type: Scatter Plot | Details: test"
    )
    pngs = [f for f in os.listdir(out_dir) if f.endswith(".png")]
    assert len(pngs) >= 1
