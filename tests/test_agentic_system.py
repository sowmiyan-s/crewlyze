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





