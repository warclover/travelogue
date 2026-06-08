"""LSE curate adapter — single entry for chapter screen planning (D-P17-01)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from travelogue.config import AppConfig, MosaicConfig, get_config
from travelogue.curation.layout_planner import AspectKind
from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState
from travelogue.curation.screen_planner import DEFAULT_FEATURED_WEIGHT, plan_screens_for_chapter
from travelogue.layout_engine.decision_log import (
    ingest_beam_logs,
    ingest_mosaic_logs,
    strategy_trace_from_pack,
    write_sidecar,
)
from travelogue.layout_engine.registry import StrategyPack, get_strategy_pack
from travelogue.layout_engine.rhythm import layout_state_from_pack


@dataclass
class ChapterPlanContext:
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


def lse_enabled(cfg: AppConfig | None = None) -> bool:
    app = cfg or get_config()
    return bool(app.layout.strategy_engine.enabled)


def resolve_pack(cfg: AppConfig) -> StrategyPack | None:
    if not cfg.layout.strategy_engine.enabled:
        return None
    sid = cfg.layout.strategy_engine.default_strategy_id
    return get_strategy_pack(sid, cfg.layout.strategy_engine.policy_path)


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
    active = pack if pack is not None else resolve_pack(cfg)
    if active is not None:
        from travelogue.curation.layout_density import LayoutDensityParams

        params = LayoutDensityParams(density=density or "balanced")  # type: ignore[arg-type]
        return layout_state_from_pack(total_photos, active, density_params=params)
    from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState

    return ScreenLayoutPlannerState.from_trip_total(
        total_photos,
        density=density or "balanced",  # type: ignore[arg-type]
    )


def plan_chapter_screens(
    ctx: ChapterPlanContext,
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

    return plan_screens_for_chapter(
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
    )


def strategy_trace_meta(cfg: AppConfig | None = None) -> dict[str, Any]:
    """FR-P17-TRACE summary for trip.curation.layoutStrategy."""
    from travelogue.layout_engine.capabilities import capability_flags_snapshot

    app = cfg or get_config()
    se = app.layout.strategy_engine
    if not se.enabled:
        return {"enabled": False}
    pack = get_strategy_pack(se.default_strategy_id, se.policy_path)
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
