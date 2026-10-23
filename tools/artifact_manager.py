# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Deterministic Artifact Store.
Persists, indexes, and authorizes CSV, JSON, and tabular deliverables
produced by specialized intelligence agents for download.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import pandas as pd
from api.dependencies import get_safe_session_dir, is_safe_filename


class ArtifactManager:
    """Manages persistent, access-controlled data artifacts across agent executions."""

    @staticmethod
    def get_artifacts_dir(session_id: str) -> Path:
        """Returns the safe artifacts directory for a given session."""
        session_dir = get_safe_session_dir(session_id)
        art_dir = session_dir / "artifacts"
        art_dir.mkdir(parents=True, exist_ok=True)
        return art_dir

    @classmethod
    def save_dataframe_csv(
        cls,
        session_id: str,
        artifact_key: str,
        df: pd.DataFrame,
        title: str,
    ) -> Optional[Dict[str, Any]]:
        """Persists a DataFrame to an authorized CSV artifact file."""
        if not session_id or not is_safe_filename(artifact_key) or df is None or df.empty:
            return None
        try:
            art_dir = cls.get_artifacts_dir(session_id)
            target = art_dir / artifact_key
            df.to_csv(target, index=False, encoding="utf-8")
            size_bytes = target.stat().st_size
            return {
                "id": f"artifact_{artifact_key.replace('.', '_')}",
                "type": "csv",
                "title": title,
                "artifact_key": artifact_key,
                "size_bytes": size_bytes,
                "download_url": f"/api/projects/{session_id}/artifacts/{artifact_key}",
            }
        except Exception as e:
            print(f"[ArtifactManager] Error saving CSV artifact {artifact_key}: {e}")
            return None

    @classmethod
    def save_rows_csv(
        cls,
        session_id: str,
        artifact_key: str,
        rows: List[Dict[str, Any]],
        title: str,
    ) -> Optional[Dict[str, Any]]:
        """Persists a list of row dictionaries to a CSV artifact."""
        if not rows:
            return None
        try:
            df = pd.DataFrame(rows)
            return cls.save_dataframe_csv(session_id, artifact_key, df, title)
        except Exception as e:
            print(f"[ArtifactManager] Error converting rows to CSV artifact {artifact_key}: {e}")
            return None

    @classmethod
    def save_json_artifact(
        cls,
        session_id: str,
        artifact_key: str,
        data: Any,
        title: str,
    ) -> Optional[Dict[str, Any]]:
        """Persists structured data to an authorized JSON artifact file."""
        if not session_id or not is_safe_filename(artifact_key) or data is None:
            return None
        try:
            art_dir = cls.get_artifacts_dir(session_id)
            target = art_dir / artifact_key
            with open(target, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            size_bytes = target.stat().st_size
            return {
                "id": f"artifact_{artifact_key.replace('.', '_')}",
                "type": "json",
                "title": title,
                "artifact_key": artifact_key,
                "size_bytes": size_bytes,
                "download_url": f"/api/projects/{session_id}/artifacts/{artifact_key}",
            }
        except Exception as e:
            print(f"[ArtifactManager] Error saving JSON artifact {artifact_key}: {e}")
            return None

    @classmethod
    def get_artifact_file(cls, session_id: str, artifact_key: str) -> Optional[Path]:
        """Resolves and validates an artifact file path, preventing directory traversal."""
        if not session_id or not is_safe_filename(artifact_key):
            return None
        try:
            art_dir = cls.get_artifacts_dir(session_id)
            target = (art_dir / artifact_key).resolve()
            if not target.is_relative_to(art_dir):
                return None
            if target.exists() and target.is_file():
                return target
        except Exception:
            pass
        return None
