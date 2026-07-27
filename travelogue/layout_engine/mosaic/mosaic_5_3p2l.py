"""3P2L left-portrait-hero family · soft pick quad vs lp-stack."""

from __future__ import annotations

from travelogue.layout_contract.orientations import AspectKind, is_std_landscape, is_std_portrait
from travelogue.layout_engine.mosaic.constants import (
    MOSAIC_5_3P2L_PORTRAIT_HERO_IDS,
    PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK,
    PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD,
)
from travelogue.layout_engine.mosaic.pattern_catalog import MosaicPattern


def _sharp(aid: str, assets_map: dict[str, dict]) -> float:
    q = (assets_map.get(aid) or {}).get("quality") or {}
    try:
        return float(q.get("sharpness") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _mean_sharp(ids: list[str], assets_map: dict[str, dict]) -> float:
    if not ids:
        return 0.0
    return sum(_sharp(aid, assets_map) for aid in ids) / len(ids)


def prefer_3p2l_pattern_id(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    tie_epsilon: float = 0.08,
) -> str:
    """Prefer quad when aux portraits are sharper; lp-stack when landscapes lead."""
    portraits = [
        aid for aid in asset_ids if is_std_portrait(aspects.get(aid) or "square")
    ]
    landscapes = [
        aid for aid in asset_ids if is_std_landscape(aspects.get(aid) or "square")
    ]
    if not portraits:
        return PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD
    main = max(portraits, key=lambda aid: _sharp(aid, assets_map))
    aux_p = [p for p in portraits if p != main]
    p_score = _mean_sharp(aux_p, assets_map)
    l_score = _mean_sharp(landscapes, assets_map)
    if l_score > p_score + tie_epsilon:
        return PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK
    return PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD


def soft_pick_3p2l_patterns(
    patterns: list[MosaicPattern],
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
) -> list[MosaicPattern]:
    """When both family SKUs are present, keep the preferred one only."""
    family = [p for p in patterns if p.pattern_id in MOSAIC_5_3P2L_PORTRAIT_HERO_IDS]
    if len(family) < 2:
        return patterns
    preferred = prefer_3p2l_pattern_id(asset_ids, aspects, assets_map)
    return [
        p
        for p in patterns
        if p.pattern_id not in MOSAIC_5_3P2L_PORTRAIT_HERO_IDS
        or p.pattern_id == preferred
    ]
