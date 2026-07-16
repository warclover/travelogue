"""AAD-12 opportunistic · minimal mosaic pattern special-case registry."""

from __future__ import annotations

from travelogue.layout_engine.mosaic.constants import (
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
)

# One extracted special-case group (portrait-main mosaic-5). Full planner
# rewrite is OUT of this wave; registration is the AC-AAD-12 minimum slice.
MOSAIC_PORTRAIT_MAIN_SPECIALS: dict[str, dict[str, object]] = {
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND: {
        "family": "mosaic-portrait-main",
        "mainRole": "portrait",
        "slotCount": 5,
    },
}


def mosaic_special_meta(pattern_id: str) -> dict[str, object] | None:
    return MOSAIC_PORTRAIT_MAIN_SPECIALS.get(str(pattern_id or ""))
