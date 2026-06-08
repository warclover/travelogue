"""LSE decision log query helpers (Studio Inspector · W2)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from travelogue.layout_engine.decision_log import SIDECAR_NAME


def read_sidecar_events(
    trip_dir: Path,
    *,
    limit: int = 50,
    offset: int = 0,
    chapter_id: str | None = None,
    strategy_id: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Read paginated events from runs/layout-decisions.jsonl."""
    path = trip_dir / "runs" / SIDECAR_NAME
    if not path.is_file():
        return [], 0
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(ev, dict):
            continue
        if chapter_id and str(ev.get("chapterId") or "") != chapter_id:
            continue
        if strategy_id and str(ev.get("strategyId") or "") != strategy_id:
            continue
        events.append(ev)
    total = len(events)
    if offset < 0:
        offset = 0
    if limit < 1:
        return [], total
    return events[offset : offset + limit], total


def lookup_weights_by_hash(
    weights_hash: str,
    *,
    store_path: str | Path | None = None,
) -> dict[str, Any] | None:
    from travelogue.layout_engine.weights_audit import lookup_weights_snapshot

    return lookup_weights_snapshot(weights_hash, store_path=store_path)


def strategy_pack_summary(pack: Any) -> dict[str, Any]:
    profile = (pack.raw.get("scoring_profiles") or {}).get("default") or {}
    return {
        "strategyId": pack.id,
        "version": pack.version,
        "status": pack.status,
        "algorithmVersion": pack.algorithm_version,
        "displayName": pack.display_name,
        "contentHash": pack.content_hash,
        "weightsHash": pack.weights_hash("default"),
        "planning": pack.raw.get("planning") or {},
        "rhythm": pack.raw.get("rhythm") or {},
        "scoringProfile": {
            "weights": profile.get("weights") or {},
            "penalties": profile.get("penalties") or {},
        },
    }
