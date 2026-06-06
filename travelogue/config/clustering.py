"""Clustering and geocode configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from travelogue.config._common import TriState, normalize_tri_state
from travelogue.config_helpers import cfg_bool, cfg_dict, cfg_float, cfg_int, cfg_str


@dataclass
class GeocodeConfig:
    enabled: bool = False


@dataclass
class GeoClusterConfig:
    event_gap_mode: Literal["fixed", "auto"] = "auto"
    event_time_gap_hours: float = 4.0
    min_photos_per_event: int = 3
    location_proximity_km: float = 5.5
    merge_time_gap_hours: float = 36.0
    merge_location_km: float = 55.0
    max_event_days: int = 4


@dataclass
class SceneClusterConfig:
    algorithm: Literal["hdbscan", "dbscan"] = "hdbscan"
    cluster_eps: float = 0.07
    cluster_min_samples: int = 10
    timeout_sec: int = 480


@dataclass
class ClusteringConfig:
    enabled: TriState = "auto"
    auto_gps_min_ratio: float = 0.40
    segment_curate_mode: Literal["event_first", "date_fallback"] = "event_first"
    scene_cluster_mode: Literal["run_aware", "off"] = "run_aware"
    deterministic: bool = True
    deterministic_strict: bool = False
    force_recluster: bool = False
    cache_abi_version: str = "v1"
    cache_config_fingerprint: str = "auto"
    geo: GeoClusterConfig = field(default_factory=GeoClusterConfig)
    scene: SceneClusterConfig = field(default_factory=SceneClusterConfig)
    enable_scene_sub_segments: bool = True
    scene_subsegment_min_photos: int = 3


def geo_cluster_from_dict(raw: dict[str, Any]) -> GeoClusterConfig:
    gap_mode = str(raw.get("eventGapMode", raw.get("event_gap_mode", "auto")))
    if gap_mode not in ("fixed", "auto"):
        gap_mode = "auto"
    return GeoClusterConfig(
        event_gap_mode=gap_mode,  # type: ignore[arg-type]
        event_time_gap_hours=cfg_float(raw, "event_time_gap_hours", "eventTimeGapHours", 4.0),
        min_photos_per_event=cfg_int(raw, "min_photos_per_event", "minPhotosPerEvent", 3),
        location_proximity_km=cfg_float(raw, "location_proximity_km", "locationProximityKm", 5.5),
        merge_time_gap_hours=cfg_float(raw, "merge_time_gap_hours", "mergeTimeGapHours", 36.0),
        merge_location_km=cfg_float(raw, "merge_location_km", "mergeLocationKm", 55.0),
        max_event_days=cfg_int(raw, "max_event_days", "maxEventDays", 4),
    )


def scene_cluster_from_dict(raw: dict[str, Any]) -> SceneClusterConfig:
    algo = str(raw.get("algorithm", "hdbscan")).lower()
    if algo not in ("hdbscan", "dbscan"):
        algo = "hdbscan"
    return SceneClusterConfig(
        algorithm=algo,  # type: ignore[arg-type]
        cluster_eps=cfg_float(raw, "cluster_eps", "clusterEps", 0.07),
        cluster_min_samples=cfg_int(raw, "cluster_min_samples", "clusterMinSamples", 10),
        timeout_sec=cfg_int(raw, "timeout_sec", "timeoutSec", 480),
    )


def clustering_from_dict(raw: dict[str, Any]) -> ClusteringConfig:
    geo_raw = cfg_dict(raw, "geo")
    scene_raw = cfg_dict(raw, "scene")
    segment_mode = cfg_str(raw, "segment_curate_mode", "segmentCurateMode", "event_first")
    if segment_mode not in ("event_first", "date_fallback"):
        segment_mode = "event_first"
    scene_mode = cfg_str(raw, "scene_cluster_mode", "sceneClusterMode", "run_aware")
    if scene_mode not in ("run_aware", "off"):
        scene_mode = "run_aware"
    return ClusteringConfig(
        enabled=normalize_tri_state(raw.get("enabled"), default="auto"),
        auto_gps_min_ratio=cfg_float(raw, "auto_gps_min_ratio", "autoGpsMinRatio", 0.40),
        segment_curate_mode=segment_mode,
        scene_cluster_mode=scene_mode,
        deterministic=bool(raw.get("deterministic", True)),
        deterministic_strict=cfg_bool(raw, "deterministic_strict", "deterministicStrict", False),
        force_recluster=cfg_bool(raw, "force_recluster", "forceRecluster", False),
        cache_abi_version=cfg_str(raw, "cache_abi_version", "cacheAbiVersion", "v1"),
        cache_config_fingerprint=cfg_str(raw, "cache_config_fingerprint", "cacheConfigFingerprint", "auto"),
        geo=geo_cluster_from_dict(geo_raw),
        scene=scene_cluster_from_dict(scene_raw),
        enable_scene_sub_segments=cfg_bool(raw, "enable_scene_sub_segments", "enableSceneSubSegments", True),
        scene_subsegment_min_photos=cfg_int(
            raw, "scene_subsegment_min_photos", "sceneSubsegmentMinPhotos", 3
        ),
    )
