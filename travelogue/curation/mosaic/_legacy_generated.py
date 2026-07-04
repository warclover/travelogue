"""LTE-generated legacy mosaic constants — do not edit by hand.

Regenerate:
  python scripts/lte_export_legacy.py --sync-python
Content hash: 0dfaffc5728be3a690cb4ff458eb93143fad855aca860b91492af17776266764
"""

from __future__ import annotations

from typing import Any

EXPLICIT_GRID_SPECS: dict[str, Any] = {
    "screen-editorial-4mix": [(1, 1, 1, 1), (2, 2, 1, 1), (1, 1, 2, 2), (2, 2, 2, 2)],
    "screen-mosaic-5-2p3l-equal": [(1, 1, 1, 3), (2, 2, 1, 3), (3, 3, 1, 1), (3, 3, 2, 2), (3, 3, 3, 3)],
    "screen-mosaic-5-2portrait-3land-balanced": [(1, 1, 1, 1), (2, 2, 1, 1), (1, 1, 2, 3), (2, 2, 2, 2), (2, 3, 3, 3)],
    "screen-mosaic-5-3portrait-2land-balanced": [(1, 1, 1, 2), (2, 2, 1, 2), (3, 3, 1, 2), (1, 2, 3, 3), (3, 3, 3, 3)],
    "screen-mosaic-5-hero-3-2-plus-4": [(1, 1, 1, 2), (2, 2, 1, 1), (3, 3, 1, 1), (2, 2, 2, 2), (3, 3, 2, 2)],
    "screen-mosaic-5-main-hero-plus-4": [(1, 2, 1, 2), (3, 3, 1, 1), (3, 3, 2, 2), (1, 1, 3, 3), (2, 2, 3, 3), (3, 3, 3, 3)],
    "screen-mosaic-5-main-landscape-2portrait-2land": [(1, 2, 1, 2), (3, 3, 1, 2), (1, 1, 3, 3), (2, 2, 3, 3), (3, 3, 3, 3)],
    "screen-mosaic-5-main-portrait-3land": [(1, 2, 1, 2), (3, 3, 1, 2), (1, 1, 3, 3), (2, 2, 3, 3), (3, 3, 3, 3)],
    "screen-mosaic-6-main-hero-plus-5": [(1, 2, 1, 2), (3, 3, 1, 1), (3, 3, 2, 2), (1, 1, 3, 3), (2, 2, 3, 3), (3, 3, 3, 3)],
    "screen-portrait-1-landscape-2": [(1, 1, 1, 2), (2, 2, 1, 1), (2, 2, 2, 2)],
}

EXPLICIT_GRID_BOUNDS: dict[str, Any] = {
    "screen-editorial-4mix": (2, 2),
    "screen-mosaic-5-2p3l-equal": (3, 3),
    "screen-mosaic-5-2portrait-3land-balanced": (3, 3),
    "screen-mosaic-5-3portrait-2land-balanced": (3, 3),
    "screen-mosaic-5-hero-3-2-plus-4": (3, 2),
    "screen-mosaic-5-main-hero-plus-4": (3, 3),
    "screen-mosaic-5-main-landscape-2portrait-2land": (3, 3),
    "screen-mosaic-5-main-portrait-3land": (3, 3),
    "screen-mosaic-6-main-hero-plus-5": (3, 3),
    "screen-portrait-1-landscape-2": (2, 2),
}

AUTO_FLOW_GRIDS: dict[str, Any] = {
    "screen-landscape-4": (2, 2, 4),
    "screen-landscape-6": (3, 2, 6),
    "screen-landscape-9": (3, 3, 9),
    "screen-portrait-2-landscape-2": (2, 2, 4),
    "screen-portrait-3-editorial": (3, 1, 3),
    "screen-portrait-3": (3, 1, 3),
    "screen-portrait-4": (2, 2, 4),
    "screen-portrait-6": (3, 2, 6),
    "screen-portrait-9": (3, 3, 9),
    "screen-portrait-grid-8": (4, 2, 8),
}

STACK_PATTERNS = frozenset({"screen-landscape-2", "screen-landscape-3"})

