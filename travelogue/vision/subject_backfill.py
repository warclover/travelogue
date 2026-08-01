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
        from travelogue.config import get_config

        root = Path(get_config().trips_dir).resolve()
        candidate = root / str(tid)
        return candidate if candidate.is_dir() else None
    except Exception:
        return None


def _hydrate_from_embedding_cache(
    trip_dir: Path,
    assets: list[dict],
    *,
    cfg: Any | None = None,
) -> int:
    """Label missing subjectClass from on-disk CLIP vectors only (no re-embed)."""
    from travelogue.vision.cache import load_embedding_cache
    from travelogue.vision.clip_encoder import get_clip_encoder

    cached = load_embedding_cache(trip_dir)
    if cached is None:
        return 0
    source = str(cached.get("source") or "")
    if source != "clip":
        return 0
    asset_ids = list(cached.get("asset_ids") or [])
    vectors = cached.get("vectors")
    if not asset_ids or vectors is None:
        return 0
    encoder = get_clip_encoder(cfg)
    apply_fn = getattr(encoder, "apply_subject_labels_from_vectors", None)
    if not callable(apply_fn):
        return 0
    return int(
        apply_fn(
            assets,
            asset_ids=asset_ids,
            vectors=vectors,
            only_missing=True,
        )
        or 0
    )


def ensure_subject_classes(
    trip: dict,
    assets: list[dict] | None = None,
    *,
    trip_dir: Path | None = None,
    cache_only: bool = True,
) -> int:
    """Label assets missing subjectClass from CLIP cache (default) / optional embed.

    Soft-fails (returns 0) when CLIP/trip_dir unavailable — cover scoring then
    proceeds without FRP food signals for those assets.

    ``cache_only=True`` (cover path default): never trigger a full re-embed; only
    hydrate labels from an existing embedding cache (may still load CLIP text
    features).
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

        cfg = get_config()
        if cache_only:
            labeled = _hydrate_from_embedding_cache(root, pool, cfg=cfg)
        else:
            from travelogue.vision.cache import prepare_scene_embeddings
            from travelogue.vision.clip_encoder import get_clip_encoder

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
            labeled = sum(1 for a in missing if a.get("subjectClass"))
    except Exception as exc:
        _log.warning("subjectClass backfill skipped: %s", exc)
        return 0
    if labeled:
        _log.info("backfilled subjectClass for %s cover-pool assets", labeled)
    return labeled


__all__ = [
    "assets_missing_subject_class",
    "ensure_subject_classes",
    "resolve_trip_dir_for_backfill",
]
