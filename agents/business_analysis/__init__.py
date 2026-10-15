# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Category 2: Business Analysis Agents.
Provides 5 specialized business intelligence agents:
  2.1 SalesAnalysisAgent
  2.2 ProfitabilityAnalysisAgent
  2.3 ExpenseOptimizationAgent
  2.4 CustomerIntelligenceAgent
  2.5 BusinessDecisionSupportAgent
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from agents.base_agent import BaseIntelligenceAgent, InspectionResult
from tools.business_tools import (
    analyze_sales_performance,
    analyze_profitability,
    optimize_expenses,
    calculate_customer_intelligence,
    model_business_decisions,
)


class SalesAnalysisAgent(BaseIntelligenceAgent):
    agent_id = "sales_analysis"
    name = "Sales Analysis Agent"
    category = "business_analysis"
    description = "Evaluates sales volume, top products, Pareto 80/20 concentration, and revenue drivers."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not num_cols:
            return InspectionResult(is_eligible=False, reason="No numeric metric columns to evaluate sales/volume.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = analyze_sales_performance(df)
        if not res.get("has_sales_data"):
            return {"metrics": {}, "findings": [res.get("reason", "Sales analysis unavailable.")]}

        return {
            "metrics": {
                "total_volume": res.get("total_revenue", 0.0),
                "pareto_ratio_pct": res.get("pareto_concentration", {}).get("items_driving_80_pct_ratio", 0.0),
                "top_performing_item": res.get("top_performing_items", [{}])[0].get("name", "N/A"),
            },
            "findings": res.get("findings", []),
            "tables": [{"title": "Top Performing Items", "rows": res.get("top_performing_items", [])}],
            "provenance": {"method": "analyze_sales_performance", "metric": res.get("revenue_metric")},
        }


class ProfitabilityAnalysisAgent(BaseIntelligenceAgent):
    agent_id = "profitability_analysis"
    name = "Profitability Analysis Agent"
    category = "business_analysis"
    description = "Calculates gross margins, contribution ratios, and flags loss-making operations."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not num_cols:
            return InspectionResult(is_eligible=False, reason="Requires numeric data to evaluate margins.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = analyze_profitability(df)
        metrics = {}
        if res.get("has_margin_data"):
            metrics = {
                "overall_margin_pct": res.get("overall_margin_pct", 0.0),
                "gross_profit": res.get("gross_profit", 0.0),
                "loss_making_pct": res.get("loss_making_pct", 0.0),
            }

        return {
            "metrics": metrics,
            "findings": res.get("findings", []),
            "provenance": {"method": "analyze_profitability", "has_direct_costs": res.get("has_margin_data", False)},
        }


class ExpenseOptimizationAgent(BaseIntelligenceAgent):
    agent_id = "expense_optimization"
    name = "Expense Optimization Agent"
    category = "business_analysis"
    description = "Categorizes expenditure, detects variance spikes, and identifies cost-saving opportunities."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not num_cols:
            return InspectionResult(is_eligible=False, reason="Requires monetary or numerical cost metrics.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = optimize_expenses(df)
        if not res.get("has_expense_data"):
            return {"metrics": {}, "findings": [res.get("reason", "Expense optimization unavailable.")]}

        return {
            "metrics": {
                "total_spend": res.get("total_spend", 0.0),
                "spikes_count": res.get("spikes_count", 0),
                "simulated_potential_savings": res.get("simulated_potential_savings", 0.0),
            },
            "findings": res.get("findings", []),
            "tables": [{"title": "Top Spending Categories", "rows": res.get("top_spending_categories", [])}],
            "provenance": {"method": "optimize_expenses", "spend_column": res.get("spend_column")},
        }


class CustomerIntelligenceAgent(BaseIntelligenceAgent):
    agent_id = "customer_intelligence"
    name = "Customer Intelligence Agent"
    category = "business_analysis"
    description = "Measures repeat engagement rates, customer lifetime volume, and high-value cohorts."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        if df is None or df.empty:
            return InspectionResult(is_eligible=False, reason="Dataset is empty.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = calculate_customer_intelligence(df)
        if not res.get("has_customer_data"):
            return {
                "metrics": {},
                "findings": ["Dataset lacks distinct customer ID or repeat frequency columns; cohort profiling omitted."],
            }

        return {
            "metrics": {
                "repeat_rate_pct": res.get("repeat_participation_rate_pct", 0.0),
                "high_value_share_pct": res.get("high_value_volume_share_pct", 0.0),
                "high_value_count": res.get("high_value_cohort_count", 0),
            },
            "findings": res.get("findings", []),
            "provenance": {"method": "calculate_customer_intelligence"},
        }


class BusinessDecisionSupportAgent(BaseIntelligenceAgent):
    agent_id = "decision_support"
    name = "Business Decision Support Agent"
    category = "business_analysis"
    description = "Synthesizes multi-agent evidence into prioritized strategic recommendations and risk safeguards."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        bus_summary = []
        if context and "context_bus" in context:
            bus_summary = [context["context_bus"].get_context_summary(max_length=1000)]

        res = model_business_decisions(df, findings_context=bus_summary)
        return {
            "metrics": {"strategic_actions_count": res.get("strategic_actions_count", 0)},
            "findings": [f"[{r['priority']}]: {r['action']} ({r['expected_impact']})" for r in res.get("recommendations", [])],
            "tables": [{"title": "Prioritized Decision Matrix", "rows": res.get("recommendations", [])}],
            "provenance": {"method": "model_business_decisions"},
        }
