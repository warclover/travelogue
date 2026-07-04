"""Usage rule IDs and pattern sets.

Pattern ids are duplicated as string literals here to avoid importing
``travelogue.curation.mosaic`` (whose ``__init__`` pulls candidates → usage_rules).
"""

from __future__ import annotations

PATTERN_LANDSCAPE_9 = "screen-landscape-9"
PATTERN_PORTRAIT_9 = "screen-portrait-9"
PATTERN_MOSAIC_5_HERO_3_2_PLUS_4 = "screen-mosaic-5-hero-3-2-plus-4"
PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4 = "screen-mosaic-5-main-hero-plus-4"
PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND = "screen-mosaic-5-main-portrait-3land"
PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5 = "screen-mosaic-6-main-hero-plus-5"
PATTERN_EDITORIAL_4MIX = "screen-editorial-4mix"

RULE_UR_01 = "UR-01"
RULE_UR_02 = "UR-02"
RULE_UR_03 = "UR-03"
RULE_UR_04 = "UR-04"
RULE_UR_05 = "UR-05"
RULE_UR_06 = "UR-06"

ALL_RULE_IDS: tuple[str, ...] = (
    RULE_UR_01,
    RULE_UR_02,
    RULE_UR_03,
    RULE_UR_04,
    RULE_UR_05,
    RULE_UR_06,
)

# Weakest-first undo order when usage filter would empty the candidate set (PRD §3.6).
USAGE_RULE_UNDO_ORDER: tuple[str, ...] = (
    RULE_UR_06,
    RULE_UR_05,
    RULE_UR_04,
    RULE_UR_03,
    RULE_UR_02,
    RULE_UR_01,
)

HERO_LED_PATTERNS: frozenset[str] = frozenset(
    {
        PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    }
)

HERO_LED_DENSE_PATTERNS: frozenset[str] = HERO_LED_PATTERNS

NINE_GRID_DENSE_PATTERNS: frozenset[str] = frozenset(
    {
        PATTERN_LANDSCAPE_9,
        PATTERN_PORTRAIT_9,
    }
)

HERO_32_PATTERN = PATTERN_MOSAIC_5_HERO_3_2_PLUS_4
MAIN_PORTRAIT_3LAND_PATTERN = PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND
EDITORIAL_4MIX_PATTERN = PATTERN_EDITORIAL_4MIX

HERO_32_WIDE_AR_THRESHOLD = 1.6
