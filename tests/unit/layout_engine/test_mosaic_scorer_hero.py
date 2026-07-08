"""Scorer preferences for hero mosaic patterns."""

from __future__ import annotations

from travelogue.config import MosaicConfig
from travelogue.curation.mosaic.constants import (
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)
from travelogue.curation.mosaic.scorer import score_candidate


def _all_landscape_assets(n: int):
    aspects = {}
    assets_map = {}
    for i in range(n):
        aid = f"a{i}"
        aspects[aid] = "landscape"
        assets_map[aid] = {
            "id": aid,
            "width": 3000,
            "height": 1687,
            "takenAt": f"2024-06-01T10:0{i}:00Z",
            "quality": {"sharpness": 0.8},
        }
    slots = [
        {"assetId": f"a{i}", "slot": i, "fit": "cover", "role": "main" if i == 0 else "tile"}
        for i in range(n)
    ]
    return aspects, assets_map, slots


def test_all_landscape_hero5_penalized_vs_hero6_boosted():
    cfg = MosaicConfig()
    aspects5, assets5, slots5 = _all_landscape_assets(5)
    aspects6, assets6, slots6 = _all_landscape_assets(6)
    s5 = score_candidate(
        {"patternId": PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4, "slots": slots5},
        aspects=aspects5,
        assets_by_id=assets5,
        cfg=cfg,
        trip_photo_total=50,
    )
    s6 = score_candidate(
        {"patternId": PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5, "slots": slots6},
        aspects=aspects6,
        assets_by_id=assets6,
        cfg=cfg,
        trip_photo_total=50,
    )
    assert s5.penalties.get("hero_narrow_tiles", 0.0) > 0.0
    assert s6.penalties.get("hero_narrow_tiles", 0.0) == 0.0
    assert s6.total >= s5.total
