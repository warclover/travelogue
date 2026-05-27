"""Load config.yaml (see config.yaml.example)."""

from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from travelogue.constants import VALID_ARC_MODES, VALID_NARRATIVE_SCOPES
from travelogue.paths import ROOT


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


@dataclass
class IngestConfig:
    max_photos: int = 250
    webp_widths: tuple[int, ...] = (800, 1600, 2400)
    webp_quality: int = 82
    generate_crops: bool = False
    min_edge_px: int = 320
    phash_threshold: int = 8
    burst_seconds: float = 3.0
    dedupe_phash: bool = True
    dedupe_burst: bool = True
    min_long_edge_layout_px: int = 800
    min_short_edge_layout_px: int = 600
    low_res_median_ratio: float = 0.55
    low_res_peak_ratio: float = 0.42
    detect_faces: bool = True
    face_min_size_px: int = 48
    featured_dir_names: tuple[str, ...] = ("主图上传", "精选", "featured", "hero")
    material_dir_names: tuple[str, ...] = ("素材上传", "素材", "material", "extras")
    featured_priority_on_truncation: bool = True
    warn_featured_count_above: int = 30


@dataclass
class CurateConfig:
    segment_gap_days: int = 14
    city_gap_days: int = 3
    min_bucket_size: int = 3
    arc_mode: str = "legacy"  # legacy | v2_adaptive | v2_five_beat (alias)
    arc_flat_variance_threshold: float = 0.08
    featured_weight: float = 1.35
    featured_min_for_cover_pool: int = 2


@dataclass
class GeocodeConfig:
    enabled: bool = False


@dataclass
class VisionConfig:
    enabled: bool = False
    max_tags_per_asset: int = 5


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
class AppConfig:
    trips_dir: Path = field(default_factory=_default_trips_dir)
    ingest: IngestConfig = field(default_factory=IngestConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    geocode: GeocodeConfig = field(default_factory=GeocodeConfig)
    curate: CurateConfig = field(default_factory=CurateConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    render: RenderConfig = field(default_factory=RenderConfig)
    narrative: NarrativeConfig = field(default_factory=NarrativeConfig)
    llm: LlmConfig = field(default_factory=LlmConfig)


def _ingest_from_dict(raw: dict[str, Any]) -> IngestConfig:
    widths = raw.get("webp_widths") or [800, 1600, 2400]
    return IngestConfig(
        max_photos=int(raw.get("max_photos", 250)),
        webp_widths=tuple(int(w) for w in widths),
        webp_quality=int(raw.get("webp_quality", 82)),
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
        detect_faces=bool(raw.get("detect_faces", True)),
        face_min_size_px=int(raw.get("face_min_size_px", 48)),
        featured_dir_names=tuple(str(x) for x in (raw.get("featured_dir_names") or ["主图上传", "精选", "featured", "hero"])),
        material_dir_names=tuple(str(x) for x in (raw.get("material_dir_names") or ["素材上传", "素材", "material", "extras"])),
        featured_priority_on_truncation=bool(raw.get("featured_priority_on_truncation", True)),
        warn_featured_count_above=int(raw.get("warn_featured_count_above", 30)),
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
            pass
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
    render_raw = data.get("render") if isinstance(data.get("render"), dict) else {}
    vision_enabled = bool(vision_raw.get("enabled", False))
    vision_max_tags = int(vision_raw.get("max_tags_per_asset", 5))
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
        export=ExportConfig(max_zip_mb=int(export_raw.get("max_zip_mb", 25))),
        render=_render_from_dict(render_raw),
        layout=LayoutConfig(
            web_layout_engine=web_engine,
            screen_plan_scope=scope,
            mixed_proximity_seconds=mixed_gap,
            scoring=_layout_scoring_from_dict(scoring_raw),
            feedback=_layout_feedback_from_dict(feedback_raw),
        ),
        vision=VisionConfig(enabled=vision_enabled, max_tags_per_asset=vision_max_tags),
        geocode=GeocodeConfig(enabled=bool(geocode_raw.get("enabled", False))),
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
