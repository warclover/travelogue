"""Trip-level clustering decision log (Phase 3 · M12)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from travelogue.util.datetime_ import utc_now_iso as _utc_now_iso


class ClusterDecisionLog:
    def __init__(self, *, pipeline_run_id: str | None = None) -> None:
        self.pipeline_run_id = pipeline_run_id
        self.entries: list[dict[str, Any]] = []

    def add(
        self,
        kind: str,
        detail: str,
        *,
        input_summary: str | None = None,
    ) -> None:
        entry: dict[str, Any] = {"ts": _utc_now_iso(), "kind": kind, "detail": detail}
        if input_summary:
            entry["inputSummary"] = input_summary
        self.entries.append(entry)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"version": "1", "entries": list(self.entries)}
        if self.pipeline_run_id:
            out["pipelineRunId"] = self.pipeline_run_id
        return out

    LOG_FILE_NAME = "cluster_decision_log.json"
    LEGACY_LOG_FILE_NAME = "decision_log.json"

    def write(self, trip_dir: Path) -> Path:
        trip_dir.mkdir(parents=True, exist_ok=True)
        path = trip_dir / self.LOG_FILE_NAME
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        # Keep legacy filename in sync so older readers (and pre-existing
        # acceptance records) still resolve until they migrate.
        legacy = trip_dir / self.LEGACY_LOG_FILE_NAME
        try:
            legacy.write_text(
                json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass
        return path


def cluster_decision_log_path(trip_dir: Path) -> Path:
    """Return the active log path, preferring the new name but falling back."""
    new_path = trip_dir / ClusterDecisionLog.LOG_FILE_NAME
    if new_path.is_file():
        return new_path
    return trip_dir / ClusterDecisionLog.LEGACY_LOG_FILE_NAME
