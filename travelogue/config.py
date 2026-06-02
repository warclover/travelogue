"""Load config.yaml (see config.yaml.example)."""

from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Literal

from travelogue.constants import VALID_ARC_MODES, VALID_NARRATIVE_SCOPES
from travelogue.config_helpers import cfg_bool, cfg_dict, cfg_float, cfg_get, cfg_int, cfg_str
from travelogue.paths import ROOT

TriState = Literal["true", "false", "auto"]


def _default_trips_dir() -> Path:
    try:
        from travelogue.desktop.bundle import default_trips_dir

        return default_trips_dir()
    except Exception:
        return ROOT / "trips"

_log = logging.getLogger(__name__)

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

from travelogue.llm.presets import PROVIDER_PRESETS


DEFAULT_RAW_BLOCKLIST_SUFFIXES: tuple[str, ...] = (
    ".cr2",
    ".cr3",
    ".nef",
    ".nrw",
    ".arw",
    ".srf",
    ".sr2",
    ".dng",
    ".rw2",
    ".orf",
    ".raf",
    ".pef",
    ".x3f",
    ".kdc",
    ".erf",
    ".3fr",
    ".iiq",
)


@dataclass
class IngestConfig:
    max_photos: int = 250
    webp_widths: tuple[int, ...] = (800, 1600, 2400, 3200)
    webp_quality: int = 82
    webp_method: int = 4
    shared_color_thumb_px: int = 32
    generate_crops: bool = False
    min_edge_px: int = 320
    phash_threshold: int = 8
    burst_seconds: float = 3.0
    dedupe_phash: bool = True
    dedupe_burst: bool = True
    min_long_edge_layout_px: int = 800
    min_short_edge_layout_px: int = 600
    low_res_median_ratio: float = 0.55
    low_res_peak_ratio: float = 0.42  # deprecated · unused; kept for config compat
    low_res_min_megapixels: float = 0.8
    low_res_mp_ratio: float = 0.45
    low_res_circuit_breaker_ratio: float = 0.25
    low_res_circuit_breaker_median_short_px: int = 1200
    detect_faces: bool = True
    face_min_size_px: int = 48
    featured_dir_names: tuple[str, ...] = ("主图上传", "精选", "featured", "hero")
    material_dir_names: tuple[str, ...] = ("素材上传", "素材", "material", "extras")
    featured_priority_on_truncation: bool = True
    warn_featured_count_above: int = 30
    reject_raw: bool = True
    raw_blocklist_suffixes: tuple[str, ...] = DEFAULT_RAW_BLOCKLIST_SUFFIXES
    raw_detect_sample_limit: int = 5


@dataclass
class CullConfig:
    enabled: bool = True
    mode: str = "rules"
    keep_ratio_floor: float = 0.80
    min_keep: int = 15
    featured_exempt: bool = True
    featured_hard_exclude: bool = False
    featured_exempt_low_res: bool = True
    max_photos_warn_only: bool = True
    sharpness_absolute_min: float = 0.0
    blur_percentile: float = 2.0
    hard_exclude_media_classes: tuple[str, ...] = ("screenshot", "thumbnail", "reupload")
    aesthetic_metric: str = "topiq_nr"
    portrait_face_aesthetic: bool = True
    allow_cpu_ml: bool = False
    ml_device: str = "auto"


@dataclass
class CurateConfig:
    segment_gap_days: int = 14
    city_gap_days: int = 3
    min_bucket_size: int = 3
    arc_mode: str = "legacy"  # legacy | v2_adaptive | v2_five_beat (alias)
    arc_flat_variance_threshold: float = 0.08
    featured_weight: float = 1.35
    featured_min_for_cover_pool: int = 2
    enable_gravity_balance: bool = True
    enable_mmr_diversity: bool = True
    max_consecutive_same_pattern: int = 2
    longshot_mmr_lambda: float = 0.72
    enable_arc_breath: bool = True


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


@dataclass
class VisionConfig:
    enabled: TriState = "false"
    auto_min_photos: int = 80
    auto_min_eligible_ratio: float = 0.60
    provider: str = "none"
    model: str = "ViT-B/32"
    max_tags_per_asset: int = 5
    subject_prompts: tuple[str, ...] = ()
    batch_size: int = 16
    session_singleton: bool = True
    prefer_web_derivative: bool = True
    preload_on_folder_pick: bool = True
    batch_auto_tune: bool = True
    batch_auto_tune_samples: int = 8
    dynamic_backoff: bool = True
    prefetch: bool = True
    web_derivative_cosine_max: float = 0.02


@dataclass
class ExportConfig:
    max_zip_mb: int = 25


@dataclass
class RenderReadingConfig:
    default_profile: str = "default_hybrid"
    share_profile: str = "performance"
    mobile_profile: str = "legacy"
    longshot_surface_profile: str = "performance"


@dataclass
class RenderConfig:
    reading: RenderReadingConfig = field(default_factory=RenderReadingConfig)


