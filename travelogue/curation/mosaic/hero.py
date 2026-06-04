"""Hero / main slot selection for mosaic patterns (M2)."""

from __future__ import annotations

from travelogue.curation.layout_planner import AspectKind


def pick_main_for_pattern(
    pattern_id: str,
    ordered_asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    median_sharp: float | None = None,
) -> str | None:
    """Pick main/hero asset for patterns with a ``main`` role."""
    from travelogue.curation.screen_planner import _pick_main_landscape_id

    from travelogue.curation.mosaic.registry import default_registry

    pat = default_registry().get(pattern_id)
    landscapes = [aid for aid in ordered_asset_ids if aspects.get(aid) == "landscape"]
    if pat and "main" in pat.roles and landscapes:
        return _pick_main_landscape_id(landscapes, assets_map, median_sharp=median_sharp)
    if ordered_asset_ids:
        return ordered_asset_ids[0]
    return None
