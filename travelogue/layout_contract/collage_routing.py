"""Collage asset routing (layout kernel). to full-frame template (PRD §3.4 · AC-P16-18)."""

from __future__ import annotations

from travelogue.layout_contract.media_class import is_collage_asset

_FULL_FRAME_PATTERN = "screen-full-frame"


def collage_routing_enabled(exclude_collage_from_mosaic: bool | None = None) -> bool:
    if exclude_collage_from_mosaic is None:
        return True
    return bool(exclude_collage_from_mosaic)


def single_asset_screen_pattern(
    pattern_id: str,
    asset_id: str,
    assets_map: dict[str, dict] | None,
    *,
    exclude_collage_from_mosaic: bool | None = None,
) -> str:
    """Route collage singles to full-frame instead of portrait/landscape-1."""
    if not collage_routing_enabled(exclude_collage_from_mosaic):
        return pattern_id
    asset = (assets_map or {}).get(asset_id, {})
    if is_collage_asset(asset):
        return _FULL_FRAME_PATTERN
    return pattern_id
