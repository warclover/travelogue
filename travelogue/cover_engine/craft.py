"""Cover Craft Focus · Hero Set constants and assignable filtering (PRD-CCF)."""

from __future__ import annotations

from typing import Iterable

#: CCF Hero Set — sole assignable styles when ``cover_craft.hero_only`` is on.
HERO_SET: tuple[str, ...] = (
    "veil-footer",
    "folio-overlap",
    "band-cut",
)

#: Still catalog-active; filtered from assignable when CCF hero_only is on.
SIDE_DISH_IDS: frozenset[str] = frozenset({"scroll-head", "contact-stamp"})

HERO_SET_FROZEN: frozenset[str] = frozenset(HERO_SET)


def is_hero_style(style_id: str) -> bool:
    return (style_id or "").strip() in HERO_SET_FROZEN


def filter_assignable_records(records: Iterable[object]) -> list:
    """Keep only Hero Set when CCF hero_only is enabled; otherwise pass through."""
    from travelogue.config.cover_craft import is_cover_craft_hero_only

    rows = list(records)
    if not is_cover_craft_hero_only():
        return rows
    return [r for r in rows if getattr(r, "id", None) in HERO_SET_FROZEN]


def craft_attr_value() -> str | None:
    """Return ``data-cover-craft`` value or None when craft CSS is off."""
    from travelogue.config.cover_craft import CRAFT_ATTR_VALUE, is_cover_craft_css_enabled

    if not is_cover_craft_css_enabled():
        return None
    return CRAFT_ATTR_VALUE
