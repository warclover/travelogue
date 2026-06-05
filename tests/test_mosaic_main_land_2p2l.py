"""Main landscape + 2P + 2L: right column must be one tall portrait, not two wide cells."""

from __future__ import annotations

from travelogue.curation.mosaic.builders import build_screen, try_order_for_pattern
from travelogue.curation.mosaic.constants import PATTERN_MOSAIC_5_MAIN_LAND_2P_2L
from travelogue.curation.mosaic.grid_specs import EXPLICIT_GRID_SPECS, gap_cells
from travelogue.curation.mosaic.registry import default_registry
from travelogue.curation.mosaic.slot_geometry import (
    screen_slots_geometry_ok,
    slot_cell_aspect_ratio,
)
from travelogue.curation.screen_planner import _is_landscape_id, _is_std_portrait_id


def _asset(aid: str, *, w: int, h: int) -> dict:
    return {
        "id": aid,
        "width": w,
        "height": h,
        "takenAt": f"2024-06-01T12:00:{int(aid[-1]):02d}Z",
        "quality": {"sharpness": 0.8},
    }


def test_main_land_2p2l_grid_fills_3x3():
    specs = EXPLICIT_GRID_SPECS[PATTERN_MOSAIC_5_MAIN_LAND_2P_2L]
    assert gap_cells(specs) == set()


def test_main_land_2p2l_right_column_is_tall_portrait_cell():
    spec = EXPLICIT_GRID_SPECS[PATTERN_MOSAIC_5_MAIN_LAND_2P_2L][1]
    assert slot_cell_aspect_ratio(spec) < 1.0


def test_main_land_2p2l_order_puts_one_portrait_in_tall_slot():
    aspects = {
        "p0": "portrait",
        "p1": "portrait",
        "l0": "landscape",
        "l1": "landscape",
        "l2": "landscape",
    }
    assets_map = {
        "p0": _asset("p0", w=1200, h=1800),
        "p1": _asset("p1", w=1200, h=1800),
        "l0": _asset("l0", w=3000, h=1687),
        "l1": _asset("l1", w=3000, h=1687),
        "l2": _asset("l2", w=3000, h=1687),
    }
    ordered = try_order_for_pattern(
        PATTERN_MOSAIC_5_MAIN_LAND_2P_2L,
        ["p0", "p1", "l0", "l1", "l2"],
        aspects,
        assets_map,
        burst_seconds=3600,
        median_sharp=0.5,
    )
    assert ordered is not None
    assert _is_landscape_id(ordered[0], aspects)
    assert _is_std_portrait_id(ordered[1], aspects)
    assert _is_landscape_id(ordered[2], aspects)
    pat = default_registry()[PATTERN_MOSAIC_5_MAIN_LAND_2P_2L]
    screen = build_screen(pat, ordered, assets_map=assets_map)
    assert screen_slots_geometry_ok(screen, aspects)
    by_slot = {int(s["slot"]): s["assetId"] for s in screen["slots"]}
    assert _is_std_portrait_id(by_slot[1], aspects)
    assert _is_landscape_id(by_slot[2], aspects)
