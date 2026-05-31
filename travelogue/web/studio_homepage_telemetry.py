"""Local Studio homepage funnel events (P9-P1-05)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_STUDIO_HOMEPAGE_EVENTS = frozenset(
    {
        "open_sheet",
        "pick_folder",
        "import_start",
        "import_success",
        "success_primary_click",
        "prep_open",
        "demo_try",
    }
)


def studio_homepage_events_path() -> Path:
    return Path.home() / ".travelogue" / "telemetry" / "studio-homepage-events.jsonl"


def append_studio_homepage_event(event: str, meta: dict[str, Any] | None = None) -> Path:
    if event not in ALLOWED_STUDIO_HOMEPAGE_EVENTS:
        raise ValueError(f"unknown studio homepage event: {event}")
    path = studio_homepage_events_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "event": event,
    }
    if meta:
        record["meta"] = meta
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path