@dataclass
class NarrativeConfig:
    tone_default: str = "relaxed"
    max_auto_fix_retries: int = 2
    banned_phrases: tuple[str, ...] = ()
    # frame: hook+epilogue only | frame_chapters: +首末章 lead | full: +全章 lead + 图注
    scope: str = "frame"


@dataclass
class LlmConfig:
    provider: str = "stub"  # stub | deepseek | dashscope
    model: str = "deepseek-chat"
    api_key_env: str = "DEEPSEEK_API_KEY"
    base_url: str | None = None
    timeout_sec: int = 120


@dataclass
class PipelineConfig:
    parallel_embed: bool = False
    parallel_embed_chunk: int = 32


@dataclass
class LayoutScoringConfig:
    """V2 layout search (ADR-002); disabled by default = legacy behavior."""
    enabled: bool = False
    beam_width: int = 3
    max_screens_per_chapter: int = 12
    min_layout_eligible: int = 3
    min_aspect_kinds: int = 1
    search_timeout_ms: int = 2000
    max_candidates_per_bucket: int = 12
    max_evaluations_per_trip: int = 500
    allow_burst_split: bool = False
    subject_run_tolerance: int = 1
    skip_duplicate_signatures: bool = True
    incremental: bool = False
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "aspect_match": 0.0,
            "sharpness": 0.0,
            "hero_separation": 0.0,
            "temporal_coherence": 0.0,
            "diversity": 0.0,
            "arc_fit": 0.0,
            "burst_integrity": 0.0,
            "luminance_continuity": 0.0,
            "subject_run": 0.0,
            "tone_continuity": 0.0,
            "layout_rhythm": 0.0,
            "gravity_balance": 0.0,
        }
    )


@dataclass
class LayoutFeedbackConfig:
    enabled: bool = False
    log_path: str | None = None


@dataclass
class LayoutConfig:
    """Web layout engine default when exportLayout is web (see docs/web端模板升级计划.md)."""
    web_layout_engine: str = "screens"  # legacy | screens
    screen_plan_scope: str = "day"  # chapter | day — day = 按策展日桶全序列组屏
    mixed_proximity_seconds: float = 12.0  # 1竖+2横混排 takenAt 跨度上限
    scoring: LayoutScoringConfig = field(default_factory=LayoutScoringConfig)
    feedback: LayoutFeedbackConfig = field(default_factory=LayoutFeedbackConfig)


@dataclass
class StudioConfig:
    """Studio workbench (Phase 4 M17 · G1)."""

    g1_confirm_structure: bool = False


@dataclass
class Phase6AcThresholds:
    """AC-P6 acceptance gates (Phase 6 §18)."""

    cluster_noise_ratio_drop_pct: float = 15.0
    event_boundary_f1_lift_pct: float = 10.0
    layout_repeat_streak_drop_pct: float = 25.0
    pipeline_time_regression_pct: float = 10.0
    peak_memory_regression_pct: float = 15.0
    cover_blind_review_winrate_pct: float = 60.0


@dataclass
class Phase6AlertThresholds:
    """Operational alert thresholds (PRD-PHASE6 §18.2)."""

    export_success_rate_min: float = 0.97
    pipeline_time_regression_alert_pct: float = 15.0
    cover_preference_winrate_min: float = 0.50


@dataclass
class Phase6RolloutConfig:
    """Gray rollout gate (PRD-PHASE6 §14). Buckets by tripId + cohortSalt."""

    stage: Literal["off", "G0", "G1", "G2", "G3"] = "off"
    traffic_percent: float = 0.0
    cohort_salt: str = "travelogue-p6"
    allowlist_trip_ids: tuple[str, ...] = ()
    blocklist_trip_ids: tuple[str, ...] = ()


@dataclass
class Phase6ObservabilityConfig:
    ac: Phase6AcThresholds = field(default_factory=Phase6AcThresholds)
    alerts: Phase6AlertThresholds = field(default_factory=Phase6AlertThresholds)
    rollout: Phase6RolloutConfig = field(default_factory=Phase6RolloutConfig)


