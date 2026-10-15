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


def test_detect_business_domain_adaptive():
    from tools.dataset_tools import detect_business_domain

    df_ecommerce = pd.DataFrame({
        "order_id": [1, 2, 3],
        "cart_value": [45.0, 120.0, 89.0],
        "shipping_cost": [5.0, 0.0, 8.0],
        "sku": ["A1", "B2", "C3"]
    })
    domain_info = detect_business_domain(df_ecommerce, "Scale store revenue")
    assert domain_info["domain"] == "E-Commerce & DTC Retail"
    assert "Average Order Value (AOV)" in domain_info["growth_terms"]
    assert any("Cart Abandonment" in term for term in domain_info["problem_terms"])

    df_saas = pd.DataFrame({
        "mrr": [1000, 2500, 5000],
        "arr": [12000, 30000, 60000],
        "churn_rate": [0.02, 0.01, 0.04],
        "plan": ["Pro", "Enterprise", "Starter"]
    })
    saas_info = detect_business_domain(df_saas, "Reduce churn")
    assert saas_info["domain"] == "B2B SaaS & Subscriptions"
    assert "Expansion MRR" in saas_info["growth_terms"]


def test_parse_and_format_growth_insights_json():
    from tools.dataset_tools import parse_growth_insights_json, format_growth_insights

    raw_json_str = """
    ```json
    {
      "detected_domain": "B2B SaaS",
      "executive_summary": "Strong ARR growth driven by enterprise tier accounts.",
      "growth_levers": [
        {
          "growth_in": "Enterprise ARR",
          "headline": "Enterprise ARR surging 42% YoY",
          "observation": "Enterprise accounts account for $1.2M in annual expansion.",
          "business_implication": "Expands gross margins to 82%.",
          "actionable_strategy": "Double outbound enterprise sales capacity."
        }
      ],
      "problem_areas": [
        {
          "problem_in": "Self-Serve Activation",
          "headline": "Self-Serve Activation drop-off",
          "observation": "New signups stall at the third onboarding step.",
          "likely_root_cause": "Complex SSO setup requirements.",
          "commercial_risk": "Estimated $140k ARR loss per quarter.",
          "actionable_strategy": "Streamline self-serve signup flow."
        }
      ],
      "roadmap": {
        "days_1_30": "Deploy self-serve onboarding fix.",
        "days_31_60": "Scale enterprise SDR hiring.",
        "days_61_90": "Launch multi-seat team workspaces."
      },
      "alerts": [
        "Customer concentration in top 3 logos exceeds 30%."
      ]
    }
    ```
    """
    parsed = parse_growth_insights_json(raw_json_str)
    assert parsed is not None
    assert parsed["detected_domain"] == "B2B SaaS"
    assert len(parsed["growth_levers"]) == 1
    assert len(parsed["problem_areas"]) == 1

    formatted = format_growth_insights(parsed, "Scale ARR")
    assert "🚀 Growth in Enterprise ARR" in formatted
    assert "⚠️ Problem in Self-Serve Activation Likely" in formatted
    assert "**Observation**:" in formatted
    assert "**Business Implication**:" in formatted
    assert "**Actionable Strategy**:" in formatted
    assert "Days 1-30" in formatted


def test_auto_insights_fallback_produces_growth_and_problem():
    from crew import _run_auto_insights_fallback

    df = pd.DataFrame({
        "revenue": [100, 200, 300, 400, 500],
        "spend": [50, 80, 110, 150, 190],
        "campaign": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
    })
    formatted_text, json_data = _run_auto_insights_fallback(df, project_goal="Boost ROI", return_tuple=True)
    
    assert isinstance(json_data, dict)
    assert "growth_levers" in json_data
    assert "problem_areas" in json_data
    assert len(json_data["growth_levers"]) >= 1
    assert len(json_data["problem_areas"]) >= 1

    # Ensure format matches Growth in X and Problem in Y likely
    assert "Growth in" in formatted_text
    assert "Problem in" in formatted_text
    assert "**Observation**:" in formatted_text
    assert "**Business Implication**:" in formatted_text
    assert "**Actionable Strategy**:" in formatted_text

