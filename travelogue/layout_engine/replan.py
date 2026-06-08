"""LSE-CAP-10 layout-only replan when layoutDensity changes (§4.5.10)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from travelogue.config import AppConfig, get_config
from travelogue.curation.layout_density import layout_density_params, normalize_layout_density


@dataclass(frozen=True)
class LayoutReplanDecision:
    layout_only: bool
    reason: str | None = None


def _read_studio_intent_density(trip_dir: Path | None) -> str | None:
    if trip_dir is None:
        return None
    path = trip_dir / "runs" / "studio-intent.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    density = data.get("layoutDensity")
    return normalize_layout_density(density) if density else None


def applied_layout_density(trip: dict, *, trip_dir: Path | None = None) -> str:
    curation = trip.get("curation") or {}
    applied = curation.get("appliedLayoutDensity")
    if applied:
        return normalize_layout_density(applied)
    from_studio = _read_studio_intent_density(trip_dir)
    if from_studio:
        return from_studio
    intent = trip.get("intent") or {}
    return normalize_layout_density(intent.get("layoutDensity"))


def should_layout_only_replan(
    trip: dict,
    *,
    trip_dir: Path | None = None,
    cfg: AppConfig | None = None,
) -> LayoutReplanDecision:
    """True when fine_craft re-curate changes layoutDensity and chapters exist."""
    app = cfg or get_config()
    intent = trip.get("intent") or {}
    mode = str(intent.get("mode") or "quick_share").strip().lower()
    if mode == "quick_share":
        return LayoutReplanDecision(layout_only=False, reason="quick_share")

    chapters = trip.get("chapters") or []
    if not chapters or not any(ch.get("items") for ch in chapters):
        return LayoutReplanDecision(layout_only=False, reason="no_existing_chapters")

    current = layout_density_params(trip, app_cfg=app).density
    previous = applied_layout_density(trip, trip_dir=trip_dir)
    if current == previous:
        return LayoutReplanDecision(layout_only=False, reason="density_unchanged")

    caps = app.layout.strategy_engine.capabilities
    if not app.layout.strategy_engine.enabled and not caps.segment_order_optimizer:
        # layout-only path requires LSE or explicit capability flag
        pass
    return LayoutReplanDecision(layout_only=True, reason="density_change")


def mark_layout_replan(trip: dict, *, reason: str) -> None:
    pipe = trip.setdefault("pipeline", {})
    pipe["layoutReplanReason"] = reason
    curation = trip.setdefault("curation", {})
    curation["layoutReplan"] = {"reason": reason, "layoutOnly": True}


def record_applied_layout_density(trip: dict, *, cfg: AppConfig | None = None) -> None:
    app = cfg or get_config()
    density = layout_density_params(trip, app_cfg=app).density
    curation = trip.setdefault("curation", {})
    curation["appliedLayoutDensity"] = density


def buckets_from_existing_chapters(trip: dict) -> dict[str, Any] | None:
    """Rebuild bucket plan fields from persisted chapters (layout-only)."""
    chapters = trip.get("chapters") or []
    if not chapters:
        return None
    buckets: list[list[str]] = []
    bucket_segment_ids: list[str] = []
    bucket_segment_ids_all: list[list[str]] = []
    for ch in chapters:
        items = ch.get("items") or []
        bucket = [str(it.get("assetId")) for it in items if it.get("assetId")]
        buckets.append(bucket)
        cur = ch.get("curation") or {}
        seg = cur.get("segmentId")
        seg_id = str(seg) if seg else ""
        bucket_segment_ids.append(seg_id)
        seg_ids = cur.get("segmentIds")
        if isinstance(seg_ids, list) and seg_ids:
            bucket_segment_ids_all.append([str(s) for s in seg_ids])
        elif seg_id:
            bucket_segment_ids_all.append([seg_id])
        else:
            bucket_segment_ids_all.append([])

    curation = trip.get("curation") or {}
    segments = curation.get("segments") or []
    segment_labels = {
        str(s.get("id")): str(s.get("label") or "")
        for s in segments
        if isinstance(s, dict) and s.get("id")
    }
    return {
        "buckets": buckets,
        "bucket_segment_ids": bucket_segment_ids,
        "bucket_segment_ids_all": bucket_segment_ids_all,
        "segments": segments,
        "segment_labels": segment_labels,
        "curation_segments": segments,
    }
