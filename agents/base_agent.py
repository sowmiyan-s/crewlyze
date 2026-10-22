# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Base Agent Contract for the 25 Agentic Data Intelligence System.
Enforces the standardized 6-step execution lifecycle:
  1. Inspect   — Validate schema, column suitability, and sample readiness
  2. Plan      — Formulate deterministic analytical strategy & parameter bounds
  3. Execute   — Perform verified Python calculation (zero LLM arithmetic)
  4. Validate  — Assert mathematical integrity and statistical guardrails
  5. Explain   — Translate computed facts into executive business prose
  6. Deliver   — Emit structured JSON results, metrics, and visual artifacts
"""

import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import pandas as pd


@dataclass
class InspectionResult:
    is_eligible: bool
    reason: str = ""
    target_columns: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentDelivery:
    agent_id: str
    name: str
    category: str
    status: str  # "completed", "ineligible", "failed"
    execution_time: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    findings: List[str] = field(default_factory=list)
    narrative: str = ""
    visuals: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "category": self.category,
            "status": self.status,
            "execution_time": round(self.execution_time, 3),
            "metrics": self.metrics,
            "findings": self.findings,
            "narrative": self.narrative,
            "visuals": self.visuals,
            "tables": self.tables,
            "provenance": self.provenance,
            "error": self.error,
        }


class BaseIntelligenceAgent:
    """
    Standardized base class for all 25 Crewlyze Intelligence Agents.
    Guarantees deterministic execution, decoupled resilience, and structured reporting.
    """

    agent_id: str = "base_agent"
    name: str = "Base Intelligence Agent"
    category: str = "data_analysis"  # data_analysis, business_analysis, data_mining, predictive_analysis, eda
    description: str = "Generic intelligence agent"

    def __init__(self, llm_caller: Optional[Callable[[str, str], str]] = None):
        self.llm_caller = llm_caller

    # ──────────────────────────────────────────────────────────────────────────
    # 6-Step Execution Lifecycle
    # ──────────────────────────────────────────────────────────────────────────

    def inspect(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> InspectionResult:
        """Step 1: Check schema compatibility and detect relevant columns."""
        if df is None or df.empty:
            return InspectionResult(is_eligible=False, reason="Dataset is empty or undefined.")
        return InspectionResult(is_eligible=True, reason="Dataset schema validated.")

    def plan(self, inspection: InspectionResult, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Step 2: Select analytical methods, parameters, and targets."""
        return {"target_columns": inspection.target_columns, "goal": project_goal}

    def execute(self, plan: Dict[str, Any], df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Step 3: Execute deterministic Python calculation (pandas, scipy, sklearn, etc.)."""
        raise NotImplementedError("Each specialized agent must implement deterministic execution.")

    def validate(self, raw_results: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Step 4: Check mathematical sanity, finite bounds, and edge cases."""
        # Sanitize NaN/inf values for JSON serialization
        def _sanitize(val: Any) -> Any:
            if isinstance(val, float):
                import math
                if math.isnan(val) or math.isinf(val):
                    return None
            elif isinstance(val, dict):
                return {k: _sanitize(v) for k, v in val.items()}
            elif isinstance(val, list):
                return [_sanitize(v) for v in val]
            return val

        return _sanitize(raw_results)

    def explain(self, validated: Dict[str, Any], project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> str:
        """Step 5: Convert verified quantitative metrics into executive business prose."""
        # By default returns a factual summary. Subclasses can invoke LLM for high-level synthesis.
        return validated.get("summary", "Analysis completed with verified quantitative metrics.")

    def deliver(self, validated: Dict[str, Any], narrative: str, execution_time: float) -> AgentDelivery:
        """Step 6: Construct structured deliverable."""
        return AgentDelivery(
            agent_id=self.agent_id,
            name=self.name,
            category=self.category,
            status="completed",
            execution_time=execution_time,
            metrics=validated.get("metrics", {}),
            findings=validated.get("findings", []),
            narrative=narrative,
            visuals=validated.get("visuals", []),
            tables=validated.get("tables", []),
            provenance=validated.get("provenance", {"method": "deterministic_python"}),
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Safe Orchestration Wrapper
    # ──────────────────────────────────────────────────────────────────────────

    def run(self, df: pd.DataFrame, project_goal: str = "", context: Optional[Dict[str, Any]] = None) -> AgentDelivery:
        """
        Coordinates the 6-step lifecycle with timing, exception containment,
        and fallback guarantees.
        """
        start_time = time.time()
        context = context or {}

        try:
            # 1. Inspect
            inspection = self.inspect(df, project_goal, context)
            if not inspection.is_eligible:
                return AgentDelivery(
                    agent_id=self.agent_id,
                    name=self.name,
                    category=self.category,
                    status="ineligible",
                    execution_time=time.time() - start_time,
                    narrative=f"Skipped: {inspection.reason}",
                    error=inspection.reason,
                )

            # 2. Plan
            plan = self.plan(inspection, df, project_goal, context)

            # 3. Execute (Deterministic calculations)
            raw_results = self.execute(plan, df, context)

            # 4. Validate
            validated = self.validate(raw_results, df)

            # 5. Explain
            narrative = self.explain(validated, project_goal, context)

            # 6. Deliver
            delivery = self.deliver(validated, narrative, time.time() - start_time)
            return delivery

        except Exception as exc:
            elapsed = time.time() - start_time
            trace_err = traceback.format_exc()
            return AgentDelivery(
                agent_id=self.agent_id,
                name=self.name,
                category=self.category,
                status="failed",
                execution_time=elapsed,
                narrative=f"Agent execution encountered an error: {str(exc)}",
                error=str(exc),
                provenance={"traceback": trace_err},
            )

    def call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Helper to invoke configured LLM safely if provided with transient rate-limit retry."""
        if self.llm_caller:
            for attempt in range(2):
                try:
                    return self.llm_caller(prompt, system_prompt)
                except Exception as e:
                    err_str = str(e).lower()
                    if attempt == 0 and any(kw in err_str for kw in ("429", "rate limit", "too many requests", "overloaded", "quota")):
                        time.sleep(2)
                        continue
                    return f"[LLM unavailable: {e}]"
        return ""
