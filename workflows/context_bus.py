# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Central Thread-Safe Context Bus & Blackboard.
Enables inter-agent communication, validated metric sharing,
and zero-latency streaming of multi-agent events.
"""

import threading
import time
from typing import Any, Callable, Dict, List, Optional
import pandas as pd


class ContextBus:
    """
    Central blackboard for coordinating the 25 Agentic Intelligence tools.
    Allows agents to inspect results from other agents without direct coupling,
    and broadcasts events to SSE streams.
    """

    def __init__(self, session_id: str = "", events_file_path: Optional[str] = None):
        self.session_id = session_id
        self.events_file_path = events_file_path
        self._lock = threading.RLock()
        self._deliveries: Dict[str, Any] = {}
        self._shared_data: Dict[str, Any] = {}
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._event_history: List[Dict[str, Any]] = []

    def set_events_file(self, path: str) -> None:
        """Set or update the target events.jsonl file path for persistent streaming."""
        with self._lock:
            self.events_file_path = path

    def add_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback for streaming live agent lifecycle events."""
        with self._lock:
            self._listeners.append(callback)

    def emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Broadcast an event to all registered listeners and append to persistent log."""
        import json
        event = {
            "session_id": self.session_id,
            "type": event_type,
            "timestamp": time.time(),
            "data": payload,
        }
        with self._lock:
            self._event_history.append(event)
            listeners = list(self._listeners)
            target_file = self.events_file_path

        # Persistent append to events.jsonl
        if target_file:
            try:
                with open(target_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event) + "\n")
            except Exception:
                pass

        for listener in listeners:
            try:
                listener(event)
            except Exception:
                pass

    def emit_stage_transition(
        self, stage_id: str, stage_number: int, total_stages: int, name: str, active_agents: Optional[List[str]] = None
    ) -> None:
        """Observable-pattern stage barrier transition event."""
        self.emit("stage_transition", {
            "stage_id": stage_id,
            "stage_number": stage_number,
            "total_stages": total_stages,
            "name": name,
            "active_agents": active_agents or [],
        })

    def emit_agent_pending(self, agent_id: str, name: str, category: str, stage_id: str = "") -> None:
        """Observable-pattern pending() state transition when an agent begins execution."""
        self.emit("agent_pending", {
            "agent_id": agent_id,
            "name": name,
            "category": category,
            "stage_id": stage_id,
            "status": "pending",
        })

    def emit_agent_fulfilled(
        self,
        agent_id: str,
        name: str,
        category: str,
        status: str,
        execution_time: float,
        summary: str = "",
        metrics_count: int = 0,
    ) -> None:
        """Observable-pattern fulfilled() state transition when an agent successfully yields deliverables."""
        self.emit("agent_fulfilled", {
            "agent_id": agent_id,
            "name": name,
            "category": category,
            "status": status,
            "execution_time": round(execution_time, 3),
            "summary": summary,
            "metrics_count": metrics_count,
        })

    def emit_agent_rejected(self, agent_id: str, name: str, category: str, error: str) -> None:
        """Observable-pattern rejected() state transition when an agent encounters an error."""
        self.emit("agent_rejected", {
            "agent_id": agent_id,
            "name": name,
            "category": category,
            "status": "failed",
            "error": error,
        })

    def emit_pipeline_completed(self, total_time: float, completed_count: int, total_agents: int) -> None:
        """Terminal pipeline completion event."""
        self.emit("pipeline_completed", {
            "total_time": round(total_time, 2),
            "completed_count": completed_count,
            "total_agents": total_agents,
        })

    def get_event_history(self, since_timestamp: float = 0.0) -> List[Dict[str, Any]]:
        """Retrieve historical events since timestamp for client reconnection replay."""
        with self._lock:
            if since_timestamp <= 0.0:
                return list(self._event_history)
            return [e for e in self._event_history if e.get("timestamp", 0) > since_timestamp]

    def publish(self, delivery: Any) -> None:
        """Publish an AgentDelivery into the blackboard."""
        with self._lock:
            self._deliveries[delivery.agent_id] = delivery

        # Emit completion or status event
        self.emit(
            "agent_completed" if delivery.status == "completed" else f"agent_{delivery.status}",
            delivery.to_dict() if hasattr(delivery, "to_dict") else delivery,
        )

    def get(self, agent_id: str) -> Optional[Any]:
        """Retrieve delivery of a specific agent."""
        with self._lock:
            return self._deliveries.get(agent_id)

    def get_category(self, category: str) -> List[Any]:
        """Retrieve all completed deliveries belonging to an analysis category."""
        with self._lock:
            return [d for d in self._deliveries.values() if getattr(d, "category", "") == category]

    def get_all(self) -> Dict[str, Any]:
        """Return all deliveries."""
        with self._lock:
            return dict(self._deliveries)

    def set_shared(self, key: str, value: Any) -> None:
        """Store arbitrary shared runtime artifacts (e.g. plot directory, cleaned path)."""
        with self._lock:
            self._shared_data[key] = value

    def get_shared(self, key: str, default: Any = None) -> Any:
        """Retrieve shared runtime artifact."""
        with self._lock:
            return self._shared_data.get(key, default)

    def get_context_summary(self, max_length: int = 2500) -> str:
        """
        Generate a concise text summary of all verified findings so far
        for cross-examination agents (e.g. InsightDiscovery or DecisionSupport).
        """
        with self._lock:
            lines = []
            for agent_id, deliv in self._deliveries.items():
                if getattr(deliv, "status", "") != "completed":
                    continue
                name = getattr(deliv, "name", agent_id)
                findings = getattr(deliv, "findings", [])
                metrics = getattr(deliv, "metrics", {})
                lines.append(f"[{name}]")
                if metrics:
                    metric_str = ", ".join(f"{k}: {v}" for k, v in list(metrics.items())[:4])
                    lines.append(f"  Key Metrics: {metric_str}")
                for f in findings[:3]:
                    lines.append(f"  - {f}")
            summary = "\n".join(lines)
            return summary[:max_length]

    def to_dict(self) -> Dict[str, Any]:
        """Export full blackboard state for dashboard serialization."""
        with self._lock:
            categorized: Dict[str, List[Dict[str, Any]]] = {
                "data_analysis": [],
                "business_analysis": [],
                "data_mining": [],
                "predictive_analysis": [],
                "eda": [],
            }
            for d in self._deliveries.values():
                d_dict = d.to_dict() if hasattr(d, "to_dict") else d
                cat = d_dict.get("category", "eda")
                if cat in categorized:
                    categorized[cat].append(d_dict)
                else:
                    categorized.setdefault(cat, []).append(d_dict)

            return {
                "session_id": self.session_id,
                "categories": categorized,
                "agents_count": len(self._deliveries),
                "completed_count": sum(1 for d in self._deliveries.values() if getattr(d, "status", "") == "completed"),
            }
