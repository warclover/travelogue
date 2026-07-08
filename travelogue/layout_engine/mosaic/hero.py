"""Hero / main slot selection for mosaic patterns (M2)."""

from __future__ import annotations

from travelogue.layout_contract.orientations import AspectKind


def pick_main_for_pattern(
    pattern_id: str,
    ordered_asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    median_sharp: float | None = None,
) -> str | None:
    """Pick main/hero asset for patterns with a ``main`` role."""
    from travelogue.layout_engine.mosaic.main_eligibility import (
        main_ar_guard_enabled,
        pick_best_main_eligible,
    )
    from travelogue.layout_engine.mosaic.pattern_catalog import default_registry
    from travelogue.layout_engine.mosaic.runtime import get_effective_mosaic_config
    from travelogue.layout_engine.planner.screen_planner import _is_landscape_id, _pick_main_landscape_id

    pat = default_registry().get(pattern_id)
    landscapes = [
        aid for aid in ordered_asset_ids if _is_landscape_id(aid, aspects)
    ]
    if pat and "main" in pat.roles and landscapes:
        cfg = get_effective_mosaic_config()
        if main_ar_guard_enabled(cfg):
            picked = pick_best_main_eligible(
                landscapes,
                assets_map,
                pattern_id=pattern_id,
                median_sharp=median_sharp,
                cfg=cfg,
            )
            if picked:
                return picked
            return None
        return _pick_main_landscape_id(landscapes, assets_map, median_sharp=median_sharp)
    if ordered_asset_ids:
        return ordered_asset_ids[0]
    return None
