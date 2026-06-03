"""Local Studio homepage funnel events (P9-P1-05)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_META_BYTES = 4096


def _trim_meta(meta: dict[str, Any]) -> dict[str, Any]:
    """限制 meta 序列化体积，防止 jsonl 被异常 payload 撑爆。"""
    encoded = json.dumps(meta, ensure_ascii=False).encode("utf-8")
    if len(encoded) <= MAX_META_BYTES:
        return meta
    trimmed: dict[str, Any] = {}
    for key, value in meta.items():
        candidate = dict(trimmed)
        candidate[key] = value
        if len(json.dumps(candidate, ensure_ascii=False).encode("utf-8")) <= MAX_META_BYTES:
            trimmed[key] = value
        else:
            break
    trimmed["_truncated"] = True
    return trimmed


ALLOWED_STUDIO_HOMEPAGE_EVENTS = frozenset(
    {
        "open_sheet",
        "pick_folder",
        "import_start",
        "import_success",
        "success_primary_click",
        "prep_open",
        "demo_try",
        "layout_tier",
        # Studio homepage v2 funnel (M20-h · TELEMETRY §2)
        "experiment_exposure",
        "homepage_view",
        "cta_click",
        "sheet_close",
        "sheet_abandon",
        "lightbox_open",
        "spread_page_view",
        "shelf_resume_click",
        "shelf_menu_open",
        "shelf_delete_confirm",
        "shelf_delete_success",
        "shelf_delete_cancel",
        "shelf_longshot_start",
        "shelf_longshot_success",
        "shelf_longshot_fail",
        "shelf_longshot_reveal",
        "shelf_longshot_busy",
        "bento_tab_switch",
        "js_error",
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
        record["meta"] = _trim_meta(meta)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path
