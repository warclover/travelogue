"""Cover closing helpers: closing asset pick (S1 last screen / S2 last chapter)."""

from __future__ import annotations

from travelogue.domain.closing_view import (
    asset_is_landscape,
    collect_layout_screen_asset_ids,
    last_chapter_curated_asset_id,
    last_screen_asset_id,
    resolve_closing_asset_id,
)
from travelogue.render.cover_opening import cover_focal_point, cover_use_contain_fit

__all__ = [
    "asset_is_landscape",
    "collect_layout_screen_asset_ids",
    "closing_focal_point",
    "closing_use_contain_fit",
    "last_chapter_curated_asset_id",
    "last_screen_asset_id",
    "resolve_closing_asset_id",
    "show_closing_title",
]


def show_closing_title(title: str) -> bool:
    return bool((title or "").strip())


closing_focal_point = cover_focal_point
closing_use_contain_fit = cover_use_contain_fit
