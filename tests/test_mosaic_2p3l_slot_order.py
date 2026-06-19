"""2P+3L mosaic patterns retired from MCS candidate selection."""

from __future__ import annotations

from travelogue.curation.mosaic.constants import (
    PATTERN_MOSAIC_5_2P3L_EQUAL,
    PATTERN_MOSAIC_5_2P_3L_BALANCED,
)
from travelogue.curation.mosaic.lte_adapter import mosaic_pattern_disabled


def test_2p3l_balanced_retired_from_mcs() -> None:
    assert mosaic_pattern_disabled(PATTERN_MOSAIC_5_2P_3L_BALANCED)


def test_2p3l_equal_retired_from_mcs() -> None:
    assert mosaic_pattern_disabled(PATTERN_MOSAIC_5_2P3L_EQUAL)
