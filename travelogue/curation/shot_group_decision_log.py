"""SSG · trip-level decision log (AC-SSG-08)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from travelogue.util.datetime_ import utc_now_iso

LOG_FILE_NAME = "shot_grouping_decision_log.json"


def write_shot_grouping_decision_log(trip_dir: Path, telemetry: dict[str, Any]) -> Path:
    trip_dir.mkdir(parents=True, exist_ok=True)
    path = trip_dir / LOG_FILE_NAME
    body = {
        "version": "1",
        "ts": utc_now_iso(),
        "kind": "shot_grouping_summary",
        "telemetry": dict(telemetry),
    }
    path.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
