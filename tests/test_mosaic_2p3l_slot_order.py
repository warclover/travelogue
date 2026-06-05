"""2P+3L balanced mosaic retired (geometry/scorer/registry conflict)."""

from __future__ import annotations

from travelogue.curation.mosaic.constants import PATTERN_MOSAIC_5_2P_3L_BALANCED
from travelogue.curation.mosaic.pattern_policy import mosaic_pattern_disabled


def test_2p3l_balanced_retired_from_mcs() -> None:
    assert mosaic_pattern_disabled(PATTERN_MOSAIC_5_2P_3L_BALANCED)
