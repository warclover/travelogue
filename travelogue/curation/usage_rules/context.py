"""WindowContext for usage rule evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.curation.layout_planner import AspectKind
from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState
from travelogue.curation.screen_planner import DEFAULT_FEATURED_WEIGHT


@dataclass(frozen=True)
class WindowContext:
    window_asset_ids: tuple[str, ...]
    aspects: dict[str, AspectKind]
    assets_map: dict[str, dict]
    layout_state: ScreenLayoutPlannerState | None
    median_sharp: float | None = None
    featured_weight: float = DEFAULT_FEATURED_WEIGHT


def build_window_context(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    layout_state: ScreenLayoutPlannerState | None = None,
    median_sharp: float | None = None,
    featured_weight: float = DEFAULT_FEATURED_WEIGHT,
) -> WindowContext:
    return WindowContext(
        window_asset_ids=tuple(asset_ids),
        aspects=aspects,
        assets_map=assets_map,
        layout_state=layout_state,
        median_sharp=median_sharp,
        featured_weight=featured_weight,
    )


def main_eligible_hero_score_gap(
    ctx: WindowContext,
    pattern_id: str,
) -> tuple[float, tuple[float, ...]]:
    """Top1−top2 hero score on main-eligible assets for ``pattern_id``."""
    from travelogue.curation.curate_scoring import effective_hero_score
    from travelogue.curation.mosaic.main_eligibility import (
        asset_eligible_for_main_slot,
        resolve_main_ar_ladder_tol,
    )
    from travelogue.curation.mosaic.runtime import get_effective_mosaic_config

    cfg = get_effective_mosaic_config()
    ladder_tol = resolve_main_ar_ladder_tol(pattern_id, cfg)
    scores: list[float] = []
    for aid in ctx.window_asset_ids:
        asset = ctx.assets_map.get(aid) or {}
        ok, _ = asset_eligible_for_main_slot(
            asset,
            pattern_id=pattern_id,
            tol=ladder_tol,
        )
        if not ok:
            continue
        scores.append(
            effective_hero_score(
                asset,
                median_sharp=ctx.median_sharp or 0.0,
                featured_weight=ctx.featured_weight,
            )
        )
    scores.sort(reverse=True)
    if len(scores) <= 1:
        return float("inf"), tuple(scores)
    return scores[0] - scores[1], tuple(scores)


def portrait_is_window_hero_max(ctx: WindowContext) -> bool:
    """True when the window has exactly one portrait and it leads window strength."""
    from travelogue.curation.screen_planner import _is_std_portrait_id

    portraits = [
        aid for aid in ctx.window_asset_ids if _is_std_portrait_id(aid, ctx.aspects)
    ]
    if len(portraits) != 1:
        return False
    portrait_id = portraits[0]

    def strength(aid: str) -> float:
        asset = ctx.assets_map.get(aid) or {}
        sharp = float((asset.get("quality") or {}).get("sharpness") or 0.0)
        mult = (
            ctx.featured_weight if asset.get("userTier") == "featured" else 1.0
        )
        return sharp * mult

    portrait_strength = strength(portrait_id)
    if portrait_strength <= 0:
        return False
    return portrait_strength >= max(strength(aid) for aid in ctx.window_asset_ids) - 1e-9


def window_std_portrait_count(ctx: WindowContext) -> int:
    """Count standard (non-tall) portraits in the window."""
    from travelogue.curation.screen_planner import _is_std_portrait_id

    return sum(
        1 for aid in ctx.window_asset_ids if _is_std_portrait_id(aid, ctx.aspects)
    )