PATTERN_GRID_CLASS: dict[str, Any] = {
    "screen-editorial-4mix": 'layout-screen__grid--editorial-4mix',
    "screen-full-frame": 'layout-screen__grid--1col',
    "screen-landscape-1": 'layout-screen__grid--1col',
    "screen-landscape-2": 'layout-screen__grid--landscape-stack-2',
    "screen-landscape-3": 'layout-screen__grid--landscape-stack-3',
    "screen-landscape-4": 'layout-screen__grid--2x2',
    "screen-landscape-6": 'layout-screen__grid--3x2',
    "screen-landscape-9": 'layout-screen__grid--3x3',
    "screen-mosaic-5-2p3l-equal": 'layout-screen__grid--mosaic-5-2p3l-equal',
    "screen-mosaic-5-2portrait-3land-balanced": 'layout-screen__grid--mosaic-5-2portrait-3land-balanced',
    "screen-mosaic-5-3portrait-2land-balanced": 'layout-screen__grid--mosaic-5-3portrait-2land-balanced',
    "screen-mosaic-5-hero-3-2-plus-4": 'layout-screen__grid--mosaic-5-hero-3-2-plus-4',
    "screen-mosaic-5-main-hero-plus-4": 'layout-screen__grid--mosaic-5-main-hero-plus-4',
    "screen-mosaic-5-main-landscape-2portrait-2land": 'layout-screen__grid--mosaic-5-main-landscape-2portrait-2land',
    "screen-mosaic-5-main-portrait-3land": 'layout-screen__grid--mosaic-5-main-portrait-3land',
    "screen-mosaic-6-main-hero-plus-5": 'layout-screen__grid--mosaic-6-main-hero-plus-5',
    "screen-portrait-1-landscape-2": 'layout-screen__grid--portrait-left-2landscape',
    "screen-portrait-1": 'layout-screen__grid--1col',
    "screen-portrait-2-landscape-2": 'layout-screen__grid--2x2',
    "screen-portrait-2": 'layout-screen__grid--2col',
    "screen-portrait-3-editorial": 'layout-screen__grid--3col',
    "screen-portrait-3": 'layout-screen__grid--3col',
    "screen-portrait-4": 'layout-screen__grid--2x2',
    "screen-portrait-6": 'layout-screen__grid--3x2',
    "screen-portrait-9": 'layout-screen__grid--3x3',
    "screen-portrait-grid-8": 'layout-screen__grid--portrait-2x4',
}

_PORTRAIT_FORBIDDEN_WIDE: dict[str, Any] = {
    "screen-mosaic-5-main-portrait-3land": frozenset({0}),
}

_LANDSCAPE_FORBIDDEN_TALL: dict[str, Any] = {
    "screen-mosaic-5-hero-3-2-plus-4": frozenset({0}),
    "screen-mosaic-5-main-portrait-3land": frozenset({1}),
}

PORTRAIT_DOMINANT_AUTO_FLOW: frozenset[str] = frozenset({"screen-portrait-1", "screen-portrait-3", "screen-portrait-4", "screen-portrait-6", "screen-portrait-9", "screen-portrait-grid-8"})

MOSAIC_3_PATTERN_IDS: tuple[str, ...] = ("screen-portrait-3", "screen-landscape-3", "screen-portrait-1-landscape-2",)

MOSAIC_4_PATTERN_IDS: tuple[str, ...] = ("screen-portrait-2-landscape-2", "screen-portrait-4", "screen-landscape-4",)

MOSAIC_5_PATTERN_IDS: tuple[str, ...] = ("screen-mosaic-5-main-portrait-3land", "screen-mosaic-5-hero-3-2-plus-4",)

MOSAIC_6_PATTERN_IDS: tuple[str, ...] = ("screen-mosaic-5-main-hero-plus-4", "screen-mosaic-6-main-hero-plus-5", "screen-portrait-6", "screen-landscape-6",)

MOSAIC_8_PATTERN_IDS: tuple[str, ...] = ("screen-portrait-grid-8",)

MOSAIC_9_PATTERN_IDS: tuple[str, ...] = ("screen-portrait-9", "screen-landscape-9",)

MOSAIC_UNIFIED_PATTERN_IDS: tuple[str, ...] = (*MOSAIC_3_PATTERN_IDS, *MOSAIC_4_PATTERN_IDS, *MOSAIC_5_PATTERN_IDS, *MOSAIC_6_PATTERN_IDS, *MOSAIC_8_PATTERN_IDS, *MOSAIC_9_PATTERN_IDS)
