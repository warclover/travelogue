"""Hero mosaic slot ordering: portrait side tiles, landscape bottom row."""

from __future__ import annotations

from travelogue.layout_engine.mosaic.builders import build_screen, try_order_for_pattern
from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
from travelogue.layout_engine.mosaic.pattern_catalog import default_registry


def _asset(aid: str, *, w: int, h: int) -> dict:
    return {
        "id": aid,
        "width": w,
        "height": h,
        "takenAt": f"2024-06-01T12:00:{int(aid[-1]):02d}Z",
        "quality": {"sharpness": 0.8},
    }


def test_hero_six_rejects_two_portraits():
    aspects = {
        "l0": "landscape",
        "l1": "landscape",
        "l2": "landscape",
        "l3": "landscape",
        "p1": "portrait",
        "p2": "portrait",
    }
    assets_map = {
        "l0": _asset("l0", w=3000, h=1687),
        "l1": _asset("l1", w=3000, h=1687),
        "l2": _asset("l2", w=3000, h=1687),
        "l3": _asset("l3", w=3000, h=1687),
        "p1": _asset("p1", w=1200, h=1800),
        "p2": _asset("p2", w=1200, h=1800),
    }
    window = ["l0", "l1", "l2", "l3", "p1", "p2"]
    ordered = try_order_for_pattern(
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
        window,
        aspects,
        assets_map,
        burst_seconds=3600,
        median_sharp=0.5,
    )
    assert ordered is None


def test_hero_six_one_portrait_one_landscape_side():
    aspects = {
        "l0": "landscape",
        "l1": "landscape",
        "l2": "landscape",
        "l3": "landscape",
        "l4": "landscape",
        "p1": "portrait",
    }
    assets_map = {
        "l0": _asset("l0", w=3000, h=1687),
        "l1": _asset("l1", w=3000, h=1687),
        "l2": _asset("l2", w=3000, h=1687),
        "l3": _asset("l3", w=3000, h=1687),
        "l4": _asset("l4", w=3000, h=1687),
        "p1": _asset("p1", w=1200, h=1800),
    }
    window = ["l0", "l1", "l2", "l3", "l4", "p1"]
    ordered = try_order_for_pattern(
        PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
        window,
        aspects,
        assets_map,
        burst_seconds=3600,
        median_sharp=0.5,
    )
    assert ordered is not None
    assert ordered[0] in {"l0", "l1", "l2", "l3", "l4"}
    side = ordered[1:3]
    assert "p1" in side
    assert sum(1 for aid in side if aid.startswith("l")) == 1
    assert set(ordered[3:]) <= {"l0", "l1", "l2", "l3", "l4"}

    pat = default_registry()[PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5]
    screen = build_screen(pat, ordered, assets_map=assets_map)
    roles = [sl["role"] for sl in screen["slots"]]
    assert roles[0] == "main"
    assert roles.count("portrait") == 1
    assert roles[3:] == ["landscape", "landscape", "landscape"]


def test_landscape_nine_window_generates_candidate():
    aspects = {f"a{i}": "landscape" for i in range(9)}
    assets_map = {f"a{i}": _asset(f"a{i}", w=3000, h=1687) for i in range(9)}
    window = [f"a{i}" for i in range(9)]
    ordered = try_order_for_pattern(
        "screen-landscape-9",
        window,
        aspects,
        assets_map,
        burst_seconds=3600,
        median_sharp=0.5,
    )
    assert ordered is not None
    assert len(ordered) == 9
