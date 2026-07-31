"""Pattern ids for mosaic / unified grid windows (Phase 15 · S2).

Semantic aliases below; authoritative tuples and grid classes live in
``_legacy_generated.py`` (YAML export CI · R-P16-02).
"""

from __future__ import annotations

from travelogue.layout_engine.mosaic._legacy_generated import (
    MOSAIC_3_PATTERN_IDS as MOSAIC_3_PATTERN_IDS,
)
from travelogue.layout_engine.mosaic._legacy_generated import (
    MOSAIC_4_PATTERN_IDS as MOSAIC_4_PATTERN_IDS,
)
from travelogue.layout_engine.mosaic._legacy_generated import (
    MOSAIC_5_PATTERN_IDS as MOSAIC_5_PATTERN_IDS,
)
from travelogue.layout_engine.mosaic._legacy_generated import (
    MOSAIC_6_PATTERN_IDS as MOSAIC_6_PATTERN_IDS,
)
from travelogue.layout_engine.mosaic._legacy_generated import (
    MOSAIC_8_PATTERN_IDS as MOSAIC_8_PATTERN_IDS,
)
from travelogue.layout_engine.mosaic._legacy_generated import (
    MOSAIC_9_PATTERN_IDS as MOSAIC_9_PATTERN_IDS,
)
from travelogue.layout_engine.mosaic._legacy_generated import (
    MOSAIC_UNIFIED_PATTERN_IDS as MOSAIC_UNIFIED_PATTERN_IDS,
)
from travelogue.layout_engine.mosaic._legacy_generated import (
    PATTERN_GRID_CLASS as PATTERN_GRID_CLASS,
)

# --- 5-slot mosaic family (S1) ---
PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND = "screen-mosaic-5-main-portrait-3land"
PATTERN_MOSAIC_5_MAIN_LAND_2P_2L = "screen-mosaic-5-main-landscape-2portrait-2land"
PATTERN_MOSAIC_5_2P_3L_BALANCED = "screen-mosaic-5-2portrait-3land-balanced"
PATTERN_MOSAIC_5_3P_2L_BALANCED = "screen-mosaic-5-3portrait-2land-balanced"
PATTERN_MOSAIC_5_2P3L_EQUAL = "screen-mosaic-5-2p3l-equal"
PATTERN_MOSAIC_5_HERO_3_2_PLUS_4 = "screen-mosaic-5-hero-3-2-plus-4"
PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4 = "screen-mosaic-5-main-hero-plus-4"
PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5 = "screen-mosaic-6-main-hero-plus-5"
# MTSO PR-C2 · experimental（勿进 MOSAIC_5_PATTERN_IDS / lte_policy 直至转正）
PATTERN_MOSAIC_5_1P4L_PORTRAIT_HERO = "screen-mosaic-5-1p4l-portrait-hero"
PATTERN_MOSAIC_5_1P4L_PORTRAIT_CENTER_RAILS = (
    "screen-mosaic-5-1p4l-portrait-center-rails"
)
PATTERN_MOSAIC_5_2P3L_PORTRAIT_HERO_RAIL = "screen-mosaic-5-2p3l-portrait-hero-rail"
PATTERN_MOSAIC_5_2P3L_RAIL = "screen-mosaic-5-2p3l-rail"
# 3P2L left-portrait-hero family（勿进 MOSAIC_5_PATTERN_IDS 直至转正）
PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD = "screen-mosaic-5-3p2l-portrait-hero-quad"
PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK = (
    "screen-mosaic-5-3p2l-portrait-hero-lp-stack"
)
MOSAIC_5_3P2L_PORTRAIT_HERO_IDS: frozenset[str] = frozenset(
    {
        PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_QUAD,
        PATTERN_MOSAIC_5_3P2L_PORTRAIT_HERO_LP_STACK,
    }
)
# 三列等分家族 · experimental（勿进 MOSAIC_* / lte_policy 直至转正）
PATTERN_MOSAIC_4_2P2L_PORTRAIT_BOOKENDS = "screen-mosaic-4-2p2l-portrait-bookends"

# --- 3 / 4 / 6 · reuse existing grid patterns (S2) ---
PATTERN_PORTRAIT_3 = "screen-portrait-3"
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
