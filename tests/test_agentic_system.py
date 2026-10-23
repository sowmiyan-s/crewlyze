"""
Unit & Integration Tests for Crewlyze 25 Agentic Intelligence System
Verifies:
1. Catalog registration: 25 unique agents across 5 defined categories.
2. Presets: all preset configurations resolve to valid agent IDs.
3. Contract compliance: Agents execute 6-step contract, return AgentDelivery with metrics and findings.
4. MasterCoordinator: Selective dispatch, staged execution, and unified deliverable synthesis.
5. Non-blocking visualization: Generates Plotly and PNG charts without LLM hangs.
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from agents.registry import AGENT_CATALOG, get_preset_agents, get_agent_instance
from agents.base_agent import AgentDelivery
from workflows.context_bus import ContextBus
from workflows.coordinator import MasterCoordinator


@pytest.fixture
def sample_business_df():
    np.random.seed(42)
    n = 100
    dates = pd.date_range('2024-01-01', periods=n, freq='D')
    return pd.DataFrame({
        'Date': dates,
        'Revenue': np.random.uniform(100, 1000, n),
        'Cost': np.random.uniform(50, 600, n),
        'Units_Sold': np.random.randint(1, 50, n),
        'Customer_ID': [f'CUST_{i%20}' for i in range(n)],
        'Category': np.random.choice(['Hardware', 'Software', 'Services'], n),
        'Region': np.random.choice(['North', 'South', 'East', 'West'], n),
    })


def test_agent_catalog_completeness():
    """Ensure exactly 25 agents are registered across the 5 required categories."""
    assert len(AGENT_CATALOG) == 25, f"Expected 25 agents, found {len(AGENT_CATALOG)}"
    
    categories = {agent["category"] for agent in AGENT_CATALOG.values()}
    expected_categories = {
        "data_analysis",
        "business_analysis",
        "data_mining",
        "predictive_analysis",
        "eda"
    }
    assert categories == expected_categories, f"Categories mismatch: {categories}"

    # Verify each category contains exactly 5 agents
    for cat in expected_categories:
        count = sum(1 for agent in AGENT_CATALOG.values() if agent["category"] == cat)
        assert count == 5, f"Category '{cat}' does not have 5 agents (has {count})"


def test_presets_validity():
    """Ensure all presets resolve to registered agent IDs."""
    presets = ["growth_bi", "quick_brief", "deep_mining", "predictive_suite", "full_audit"]
    for preset in presets:
        agent_ids = get_preset_agents(preset)
        assert len(agent_ids) > 0
        for aid in agent_ids:
            assert aid in AGENT_CATALOG, f"Preset '{preset}' references unknown agent '{aid}'"


def test_agent_contract_execution(sample_business_df):
    """Test individual agent execution under the 6-step contract."""
    bus = ContextBus(session_id="test_contract_session")
    bus.set_shared("raw_df", sample_business_df)
    bus.set_shared("business_goal", "Maximize profitability")
    agent = get_agent_instance("sales_analysis")
    
    assert agent.agent_id == "sales_analysis"
    assert agent.category == "business_analysis"
    
    delivery = agent.run(sample_business_df, project_goal="Maximize profitability")
    assert isinstance(delivery, AgentDelivery)
    assert delivery.status in ["completed", "ineligible"]
    if delivery.status == "completed":
        assert len(delivery.findings) > 0
        assert isinstance(delivery.metrics, dict)
        assert delivery.execution_time >= 0


def test_master_coordinator_end_to_end(sample_business_df):
    """Run MasterCoordinator with a standard preset and ensure complete synthesis."""
    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = MasterCoordinator(
            session_id="test_coord_session",
            project_goal="Optimize unit margins and sales run-rate",
            output_dir=tmpdir,
        )
        
        summary = coordinator.run_pipeline(
            df=sample_business_df,
            preset="growth_bi"
        )
        assert summary["total_execution_time"] > 0
        assert summary["rows_count"] == 100
        assert summary["cols_count"] == 7
        assert "categories" in summary
        assert "executive_narrative" in summary
        assert len(summary["executive_findings"]) > 0
        
        # Check that visuals are decoupled and produced cleanly
        assert isinstance(summary["plotly_charts"], list)
        assert isinstance(summary["png_charts"], list)


def test_export_pdf_with_agentic_summary(sample_business_df):
    """Ensure export_pdf cleanly serializes 25-agent results into a valid PDF binary."""
    from ui.export import export_pdf
    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = MasterCoordinator(
            session_id="test_pdf_session",
            project_goal="Maximize growth",
            output_dir=tmpdir,
        )
        summary = coordinator.run_pipeline(
            df=sample_business_df,
            preset="quick_brief"
        )
        pdf_bytes = export_pdf(summary, filename="test_report.pdf")
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF")


@pytest.mark.parametrize("category", [
    "data_analysis",
    "business_analysis",
    "data_mining",
    "predictive_analysis",
    "eda",
])
def test_isolated_usecase_categories(sample_business_df, category):
    """Ensure each of the 5 analysis use-case steps runs isolated, produces realistic results, and generates a PDF report."""
    from ui.export import export_pdf
    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = MasterCoordinator(
            session_id=f"test_cat_{category}",
            project_goal=f"Test {category} isolated use case",
            output_dir=tmpdir,
        )
        result = coordinator.run_pipeline(
            df=sample_business_df,
            selected_categories=[category],
        )

        assert result["total_execution_time"] > 0
        cat_agents = result["categories"].get(category, [])
        assert len(cat_agents) == 5, f"Expected 5 agents in {category}, got {len(cat_agents)}"

        completed = [a for a in cat_agents if a.get("status") == "completed"]
        assert len(completed) >= 4, f"Expected at least 4 completed agents in {category}, got {len(completed)}"

        for agent in completed:
            assert isinstance(agent.get("metrics"), dict)
            assert isinstance(agent.get("findings"), list)
            assert len(agent.get("findings")) > 0

        # Verify individual category produces valid PDF report
        pdf_bytes = export_pdf(result, filename=f"report_{category}.pdf")
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF")


def test_selective_card_agent_execution(sample_business_df):
    """Ensure that selecting a specific subset of agents within a card executes only those agents safely."""
    from ui.export import export_pdf
    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = MasterCoordinator(
            session_id="test_selective_subset",
            project_goal="Selective test",
            output_dir=tmpdir,
        )
        # Select 2 agents from Business Analysis
        selected_subset = ["sales_analysis", "profitability_analysis"]
        result = coordinator.run_pipeline(
            df=sample_business_df,
            selected_agent_ids=selected_subset,
        )

        assert result["total_execution_time"] > 0
        biz_agents = result["categories"].get("business_analysis", [])
        executed_ids = [a["agent_id"] for a in biz_agents if a.get("status") == "completed"]
        assert "sales_analysis" in executed_ids
        assert "profitability_analysis" in executed_ids
        # Other agents in business analysis should not have been executed
        assert "expense_optimization" not in executed_ids
        assert "decision_support" not in executed_ids

        # Ensure PDF export handles selective execution safely
        pdf_bytes = export_pdf(result, filename="report_selective.pdf")
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF")


def test_distinct_report_manifests_completeness():
    """Ensure all 25 registered agent capabilities have a distinct report manifest."""
    from ui.export import REPORT_MANIFESTS
    from agents.registry import AGENT_CLASSES

    for aid in AGENT_CLASSES.keys():
        assert aid in REPORT_MANIFESTS, f"Missing report manifest for agent '{aid}'"
        manifest = REPORT_MANIFESTS[aid]
        assert manifest["title"], f"Manifest '{aid}' missing title"
        assert manifest["subtitle"], f"Manifest '{aid}' missing subtitle"
        assert manifest["domain_badge"], f"Manifest '{aid}' missing domain_badge"
        assert manifest["disclaimer"], f"Manifest '{aid}' missing disclaimer"


def test_export_distinct_agent_pdf(sample_business_df):
    """Ensure export_distinct_agent_pdf produces a valid, styled capability-specific PDF."""
    from ui.export import export_distinct_agent_pdf

    agent_data = {
        "agent_id": "sales_analysis",
        "name": "Sales Analysis Agent",
        "category": "business_analysis",
        "status": "completed",
        "execution_time": 1.25,
        "metrics": {
            "total_revenue": 145020.50,
            "top_category_share": 0.48,
            "transaction_count": 100,
        },
        "findings": [
            "**Observation**: Top 20% of customers drive 74% of cumulative sales volume.\n**Business Implication**: Severe revenue concentration risk.\n**Actionable Strategy**: Diversify tier-2 accounts.",
            "Hardware category delivers 48% of total volume with an average ticket of $620."
        ],
        "narrative": "Comprehensive commercial sales analysis reveals strong revenue concentration.",
        "limitations": ["Observational transaction data without marketing attribution."],
        "recommendations": ["Expand mid-tier enterprise outreach", "Bundle hardware with services"],
    }
    dataset_meta = {
        "filename": "sample_sales.csv",
        "rows_count": 100,
        "cols_count": 7,
    }

    pdf_bytes = export_distinct_agent_pdf(agent_data, dataset_meta, df=sample_business_df)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_export_pdf_dispatch_distinct_and_consolidated(sample_business_df):
    """Ensure export_pdf cleanly dispatches between distinct reports and consolidated reports."""
    from ui.export import export_pdf

    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = MasterCoordinator(
            session_id="test_dispatch_pdf",
            project_goal="Test distinct PDF dispatching",
            output_dir=tmpdir,
        )
        result = coordinator.run_pipeline(
            df=sample_business_df,
            selected_agent_ids=["sales_analysis", "profitability_analysis"],
        )

        # 1. Distinct report for sales_analysis
        sales_pdf = export_pdf(result, analysis_id="sales_analysis")
        assert len(sales_pdf) > 1000
        assert sales_pdf.startswith(b"%PDF")

        # 2. Distinct report for profitability_analysis
        profit_pdf = export_pdf(result, analysis_id="profitability_analysis")
        assert len(profit_pdf) > 1000
        assert profit_pdf.startswith(b"%PDF")

        # 3. Consolidated executive report
        consolidated_pdf = export_pdf(result, analysis_id="consolidated")
        assert len(consolidated_pdf) > 1000
        assert consolidated_pdf.startswith(b"%PDF")

        # 4. Default when analysis_id is omitted
        default_pdf = export_pdf(result)
        assert len(default_pdf) > 1000
        assert default_pdf.startswith(b"%PDF")


def test_artifact_manager_basic_operations(sample_business_df):
    """Verify ArtifactManager safely writes, indexes, and validates CSV and JSON artifacts."""
    from tools.artifact_manager import ArtifactManager

    session_id = "test_artifact_session"
    art_csv = ArtifactManager.save_dataframe_csv(
        session_id=session_id,
        artifact_key="sample_test_data.csv",
        df=sample_business_df.head(10),
        title="Sample Test CSV",
    )
    assert art_csv is not None
    assert art_csv["type"] == "csv"
    assert art_csv["artifact_key"] == "sample_test_data.csv"
    assert art_csv["size_bytes"] > 0
    assert "test_artifact_session" in art_csv["download_url"]

    # Verify JSON saving
    sample_json = {"metric": "churn_risk", "score": 0.85, "features": ["tenure", "spend"]}
    art_json = ArtifactManager.save_json_artifact(
        session_id=session_id,
        artifact_key="sample_test_data.json",
        data=sample_json,
        title="Sample Test JSON",
    )
    assert art_json is not None
    assert art_json["type"] == "json"
    assert art_json["size_bytes"] > 0

    # Retrieve and verify file paths
    csv_file = ArtifactManager.get_artifact_file(session_id, "sample_test_data.csv")
    assert csv_file is not None and csv_file.exists()


def test_artifact_manager_security_traversal():
    """Verify ArtifactManager safely rejects path traversal attempts."""
    from tools.artifact_manager import ArtifactManager

    # Unsafe artifact keys
    assert ArtifactManager.get_artifact_file("test_artifact_session", "../evil.csv") is None
    assert ArtifactManager.get_artifact_file("test_artifact_session", "..\\evil.csv") is None
    assert ArtifactManager.get_artifact_file("test_artifact_session", "evil/nested.csv") is None


def test_pipeline_artifact_generation(sample_business_df):
    """Verify that running agents through MasterCoordinator creates downloadable artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = MasterCoordinator(
            session_id="test_pipeline_artifacts_session",
            project_goal="Generate core artifacts",
            output_dir=tmpdir,
        )
        result = coordinator.run_pipeline(
            df=sample_business_df,
            selected_agent_ids=["data_cleaner", "sales_analysis", "dataset_explorer"],
        )

        assert "artifacts" in result
        assert isinstance(result["artifacts"], list)
        assert len(result["artifacts"]) > 0

        keys = [a["artifact_key"] for a in result["artifacts"]]
        # At least sales_pareto_breakdown.csv or column_dictionary.csv must have been created
        assert any("sales" in k or "column" in k or "hygiene" in k for k in keys)

        for art in result["artifacts"]:
            assert "download_url" in art
            assert "size_bytes" in art
            assert art["size_bytes"] > 0


def test_distinct_agent_pdf_generation(sample_business_df):
    """Ensure distinct PDF export works for individual agents and dispatches correctly."""
    from ui.export import export_pdf
    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = MasterCoordinator(
            session_id="test_distinct_pdf_session",
            project_goal="Verify distinct agent PDF output",
            output_dir=tmpdir,
        )
        result = coordinator.run_pipeline(
            df=sample_business_df,
            selected_agent_ids=["sales_analysis", "statistical_analysis", "anomaly_detection"],
        )
        for aid in ["sales_analysis", "statistical_analysis", "anomaly_detection"]:
            pdf_bytes = export_pdf(result, filename=f"distinct_{aid}.pdf", analysis_id=aid)
            assert len(pdf_bytes) > 1000
            assert pdf_bytes.startswith(b"%PDF")





