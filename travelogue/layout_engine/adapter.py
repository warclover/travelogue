"""LSE curate adapter — single entry for chapter screen planning (D-P17-01)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from travelogue.config import AppConfig, MosaicConfig, get_config
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_engine.decision_log import (
    ingest_beam_logs,
    ingest_mosaic_logs,
    strategy_trace_from_pack,
    write_sidecar,
)
from travelogue.layout_engine.registry import StrategyPack, get_strategy_pack
from travelogue.layout_engine.rhythm import layout_state_from_pack
from travelogue.media.image_ops import AspectKind

# Keep out of screen_planner import graph (adapter ↔ attach circular).
DEFAULT_FEATURED_WEIGHT = 1.35


@dataclass
class ChapterPlanRequest:
    """plan_chapter_screens 的入参 DTO（只读请求）。

    注意：与 screen_planner_stages.ChapterPlanContext（规划期可变状态）不同层，
    为避免同名混淆于 2026-06 重命名。
    """

    asset_ids: list[str]
    aspects: dict[str, AspectKind]
    chapter_id: str = "ch"
    assets: dict[str, dict] | None = None
    burst_seconds: float = 3.0
    mixed_proximity_seconds: float | None = None
    orientation_summary: dict | None = None
    skip_screen_asset_ids: set[str] | None = None
    layout_state: ScreenLayoutPlannerState | None = None
    trip_photo_total: int | None = None
    preferred_hero_id: str | None = None
    include_chapter_hero: bool = True
    enable_mosaic: bool = True
    featured_weight: float = DEFAULT_FEATURED_WEIGHT
    enable_portrait_grid8: bool = True
    enable_food_grid: bool = True
    mundane_grid_buckets: tuple[str, ...] = ("food",)
    median_sharp: float | None = None
    late_chapter_active: bool = False
    flush_lookahead_portraits: int = 0
    trip: dict | None = None
    app_config: AppConfig | None = None


def lse_enabled(cfg: AppConfig | None = None) -> bool:
    app = cfg or get_config()
    return bool(app.layout.strategy_engine.enabled)


def resolve_pack(cfg: AppConfig) -> StrategyPack | None:
    if not cfg.layout.strategy_engine.enabled:
        return None
    sid = cfg.layout.strategy_engine.default_strategy_id
    return get_strategy_pack(sid, cfg.layout.strategy_engine.policy_path)


def _planner_module(cfg: AppConfig) -> Any:
    import travelogue.layout_engine.planner.screen_planner as mod

    return mod


def _stage_enabled(pack: StrategyPack | None, stage: str, *, default: bool = True) -> bool:
    if pack is None:
        return default
    stages = (pack.raw.get("planning") or {}).get("stages") or {}
    enabled = stages.get("enabled")
    if not isinstance(enabled, list):
        return default
    return stage in enabled


def mixed_proximity_from_pack(pack: StrategyPack | None, *, cfg: AppConfig) -> float:
    if pack is not None:
        planning = pack.raw.get("planning") or {}
        return float(planning.get("mixed_proximity_seconds", cfg.layout.mixed_proximity_seconds))
    return float(cfg.layout.mixed_proximity_seconds)


def mosaic_config_from_pack(
    cfg: AppConfig,
    pack: StrategyPack | None = None,
) -> MosaicConfig:
    """Inject scoring_profiles.default → MosaicConfig (audit A authority)."""
    active = pack if pack is not None else resolve_pack(cfg)
    base = cfg.mosaic
    if active is None:
        return base
    profile = (active.raw.get("scoring_profiles") or {}).get("default") or {}
    from travelogue.layout_engine.runtime_store import runtime_scoring_overlay

    overlay = runtime_scoring_overlay(cfg)
    from travelogue.layout_engine.capabilities import effective_capabilities

    caps = effective_capabilities(cfg, active)
    search = active.raw.get("search") or {}
    mosaic_stage = (active.raw.get("planning") or {}).get("stages") or {}
    mosaic_stage = mosaic_stage.get("mosaic") if isinstance(mosaic_stage.get("mosaic"), dict) else {}
    self_heal = active.raw.get("self_heal") or {}
    sizes_raw = mosaic_stage.get("enabled_window_sizes") or list(base.enabled_window_sizes)
    sizes = tuple(int(x) for x in sizes_raw)
    weights = dict(base.weights)
    for k, v in (profile.get("weights") or {}).items():
        weights[str(k)] = float(v)
    for k, v in overlay["weights"].items():
        weights[str(k)] = float(v)
    penalties = dict(base.penalties)
    for k, v in (profile.get("penalties") or {}).items():
        penalties[str(k)] = float(v)
    for k, v in overlay["penalties"].items():
        penalties[str(k)] = float(v)
    if caps.saliency_scoring:
        penalties.setdefault("salient_crop", 0.28)
    if caps.tone_harmony:
        weights["tone_continuity"] = max(float(weights.get("tone_continuity") or 0.0), 0.07)
        weights["luminance_continuity"] = max(
            float(weights.get("luminance_continuity") or 0.0), 0.06
        )
    slot_cfg = active.raw.get("slot_assignment") if isinstance(active.raw.get("slot_assignment"), dict) else {}
    max_matrix_n = int(slot_cfg.get("max_matrix_n") or 16)
    hungarian = bool(caps.hungarian_assignment or str(slot_cfg.get("mode") or "") == "hungarian")
    highlight_raw = active.raw.get("highlight_windows") if isinstance(active.raw.get("highlight_windows"), dict) else {}
    highlight_boost = 1.0
    if caps.highlight_windows or bool(highlight_raw.get("enabled", False)):
        highlight_boost = float(highlight_raw.get("boost", 1.25))
    return replace(
        base,
        scorer_version=str(active.algorithm_version),
        min_candidate_score=float(search.get("min_candidate_score", base.min_candidate_score)),
        enabled_window_sizes=sizes or base.enabled_window_sizes,
        weights=weights,
        penalties=penalties,
        self_heal_enabled=bool(self_heal.get("enabled", base.self_heal_enabled)),
        allow_drop=bool(self_heal.get("allow_drop", base.allow_drop)),
        max_drop_ratio=float(self_heal.get("max_drop_ratio", base.max_drop_ratio)),
        self_heal_max_rescore=int(
            self_heal.get("max_rescore", self_heal.get("maxRescore", base.self_heal_max_rescore))
        ),
        self_heal_max_drop_attempts=int(
            self_heal.get(
                "max_drop_attempts",
                self_heal.get("maxDropAttempts", base.self_heal_max_drop_attempts),
            )
        ),
        lse_saliency_scoring=caps.saliency_scoring,
        lse_tone_harmony=caps.tone_harmony,
        lse_beat_profile=str(caps.beat_profile or "flat"),
        lse_hungarian_assignment=hungarian,
        lse_quality_unified=bool(getattr(caps, "quality_unified", False)),
        lse_slot_max_matrix_n=max(1, min(max_matrix_n, 16)),
        lse_highlight_boost=highlight_boost,
    )


def layout_state_for_trip(
    total_photos: int,
    *,
    cfg: AppConfig,
    pack: StrategyPack | None = None,
    density: str | None = None,
) -> ScreenLayoutPlannerState:
    from travelogue.layout_contract.density import LayoutDensityParams
    from travelogue.layout_contract.rhythm import RhythmRules

    active = pack if pack is not None else resolve_pack(cfg)
    if active is not None:
        params = LayoutDensityParams(density=density or "balanced")  # type: ignore[arg-type]
        return _apply_track_dense_cap(
            layout_state_from_pack(total_photos, active, density_params=params)
        )
    return _apply_track_dense_cap(
        ScreenLayoutPlannerState.from_trip_total(
            total_photos,
            density=density or "balanced",  # type: ignore[arg-type]
            rhythm=RhythmRules.from_config(cfg),
        )
    )


def _apply_track_dense_cap(state: ScreenLayoutPlannerState) -> ScreenLayoutPlannerState:
    """LTN C7 · optional track dense cap after P21 / density limits.

    LTN E4 · refresh soft opportunity min after max settles (never raises max).
    """
    from travelogue.layout_contract.asymmetric_quota import dense_opportunity_min_for
    from travelogue.layout_engine.mosaic.runtime import get_effective_mosaic_config

    cfg = get_effective_mosaic_config()
    cap = getattr(cfg, "track_dense_collage_cap", None)
    if cap is not None:
        state.dense_collage_max = min(int(state.dense_collage_max), max(0, int(cap)))
    track_id = getattr(cfg, "track_id", None)
    state.dense_collage_opportunity_min = dense_opportunity_min_for(
        dense_max=state.dense_collage_max,
        track=track_id,
    )
    return state


def resolve_attach_layout_state(
    trip_photo_total: int,
    *,
    cfg: AppConfig | None = None,
    density: str | None = None,
) -> ScreenLayoutPlannerState:
    """Single entry for screen_planner_attach (M-B4a adapter convergence)."""
    from travelogue.layout_contract.rhythm import RhythmRules

    if cfg is None:
        state = ScreenLayoutPlannerState.from_trip_total(
            trip_photo_total,
            density=density or "balanced",  # type: ignore[arg-type]
            rhythm=RhythmRules.from_config(None),
        )
        return _apply_track_dense_cap(state)
    return layout_state_for_trip(trip_photo_total, cfg=cfg, density=density or "balanced")


def plan_chapter_screens(
    ctx: ChapterPlanRequest,
    *,
    cfg: AppConfig | None = None,
    pack: StrategyPack | None = None,
) -> list[dict]:
    """
    Curate-facing entry. When LSE disabled, delegates to legacy plan_screens_for_chapter.
    """
    app = cfg or get_config()
    active_pack = pack if pack is not None else resolve_pack(app)
    mix_gap = ctx.mixed_proximity_seconds
    if mix_gap is None:
        mix_gap = mixed_proximity_from_pack(active_pack, cfg=app)

    from travelogue.layout_engine.runtime_store import effective_disable_stages

    disable_stages = effective_disable_stages(app)
    mosaic_enabled = ctx.enable_mosaic and _stage_enabled(active_pack, "mosaic") and "mosaic" not in disable_stages
    portrait_grid8 = ctx.enable_portrait_grid8 and _stage_enabled(active_pack, "portrait")
    food_grid = ctx.enable_food_grid and _stage_enabled(active_pack, "mixed", default=True)

    layout_state = ctx.layout_state
    if layout_state is None and active_pack is not None and ctx.trip_photo_total:
        layout_state = layout_state_for_trip(ctx.trip_photo_total, cfg=app, pack=active_pack)

    mod = _planner_module(app)
    return mod.plan_screens_for_chapter(
        ctx.asset_ids,
        ctx.aspects,
        chapter_id=ctx.chapter_id,
        assets=ctx.assets,
        burst_seconds=ctx.burst_seconds,
        mixed_proximity_seconds=mix_gap,
        orientation_summary=ctx.orientation_summary,
        skip_screen_asset_ids=ctx.skip_screen_asset_ids,
        layout_state=layout_state,
        trip_photo_total=ctx.trip_photo_total,
        preferred_hero_id=ctx.preferred_hero_id,
        include_chapter_hero=ctx.include_chapter_hero,
        enable_mosaic=mosaic_enabled,
        featured_weight=ctx.featured_weight,
        enable_portrait_grid8=portrait_grid8,
        enable_food_grid=food_grid,
        mundane_grid_buckets=ctx.mundane_grid_buckets,
        median_sharp=ctx.median_sharp,
        late_chapter_active=ctx.late_chapter_active,
        flush_lookahead_portraits=ctx.flush_lookahead_portraits,
        trip=ctx.trip,
        app_config=app,
    )


def strategy_trace_meta(cfg: AppConfig | None = None) -> dict[str, Any]:
    """FR-P17-TRACE summary for trip.curation.layoutStrategy."""
    from travelogue.layout_engine.capabilities import capability_flags_snapshot

    app = cfg or get_config()
    se = app.layout.strategy_engine
    if not se.enabled:
        return {"enabled": False}
    pack = get_strategy_pack(se.default_strategy_id, se.policy_path)
    from travelogue.layout_engine.weights_audit import record_pack_weights_snapshot

    record_pack_weights_snapshot(pack, profile_id="default")
    return {
        "enabled": True,
        "strategyId": pack.id,
        "strategyVersion": pack.version,
        "strategyRevision": 0,
        "weightsHash": pack.weights_hash("default"),
        "algorithmVersion": pack.algorithm_version,
        "contentHash": pack.content_hash,
        "capabilityFlags": capability_flags_snapshot(app, pack),
    }


def persist_layout_observability(
    curation: dict[str, Any],
    *,
    trip_dir: Path | None,
    cfg: AppConfig,
    mosaic_logs: list[dict[str, Any]] | None = None,
    beam_logs: list[dict[str, Any]] | None = None,
) -> None:
    """Sidecar + trip summary (W1-06 / W1-08)."""
    curation["layoutStrategy"] = strategy_trace_meta(cfg)
    if not lse_enabled(cfg):
        return

    events: list[dict[str, Any]] = []
    trace = None
    if lse_enabled(cfg):
        pack = resolve_pack(cfg)
        if pack is not None:
            from travelogue.layout_engine.weights_audit import record_pack_weights_snapshot

            record_pack_weights_snapshot(pack, profile_id="default")
            trace = strategy_trace_from_pack(pack)
    if mosaic_logs:
        events.extend(ingest_mosaic_logs(mosaic_logs, trace=trace))
    if beam_logs:
        events.extend(ingest_beam_logs(beam_logs, trace=trace))

    if not events or trip_dir is None:
        return

    max_events = int(cfg.layout.strategy_engine.telemetry.decision_log_max_events)
    summary = write_sidecar(trip_dir, events, max_events=max_events)
    layout_strategy = dict(curation.get("layoutStrategy") or {})
    layout_strategy.update(summary)
    curation["layoutStrategy"] = layout_strategy


# --- Curation-facing facade (AAD-11 · whitelist thin imports) -----------------
# Prefer: curation → layout_engine.adapter (+ compose_trip when needed).
# Keep peripheral modules off planner/mosaic internals.


def resolve_lse_config_for_trip(cfg: AppConfig, trip_id: str) -> AppConfig:
    from travelogue.layout_engine.rollout import resolve_lse_config_for_trip as _resolve

    return _resolve(cfg, trip_id)


def effective_capabilities(cfg: AppConfig, pack: StrategyPack | None = None) -> Any:
    from travelogue.layout_engine.capabilities import effective_capabilities as _caps

    return _caps(cfg, pack)


def apply_segment_order_to_buckets(
    buckets: list[list[str]],
    assets: list[dict],
    *,
    enabled: bool,
    max_segment_len: int = 30,
) -> None:
    from travelogue.layout_engine.segment_order import apply_segment_order_to_buckets as _apply

    _apply(buckets, assets, enabled=enabled, max_segment_len=max_segment_len)


def buckets_from_existing_chapters(trip: dict) -> dict[str, Any] | None:
    from travelogue.layout_engine.replan import buckets_from_existing_chapters as _buckets

    return _buckets(trip)


def should_layout_only_replan(
    trip: dict,
    *,
    trip_dir: Path | None = None,
    cfg: AppConfig | None = None,
) -> Any:
    from travelogue.layout_engine.replan import should_layout_only_replan as _should

    return _should(trip, trip_dir=trip_dir, cfg=cfg)


def mark_layout_replan(trip: dict, *, reason: str) -> None:
    from travelogue.layout_engine.replan import mark_layout_replan as _mark

    _mark(trip, reason=reason)


def record_applied_layout_density(trip: dict, *, cfg: AppConfig | None = None) -> None:
    from travelogue.layout_engine.replan import record_applied_layout_density as _record

    _record(trip, cfg=cfg)


def begin_mosaic_capture() -> None:
    from travelogue.layout_engine.mosaic.hook import begin_mosaic_capture as _begin

    _begin()


def drain_mosaic_logs() -> list[dict[str, Any]]:
    from travelogue.layout_engine.mosaic.hook import drain_mosaic_logs as _drain

    return _drain()


def drain_mosaic_capture() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from travelogue.layout_engine.mosaic.hook import drain_mosaic_capture as _drain

    return _drain()


def set_mosaic_log_capture(enabled: bool) -> None:
    from travelogue.layout_engine.mosaic.hook import set_mosaic_log_capture as _set

    _set(enabled)


def drain_mosaic_dropped() -> list[str]:
    from travelogue.layout_engine.mosaic.hook import drain_mosaic_dropped as _drain

    return _drain()


def set_mosaic_config_override(cfg: MosaicConfig | None) -> None:
    from travelogue.layout_engine.mosaic.runtime import set_mosaic_config_override as _set

    _set(cfg)


def reset_mosaic_config_override() -> None:
    from travelogue.layout_engine.mosaic.runtime import reset_mosaic_config_override as _reset

    _reset()


def cohort_mosaic_override(cfg: AppConfig) -> MosaicConfig | None:
    from travelogue.layout_engine.mosaic.runtime import cohort_mosaic_override as _cohort

    return _cohort(cfg)


def set_mosaic_disabled_patterns(pattern_ids: tuple[str, ...] | list[str]) -> None:
    from travelogue.layout_engine.mosaic.runtime import set_mosaic_disabled_patterns as _set

    _set(pattern_ids)


def reset_mosaic_disabled_patterns() -> None:
    from travelogue.layout_engine.mosaic.runtime import reset_mosaic_disabled_patterns as _reset

    _reset()


def effective_pattern_blacklist(cfg: AppConfig, *, pack: Any | None = None) -> tuple[str, ...]:
    from travelogue.layout_engine.pattern_policy import effective_pattern_blacklist as _bl

    return _bl(cfg, pack=pack)


def compute_coverage_metrics(**kwargs: Any) -> dict[str, Any]:
    from travelogue.layout_engine.mosaic.coverage import compute_coverage_metrics as _cov

    return _cov(**kwargs)


def record_mosaic_layout_metrics(**kwargs: Any) -> None:
    from travelogue.layout_engine.mosaic.telemetry import record_mosaic_layout_metrics as _rec

    _rec(**kwargs)


def record_per_template_layout_metrics(**kwargs: Any) -> None:
    from travelogue.layout_engine.mosaic.telemetry import (
        record_per_template_layout_metrics as _rec,
    )

    _rec(**kwargs)


def build_editorial_hints(*args: Any, **kwargs: Any) -> Any:
    from travelogue.layout_engine.editorial_hints import build_editorial_hints as _build

    return _build(*args, **kwargs)


def editorial_hints_from_pack(raw: dict | None) -> dict[str, Any]:
    from travelogue.layout_engine.editorial_hints import editorial_hints_from_pack as _from

    return _from(raw)


def attach_screens_to_chapters(*args: Any, **kwargs: Any) -> list[dict]:
    from travelogue.layout_engine.planner.screen_planner import attach_screens_to_chapters as _attach

    return _attach(*args, **kwargs)


def make_screen(*args: Any, **kwargs: Any) -> dict:
    """Public wrapper for screen_planner._make_screen (moment / peripheral use)."""
    from travelogue.layout_engine.planner.screen_planner import _make_screen

    return _make_screen(*args, **kwargs)


def enrich_layout_metrics_with_mosaic(
    out: dict[str, Any],
    chapters: list[dict],
    *,
    mosaic_logs: list[dict] | None,
    pattern_ids: list[str],
) -> None:
    """Single mosaic metrics entry for curation.layout_metrics (AAD-11)."""
    from travelogue.layout_engine.mosaic.constants import MOSAIC_UNIFIED_PATTERN_IDS
    from travelogue.layout_engine.mosaic.metrics import compute_mosaic_metrics

    pids = pattern_ids
    if mosaic_logs is not None or any("mosaic-5" in pid for pid in pids):
        out.update(compute_mosaic_metrics(chapters, mosaic_logs=mosaic_logs))
    elif any(p in MOSAIC_UNIFIED_PATTERN_IDS for p in pids):
        out.update(compute_mosaic_metrics(chapters, mosaic_logs=None))
