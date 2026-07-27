"""Backfill CLIP subjectClass before cover / FRP decisions."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)


def assets_missing_subject_class(assets: list[dict]) -> list[dict]:
    return [
        a
        for a in assets
        if a.get("id")
        and a.get("type", "image") != "video"
        and not a.get("subjectClass")
    ]


def resolve_trip_dir_for_backfill(trip: dict) -> Path | None:
    """Best-effort trip root for embedding cache / image paths."""
    for key in ("_tripDir", "tripDir"):
        raw = trip.get(key)
        if raw:
            path = Path(str(raw))
            if path.is_dir():
                return path
    tid = trip.get("tripId") or trip.get("id")
    if not tid:
        return None
    try:
        from travelogue.runtime import app_context_for_trips_dir

        svc = app_context_for_trips_dir(None).trip_service()
        return svc.resolve_trip_json(str(tid)).parent
    except Exception:
        return None


def ensure_subject_classes(
    trip: dict,
    assets: list[dict] | None = None,
    *,
    trip_dir: Path | None = None,
) -> int:
    """Label assets missing subjectClass from CLIP cache / incremental embed.

    Soft-fails (returns 0) when CLIP/trip_dir unavailable — cover scoring then
    proceeds without FRP food signals for those assets.
    """
    pool = assets if assets is not None else list(trip.get("assets") or [])
    missing = assets_missing_subject_class(pool)
    if not missing:
        return 0
    root = trip_dir or resolve_trip_dir_for_backfill(trip)
    if root is None or not root.is_dir():
        return 0
    try:
        from travelogue.config import get_config
        from travelogue.vision.cache import prepare_scene_embeddings
        from travelogue.vision.clip_encoder import get_clip_encoder

        cfg = get_config()
        encoder = get_clip_encoder(cfg)
        # Mutates asset dicts in place (same objects as trip["assets"] when shared).
        prepare_scene_embeddings(
            root,
            pool if pool else list(trip.get("assets") or []),
            encoder,
            force_recluster=False,
            deterministic=True,
            cfg=cfg,
            apply_subject_class=True,
        )
    except Exception as exc:
        _log.warning("subjectClass backfill skipped: %s", exc)
        return 0
    labeled = sum(1 for a in missing if a.get("subjectClass"))
    if labeled:
        _log.info("backfilled subjectClass for %s cover-pool assets", labeled)
    return labeled


__all__ = [
    "assets_missing_subject_class",
    "ensure_subject_classes",
    "resolve_trip_dir_for_backfill",
]
