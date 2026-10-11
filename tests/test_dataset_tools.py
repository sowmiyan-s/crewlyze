import tempfile
import pandas as pd
import pytest
from tools.dataset_tools import auto_coerce_types, build_dataset_profile, read_csv_robust


def test_auto_coerce_types_comprehensive():
    df = pd.DataFrame({
        "int_str": ["10", "20", "30", "40", "50"],
        "currency": ["$1,000", "$2,500", "$3,200", "$4,100", "$5,000"],
        "pct": ["95%", "88%", "92%", "100%", "76%"],
        "year_only": ["1990", "1991", "1992", "1993", "1994"],
        "real_date": ["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01", "2024-05-01"],
        "binary_label": ["Yes", "No", "Yes", "No", "Yes"],
        "category": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
    })
    
    # Add a duplicate row
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    assert len(df) == 6

    cleaned_df, actions = auto_coerce_types(df)

    # 1. Deduplication
    assert len(cleaned_df) == 5
    assert any("duplicated" in a.lower() for a in actions)

    # 2. Integer parsing
    assert str(cleaned_df["int_str"].dtype) == "int64"

    # 3. Currency cleaning
    assert str(cleaned_df["currency"].dtype) == "int64"
    assert cleaned_df["currency"].iloc[0] == 1000

    # 4. Percentage cleaning
    assert str(cleaned_df["pct"].dtype) == "int64"
    assert cleaned_df["pct"].iloc[0] == 95

    # 5. Year retention (should not become datetime timestamp)
    assert str(cleaned_df["year_only"].dtype).startswith("int")

    # 6. Real date conversion
    assert str(cleaned_df["real_date"].dtype).startswith("datetime")

    # 7. Binary boolean conversion
    assert str(cleaned_df["binary_label"].dtype) == "bool"


def test_build_dataset_profile():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as tmp:
        df = pd.DataFrame({
            "product_id": [101, 102, 103, 104],
            "price": [19.99, 29.99, 9.99, 49.99],
            "units_sold": [50, 80, 120, 25],
            "category": ["Books", "Electronics", "Books", "Clothing"]
        })
        df.to_csv(tmp.name, index=False)
        tmp_path = tmp.name

    profile = build_dataset_profile(tmp_path)
    assert isinstance(profile, str)
    assert "4 rows" in profile
    assert "4 columns" in profile
    assert "price" in profile
    assert "units_sold" in profile


def test_read_csv_robust():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tmp:
        tmp.write("col_a,col_b\n1,hello\n2,world\n")
        tmp_path = tmp.name

    df = read_csv_robust(tmp_path)
    assert len(df) == 2
    assert list(df.columns) == ["col_a", "col_b"]
