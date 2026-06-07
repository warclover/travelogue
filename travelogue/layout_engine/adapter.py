"""LSE curate adapter — single entry for chapter screen planning (D-P17-01)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from travelogue.config import AppConfig, get_config
from travelogue.curation.layout_planner import AspectKind
from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState
from travelogue.curation.screen_planner import DEFAULT_FEATURED_WEIGHT, plan_screens_for_chapter
from travelogue.layout_engine.registry import StrategyPack, get_strategy_pack


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


def _lse_enabled(cfg: AppConfig | None) -> bool:
    app = cfg or get_config()
    return bool(app.layout.strategy_engine.enabled)


def _resolve_pack(cfg: AppConfig) -> StrategyPack | None:
    if not cfg.layout.strategy_engine.enabled:
        return None
    sid = cfg.layout.strategy_engine.default_strategy_id
    return get_strategy_pack(sid, cfg.layout.strategy_engine.policy_path)


def mixed_proximity_from_pack(pack: StrategyPack | None, *, cfg: AppConfig) -> float:
    if pack is not None:
        planning = pack.raw.get("planning") or {}
        return float(planning.get("mixed_proximity_seconds", cfg.layout.mixed_proximity_seconds))
    return float(cfg.layout.mixed_proximity_seconds)


def plan_chapter_screens(
    ctx: ChapterPlanContext,
    *,
    cfg: AppConfig | None = None,
    pack: StrategyPack | None = None,
) -> list[dict]:
    """
    Curate-facing entry. When LSE disabled, delegates to legacy plan_screens_for_chapter.
    W1: enabled=true uses pack planning fields; scoring injection expands in W1-04+.
    """
    app = cfg or get_config()
    active_pack = pack if pack is not None else _resolve_pack(app)
    mix_gap = ctx.mixed_proximity_seconds
    if mix_gap is None:
        mix_gap = mixed_proximity_from_pack(active_pack, cfg=app)

    mosaic_enabled = ctx.enable_mosaic
    if active_pack is not None:
        stages = (active_pack.raw.get("planning") or {}).get("stages") or {}
        enabled_stages = stages.get("enabled") or []
        overrides = app.layout.strategy_engine.overrides.disable_stages
        if "mosaic" in overrides or "mosaic" not in enabled_stages:
            mosaic_enabled = False

    return plan_screens_for_chapter(
        ctx.asset_ids,
        ctx.aspects,
        chapter_id=ctx.chapter_id,
        assets=ctx.assets,
        burst_seconds=ctx.burst_seconds,
        mixed_proximity_seconds=mix_gap,
        orientation_summary=ctx.orientation_summary,
        skip_screen_asset_ids=ctx.skip_screen_asset_ids,
        layout_state=ctx.layout_state,
        trip_photo_total=ctx.trip_photo_total,
        preferred_hero_id=ctx.preferred_hero_id,
        include_chapter_hero=ctx.include_chapter_hero,
        enable_mosaic=mosaic_enabled,
        featured_weight=ctx.featured_weight,
        enable_portrait_grid8=ctx.enable_portrait_grid8,
        enable_food_grid=ctx.enable_food_grid,
        mundane_grid_buckets=ctx.mundane_grid_buckets,
        median_sharp=ctx.median_sharp,
    )


def strategy_trace_meta(cfg: AppConfig | None = None) -> dict[str, Any]:
    """FR-P17-TRACE summary for trip.curation.layoutStrategy."""
    app = cfg or get_config()
    se = app.layout.strategy_engine
    if not se.enabled:
        return {"enabled": False}
    pack = get_strategy_pack(se.default_strategy_id, se.policy_path)
    return {
        "enabled": True,
        "strategyId": pack.id,
        "strategyVersion": pack.version,
        "weightsHash": pack.weights_hash("default"),
        "algorithmVersion": pack.algorithm_version,
        "contentHash": pack.content_hash,
    }
