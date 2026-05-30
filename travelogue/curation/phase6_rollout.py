"""Phase 6 rollout helpers · P5 rollback patch (PRD §14.3)."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Any

from travelogue.config import AppConfig, load_config


def p5_rollback_patch() -> dict[str, Any]:
    """Config patch that restores P5-stable clustering/layout behavior."""
    return {
        "clustering": {
            "scene": {
                "algorithm": "dbscan",
            },
            "geo": {
                "eventGapMode": "fixed",
            },
            "enableSceneSubSegments": False,
        },
        "curate": {
            "layout": {
                "enable_gravity_balance": False,
                "enable_mmr_diversity": False,
                "enable_arc_breath": False,
            },
            "enable_gravity_balance": False,
            "enable_mmr_diversity": False,
            "enable_arc_breath": False,
        },
    }


def g1_rollout_patch(
    *,
    traffic_percent: float = 10.0,
    cohort_salt: str = "p6-g1-2026-05",
    allowlist_trip_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Config patch for G1 10% gray rollout (PRD §14.1)."""
    return rollout_stage_patch(
        stage="G1",
        traffic_percent=traffic_percent,
        cohort_salt=cohort_salt,
        allowlist_trip_ids=allowlist_trip_ids,
    )


def g2_rollout_patch(
    *,
    traffic_percent: float = 50.0,
    cohort_salt: str = "p6-g1-2026-05",
    allowlist_trip_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Config patch for G2 50% gray rollout (PRD §14.1)."""
    return rollout_stage_patch(
        stage="G2",
        traffic_percent=traffic_percent,
        cohort_salt=cohort_salt,
        allowlist_trip_ids=allowlist_trip_ids,
    )


def g3_rollout_patch(
    *,
    traffic_percent: float = 100.0,
    cohort_salt: str = "p6-g1-2026-05",
    allowlist_trip_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Config patch for G3 full rollout (PRD §14.1)."""
    return rollout_stage_patch(
        stage="G3",
        traffic_percent=traffic_percent,
        cohort_salt=cohort_salt,
        allowlist_trip_ids=allowlist_trip_ids,
    )


def rollout_stage_patch(
    *,
    stage: str,
    traffic_percent: float,
    cohort_salt: str,
    allowlist_trip_ids: list[str] | None = None,
) -> dict[str, Any]:
    patch: dict[str, Any] = {
        "phase6": {
            "rollout": {
                "stage": stage,
                "trafficPercent": traffic_percent,
                "cohortSalt": cohort_salt,
                "allowlistTripIds": list(allowlist_trip_ids or []),
                "blocklistTripIds": [],
            },
        },
    }
    return patch


def apply_config_patch(config_path: Path | None, patch: dict[str, Any]) -> Path:
    """Deep-merge patch into config.yaml."""
    if config_path is None:
        cfg = load_config()
        config_path = cfg.config_path or Path.cwd() / "config.yaml"

    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML required for rollout") from exc

    data: dict[str, Any] = {}
    if config_path.is_file():
        with config_path.open(encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
            if isinstance(loaded, dict):
                data = loaded

    def _deep_merge(base: dict, extra: dict) -> dict:
        out = dict(base)
        for key, val in extra.items():
            if isinstance(val, dict) and isinstance(out.get(key), dict):
                out[key] = _deep_merge(out[key], val)
            else:
                out[key] = val
        return out

    merged = _deep_merge(data, patch)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(merged, f, allow_unicode=True, sort_keys=False)
    return config_path


def apply_p5_rollback_config(config_path: Path | None = None) -> Path:
    """Merge P5 rollback settings into config.yaml (creates file if missing)."""
    return apply_config_patch(config_path, p5_rollback_patch())


def apply_g1_rollout_config(
    config_path: Path | None = None,
    *,
    traffic_percent: float = 10.0,
    cohort_salt: str = "p6-g1-2026-05",
    allowlist_trip_ids: list[str] | None = None,
) -> Path:
    """Merge G1 rollout gate into config.yaml."""
    patch = g1_rollout_patch(
        traffic_percent=traffic_percent,
        cohort_salt=cohort_salt,
        allowlist_trip_ids=allowlist_trip_ids,
    )
    return apply_config_patch(config_path, patch)


def apply_g2_rollout_config(
    config_path: Path | None = None,
    *,
    traffic_percent: float = 50.0,
    cohort_salt: str = "p6-g1-2026-05",
    allowlist_trip_ids: list[str] | None = None,
) -> Path:
    """Merge G2 rollout gate into config.yaml."""
    patch = g2_rollout_patch(
        traffic_percent=traffic_percent,
        cohort_salt=cohort_salt,
        allowlist_trip_ids=allowlist_trip_ids,
    )
    return apply_config_patch(config_path, patch)


def apply_g3_rollout_config(
    config_path: Path | None = None,
    *,
    traffic_percent: float = 100.0,
    cohort_salt: str = "p6-g1-2026-05",
    allowlist_trip_ids: list[str] | None = None,
) -> Path:
    """Merge G3 full rollout gate into config.yaml."""
    patch = g3_rollout_patch(
        traffic_percent=traffic_percent,
        cohort_salt=cohort_salt,
        allowlist_trip_ids=allowlist_trip_ids,
    )
    return apply_config_patch(config_path, patch)


def rollout_bucket(trip_id: str, *, cohort_salt: str, traffic_percent: float) -> int:
    """Deterministic bucket 0..99 for trip_id (stable across runs)."""
    if traffic_percent <= 0:
        return 100
    if traffic_percent >= 100:
        return 0
    digest = hashlib.sha256(f"{cohort_salt}:{trip_id}".encode()).hexdigest()
    return int(digest[:8], 16) % 100


def phase6_in_rollout_cohort(trip_id: str, cfg: AppConfig) -> bool:
    """True when trip should receive Phase 6 behavior under current rollout gate."""
    rollout = cfg.phase6.rollout
    tid = str(trip_id or "").strip()
    if not tid:
        return True
    if tid in rollout.blocklist_trip_ids:
        return False
    if tid in rollout.allowlist_trip_ids:
        return True
    if rollout.stage == "off" or rollout.traffic_percent <= 0:
        return True
    if rollout.traffic_percent >= 100:
        return True
    bucket = rollout_bucket(
        tid,
        cohort_salt=rollout.cohort_salt,
        traffic_percent=rollout.traffic_percent,
    )
    return bucket < int(round(rollout.traffic_percent))


def resolve_curate_config_for_trip(cfg: AppConfig, trip_id: str) -> AppConfig:
    """Return cfg with P5-stable overrides when trip is outside the rollout cohort."""
    if phase6_in_rollout_cohort(trip_id, cfg):
        return cfg
    clustering = cfg.clustering
    curate = cfg.curate
    return replace(
        cfg,
        clustering=replace(
            clustering,
            scene=replace(clustering.scene, algorithm="dbscan"),
            geo=replace(clustering.geo, event_gap_mode="fixed"),
            enable_scene_sub_segments=False,
        ),
        curate=replace(
            curate,
            enable_gravity_balance=False,
            enable_mmr_diversity=False,
            enable_arc_breath=False,
            max_consecutive_same_pattern=99,
        ),
    )


def phase6_rollout_snapshot(cfg: AppConfig) -> dict[str, Any]:
    r = cfg.phase6.rollout
    return {
        "stage": r.stage,
        "trafficPercent": r.traffic_percent,
        "cohortSalt": r.cohort_salt,
        "allowlistTripIds": list(r.allowlist_trip_ids),
        "blocklistTripIds": list(r.blocklist_trip_ids),
    }


def phase6_feature_snapshot(cfg: AppConfig) -> dict[str, Any]:
    """Runtime snapshot for rollout logs / AC-P6-07 drills."""
    return {
        "sceneAlgorithm": cfg.clustering.scene.algorithm,
        "eventGapMode": cfg.clustering.geo.event_gap_mode,
        "enableSceneSubSegments": cfg.clustering.enable_scene_sub_segments,
        "enableGravityBalance": cfg.curate.enable_gravity_balance,
        "enableMmrDiversity": cfg.curate.enable_mmr_diversity,
        "enableArcBreath": cfg.curate.enable_arc_breath,
        "maxConsecutiveSamePattern": cfg.curate.max_consecutive_same_pattern,
    }
