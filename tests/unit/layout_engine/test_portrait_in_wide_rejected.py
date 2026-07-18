"""Portrait assets must not cover-fill landscape-AR mosaic cells."""

from __future__ import annotations

import pytest

from travelogue.layout_engine.mosaic.slot_geometry import screen_slots_geometry_ok


def _mixed_2l2p_screen(pattern_id: str) -> tuple[dict, dict[str, str]]:
    aspects = {
        "l0": "landscape",
        "p0": "portrait",
        "p1": "portrait",
        "l1": "landscape",
    }
    screen = {
        "patternId": pattern_id,
        "slots": [
            {"slot": 0, "assetId": "l0", "role": "landscape", "rect": [1, 1, 1, 1]},
            {"slot": 1, "assetId": "p0", "role": "portrait", "rect": [2, 2, 1, 1]},
            {"slot": 2, "assetId": "p1", "role": "portrait", "rect": [1, 1, 2, 2]},
            {"slot": 3, "assetId": "l1", "role": "landscape", "rect": [2, 2, 2, 2]},
        ],
    }
    return screen, aspects


@pytest.mark.unit
@pytest.mark.parametrize(
    "pattern_id",
    [
        "screen-mosaic-4-2l2p-weighted",
        "screen-editorial-4mix",
        "screen-portrait-2-landscape-2",
    ],
)
def test_equal_2x2_rejects_portrait_in_wide_cells(pattern_id: str) -> None:
    screen, aspects = _mixed_2l2p_screen(pattern_id)
    assert screen_slots_geometry_ok(screen, aspects) is False


@pytest.mark.unit
def test_landscape_4_all_landscape_still_ok() -> None:
    aspects = {f"l{i}": "landscape" for i in range(4)}
    screen = {
        "patternId": "screen-landscape-4",
        "slots": [{"slot": i, "assetId": f"l{i}"} for i in range(4)],
    }
    assert screen_slots_geometry_ok(screen, aspects) is True
