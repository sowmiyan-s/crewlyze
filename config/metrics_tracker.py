# Crewlyze Metrics Tracker
# Copyright (c) 2026 Sowmiyan S
# Licensed under the MIT License

import os
import json
import time
from pathlib import Path

def get_metrics_file_path() -> Path:
    user_home = Path.home() / ".crewlyze"
    return Path(os.getenv("CREWLYZE_DATA_DIR", str(user_home / "data"))) / "metrics.json"

def log_metric(
    session_id: str,
    dataset_name: str,
    rows: int,
    cols: int,
    stages: dict,
    total_time: float,
    success: bool = True,
    token_usage: int = 0,
    estimated_cost: float = 0.0
):
    metrics_path = get_metrics_file_path()
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    
    new_entry = {
        "session_id": session_id,
        "dataset_name": dataset_name,
        "rows": rows,
        "columns": cols,
        "timestamp": time.time() * 1000,  # Milliseconds since epoch
        "stages": stages,
        "total_time": total_time,
        "token_usage": token_usage,
        "estimated_cost": estimated_cost,
        "success": success
    }
    
    metrics = []
    if metrics_path.exists():
        try:
            with open(metrics_path, "r", encoding="utf-8") as f:
                metrics = json.load(f)
                if not isinstance(metrics, list):
                    metrics = []
        except Exception:
            metrics = []
            
    metrics.append(new_entry)
    
    # Cap to last 100 entries to prevent file from growing indefinitely
    metrics = metrics[-100:]
    
    try:
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
    except Exception as e:
        print(f"Failed to save metrics: {e}")

def get_metrics() -> list:
    metrics_path = get_metrics_file_path()
    if not metrics_path.exists():
        return []
    try:
        with open(metrics_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
