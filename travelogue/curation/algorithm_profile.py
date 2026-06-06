"""Algorithm freshness profile + stale detection (ingest / cull / curate / render)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from travelogue.config import AppConfig, get_config

PROFILE_VERSION = "1"


def _utc_now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _cover_scoring_hash(app_cfg: AppConfig) -> str:
    from travelogue.curation.cover_scoring_params import CoverScoringParams

    params: CoverScoringParams = app_cfg.curate.cover_scoring
    payload = json.dumps(asdict(params), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _cover_scoring_v2_hash(app_cfg: AppConfig) -> str:
    from dataclasses import asdict as dc_asdict

    params = app_cfg.curate.cover_scoring_v2
    payload = json.dumps(dc_asdict(params), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def expected_profile(app_cfg: AppConfig | None = None, *, layout_engine: str | None = None) -> dict[str, Any]:
    """Snapshot of algorithm knobs the running app would apply."""
    cfg = app_cfg or get_config()
    from travelogue.curation.aesthetic_score import AESTHETIC_VERSION

    out: dict[str, Any] = {
        "profileVersion": PROFILE_VERSION,
        "aestheticVersion": AESTHETIC_VERSION,
        "aestheticEnabled": bool(cfg.aesthetic.enabled),
        "cullEnabled": bool(cfg.cull.enabled),
        "cullKeepRatioFloor": float(cfg.cull.keep_ratio_floor),
        "coverScoringHash": _cover_scoring_hash(cfg),
        "coverScoringVersion": str(getattr(cfg.curate, "cover_scoring_version", "v2")),
        "coverScoringV2Hash": _cover_scoring_v2_hash(cfg),
        "sharpnessVersion": str(getattr(cfg.ingest, "sharpness_version", "v2")),
    }
    if layout_engine:
        out["layoutEngine"] = layout_engine
    return out


def _stored_profile(trip: dict) -> dict[str, Any]:
    raw = (trip.get("curation") or {}).get("algorithmProfile")
    return dict(raw) if isinstance(raw, dict) else {}


def write_ingest_profile(trip: dict, *, app_cfg: AppConfig | None = None) -> dict[str, Any]:
    """Record post-ingest algorithm state (after cull + aesthetic attach)."""
    cfg = app_cfg or get_config()
    curation = trip.setdefault("curation", {})
    profile = _stored_profile(trip)
    profile.update(expected_profile(cfg))
    profile["ingestedAt"] = _utc_now_iso()
    curation["algorithmProfile"] = profile
    return profile


def write_curate_profile(
    trip: dict,
    *,
    app_cfg: AppConfig | None = None,
    export_layout: str | None = None,
    layout_engine: str | None = None,
) -> dict[str, Any]:
    """Record post-curate algorithm state."""
    cfg = app_cfg or get_config()
    curation = trip.setdefault("curation", {})
    profile = _stored_profile(trip)
    profile.update(expected_profile(cfg, layout_engine=layout_engine or trip.get("layoutEngine")))
    if export_layout:
        profile["exportLayout"] = export_layout
    elif trip.get("exportLayout"):
        profile["exportLayout"] = trip.get("exportLayout")
    profile["curatedAt"] = _utc_now_iso()
    if not profile.get("ingestedAt"):
        profile["ingestedAt"] = profile["curatedAt"]
    curation["algorithmProfile"] = profile
    return profile


def _trip_updated_mtime(trip_dir: Path, trip: dict) -> float:
    trip_json = trip_dir / "trip.json"
    try:
        updated = trip.get("updatedAt")
        if updated:
            dt = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
            return dt.timestamp()
    except (TypeError, ValueError, OSError):
        pass
    try:
        return trip_json.stat().st_mtime
    except OSError:
        return 0.0


def preview_outputs_stale(trip_dir: Path, *, trip_mtime: float) -> bool:
    preview = trip_dir / "preview.jpg"
    if not preview.is_file():
        return False
    try:
        return trip_mtime > preview.stat().st_mtime + 0.5
    except OSError:
        return False


def _aesthetic_scored_count(trip: dict) -> tuple[int, int]:
    from travelogue.curation.aesthetic_score import asset_aesthetic

    images = [
        a
        for a in (trip.get("assets") or [])
        if a.get("type", "image") != "video" and a.get("id")
    ]
    scored = sum(1 for a in images if asset_aesthetic(a))
    return scored, len(images)


def cull_config_stale(trip: dict, *, app_cfg: AppConfig | None = None) -> bool:
    cfg = app_cfg or get_config()
    if not cfg.cull.enabled:
        return False
    stored = _stored_profile(trip)
    cull = (trip.get("curation") or {}).get("cullSummary") or {}
    recorded = stored.get("cullKeepRatioFloor")
    if recorded is None:
        recorded = cull.get("keepRatioFloor")
    if recorded is None:
        return True
    return float(recorded) < float(cfg.cull.keep_ratio_floor) - 1e-9


def aesthetic_data_stale(trip: dict, *, app_cfg: AppConfig | None = None) -> bool:
    cfg = app_cfg or get_config()
    if not cfg.aesthetic.enabled:
        return False
    scored, total = _aesthetic_scored_count(trip)
    if total <= 0:
        return False
    if scored == 0:
        return True
    stored = _stored_profile(trip)
    from travelogue.curation.aesthetic_score import AESTHETIC_VERSION

    if stored.get("aestheticVersion") and stored.get("aestheticVersion") != AESTHETIC_VERSION:
        return True
    return False


def layout_config_stale(trip: dict, *, app_cfg: AppConfig | None = None) -> bool:
    cfg = app_cfg or get_config()
    stored = _stored_profile(trip)
    if not stored:
        return bool(trip.get("chapters"))
    expected = expected_profile(cfg)
    if stored.get("coverScoringHash") != expected.get("coverScoringHash"):
        return True
    if stored.get("coverScoringVersion") != expected.get("coverScoringVersion"):
        return True
    if stored.get("coverScoringV2Hash") != expected.get("coverScoringV2Hash"):
        return True
    if stored.get("sharpnessVersion") != expected.get("sharpnessVersion"):
        return True
    engine = trip.get("layoutEngine")
    if engine and stored.get("layoutEngine") and stored.get("layoutEngine") != engine:
        return False
    if stored.get("aestheticEnabled") != expected.get("aestheticEnabled"):
        return True
    return False


def assess_algorithm_freshness(
    trip: dict,
    trip_dir: Path | None = None,
    *,
    app_cfg: AppConfig | None = None,
) -> dict[str, Any]:
    """Stale flags for Studio shelf / entry payloads."""
    cfg = app_cfg or get_config()
    scored, image_count = _aesthetic_scored_count(trip)

    aesthetic_stale = aesthetic_data_stale(trip, app_cfg=cfg)
    cull_stale = cull_config_stale(trip, app_cfg=cfg)
    layout_stale = layout_config_stale(trip, app_cfg=cfg)

    preview_stale = False
    if trip_dir is not None:
        preview_stale = preview_outputs_stale(
            trip_dir,
            trip_mtime=_trip_updated_mtime(trip_dir, trip),
        )

    hints: list[str] = []
    if aesthetic_stale:
        hints.append("审美评分未生成或版本过期，请重新导入照片")
    if cull_stale:
        hints.append("选片配置已更新，请重新挑选（重新排版将自动重跑选片）")
    if layout_stale:
        hints.append("封面/排版算法已更新，建议重新排版")
    if preview_stale:
        hints.append("书架封面预览过期，重新排版后将自动更新")

    algorithm_stale = aesthetic_stale or cull_stale or layout_stale or preview_stale
    return {
        "stale": algorithm_stale,
        "algorithmStale": algorithm_stale,
        "aestheticStale": aesthetic_stale,
        "cullStale": cull_stale,
        "layoutStale": layout_stale,
        "previewStale": preview_stale,
        "staleHints": hints,
        "staleHint": hints[0] if hints else None,
        "aestheticScoredCount": scored,
        "aestheticImageCount": image_count,
        "storedProfile": _stored_profile(trip) or None,
        "expectedProfile": expected_profile(cfg),
    }


def should_recull_on_curate(
    trip: dict,
    *,
    refresh_algorithms: bool | None = None,
    app_cfg: AppConfig | None = None,
) -> bool:
    cfg = app_cfg or get_config()
    if not cfg.cull.enabled:
        return False
    if refresh_algorithms is True:
        return True
    if refresh_algorithms is False:
        return False
    return cull_config_stale(trip, app_cfg=cfg)


def maybe_refresh_cull(
    trip: dict,
    *,
    trip_dir: Path | None = None,
    app_cfg: AppConfig | None = None,
    refresh_algorithms: bool | None = None,
) -> dict[str, Any] | None:
    """Re-run photo cull when config changed; returns cull summary or None."""
    cfg = app_cfg or get_config()
    if not should_recull_on_curate(trip, refresh_algorithms=refresh_algorithms, app_cfg=cfg):
        return None
    from travelogue.curation.photo_cull import apply_photo_cull

    return apply_photo_cull(
        trip,
        trip.get("assets") or [],
        cfg=cfg,
        trip_dir=trip_dir,
    )
