"""MTSO PR-B · six-hero structural/admit qualification (pure, no candidate gen)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from travelogue.config.mosaic import (
    MosaicConfig,
    effective_selection_optimization_enabled,
)
from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
from travelogue.layout_contract.orientations import AspectKind

if TYPE_CHECKING:
    from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState


@dataclass(frozen=True)
class HeroSixQualify:
    structural: bool
    admit: bool
    reason: str = ""
    gap: float | None = None


def effective_hero_six_opportunity_enabled(cfg: MosaicConfig | None) -> bool:
    if not effective_selection_optimization_enabled(cfg):
        return False
    so = getattr(cfg, "selection_optimization", None)
    return bool(so is not None and getattr(so, "hero_six_opportunity_enabled", True))


def effective_mixed_hero_routing_enabled(cfg: MosaicConfig | None) -> bool:
    if not effective_selection_optimization_enabled(cfg):
        return False
    so = getattr(cfg, "selection_optimization", None)
    return bool(so is not None and getattr(so, "mixed_hero_routing_enabled", True))


def _hero_gap_threshold(cfg: MosaicConfig | None) -> float:
    so = getattr(cfg, "selection_optimization", None) if cfg is not None else None
    gap = getattr(so, "hero_gap_threshold", None) if so is not None else None
    if gap is not None:
        return float(gap)
    from travelogue.config import get_config

    return float(get_config().layout.usage_rules.hero_gap_threshold)


def _orientation_ok(
    window: list[str], aspects: dict[str, AspectKind]
) -> tuple[bool, str]:
    """SUP-01 · only std landscape / std portrait count; square/tall disqualify pools."""
    from travelogue.layout_engine.planner.screen_planner import (
        _is_landscape_id,
        _is_std_portrait_id,
    )

    lands = [a for a in window if _is_landscape_id(a, aspects)]
    ports = [a for a in window if _is_std_portrait_id(a, aspects)]
    if len(lands) + len(ports) != len(window):
        return False, "six_hero_non_std_aspect"
    if len(ports) >= 2:
        return False, "six_hero_portrait_overflow"
    if len(ports) == 0 and len(lands) == 6:
        return True, ""
    if len(ports) == 1 and len(lands) == 5:
        return True, ""
    return False, "six_hero_orientation_mix"


def qualify_hero_six(
    window: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    cfg: MosaicConfig,
    layout_state: ScreenLayoutPlannerState | None,
    seg_cap: int,
    median_sharp: float | None = None,
) -> HeroSixQualify:
    """Two-stage qualify: structural then admit (quota read-only; no candidate gen)."""
    if len(window) != 6:
        return HeroSixQualify(False, False, "six_hero_window_size")
    if int(seg_cap) < 6:
        return HeroSixQualify(False, False, "six_hero_blocked:segment_cap")

    ok_orient, orient_reason = _orientation_ok(window, aspects)
    if not ok_orient:
        return HeroSixQualify(False, False, orient_reason)

    from travelogue.layout_engine.mosaic.builders import _order_hero_six_detailed

    ordered, order_reason = _order_hero_six_detailed(
        list(window), aspects, assets_map, median_sharp=median_sharp
    )
    if not ordered:
        return HeroSixQualify(False, False, order_reason or "six_hero_order_failed")

    from travelogue.layout_contract.usage_context import build_window_context
    from travelogue.layout_engine.usage_rules.context import main_eligible_hero_score_gap

    wctx = build_window_context(
        list(window), aspects, assets_map, median_sharp=median_sharp
    )
    gap, _scores = main_eligible_hero_score_gap(
        wctx, PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
    )
    thr = _hero_gap_threshold(cfg)
    # SUP-02 · gap=inf (single eligible main) is structurally qualified
    if gap < thr:
        return HeroSixQualify(False, False, "six_hero_gap_below", gap=gap)

    structural = True

    if layout_state is None:
        return HeroSixQualify(True, False, "six_hero_no_layout_state", gap=gap)
    if not layout_state.can_use_dense_collage_window(6):
        return HeroSixQualify(True, False, "six_hero_dense_quota", gap=gap)
    if not layout_state.can_use_large_mosaic_window(6):
        return HeroSixQualify(True, False, "six_hero_large_quota", gap=gap)

    return HeroSixQualify(True, True, "", gap=gap)


def six_hero_outcome_label(
    *,
    structural: bool,
    admit: bool,
    reason: str,
    attempted_six: bool,
    won_six: bool,
) -> str:
    """AC-MTSO-03 · stable window-level six-hero outcome bucket."""
    if won_six:
        return "won"
    if reason.startswith("six_hero_blocked:segment_cap") or reason == "six_hero_blocked:segment_cap":
        return "segment_blocked"
    if reason in ("six_hero_dense_quota", "six_hero_large_quota"):
        return "quota_blocked"
    if not structural:
        return "qualify_fail"
    if structural and not admit:
        return "quota_blocked"
    if attempted_six:
        return "score_lose"
    return "not_attempted"


def mixed_portrait_is_hero(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    median_sharp: float | None = None,
    featured_weight: float = 1.35,
    layout_state: ScreenLayoutPlannerState | None = None,
    cfg: MosaicConfig | None = None,
) -> bool:
    """PR-C1 · D-MTSO-03: portrait is sharpness max OR hero-score gap ≥ threshold."""
    from travelogue.layout_contract.usage_context import build_window_context
    from travelogue.layout_engine.planner.screen_planner import (
        _is_landscape_id,
        _is_std_portrait_id,
    )
    from travelogue.layout_engine.scoring.hero import effective_hero_score
    from travelogue.layout_engine.usage_rules.context import portrait_is_window_hero_max

    wctx = build_window_context(
        list(asset_ids),
        aspects,
        assets_map,
        layout_state=layout_state,
        median_sharp=median_sharp,
        featured_weight=featured_weight,
    )
    if portrait_is_window_hero_max(wctx):
        return True

    portraits = [
        aid for aid in asset_ids if _is_std_portrait_id(aid, aspects)
    ]
    if len(portraits) != 1:
        return False
    lands = [aid for aid in asset_ids if _is_landscape_id(aid, aspects)]
    if not lands:
        return False
    med = float(median_sharp or 0.0)
    p_score = effective_hero_score(
        assets_map.get(portraits[0]) or {},
        median_sharp=med,
        featured_weight=featured_weight,
    )
    land_scores = [
        effective_hero_score(
            assets_map.get(aid) or {},
            median_sharp=med,
            featured_weight=featured_weight,
        )
        for aid in lands
    ]
    thr = _hero_gap_threshold(cfg)
    return (p_score - max(land_scores)) >= thr - 1e-9
