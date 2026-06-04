"""Render must preserve mosaic slot count even when an asset is missing."""

from __future__ import annotations

from travelogue.curation.mosaic.constants import PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
from travelogue.render.context import build_layout_screen


def test_mosaic6_keeps_all_slot_figures_when_one_asset_missing():
    assets = {
        f"a{i}": {
            "id": f"a{i}",
            "width": 3000,
            "height": 1687,
            "storageKey": f"assets/a{i}.webp",
        }
        for i in range(6)
        if i != 4
    }
    screen = {
        "patternId": PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
        "slots": [
            {"assetId": f"a{i}", "slot": i, "fit": "cover", "role": "main" if i == 0 else "tile"}
            for i in range(6)
        ],
    }
    ctx = build_layout_screen(
        screen,
        assets,
        meta_title="test",
        export_layout="web",
    )
    assert len(ctx["slots"]) == 6
    assert ctx["slots"][4]["slotIndex"] == 4
    assert ctx["slots"][4].get("hasSrc") is False
    assert ctx["slots"][5].get("hasSrc") is True


def test_six_landscape_window_prefers_mosaic6():
    from travelogue.config import MosaicConfig
    from travelogue.curation.mosaic.compose import pick_best_window

    aspects = {}
    assets_map = {}
    for i in range(6):
        aid = f"a{i}"
        aspects[aid] = "landscape"
        assets_map[aid] = {
            "id": aid,
            "width": 3000,
            "height": 1687,
            "takenAt": f"2024-06-01T10:0{i}:00Z",
            "quality": {"sharpness": 0.8},
        }
    pick = pick_best_window(
        list(aspects.keys()),
        aspects,
        assets_map,
        cfg=MosaicConfig(enabled=True, deterministic_strict=True),
        window_size=6,
        trip_photo_total=50,
    )
    assert pick.screen is not None
    assert pick.screen["patternId"] == PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
    assert len(pick.screen["slots"]) == 6
