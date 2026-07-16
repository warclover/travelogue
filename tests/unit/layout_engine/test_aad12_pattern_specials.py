"""AAD-12 · mosaic portrait-main special registry smoke."""

from __future__ import annotations

from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND
from travelogue.layout_engine.mosaic.pattern_specials import (
    MOSAIC_PORTRAIT_MAIN_SPECIALS,
    mosaic_special_meta,
)


def test_aad12_portrait_main_special_registered() -> None:
    meta = mosaic_special_meta(PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND)
    assert meta is not None
    assert meta["family"] == "mosaic-portrait-main"
    assert PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND in MOSAIC_PORTRAIT_MAIN_SPECIALS


def test_aad12_unknown_pattern_returns_none() -> None:
    assert mosaic_special_meta("screen-landscape-1") is None