@dataclass
class AppConfig:
    trips_dir: Path = field(default_factory=_default_trips_dir)
    ingest: IngestConfig = field(default_factory=IngestConfig)
    cull: CullConfig = field(default_factory=CullConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    clustering: ClusteringConfig = field(default_factory=ClusteringConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    geocode: GeocodeConfig = field(default_factory=GeocodeConfig)
    curate: CurateConfig = field(default_factory=CurateConfig)
    studio: StudioConfig = field(default_factory=StudioConfig)
    config_path: Path | None = None
    export: ExportConfig = field(default_factory=ExportConfig)
    render: RenderConfig = field(default_factory=RenderConfig)
    narrative: NarrativeConfig = field(default_factory=NarrativeConfig)
    llm: LlmConfig = field(default_factory=LlmConfig)
    phase6: Phase6ObservabilityConfig = field(default_factory=Phase6ObservabilityConfig)


def _phase6_ac_from_dict(raw: dict[str, Any]) -> Phase6AcThresholds:
    defaults = Phase6AcThresholds()
    return Phase6AcThresholds(
        cluster_noise_ratio_drop_pct=float(
            raw.get("clusterNoiseRatioDropPct", raw.get("cluster_noise_ratio_drop_pct", defaults.cluster_noise_ratio_drop_pct))
        ),
        event_boundary_f1_lift_pct=float(
            raw.get("eventBoundaryF1LiftPct", raw.get("event_boundary_f1_lift_pct", defaults.event_boundary_f1_lift_pct))
        ),
        layout_repeat_streak_drop_pct=float(
            raw.get("layoutRepeatStreakDropPct", raw.get("layout_repeat_streak_drop_pct", defaults.layout_repeat_streak_drop_pct))
        ),
        pipeline_time_regression_pct=float(
            raw.get("pipelineTimeRegressionPct", raw.get("pipeline_time_regression_pct", defaults.pipeline_time_regression_pct))
        ),
        peak_memory_regression_pct=float(
            raw.get("peakMemoryRegressionPct", raw.get("peak_memory_regression_pct", defaults.peak_memory_regression_pct))
        ),
        cover_blind_review_winrate_pct=float(
            raw.get("coverBlindReviewWinratePct", raw.get("cover_blind_review_winrate_pct", defaults.cover_blind_review_winrate_pct))
        ),
    )


def _phase6_alerts_from_dict(raw: dict[str, Any]) -> Phase6AlertThresholds:
    defaults = Phase6AlertThresholds()
    return Phase6AlertThresholds(
        export_success_rate_min=float(
            raw.get("exportSuccessRateMin", raw.get("export_success_rate_min", defaults.export_success_rate_min))
        ),
        pipeline_time_regression_alert_pct=float(
            raw.get(
                "pipelineTimeRegressionAlertPct",
                raw.get("pipeline_time_regression_alert_pct", defaults.pipeline_time_regression_alert_pct),
            )
        ),
        cover_preference_winrate_min=float(
            raw.get("coverPreferenceWinrateMin", raw.get("cover_preference_winrate_min", defaults.cover_preference_winrate_min))
        ),
    )


def _phase6_from_dict(raw: dict[str, Any]) -> Phase6ObservabilityConfig:
    ac_raw = raw.get("ac") if isinstance(raw.get("ac"), dict) else {}
    alerts_raw = raw.get("alerts") if isinstance(raw.get("alerts"), dict) else {}
    rollout_raw = raw.get("rollout") if isinstance(raw.get("rollout"), dict) else {}
    stage_raw = str(rollout_raw.get("stage", "off")).strip().upper()
    if stage_raw == "OFF" or stage_raw not in ("G0", "G1", "G2", "G3"):
        stage_key: Literal["off", "G0", "G1", "G2", "G3"] = "off"
    else:
        stage_key = stage_raw  # type: ignore[assignment]
    allow_raw = rollout_raw.get("allowlistTripIds") or rollout_raw.get("allowlist_trip_ids") or []
    block_raw = rollout_raw.get("blocklistTripIds") or rollout_raw.get("blocklist_trip_ids") or []
    rollout = Phase6RolloutConfig(
        stage=stage_key,
        traffic_percent=float(
            rollout_raw.get("trafficPercent", rollout_raw.get("traffic_percent", 0.0))
        ),
        cohort_salt=str(rollout_raw.get("cohortSalt", rollout_raw.get("cohort_salt", "travelogue-p6"))),
        allowlist_trip_ids=tuple(str(x) for x in allow_raw if x) if isinstance(allow_raw, list) else (),
        blocklist_trip_ids=tuple(str(x) for x in block_raw if x) if isinstance(block_raw, list) else (),
    )
    return Phase6ObservabilityConfig(
        ac=_phase6_ac_from_dict(ac_raw),
        alerts=_phase6_alerts_from_dict(alerts_raw),
        rollout=rollout,
    )


def _ingest_from_dict(raw: dict[str, Any]) -> IngestConfig:
    widths = raw.get("webp_widths") or [800, 1600, 2400, 3200]
    raw_suffixes = raw.get("raw_blocklist_suffixes") or raw.get("rawBlocklistSuffixes")
    if isinstance(raw_suffixes, list) and raw_suffixes:
        suffixes = tuple(str(s).lower() if str(s).startswith(".") else f".{str(s).lower()}" for s in raw_suffixes)
    else:
        suffixes = DEFAULT_RAW_BLOCKLIST_SUFFIXES
    return IngestConfig(
        max_photos=int(raw.get("max_photos", 250)),
        webp_widths=tuple(int(w) for w in widths),
        webp_quality=int(raw.get("webp_quality", 82)),
        webp_method=int(raw.get("webp_method", 4)),
        shared_color_thumb_px=int(raw.get("shared_color_thumb_px", raw.get("sharedColorThumbPx", 32))),
        generate_crops=bool(raw.get("generate_crops", False)),
        min_edge_px=int(raw.get("min_edge_px", 320)),
        phash_threshold=int(raw.get("phash_threshold", 8)),
        burst_seconds=float(raw.get("burst_seconds", 3.0)),
        dedupe_phash=bool(raw.get("dedupe_phash", True)),
        dedupe_burst=bool(raw.get("dedupe_burst", True)),
        min_long_edge_layout_px=int(raw.get("min_long_edge_layout_px", 800)),
        min_short_edge_layout_px=int(raw.get("min_short_edge_layout_px", 600)),
        low_res_median_ratio=float(raw.get("low_res_median_ratio", 0.55)),
        low_res_peak_ratio=float(raw.get("low_res_peak_ratio", 0.42)),
        low_res_min_megapixels=float(raw.get("low_res_min_megapixels", 0.8)),
        low_res_mp_ratio=float(raw.get("low_res_mp_ratio", 0.45)),
        low_res_circuit_breaker_ratio=float(raw.get("low_res_circuit_breaker_ratio", 0.25)),
        low_res_circuit_breaker_median_short_px=int(
            raw.get("low_res_circuit_breaker_median_short_px", 1200)
        ),
        detect_faces=bool(raw.get("detect_faces", True)),
        face_min_size_px=int(raw.get("face_min_size_px", 48)),
        featured_dir_names=tuple(str(x) for x in (raw.get("featured_dir_names") or ["主图上传", "精选", "featured", "hero"])),
        material_dir_names=tuple(str(x) for x in (raw.get("material_dir_names") or ["素材上传", "素材", "material", "extras"])),
        featured_priority_on_truncation=bool(raw.get("featured_priority_on_truncation", True)),
        warn_featured_count_above=int(raw.get("warn_featured_count_above", 30)),
        reject_raw=bool(raw.get("reject_raw", raw.get("rejectRaw", True))),
        raw_blocklist_suffixes=suffixes,
        raw_detect_sample_limit=int(raw.get("raw_detect_sample_limit", raw.get("rawDetectSampleLimit", 5))),
    )


def _cull_from_dict(raw: dict[str, Any]) -> CullConfig:
    ml_raw = raw.get("ml") if isinstance(raw.get("ml"), dict) else {}
    hard_raw = raw.get("hard_exclude_media_classes") or raw.get("hardExcludeMediaClasses") or [
        "screenshot",
        "thumbnail",
        "reupload",
    ]
    return CullConfig(
        enabled=bool(raw.get("enabled", True)),
        mode=str(raw.get("mode", "rules")),
        keep_ratio_floor=float(raw.get("keep_ratio_floor", raw.get("keepRatioFloor", 0.80))),
        min_keep=int(raw.get("min_keep", raw.get("minKeep", 15))),
        featured_exempt=bool(raw.get("featured_exempt", raw.get("featuredExempt", True))),
        featured_hard_exclude=bool(raw.get("featured_hard_exclude", raw.get("featuredHardExclude", False))),
        featured_exempt_low_res=bool(
            raw.get("featured_exempt_low_res", raw.get("featuredExemptLowRes", True))
        ),
        max_photos_warn_only=bool(raw.get("max_photos_warn_only", raw.get("maxPhotosWarnOnly", True))),
        sharpness_absolute_min=float(raw.get("sharpness_absolute_min", raw.get("sharpnessAbsoluteMin", 0.0))),
        blur_percentile=float(raw.get("blur_percentile", raw.get("blurPercentile", 2.0))),
        hard_exclude_media_classes=tuple(str(x) for x in hard_raw if x),
        aesthetic_metric=str(ml_raw.get("aesthetic_metric", ml_raw.get("aestheticMetric", "topiq_nr"))),
        portrait_face_aesthetic=bool(
            ml_raw.get("portrait_face_aesthetic", ml_raw.get("portraitFaceAesthetic", True))
        ),
        allow_cpu_ml=bool(ml_raw.get("allow_cpu_ml", ml_raw.get("allowCpuMl", False))),
        ml_device=str(ml_raw.get("device", "auto")),
    )


def _layout_scoring_from_dict(raw: dict[str, Any]) -> LayoutScoringConfig:
    weights_raw = raw.get("weights") if isinstance(raw.get("weights"), dict) else {}
    default_weights = LayoutScoringConfig().weights
    weights = {k: float(weights_raw.get(k, default_weights.get(k, 0.0))) for k in default_weights}
    return LayoutScoringConfig(
        enabled=bool(raw.get("enabled", False)),
        beam_width=int(raw.get("beam_width", 3)),
        max_screens_per_chapter=int(raw.get("max_screens_per_chapter", 12)),
        min_layout_eligible=int(raw.get("min_layout_eligible", 3)),
        min_aspect_kinds=int(raw.get("min_aspect_kinds", 1)),
        search_timeout_ms=int(raw.get("search_timeout_ms", 2000)),
        max_candidates_per_bucket=int(raw.get("max_candidates_per_bucket", 12)),
        max_evaluations_per_trip=int(raw.get("max_evaluations_per_trip", 500)),
        allow_burst_split=bool(raw.get("allow_burst_split", False)),
        subject_run_tolerance=int(raw.get("subject_run_tolerance", 1)),
        skip_duplicate_signatures=cfg_bool(
            raw, "skip_duplicate_signatures", "skipDuplicateSignatures", True
        ),
        incremental=bool(raw.get("incremental", False)),
        weights=weights,
    )


def _render_reading_from_dict(raw: dict[str, Any]) -> RenderReadingConfig:
    return RenderReadingConfig(
        default_profile=str(raw.get("default_profile", "default_hybrid")),
        share_profile=str(raw.get("share_profile", "performance")),
        mobile_profile=str(raw.get("mobile_profile", "legacy")),
        longshot_surface_profile=str(raw.get("longshot_surface_profile", "performance")),
    )


def _render_from_dict(raw: dict[str, Any]) -> RenderConfig:
    reading_raw = raw.get("reading") if isinstance(raw.get("reading"), dict) else {}
    return RenderConfig(reading=_render_reading_from_dict(reading_raw))


def _layout_feedback_from_dict(raw: dict[str, Any]) -> LayoutFeedbackConfig:
    log_path = raw.get("log_path")
    return LayoutFeedbackConfig(
        enabled=bool(raw.get("enabled", False)),
        log_path=str(log_path).strip() if log_path else None,
    )


def _normalize_arc_mode(raw: object) -> str:
    val = str(raw or "legacy").strip().lower()
    if val not in VALID_ARC_MODES:
        _log.warning("invalid curate.arc_mode %r, using legacy", raw)
        return "legacy"
    return val


def _normalize_narrative_scope(raw: object) -> str:
    val = str(raw or "frame").strip().lower()
    if val not in VALID_NARRATIVE_SCOPES:
        _log.warning("invalid narrative.scope %r, using frame", raw)
        return "frame"
    return val


def _normalize_tri_state(raw: object, *, default: str = "auto") -> str:
    if isinstance(raw, bool):
        return "true" if raw else "false"
    val = str(raw or default).strip().lower()
    if val in ("true", "1", "on", "yes"):
        return "true"
    if val in ("false", "0", "off", "no"):
        return "false"
    if val == "auto":
        return "auto"
    _log.warning("invalid tri-state %r, using %s", raw, default)
    return default


def _geo_cluster_from_dict(raw: dict[str, Any]) -> GeoClusterConfig:
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


def _scene_cluster_from_dict(raw: dict[str, Any]) -> SceneClusterConfig:
    algo = str(raw.get("algorithm", "hdbscan")).lower()
    if algo not in ("hdbscan", "dbscan"):
        algo = "hdbscan"
    return SceneClusterConfig(
        algorithm=algo,  # type: ignore[arg-type]
        cluster_eps=cfg_float(raw, "cluster_eps", "clusterEps", 0.07),
        cluster_min_samples=cfg_int(raw, "cluster_min_samples", "clusterMinSamples", 10),
        timeout_sec=cfg_int(raw, "timeout_sec", "timeoutSec", 480),
    )


def _clustering_from_dict(raw: dict[str, Any]) -> ClusteringConfig:
    geo_raw = cfg_dict(raw, "geo")
    scene_raw = cfg_dict(raw, "scene")
    segment_mode = cfg_str(raw, "segment_curate_mode", "segmentCurateMode", "event_first")
    if segment_mode not in ("event_first", "date_fallback"):
        segment_mode = "event_first"
    scene_mode = cfg_str(raw, "scene_cluster_mode", "sceneClusterMode", "run_aware")
    if scene_mode not in ("run_aware", "off"):
        scene_mode = "run_aware"
    return ClusteringConfig(
        enabled=_normalize_tri_state(raw.get("enabled"), default="auto"),
        auto_gps_min_ratio=cfg_float(raw, "auto_gps_min_ratio", "autoGpsMinRatio", 0.40),
        segment_curate_mode=segment_mode,
        scene_cluster_mode=scene_mode,
        deterministic=bool(raw.get("deterministic", True)),
        deterministic_strict=cfg_bool(raw, "deterministic_strict", "deterministicStrict", False),
        force_recluster=cfg_bool(raw, "force_recluster", "forceRecluster", False),
        cache_abi_version=cfg_str(raw, "cache_abi_version", "cacheAbiVersion", "v1"),
        cache_config_fingerprint=cfg_str(raw, "cache_config_fingerprint", "cacheConfigFingerprint", "auto"),
        geo=_geo_cluster_from_dict(geo_raw),
        scene=_scene_cluster_from_dict(scene_raw),
        enable_scene_sub_segments=cfg_bool(raw, "enable_scene_sub_segments", "enableSceneSubSegments", True),
        scene_subsegment_min_photos=cfg_int(
            raw, "scene_subsegment_min_photos", "sceneSubsegmentMinPhotos", 3
        ),
    )


def _vision_from_dict(raw: dict[str, Any]) -> VisionConfig:
    enabled_raw = raw.get("enabled", False)
    if isinstance(enabled_raw, bool):
        enabled = "true" if enabled_raw else "false"
    else:
        enabled = _normalize_tri_state(enabled_raw, default="false")
    prompts_raw = cfg_get(raw, "subject_prompts", "subjectPrompts", ())
    prompts = tuple(str(p).strip() for p in prompts_raw if str(p).strip()) if isinstance(prompts_raw, list) else ()
    return VisionConfig(
        enabled=enabled,
        auto_min_photos=cfg_int(raw, "auto_min_photos", "autoMinPhotos", 80),
        auto_min_eligible_ratio=cfg_float(raw, "auto_min_eligible_ratio", "autoMinEligibleRatio", 0.60),
        provider=str(raw.get("provider", "none")),
        model=str(raw.get("model", "ViT-B/32")),
        max_tags_per_asset=int(raw.get("max_tags_per_asset", 5)),
        subject_prompts=prompts,
        batch_size=cfg_int(raw, "batch_size", "batchSize", 16),
        session_singleton=cfg_bool(raw, "session_singleton", "sessionSingleton", True),
        prefer_web_derivative=cfg_bool(raw, "prefer_web_derivative", "preferWebDerivative", True),
        preload_on_folder_pick=cfg_bool(raw, "preload_on_folder_pick", "preloadOnFolderPick", True),
        batch_auto_tune=cfg_bool(raw, "batch_auto_tune", "batchAutoTune", True),
        batch_auto_tune_samples=cfg_int(raw, "batch_auto_tune_samples", "batchAutoTuneSamples", 8),
        dynamic_backoff=cfg_bool(raw, "dynamic_backoff", "dynamicBackoff", True),
        prefetch=bool(raw.get("prefetch", True)),
        web_derivative_cosine_max=cfg_float(
            raw, "web_derivative_cosine_max", "webDerivativeCosineMax", 0.02
        ),
    )


def _pipeline_from_dict(raw: dict[str, Any]) -> PipelineConfig:
    return PipelineConfig(
        parallel_embed=cfg_bool(raw, "parallel_embed", "parallelEmbed", False),
        parallel_embed_chunk=cfg_int(raw, "parallel_embed_chunk", "parallelEmbedChunk", 32),
    )


def studio_config_expose(cfg: AppConfig) -> dict[str, Any]:
    """Subset of config safe for Studio GET /__travelogue/config."""
    return {
        "clustering": {
            "enabled": cfg.clustering.enabled,
            "segmentCurateMode": cfg.clustering.segment_curate_mode,
            "sceneClusterMode": cfg.clustering.scene_cluster_mode,
        },
        "vision": {
            "enabled": cfg.vision.enabled,
        },
        "layout": {
            "scoring": {
                "enabled": cfg.layout.scoring.enabled,
            },
        },
        "studio": {
            "g1ConfirmStructure": cfg.studio.g1_confirm_structure,
        },
    }


def patch_config_file(path: Path, patch: dict[str, Any]) -> None:
    """Merge whitelisted keys into config.yaml on disk."""
    if yaml is None:
        raise RuntimeError("PyYAML required to patch config")
    data: dict[str, Any] = {}
    if path.is_file():
        with path.open(encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
            if isinstance(loaded, dict):
                data = loaded
    allowed_clustering = {"enabled", "segmentCurateMode", "sceneClusterMode"}
    allowed_vision = {"enabled"}
    allowed_layout_scoring = {"enabled"}
    allowed_studio = {"g1ConfirmStructure", "g1_confirm_structure"}
    clu_patch = patch.get("clustering") if isinstance(patch.get("clustering"), dict) else {}
    vis_patch = patch.get("vision") if isinstance(patch.get("vision"), dict) else {}
    layout_patch = patch.get("layout") if isinstance(patch.get("layout"), dict) else {}
    studio_patch = patch.get("studio") if isinstance(patch.get("studio"), dict) else {}
    if clu_patch:
        target = data.setdefault("clustering", {})
        if not isinstance(target, dict):
            target = {}
            data["clustering"] = target
        for key, val in clu_patch.items():
            if key in allowed_clustering:
                target[key] = val
    if vis_patch:
        target = data.setdefault("vision", {})
        if not isinstance(target, dict):
            target = {}
            data["vision"] = target
        for key, val in vis_patch.items():
            if key in allowed_vision:
                target[key] = val
    scoring_patch = (
        layout_patch.get("scoring") if isinstance(layout_patch.get("scoring"), dict) else {}
    )
    if scoring_patch:
        layout_target = data.setdefault("layout", {})
        if not isinstance(layout_target, dict):
            layout_target = {}
            data["layout"] = layout_target
        scoring_target = layout_target.setdefault("scoring", {})
        if not isinstance(scoring_target, dict):
            scoring_target = {}
            layout_target["scoring"] = scoring_target
        for key, val in scoring_patch.items():
            if key in allowed_layout_scoring:
                scoring_target[key] = val
    if studio_patch:
        target = data.setdefault("studio", {})
        if not isinstance(target, dict):
            target = {}
            data["studio"] = target
        for key, val in studio_patch.items():
            if key in allowed_studio:
                norm_key = "g1_confirm_structure" if key == "g1ConfirmStructure" else key
                target[norm_key] = val
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def load_config(path: Path | None = None) -> AppConfig:
    """Load config.yaml from path, or ./config.yaml, or defaults."""
    candidates = [path, Path.cwd() / "config.yaml", ROOT / "config.yaml"]
    cfg_path = next((p for p in candidates if p and p.is_file()), None)
    data: dict[str, Any] = {}
    if cfg_path and yaml is not None:
        with cfg_path.open(encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
            if isinstance(loaded, dict):
                data = loaded
    trips = data.get("trips_dir", "./trips")
    trips_dir = Path(trips)
    if not trips_dir.is_absolute():
        base = Path.cwd()
        try:
            from travelogue.desktop.bundle import exe_dir, is_frozen

            if is_frozen():
                base = exe_dir()
        except Exception:
            _log.debug("frozen exe_dir lookup failed; using cwd for trips_dir", exc_info=True)
        trips_dir = (base / trips_dir).resolve()
    ingest_raw = data.get("ingest") if isinstance(data.get("ingest"), dict) else {}
    layout_raw = data.get("layout") if isinstance(data.get("layout"), dict) else {}
    web_engine = str(layout_raw.get("web_layout_engine", "screens")).strip().lower()
    if web_engine not in ("legacy", "screens"):
        web_engine = "screens"
    scope = str(layout_raw.get("screen_plan_scope", "day")).strip().lower()
    if scope not in ("chapter", "day"):
        scope = "day"
    mixed_gap = float(layout_raw.get("mixed_proximity_seconds", 12.0))
    scoring_raw = layout_raw.get("scoring") if isinstance(layout_raw.get("scoring"), dict) else {}
    feedback_raw = layout_raw.get("feedback") if isinstance(layout_raw.get("feedback"), dict) else {}
    export_raw = data.get("export") if isinstance(data.get("export"), dict) else {}
    vision_raw = data.get("vision") if isinstance(data.get("vision"), dict) else {}
    narrative_raw = data.get("narrative") if isinstance(data.get("narrative"), dict) else {}
    llm_raw = data.get("llm") if isinstance(data.get("llm"), dict) else {}
    geocode_raw = data.get("geocode") if isinstance(data.get("geocode"), dict) else {}
    curate_raw = data.get("curate") if isinstance(data.get("curate"), dict) else {}
    curate_layout_raw = curate_raw.get("layout") if isinstance(curate_raw.get("layout"), dict) else {}
    render_raw = data.get("render") if isinstance(data.get("render"), dict) else {}
    clustering_raw = data.get("clustering") if isinstance(data.get("clustering"), dict) else {}
    pipeline_raw = data.get("pipeline") if isinstance(data.get("pipeline"), dict) else {}
    cull_raw = data.get("cull") if isinstance(data.get("cull"), dict) else {}
    studio_raw = data.get("studio") if isinstance(data.get("studio"), dict) else {}
    phase6_raw = data.get("phase6") if isinstance(data.get("phase6"), dict) else {}
    banned_raw = narrative_raw.get("banned_phrases") or []
    banned = tuple(str(p) for p in banned_raw if p) if isinstance(banned_raw, list) else ()
    llm_provider = str(llm_raw.get("provider", "stub")).strip().lower()
    if llm_provider not in ("stub", "deepseek", "dashscope"):
        llm_provider = "stub"
    llm_preset = PROVIDER_PRESETS.get(llm_provider, {})
    llm_base = llm_raw.get("base_url")
    llm_base_url = str(llm_base).strip() if llm_base else None
    return AppConfig(
        trips_dir=trips_dir,
        ingest=_ingest_from_dict(ingest_raw),
        cull=_cull_from_dict(cull_raw),
        pipeline=_pipeline_from_dict(pipeline_raw),
        export=ExportConfig(max_zip_mb=int(export_raw.get("max_zip_mb", 25))),
        render=_render_from_dict(render_raw),
        layout=LayoutConfig(
            web_layout_engine=web_engine,
            screen_plan_scope=scope,
            mixed_proximity_seconds=mixed_gap,
            scoring=_layout_scoring_from_dict(scoring_raw),
            feedback=_layout_feedback_from_dict(feedback_raw),
        ),
        clustering=_clustering_from_dict(clustering_raw),
        vision=_vision_from_dict(vision_raw),
        geocode=GeocodeConfig(enabled=bool(geocode_raw.get("enabled", False))),
        config_path=cfg_path,
        curate=CurateConfig(
            segment_gap_days=int(curate_raw.get("segment_gap_days", 14)),
            city_gap_days=int(curate_raw.get("city_gap_days", 3)),
            min_bucket_size=int(curate_raw.get("min_bucket_size", 3)),
            arc_mode=_normalize_arc_mode(curate_raw.get("arc_mode", "legacy")),
            arc_flat_variance_threshold=float(
                curate_raw.get("arc_flat_variance_threshold", 0.08)
            ),
            featured_weight=float(curate_raw.get("featured_weight", 1.35)),
            featured_min_for_cover_pool=int(curate_raw.get("featured_min_for_cover_pool", 2)),
            enable_gravity_balance=bool(
                curate_layout_raw.get(
                    "enable_gravity_balance",
                    curate_raw.get("enable_gravity_balance", True),
                )
            ),
            enable_mmr_diversity=bool(
                curate_layout_raw.get(
                    "enable_mmr_diversity",
                    curate_raw.get("enable_mmr_diversity", True),
                )
            ),
            max_consecutive_same_pattern=int(
                curate_layout_raw.get(
                    "max_consecutive_same_pattern",
                    curate_raw.get("max_consecutive_same_pattern", 2),
                )
            ),
            longshot_mmr_lambda=float(
                curate_layout_raw.get(
                    "longshot_mmr_lambda",
                    curate_raw.get("longshot_mmr_lambda", 0.72),
                )
            ),
            enable_arc_breath=bool(
                curate_layout_raw.get(
                    "enable_arc_breath",
                    curate_raw.get("enable_arc_breath", True),
                )
            ),
        ),
        narrative=NarrativeConfig(
            tone_default=str(narrative_raw.get("tone_default", "relaxed")),
            max_auto_fix_retries=int(narrative_raw.get("max_auto_fix_retries", 2)),
            banned_phrases=banned,
            scope=_normalize_narrative_scope(narrative_raw.get("scope", "frame")),
        ),
        llm=LlmConfig(
            provider=llm_provider,
            model=str(llm_raw.get("model") or llm_preset.get("default_model", "deepseek-chat")),
            api_key_env=str(llm_raw.get("api_key_env") or llm_preset.get("api_key_env", "DEEPSEEK_API_KEY")),
            base_url=llm_base_url,
            timeout_sec=int(llm_raw.get("timeout_sec", 120)),
        ),
        studio=StudioConfig(
            g1_confirm_structure=bool(
                studio_raw.get("g1_confirm_structure", studio_raw.get("g1ConfirmStructure", False))
            ),
        ),
        phase6=_phase6_from_dict(phase6_raw),
    )


def default_web_layout_engine(export_layout: str, *, cfg: AppConfig | None = None) -> str:
    """Resolve layoutEngine when not set on trip (config + exportLayout)."""
    if export_layout not in ("web", "auto"):
        return "legacy"
    app = cfg or get_config()
    if app.layout.web_layout_engine == "screens":
        return "screens"
    return "legacy"


def default_screen_plan_scope(*, cfg: AppConfig | None = None) -> str:
    return (cfg or get_config()).layout.screen_plan_scope


def default_mixed_proximity_seconds(*, cfg: AppConfig | None = None) -> float:
    return (cfg or get_config()).layout.mixed_proximity_seconds


def reading_profile_defaults(cfg: AppConfig | None = None) -> dict[str, str]:
    """Map AppConfig.render.reading to resolve_reading_payload config_defaults."""
    app = cfg or get_config()
    reading = app.render.reading
    return {
        "draft_web_profile": reading.default_profile,
        "share_zip_profile": reading.share_profile,
        "mobile_profile": reading.mobile_profile,
        "longshot_surface_profile": reading.longshot_surface_profile,
    }


_config_ctx: ContextVar[AppConfig | None] = ContextVar("app_config", default=None)
_cached: AppConfig | None = None
_cache_lock = threading.Lock()


@contextmanager
def config_override(cfg: AppConfig) -> Iterator[AppConfig]:
    """Temporarily use *cfg* for ``get_config()`` in this context (thread/async safe)."""
    token = _config_ctx.set(cfg)
    try:
        yield cfg
    finally:
        _config_ctx.reset(token)


@contextmanager
def app_config_scope(cfg: AppConfig | None = None) -> Iterator[AppConfig]:
    """Pin *cfg* (or current ``get_config()``) for a pipeline stage or HTTP request."""
    active = cfg or get_config()
    with config_override(active):
        yield active


def reset_config_cache() -> None:
    """Clear process-wide lazy cache (tests)."""
    global _cached
    with _cache_lock:
        _cached = None


def get_config(*, reload: bool = False, path: Path | None = None) -> AppConfig:
    override = _config_ctx.get()
    if override is not None:
        return override

    global _cached
    from travelogue.env import load_dotenv_files

    load_dotenv_files()
    with _cache_lock:
        if _cached is None or reload:
            _cached = load_config(path)
        return _cached
