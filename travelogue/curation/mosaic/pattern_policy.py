"""Which mosaic / grid patternIds are allowed under current config."""

from __future__ import annotations

from travelogue.config import MosaicConfig
from travelogue.curation.mosaic.constants import (
    MOSAIC_5_PATTERN_IDS,
    PATTERN_MOSAIC_5_2P_3L_BALANCED,
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_5_MAIN_LAND_2P_2L,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)
from travelogue.curation.mosaic.runtime import mosaic_window_size_enabled
from travelogue.curation.screen_layout_state import pattern_slot_count

_FIVE_SLOT_MOSAIC_PATTERNS = frozenset(MOSAIC_5_PATTERN_IDS)
_SIX_SLOT_MOSAIC_PATTERNS = frozenset(
    {
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
        PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    }
)
# Retired: registry/grid/scorer geometry disagree (2 portrait slots, 1 tall cell).
_RETIRED_MOSAIC_PATTERNS = frozenset(
    {
        PATTERN_MOSAIC_5_2P_3L_BALANCED,
        PATTERN_MOSAIC_5_MAIN_LAND_2P_2L,
    }
)


def mosaic_pattern_disabled(
    pattern_id: str,
    *,
    cfg: MosaicConfig | None = None,
) -> bool:
    """True when this patternId must not be emitted (5/6 slot windows off)."""
    if pattern_id in _RETIRED_MOSAIC_PATTERNS:
        return True
    if pattern_id in _FIVE_SLOT_MOSAIC_PATTERNS and not mosaic_window_size_enabled(5, cfg):
        return True
    if pattern_id in _SIX_SLOT_MOSAIC_PATTERNS and not mosaic_window_size_enabled(6, cfg):
        return True
    n = pattern_slot_count(pattern_id)
    if n == 5 and not mosaic_window_size_enabled(5, cfg):
        return True
    if n == 6 and not mosaic_window_size_enabled(6, cfg):
        return True
    return False
