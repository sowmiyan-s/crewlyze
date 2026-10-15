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

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self._lock = threading.RLock()
        self._deliveries: Dict[str, Any] = {}
        self._shared_data: Dict[str, Any] = {}
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._event_history: List[Dict[str, Any]] = []

    def add_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback for streaming live agent lifecycle events."""
        with self._lock:
            self._listeners.append(callback)

    def emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Broadcast an event to all registered listeners (e.g., SSE logger)."""
        event = {
            "session_id": self.session_id,
            "type": event_type,
            "timestamp": time.time(),
            "data": payload,
        }
        with self._lock:
            self._event_history.append(event)
            listeners = list(self._listeners)

        for listener in listeners:
            try:
                listener(event)
            except Exception:
                pass

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
