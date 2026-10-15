# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Master Coordinator & Orchestrator for the 25 Agentic Data Intelligence System.
Intelligently dispatches specialized agents, enforces non-blocking decoupled execution,
and streams live progress over the ContextBus.
"""

import time
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import pandas as pd

from agents.base_agent import AgentDelivery
from agents.registry import (
    CATEGORIES_MANIFEST,
    get_agents_for_selection,
    get_agent_instance,
)
from workflows.context_bus import ContextBus


class MasterCoordinator:
    """
    Orchestrates the 25 Agentic Data Intelligence Tools.
    Replaces the rigid 8-stage waterfall with a dynamic, resilient multi-agent architecture.
    """

    def __init__(
        self,
        session_id: str,
        project_goal: str = "",
        output_dir: Optional[str] = None,
        llm_caller: Optional[Callable[[str, str], str]] = None,
    ):
        self.session_id = session_id
        self.project_goal = project_goal
        self.output_dir = output_dir or ""
        self.llm_caller = llm_caller
        self.bus = ContextBus(session_id=session_id)

    def run_pipeline(
        self,
        df: pd.DataFrame,
        selected_agent_ids: Optional[List[str]] = None,
        selected_categories: Optional[List[str]] = None,
        preset: Optional[str] = None,
        progress_callback: Optional[Callable[[str, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Coordinates and executes selected agents in staged, dependency-optimized groups.
        """
        start_total = time.time()
        print(f"\n[Coordinator] Initializing 25 Agentic Intelligence System for session '{self.session_id}'...")

        # Store shared state in context bus
        self.bus.set_shared("output_dir", self.output_dir)
        self.bus.set_shared("raw_df", df)

        # Wire progress listener
        if progress_callback:
            def _bus_listener(event: Dict[str, Any]):
                etype = event.get("type", "")
                data = event.get("data", {})
                if etype in ("agent_completed", "agent_ineligible", "agent_failed"):
                    aid = data.get("agent_id", "")
                    progress_callback(aid, data.get("narrative") or data.get("findings", [""])[0])
            self.bus.add_listener(_bus_listener)

        # 1. Resolve agent list
        agents = get_agents_for_selection(
            selected_agent_ids=selected_agent_ids,
            selected_categories=selected_categories,
            preset=preset,
            llm_caller=self.llm_caller,
        )

        total_agents = len(agents)
        print(f"[Coordinator] Dispatched {total_agents} specialized intelligence agents.")

        # Staged grouping for natural information flow
        # Group 1: Foundations (Explorer, Ingestion, Quality)
        # Group 2: Empirical Analytics (Stats, Sales, Profitability, Customer, Mining, Trends)
        # Group 3: Predictive ML (Forecasting, Risk Model, Simulation)
        # Group 4: Visuals (VisualizationAgent — decoupled)
        # Group 5: Strategic Synthesis (Insights, Decision Support, Storytelling)

        foundations = []
        analytics = []
        predictive = []
        visuals = []
        synthesis = []

        for a in agents:
            aid = a.agent_id
            if aid in ("dataset_explorer", "data_cleaner", "quality_inspector"):
                foundations.append(a)
            elif aid in ("visualization",):
                visuals.append(a)
            elif aid in ("insight_discovery", "decision_support", "storytelling"):
                synthesis.append(a)
            elif a.category == "predictive_analysis":
                predictive.append(a)
            else:
                analytics.append(a)

        execution_order = foundations + analytics + predictive + visuals + synthesis
        active_df = df
        completed_count = 0

        # Execute agents sequentially with immediate error containment
        for idx, agent in enumerate(execution_order, 1):
            print(f"[{idx}/{total_agents}] Executing {agent.name} ({agent.category}) ...")
            self.bus.emit("agent_started", {"agent_id": agent.agent_id, "name": agent.name, "category": agent.category})

            context = {"context_bus": self.bus, "session_id": self.session_id}
            delivery = agent.run(active_df, project_goal=self.project_goal, context=context)

            # Check if cleaner provided cleaned dataframe
            if agent.agent_id == "data_cleaner":
                cleaned_candidate = self.bus.get_shared("cleaned_df")
                if cleaned_candidate is not None:
                    active_df = cleaned_candidate

            self.bus.publish(delivery)

            if delivery.status == "completed":
                completed_count += 1
                status_icon = "[OK]"
            elif delivery.status == "ineligible":
                status_icon = "[SKIPPED]"
            else:
                status_icon = "[FAILED]"

            print(f"  {status_icon} {agent.name} {delivery.status} in {delivery.execution_time:.2f}s.\n")

        total_time = time.time() - start_total
        print(f"[Coordinator] Pipeline completed: {completed_count}/{total_agents} agents finished in {total_time:.2f}s.\n")

        # 3. Format unified results package
        results_package = self._format_results_package(active_df, total_time)
        return results_package

    def _format_results_package(self, df: pd.DataFrame, total_time: float) -> Dict[str, Any]:
        """
        Structures the full blackboard output into a rich, serializable payload
        compatible with both the new 5-domain UI and legacy dashboard views.
        """
        all_deliveries = self.bus.get_all()
        categories_data = {
            "data_analysis": [],
            "business_analysis": [],
            "data_mining": [],
            "predictive_analysis": [],
            "eda": [],
        }

        # Collect high-level findings
        executive_findings = []
        plotly_charts = []
        png_charts = []

        for deliv in all_deliveries.values():
            d_dict = deliv.to_dict()
            cat = deliv.category
            if cat in categories_data:
                categories_data[cat].append(d_dict)

            # Accumulate findings
            for f in deliv.findings:
                if f and len(f) > 10:
                    executive_findings.append(f)

            # Extract visuals
            for v in deliv.visuals:
                if isinstance(v, dict):
                    plotly_charts.append({
                        "title": v.get("title", "Visual"),
                        "fig_json": v,
                        "insight": v.get("insight", ""),
                    })

        # Scan for PNG charts in output directory
        if self.output_dir:
            out_p = Path(self.output_dir)
            if out_p.exists():
                png_charts = [f.name for f in out_p.glob("*.png")]

        # Extract primary narrative
        story_deliv = all_deliveries.get("storytelling")
        narrative = story_deliv.narrative if story_deliv else ""

        # Extract cleaner steps
        cleaner_deliv = all_deliveries.get("data_cleaner")
        cleaning_steps = "\n".join(cleaner_deliv.findings) if cleaner_deliv else "Raw dataset ingested directly."

        # Extract insights json for strategic dashboard
        insights_json = {
            "executive_summary": narrative,
            "growth_levers": [f for f in executive_findings if any(k in f.lower() for k in ["grow", "top", "lead", "expand", "pareto", "high"])][:5],
            "problem_areas": [f for f in executive_findings if any(k in f.lower() for k in ["skew", "outlier", "risk", "spike", "drop", "erod", "loss"])][:5],
        }

        return {
            "session_id": self.session_id,
            "total_execution_time": round(total_time, 2),
            "rows_count": int(df.shape[0]),
            "cols_count": int(df.shape[1]),
            "numeric_count": int(len(df.select_dtypes(include=["number"]).columns)),
            "cat_count": int(df.shape[1]) - int(len(df.select_dtypes(include=["number"]).columns)),
            "dataframe": df,
            "categories": categories_data,
            "executive_narrative": narrative,
            "executive_findings": executive_findings[:12],
            "insights": "\n\n".join(executive_findings[:8]),
            "insights_json": insights_json,
            "cleaning_steps": cleaning_steps,
            "plotly_charts": plotly_charts,
            "png_charts": png_charts,
            "output_dir": self.output_dir,
            "code": "# 25 Agentic Data Intelligence System execution\n# Pure Python deterministic engines (pandas, scipy, scikit-learn)",
        }
