"""Pattern ids for mosaic / unified grid windows (Phase 15 · S2).

Tuple aliases resolve via ``legacy_specs`` at runtime; CI snapshot in ``_legacy_generated.py``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from travelogue.curation.mosaic.legacy_specs import (
    mosaic_pattern_id_groups,
    mosaic_unified_pattern_ids,
    pattern_grid_class,
)

_LAZY_EXPORTS: dict[str, Callable[[], Any]] = {
    "MOSAIC_3_PATTERN_IDS": lambda: mosaic_pattern_id_groups()["MOSAIC_3_PATTERN_IDS"],
    "MOSAIC_4_PATTERN_IDS": lambda: mosaic_pattern_id_groups()["MOSAIC_4_PATTERN_IDS"],
    "MOSAIC_5_PATTERN_IDS": lambda: mosaic_pattern_id_groups()["MOSAIC_5_PATTERN_IDS"],
    "MOSAIC_6_PATTERN_IDS": lambda: mosaic_pattern_id_groups()["MOSAIC_6_PATTERN_IDS"],
    "MOSAIC_8_PATTERN_IDS": lambda: mosaic_pattern_id_groups()["MOSAIC_8_PATTERN_IDS"],
    "MOSAIC_9_PATTERN_IDS": lambda: mosaic_pattern_id_groups()["MOSAIC_9_PATTERN_IDS"],
    "MOSAIC_UNIFIED_PATTERN_IDS": mosaic_unified_pattern_ids,
    "PATTERN_GRID_CLASS": pattern_grid_class,
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_EXPORTS:
        return _LAZY_EXPORTS[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(
        set(_LAZY_EXPORTS.keys())
        | {
            "PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND",
            "PATTERN_MOSAIC_5_MAIN_LAND_2P_2L",
            "PATTERN_MOSAIC_5_2P_3L_BALANCED",
            "PATTERN_MOSAIC_5_3P_2L_BALANCED",
            "PATTERN_MOSAIC_5_2P3L_EQUAL",
            "PATTERN_MOSAIC_5_HERO_3_2_PLUS_4",
            "PATTERN_MOSAIC_5_TOP_HERO_4",
            "PATTERN_MOSAIC_5_LEFT3_RIGHT2",
            "PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4",
            "PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5",
            "PATTERN_MOSAIC_6_GRID_HERO_BR",
            "PATTERN_PORTRAIT_3",
            "PATTERN_LANDSCAPE_2",
            "PATTERN_LANDSCAPE_3",
            "PATTERN_PORTRAIT_1_LANDSCAPE_2",
            "PATTERN_PORTRAIT_2_LANDSCAPE_2",
            "PATTERN_PORTRAIT_4",
            "PATTERN_LANDSCAPE_4",
            "PATTERN_PORTRAIT_6",
            "PATTERN_LANDSCAPE_6",
            "PATTERN_PORTRAIT_GRID_8",
            "PATTERN_PORTRAIT_9",
            "PATTERN_LANDSCAPE_9",
            "PATTERN_FULL_FRAME",
        }
    )


# --- 5-slot mosaic family (S1) ---
PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND = "screen-mosaic-5-main-portrait-3land"
PATTERN_MOSAIC_5_MAIN_LAND_2P_2L = "screen-mosaic-5-main-landscape-2portrait-2land"
PATTERN_MOSAIC_5_2P_3L_BALANCED = "screen-mosaic-5-2portrait-3land-balanced"
PATTERN_MOSAIC_5_3P_2L_BALANCED = "screen-mosaic-5-3portrait-2land-balanced"
PATTERN_MOSAIC_5_2P3L_EQUAL = "screen-mosaic-5-2p3l-equal"
PATTERN_MOSAIC_5_HERO_3_2_PLUS_4 = "screen-mosaic-5-hero-3-2-plus-4"
PATTERN_MOSAIC_5_TOP_HERO_4 = "screen-mosaic-5-top-hero-4"
PATTERN_MOSAIC_5_LEFT3_RIGHT2 = "screen-mosaic-5-left3-right2"
PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4 = "screen-mosaic-5-main-hero-plus-4"
PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5 = "screen-mosaic-6-main-hero-plus-5"
PATTERN_MOSAIC_6_GRID_HERO_BR = "screen-mosaic-6-grid-hero-br"

# --- 3 / 4 / 6 · reuse existing grid patterns (S2) ---
PATTERN_PORTRAIT_3 = "screen-portrait-3"
PATTERN_LANDSCAPE_2 = "screen-landscape-2"
PATTERN_LANDSCAPE_3 = "screen-landscape-3"
PATTERN_PORTRAIT_1_LANDSCAPE_2 = "screen-portrait-1-landscape-2"
PATTERN_PORTRAIT_2_LANDSCAPE_2 = "screen-portrait-2-landscape-2"
PATTERN_PORTRAIT_4 = "screen-portrait-4"
PATTERN_LANDSCAPE_4 = "screen-landscape-4"
PATTERN_PORTRAIT_6 = "screen-portrait-6"
PATTERN_LANDSCAPE_6 = "screen-landscape-6"

# --- 8 / 9 · grid-8 + 3×3 nine-grid (P15+) ---
PATTERN_PORTRAIT_GRID_8 = "screen-portrait-grid-8"
PATTERN_PORTRAIT_9 = "screen-portrait-9"
PATTERN_LANDSCAPE_9 = "screen-landscape-9"

PATTERN_FULL_FRAME = "screen-full-frame"
