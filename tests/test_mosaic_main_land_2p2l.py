"""Main-land 2P+2L mosaic retired (geometry/scorer/registry conflict)."""

from __future__ import annotations

from travelogue.curation.mosaic.constants import PATTERN_MOSAIC_5_MAIN_LAND_2P_2L
from travelogue.curation.mosaic.pattern_policy import mosaic_pattern_disabled


def test_main_land_2p2l_retired_from_mcs() -> None:
    assert mosaic_pattern_disabled(PATTERN_MOSAIC_5_MAIN_LAND_2P_2L)
