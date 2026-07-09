"""Template platform metrics writer (layer-0)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def metrics_path() -> Path:
    return Path.home() / ".travelogue" / "telemetry" / "template-metrics.jsonl"


def record_template_metric(name: str, **labels: Any) -> None:
    """Append metric event; never raises."""
    try:
        path = metrics_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "at": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "name": name,
            **labels,
        }
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass
