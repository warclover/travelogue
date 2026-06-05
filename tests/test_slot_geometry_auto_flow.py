"""Auto-flow grids (2x2 etc.): portrait must not land in wide cells on the 16:9 stage."""

from __future__ import annotations

from travelogue.curation.mosaic.slot_geometry import (
    auto_flow_cell_aspect_ratio,
    screen_slots_geometry_ok,
)


def _screen(pattern_id: str, aspect_by_aid: dict[str, str]) -> dict:
    slots = [
        {"slot": i, "assetId": aid} for i, aid in enumerate(aspect_by_aid)
    ]
    return {"patternId": pattern_id, "slots": slots}


def test_auto_flow_cell_aspect_ratio_values():
    assert auto_flow_cell_aspect_ratio(2, 2) > 1.25  # 2x2 → ~1.78 wide
    assert auto_flow_cell_aspect_ratio(3, 1) < 0.92  # 3 cols, 1 row → ~0.59 tall
    assert auto_flow_cell_aspect_ratio(4, 2) < 0.92  # grid-8 → ~0.89 tall


def test_portrait_4_all_portrait_rejected():
    aspects = {"p0": "portrait", "p1": "portrait", "p2": "portrait", "p3": "portrait"}
    screen = _screen("screen-portrait-4", aspects)
    assert screen_slots_geometry_ok(screen, aspects) is False


def test_landscape_4_all_landscape_ok():
    aspects = {"l0": "landscape", "l1": "landscape", "l2": "landscape", "l3": "landscape"}
    screen = _screen("screen-landscape-4", aspects)
    assert screen_slots_geometry_ok(screen, aspects) is True


def test_portrait_3_columns_ok_for_portrait():
    aspects = {"p0": "portrait", "p1": "portrait", "p2": "portrait"}
    screen = _screen("screen-portrait-3", aspects)
    assert screen_slots_geometry_ok(screen, aspects) is True


def test_portrait_grid8_ok_for_portrait():
    aspects = {f"p{i}": "portrait" for i in range(8)}
    screen = _screen("screen-portrait-grid-8", aspects)
    assert screen_slots_geometry_ok(screen, aspects) is True


def test_portrait_2_landscape_2_portrait_in_wide_rejected():
    aspects = {"p0": "portrait", "p1": "portrait", "l0": "landscape", "l1": "landscape"}
    screen = _screen("screen-portrait-2-landscape-2", aspects)
    assert screen_slots_geometry_ok(screen, aspects) is False
