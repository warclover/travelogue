"""Pattern ids for mosaic / unified grid windows (Phase 15 · S2)."""

from __future__ import annotations

# --- 5-slot mosaic family (S1) ---
PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND = "screen-mosaic-5-main-portrait-3land"
PATTERN_MOSAIC_5_MAIN_LAND_2P_2L = "screen-mosaic-5-main-landscape-2portrait-2land"
PATTERN_MOSAIC_5_2P_3L_BALANCED = "screen-mosaic-5-2portrait-3land-balanced"
PATTERN_MOSAIC_5_3P_2L_BALANCED = "screen-mosaic-5-3portrait-2land-balanced"
PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4 = "screen-mosaic-5-main-hero-plus-4"
PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5 = "screen-mosaic-6-main-hero-plus-5"

MOSAIC_5_PATTERN_IDS: tuple[str, ...] = (
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
    PATTERN_MOSAIC_5_MAIN_LAND_2P_2L,
    PATTERN_MOSAIC_5_2P_3L_BALANCED,
    PATTERN_MOSAIC_5_3P_2L_BALANCED,
)

# --- 3 / 4 / 6 · reuse existing grid patterns (S2) ---
PATTERN_PORTRAIT_3 = "screen-portrait-3"
PATTERN_LANDSCAPE_3 = "screen-landscape-3"
PATTERN_PORTRAIT_1_LANDSCAPE_2 = "screen-portrait-1-landscape-2"
PATTERN_PORTRAIT_2_LANDSCAPE_2 = "screen-portrait-2-landscape-2"
PATTERN_PORTRAIT_4 = "screen-portrait-4"
PATTERN_LANDSCAPE_4 = "screen-landscape-4"
PATTERN_PORTRAIT_6 = "screen-portrait-6"
PATTERN_LANDSCAPE_6 = "screen-landscape-6"

MOSAIC_3_PATTERN_IDS: tuple[str, ...] = (
    PATTERN_PORTRAIT_3,
    PATTERN_LANDSCAPE_3,
    PATTERN_PORTRAIT_1_LANDSCAPE_2,
)
MOSAIC_4_PATTERN_IDS: tuple[str, ...] = (
    PATTERN_PORTRAIT_2_LANDSCAPE_2,
    PATTERN_PORTRAIT_4,
    PATTERN_LANDSCAPE_4,
)

MOSAIC_6_PATTERN_IDS: tuple[str, ...] = (
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    PATTERN_PORTRAIT_6,
    PATTERN_LANDSCAPE_6,
)

# --- 8 / 9 · grid-8 + 3×3 nine-grid (P15+)
PATTERN_PORTRAIT_GRID_8 = "screen-portrait-grid-8"
PATTERN_PORTRAIT_9 = "screen-portrait-9"
PATTERN_LANDSCAPE_9 = "screen-landscape-9"

MOSAIC_8_PATTERN_IDS: tuple[str, ...] = (PATTERN_PORTRAIT_GRID_8,)
MOSAIC_9_PATTERN_IDS: tuple[str, ...] = (
    PATTERN_PORTRAIT_9,
    PATTERN_LANDSCAPE_9,
)

MOSAIC_UNIFIED_PATTERN_IDS: tuple[str, ...] = (
    *MOSAIC_3_PATTERN_IDS,
    *MOSAIC_4_PATTERN_IDS,
    *MOSAIC_5_PATTERN_IDS,
    *MOSAIC_6_PATTERN_IDS,
    *MOSAIC_8_PATTERN_IDS,
    *MOSAIC_9_PATTERN_IDS,
)

PATTERN_GRID_CLASS: dict[str, str] = {
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND: "layout-screen__grid--mosaic-5-main-portrait-3land",
    PATTERN_MOSAIC_5_MAIN_LAND_2P_2L: "layout-screen__grid--mosaic-5-main-landscape-2portrait-2land",
    PATTERN_MOSAIC_5_2P_3L_BALANCED: "layout-screen__grid--mosaic-5-2portrait-3land-balanced",
    PATTERN_MOSAIC_5_3P_2L_BALANCED: "layout-screen__grid--mosaic-5-3portrait-2land-balanced",
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4: "layout-screen__grid--mosaic-6-main-hero-plus-5",
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5: "layout-screen__grid--mosaic-6-main-hero-plus-5",
    PATTERN_PORTRAIT_3: "layout-screen__grid--3col",
    PATTERN_LANDSCAPE_3: "layout-screen__grid--landscape-stack-3",
    PATTERN_PORTRAIT_1_LANDSCAPE_2: "layout-screen__grid--portrait-left-2landscape",
    PATTERN_PORTRAIT_2_LANDSCAPE_2: "layout-screen__grid--2x2",
    PATTERN_PORTRAIT_4: "layout-screen__grid--2x2",
    PATTERN_LANDSCAPE_4: "layout-screen__grid--2x2",
    PATTERN_PORTRAIT_6: "layout-screen__grid--3x2",
    PATTERN_LANDSCAPE_6: "layout-screen__grid--3x2",
    PATTERN_PORTRAIT_GRID_8: "layout-screen__grid--portrait-2x4",
    PATTERN_PORTRAIT_9: "layout-screen__grid--3x3",
    PATTERN_LANDSCAPE_9: "layout-screen__grid--3x3",
}
