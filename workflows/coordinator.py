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
        self._cancelled = False

    def is_cancelled(self) -> bool:
        """Checks if a cancellation request has been submitted for this session."""
        if self._cancelled:
            return True
        if self.session_id:
            try:
                from api.dependencies import SESSIONS_DIR
                done_path = SESSIONS_DIR / self.session_id / "done.txt"
                if done_path.exists():
                    self._cancelled = True
                    return True
            except Exception:
                pass
        return False

    def cancel(self):
        """Manually trigger cancellation."""
        self._cancelled = True

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

        active_df = df
        completed_count = 0

        def _execute_agent(agent_item, current_df):
            if self.is_cancelled():
                return AgentDelivery(
                    agent_id=agent_item.agent_id,
                    name=agent_item.name,
                    category=agent_item.category,
                    status="ineligible",
                    narrative="Execution halted due to cancellation."
                )
            self.bus.emit("agent_started", {"agent_id": agent_item.agent_id, "name": agent_item.name, "category": agent_item.category})
            context = {"context_bus": self.bus, "session_id": self.session_id}
            deliv = agent_item.run(current_df, project_goal=self.project_goal, context=context)
            self.bus.publish(deliv)
            status_icon = "[OK]" if deliv.status == "completed" else ("[SKIPPED]" if deliv.status == "ineligible" else "[FAILED]")
            print(f"  {status_icon} {agent_item.name} ({deliv.category}) {deliv.status} in {deliv.execution_time:.2f}s.")
            return deliv

        # Stage 1/5: Foundations (Sequential so data_cleaner passes cleaned_df forward)
        for agent in foundations:
            if self.is_cancelled():
                print("[Coordinator] Halting execution at Stage 1 due to cancellation.")
                break
            print(f"[Coordinator: Stage 1/5] Foundations: {agent.name} ...")
            deliv = _execute_agent(agent, active_df)
            if agent.agent_id == "data_cleaner":
                cleaned_cand = self.bus.get_shared("cleaned_df")
                if cleaned_cand is not None:
                    active_df = cleaned_cand
            if deliv.status == "completed":
                completed_count += 1

        # Stage 2/5: Empirical Analytics (Concurrent execution on sanitized active_df)
        if analytics and not self.is_cancelled():
            print(f"[Coordinator: Stage 2/5] Concurrently executing {len(analytics)} empirical analytics agents ...")
            workers = min(6, len(analytics))
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(_execute_agent, a, active_df): a for a in analytics}
                for fut in as_completed(futures):
                    deliv = fut.result()
                    if deliv.status == "completed":
                        completed_count += 1

        # Stage 3/5: Predictive Auto-ML & Simulations (Concurrent execution)
        if predictive and not self.is_cancelled():
            print(f"[Coordinator: Stage 3/5] Concurrently executing {len(predictive)} predictive agents ...")
            workers = min(4, len(predictive))
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(_execute_agent, a, active_df): a for a in predictive}
                for fut in as_completed(futures):
                    deliv = fut.result()
                    if deliv.status == "completed":
                        completed_count += 1

        # Stage 4/5: Decoupled Visual Intelligence
        if not self.is_cancelled():
            for agent in visuals:
                if self.is_cancelled():
                    break
                print(f"[Coordinator: Stage 4/5] Visuals: {agent.name} ...")
                deliv = _execute_agent(agent, active_df)
                if deliv.status == "completed":
                    completed_count += 1

        # Stage 5/5: Strategic Synthesis & Storytelling (Consuming the full Blackboard context)
        if not self.is_cancelled():
            for agent in synthesis:
                if self.is_cancelled():
                    break
                print(f"[Coordinator: Stage 5/5] Strategic Synthesis: {agent.name} ...")
                deliv = _execute_agent(agent, active_df)
                if deliv.status == "completed":
                    completed_count += 1

        total_time = time.time() - start_total
        print(f"\n[Coordinator] Staged pipeline completed: {completed_count}/{total_agents} agents finished in {total_time:.2f}s.\n")

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
