# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Master Registry for the 25 Agentic Data Intelligence System.
Defines agent metadata, capability manifests, presets, and dynamic factories.
"""

from typing import Any, Callable, Dict, List, Optional, Type
from agents.base_agent import BaseIntelligenceAgent

# Import all 25 Specialized Agents
from agents.data_analysis import (
    DataCleanerAgent,
    StatisticalAnalysisAgent,
    TrendAnalysisAgent,
    ComparativeAnalysisAgent,
    InsightDiscoveryAgent,
)
from agents.business_analysis import (
    SalesAnalysisAgent,
    ProfitabilityAnalysisAgent,
    ExpenseOptimizationAgent,
    CustomerIntelligenceAgent,
    BusinessDecisionSupportAgent,
)
from agents.data_mining import (
    PatternDiscoveryAgent,
    RelationshipAnalysisAgent,
    SegmentationAgent,
    AnomalyDetectionAgent,
    AssociationMiningAgent,
)
from agents.predictive_analysis import (
    SalesForecastingAgent,
    BudgetForecastingAgent,
    DemandForecastingAgent,
    RiskPredictionAgent,
    WhatIfSimulationAgent,
)
from agents.eda import (
    DatasetExplorerAgent,
    NaturalLanguageDataQueryAgent,
    VisualizationAgent,
    DataQualityInspectorAgent,
    DataStorytellingAgent,
)

# ─────────────────────────────────────────────────────────────────────────────
# 25 Agents Manifest
# ─────────────────────────────────────────────────────────────────────────────

AGENT_CLASSES: Dict[str, Type[BaseIntelligenceAgent]] = {
    # 1. Data Analysis Agents
    "data_cleaner": DataCleanerAgent,
    "statistical_analysis": StatisticalAnalysisAgent,
    "trend_analysis": TrendAnalysisAgent,
    "comparative_analysis": ComparativeAnalysisAgent,
    "insight_discovery": InsightDiscoveryAgent,

    # 2. Business Analysis Agents
    "sales_analysis": SalesAnalysisAgent,
    "profitability_analysis": ProfitabilityAnalysisAgent,
    "expense_optimization": ExpenseOptimizationAgent,
    "customer_intelligence": CustomerIntelligenceAgent,
    "decision_support": BusinessDecisionSupportAgent,

    # 3. Data Mining Agents
    "pattern_discovery": PatternDiscoveryAgent,
    "relationship_analysis": RelationshipAnalysisAgent,
    "segmentation": SegmentationAgent,
    "anomaly_detection": AnomalyDetectionAgent,
    "association_mining": AssociationMiningAgent,

    # 4. Predictive Analysis Agents
    "sales_forecasting": SalesForecastingAgent,
    "budget_forecasting": BudgetForecastingAgent,
    "demand_forecasting": DemandForecastingAgent,
    "risk_prediction": RiskPredictionAgent,
    "whatif_simulation": WhatIfSimulationAgent,

    # 5. Exploratory Data Analysis Agents
    "dataset_explorer": DatasetExplorerAgent,
    "natural_query": NaturalLanguageDataQueryAgent,
    "visualization": VisualizationAgent,
    "quality_inspector": DataQualityInspectorAgent,
    "storytelling": DataStorytellingAgent,
}

CATEGORIES_MANIFEST: Dict[str, Dict[str, Any]] = {
    "data_analysis": {
        "id": "data_analysis",
        "title": "Data Analysis",
        "icon": "bar-chart-2",
        "description": "Hygiene, descriptive distributions, trends, comparative benchmarks, and empirical insights.",
        "agent_ids": [
            "data_cleaner",
            "statistical_analysis",
            "trend_analysis",
            "comparative_analysis",
            "insight_discovery",
        ],
    },
    "business_analysis": {
        "id": "business_analysis",
        "title": "Business Analysis",
        "icon": "briefcase",
        "description": "Sales Pareto decomposition, profitability margins, expense creep, customer retention, and decision matrix.",
        "agent_ids": [
            "sales_analysis",
            "profitability_analysis",
            "expense_optimization",
            "customer_intelligence",
            "decision_support",
        ],
    },
    "data_mining": {
        "id": "data_mining",
        "title": "Data Mining",
        "icon": "layers",
        "description": "Unsupervised pattern clustering, cross-feature correlations, strategic segmentation, and anomaly detection.",
        "agent_ids": [
            "pattern_discovery",
            "relationship_analysis",
            "segmentation",
            "anomaly_detection",
            "association_mining",
        ],
    },
    "predictive_analysis": {
        "id": "predictive_analysis",
        "title": "Predictive Analysis",
        "icon": "cpu",
        "description": "Sales trajectory forecasting, budget run-rates, inventory demand buffers, ML risk drivers, and scenario simulation.",
        "agent_ids": [
            "sales_forecasting",
            "budget_forecasting",
            "demand_forecasting",
            "risk_prediction",
            "whatif_simulation",
        ],
    },
    "eda": {
        "id": "eda",
        "title": "Exploratory Data Analysis (EDA)",
        "icon": "search",
        "description": "Schema discovery, natural-language query engine, decoupled executive visuals, quality audit, and narrative storytelling.",
        "agent_ids": [
            "dataset_explorer",
            "natural_query",
            "visualization",
            "quality_inspector",
            "storytelling",
        ],
    },
}

# Standardized User Presets
ANALYSIS_PRESETS: Dict[str, List[str]] = {
    "quick_brief": [
        "dataset_explorer",
        "quality_inspector",
        "statistical_analysis",
        "visualization",
        "insight_discovery",
        "storytelling",
    ],
    "growth_bi": [
        "data_cleaner",
        "dataset_explorer",
        "sales_analysis",
        "profitability_analysis",
        "customer_intelligence",
        "relationship_analysis",
        "visualization",
        "decision_support",
        "storytelling",
    ],
    "deep_mining": [
        "data_cleaner",
        "statistical_analysis",
        "pattern_discovery",
        "relationship_analysis",
        "segmentation",
        "anomaly_detection",
        "association_mining",
        "risk_prediction",
        "visualization",
    ],
    "predictive_suite": [
        "dataset_explorer",
        "trend_analysis",
        "sales_forecasting",
        "budget_forecasting",
        "demand_forecasting",
        "risk_prediction",
        "whatif_simulation",
        "visualization",
    ],
    "full_audit": list(AGENT_CLASSES.keys()),
}


def get_agent_instance(agent_id: str, llm_caller: Optional[Callable] = None) -> Optional[BaseIntelligenceAgent]:
    """Factory to instantiate an agent by ID."""
    cls = AGENT_CLASSES.get(agent_id)
    if cls:
        return cls(llm_caller=llm_caller)
    return None


def get_agents_for_selection(
    selected_agent_ids: Optional[List[str]] = None,
    selected_categories: Optional[List[str]] = None,
    preset: Optional[str] = None,
    llm_caller: Optional[Callable] = None,
) -> List[BaseIntelligenceAgent]:
    """
    Resolves agent selection from IDs, categories, or presets.
    Defaults to 'growth_bi' if no specific selection is provided.
    """
    target_ids = set()

    if preset and preset in ANALYSIS_PRESETS:
        target_ids.update(ANALYSIS_PRESETS[preset])

    if selected_categories:
        for cat in selected_categories:
            if cat in CATEGORIES_MANIFEST:
                target_ids.update(CATEGORIES_MANIFEST[cat]["agent_ids"])

    if selected_agent_ids:
        target_ids.update(selected_agent_ids)

    if not target_ids:
        target_ids.update(ANALYSIS_PRESETS["growth_bi"])

    # Maintain consistent category order
    ordered_ids = [aid for aid in AGENT_CLASSES.keys() if aid in target_ids]
    return [get_agent_instance(aid, llm_caller=llm_caller) for aid in ordered_ids if aid in AGENT_CLASSES]


def get_preset_agents(preset_name: str) -> List[str]:
    """Retrieve the list of agent IDs assigned to a preset."""
    return ANALYSIS_PRESETS.get(preset_name, ANALYSIS_PRESETS["growth_bi"])


AGENT_CATALOG: Dict[str, Dict[str, Any]] = {
    aid: {
        "id": aid,
        "class": cls,
        "category": (
            "data_analysis" if aid in CATEGORIES_MANIFEST["data_analysis"]["agent_ids"] else
            "business_analysis" if aid in CATEGORIES_MANIFEST["business_analysis"]["agent_ids"] else
            "data_mining" if aid in CATEGORIES_MANIFEST["data_mining"]["agent_ids"] else
            "predictive_analysis" if aid in CATEGORIES_MANIFEST["predictive_analysis"]["agent_ids"] else
            "eda"
        ),
    }
    for aid, cls in AGENT_CLASSES.items()
}

