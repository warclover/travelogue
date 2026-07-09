"""Render must preserve mosaic slot count even when an asset is missing."""

from __future__ import annotations

from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
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
