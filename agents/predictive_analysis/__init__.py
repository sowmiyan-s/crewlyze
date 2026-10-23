# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Category 4: Predictive Analysis Agents.
Provides 5 specialized predictive modeling agents:
  4.1 SalesForecastingAgent
  4.2 BudgetForecastingAgent
  4.3 DemandForecastingAgent
  4.4 RiskPredictionAgent
  4.5 WhatIfSimulationAgent
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from agents.base_agent import BaseIntelligenceAgent, InspectionResult
from tools.artifact_manager import ArtifactManager
from tools.predictive_tools import (
    forecast_sales,
    forecast_budget,
    forecast_demand,
    predict_risk_model,
    simulate_what_if,
)


class SalesForecastingAgent(BaseIntelligenceAgent):
    agent_id = "sales_forecasting"
    name = "Sales Forecasting Agent"
    category = "predictive_analysis"
    description = "Projects future sales/volume trajectory with holdout validation and confidence bounds."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not num_cols:
            return InspectionResult(is_eligible=False, reason="Numeric metric required to generate sales forecasts.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = forecast_sales(df)
        if not res.get("has_forecast"):
            return {"metrics": {}, "findings": [res.get("reason", "Forecast unavailable.")]}

        preds = res.get("predictions", [])
        artifacts = []
        sid = context.get("session_id") if context else None
        if sid and preds:
            art = ArtifactManager.save_rows_csv(
                sid,
                "forecast_horizon.csv",
                preds,
                "Sales Forecast Trajectory Horizons",
            )
            if art:
                artifacts.append(art)

        return {
            "metrics": {
                "trajectory": res.get("trajectory"),
                "validation_mape_pct": res.get("validation_mape_pct"),
                "next_period_prediction": preds[0].get("predicted_value") if preds else 0.0,
            },
            "findings": res.get("findings", []),
            "tables": [{"title": "Forecast Horizon Predictions", "rows": preds}],
            "artifacts": artifacts,
            "provenance": {"method": "forecast_sales", "model": res.get("algorithm")},
        }


class BudgetForecastingAgent(BaseIntelligenceAgent):
    agent_id = "budget_forecasting"
    name = "Budget Forecasting Agent"
    category = "predictive_analysis"
    description = "Models forward-looking expenditure burn rate and operational cash commitments."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not num_cols:
            return InspectionResult(is_eligible=False, reason="Numeric cost metrics required for budget projection.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = forecast_budget(df)
        if not res.get("has_budget_forecast"):
            return {"metrics": {}, "findings": [res.get("reason", "Budget forecast unavailable.")]}

        artifacts = []
        sid = context.get("session_id") if context else None
        if sid and res.get("projected_total_commitment"):
            run_rate = res.get("current_period_run_rate", 0.0)
            horizon = res.get("projected_horizon_periods", 6)
            proj_rows = [
                {
                    "period_offset": p,
                    "run_rate": round(run_rate, 2),
                    "cumulative_commitment": round(run_rate * p, 2),
                }
                for p in range(1, horizon + 1)
            ]
            art = ArtifactManager.save_rows_csv(
                sid,
                "budget_burn_projection.csv",
                proj_rows,
                "Forward Budget Commitment & Burn Rate Projection",
            )
            if art:
                artifacts.append(art)

        return {
            "metrics": {
                "current_run_rate": res.get("current_period_run_rate", 0.0),
                "projected_total_commitment": res.get("projected_total_commitment", 0.0),
            },
            "findings": res.get("findings", []),
            "artifacts": artifacts,
            "provenance": {"method": "forecast_budget"},
        }


class DemandForecastingAgent(BaseIntelligenceAgent):
    agent_id = "demand_forecasting"
    name = "Demand Forecasting Agent"
    category = "predictive_analysis"
    description = "Calculates demand volatility, buffer safety stock, and recommended reorder points."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not num_cols:
            return InspectionResult(is_eligible=False, reason="Numeric demand columns required.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = forecast_demand(df)
        if not res.get("has_demand_forecast"):
            return {"metrics": {}, "findings": [res.get("reason", "Demand forecast unavailable.")]}

        artifacts = []
        sid = context.get("session_id") if context else None
        if sid and res.get("recommended_safety_buffer"):
            buffer_rows = [
                {"metric": "Average Demand", "value": res.get("average_demand", 0.0)},
                {"metric": "Demand Volatility (Std Dev)", "value": res.get("demand_volatility_std", 0.0)},
                {"metric": "Coefficient of Variation", "value": res.get("coefficient_of_variation", 0.0)},
                {"metric": "Recommended Safety Buffer", "value": res.get("recommended_safety_buffer", 0.0)},
                {"metric": "Recommended Reorder Point", "value": res.get("recommended_reorder_point", 0.0)},
            ]
            art = ArtifactManager.save_rows_csv(
                sid,
                "demand_safety_buffers.csv",
                buffer_rows,
                "Demand Volatility & Safety Stock Buffers",
            )
            if art:
                artifacts.append(art)

        return {
            "metrics": {
                "average_demand": res.get("average_demand", 0.0),
                "safety_buffer": res.get("recommended_safety_buffer", 0.0),
                "reorder_point": res.get("recommended_reorder_point", 0.0),
            },
            "findings": res.get("findings", []),
            "artifacts": artifacts,
            "provenance": {"method": "forecast_demand"},
        }


class RiskPredictionAgent(BaseIntelligenceAgent):
    agent_id = "risk_prediction"
    name = "Risk Prediction Agent"
    category = "predictive_analysis"
    description = "Trains Random Forest multi-algorithm models to predict targets and extract feature importances."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        if len(df.columns) < 2:
            return InspectionResult(is_eligible=False, reason="At least 2 columns required to train predictive models.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = predict_risk_model(df, plan.get("goal", ""))
        if not res.get("has_risk_prediction"):
            return {"metrics": {}, "findings": [res.get("reason", "Risk modeling unavailable.")]}

        drivers = res.get("top_drivers", [])
        artifacts = []
        sid = context.get("session_id") if context else None
        if sid and drivers:
            art = ArtifactManager.save_rows_csv(
                sid,
                "risk_feature_importance.csv",
                drivers,
                "Risk & Predictive Feature Importance Rankings",
            )
            if art:
                artifacts.append(art)

        return {
            "metrics": {
                "target_variable": res.get("target_variable"),
                "model_score": res.get("validation_score"),
                "task_type": res.get("task_type"),
                "top_driver": drivers[0].get("feature") if drivers else "N/A",
            },
            "findings": res.get("findings", []),
            "tables": [{"title": "Feature Importance Rankings", "rows": drivers}],
            "artifacts": artifacts,
            "provenance": {"method": "predict_risk_model", "model": res.get("winning_model")},
        }


class WhatIfSimulationAgent(BaseIntelligenceAgent):
    agent_id = "whatif_simulation"
    name = "What-If Simulation Agent"
    category = "predictive_analysis"
    description = "Simulates strategic parameter shifts and estimates outcome elasticity deltas."

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if len(num_cols) < 2:
            return InspectionResult(is_eligible=False, reason="Requires at least 2 numerical metrics for scenario simulation.")
        return InspectionResult(is_eligible=True)

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = simulate_what_if(df)
        if not res.get("has_simulation"):
            return {"metrics": {}, "findings": [res.get("reason", "Simulation unavailable.")]}

        scenario = res.get("projected_scenario", {})
        artifacts = []
        sid = context.get("session_id") if context else None
        if sid and scenario:
            base = res.get("baseline", {})
            sim_rows = [
                {"parameter": "Shift Percentage", "value": f"{res.get('simulated_shift_pct')}%"},
                {"parameter": f"Baseline {res.get('primary_lever')}", "value": base.get(res.get('primary_lever'), 0.0)},
                {"parameter": f"Baseline {res.get('outcome_metric')}", "value": base.get(res.get('outcome_metric'), 0.0)},
                {"parameter": f"Projected {res.get('primary_lever')}", "value": scenario.get(res.get('primary_lever'), 0.0)},
                {"parameter": f"Projected {res.get('outcome_metric')}", "value": scenario.get(res.get('outcome_metric'), 0.0)},
                {"parameter": "Projected Outcome Delta", "value": scenario.get("outcome_delta", 0.0)},
            ]
            art = ArtifactManager.save_rows_csv(
                sid,
                "whatif_scenario_simulation.csv",
                sim_rows,
                "What-If Elasticity Scenario Simulation",
            )
            if art:
                artifacts.append(art)

        return {
            "metrics": {
                "simulated_shift_pct": res.get("simulated_shift_pct"),
                "primary_lever": res.get("primary_lever"),
                "projected_outcome_delta": scenario.get("outcome_delta", 0.0),
            },
            "findings": res.get("findings", []),
            "artifacts": artifacts,
            "provenance": {"method": "simulate_what_if"},
        }
