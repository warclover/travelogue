"""Collage asset routing to full-frame template (PRD §3.4 · AC-P16-18)."""

from __future__ import annotations

from travelogue.config import get_config
from travelogue.curation.media_classify import is_collage_asset

_FULL_FRAME_PATTERN = "screen-full-frame"


def collage_routing_enabled() -> bool:
    te = getattr(get_config().layout, "template_engine", None)
    return te is not None and bool(getattr(te, "exclude_collage_from_mosaic", True))


def single_asset_screen_pattern(
    pattern_id: str,
    asset_id: str,
    assets_map: dict[str, dict] | None,
) -> str:
    """Route collage singles to full-frame instead of portrait/landscape-1."""
    if not collage_routing_enabled():
        return pattern_id
    asset = (assets_map or {}).get(asset_id, {})
    if is_collage_asset(asset):
        return _FULL_FRAME_PATTERN
    return pattern_id
