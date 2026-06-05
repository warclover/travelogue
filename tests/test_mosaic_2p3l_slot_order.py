"""2P+3L balanced mosaic: assets must match slot cell aspect (no portrait in wide top cells)."""

from __future__ import annotations

from travelogue.curation.mosaic.builders import build_screen, try_order_for_pattern
from travelogue.curation.mosaic.constants import PATTERN_MOSAIC_5_2P_3L_BALANCED
from travelogue.curation.mosaic.grid_specs import EXPLICIT_GRID_SPECS
from travelogue.curation.mosaic.registry import default_registry
from travelogue.curation.screen_planner import _is_std_portrait_id
from travelogue.curation.mosaic.slot_geometry import (
    asset_fits_cell,
    screen_slots_geometry_ok,
    slot_cell_aspect_ratio,
)


def _asset(aid: str, *, w: int, h: int) -> dict:
    return {
        "id": aid,
        "width": w,
        "height": h,
        "takenAt": f"2024-06-01T12:00:{int(aid[-1]):02d}Z",
        "quality": {"sharpness": 0.8},
    }


def test_2p3l_top_row_cells_are_landscape_aspect():
    specs = EXPLICIT_GRID_SPECS[PATTERN_MOSAIC_5_2P_3L_BALANCED]
    for spec in specs[:2]:
        assert slot_cell_aspect_ratio(spec) > 1.0


def test_2p3l_tall_slot_is_portrait_aspect():
    spec = EXPLICIT_GRID_SPECS[PATTERN_MOSAIC_5_2P_3L_BALANCED][2]
    assert slot_cell_aspect_ratio(spec) < 1.0


def test_2p3l_order_puts_portraits_out_of_wide_top_slots():
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
    window = ["p0", "p1", "l0", "l1", "l2"]
    ordered = try_order_for_pattern(
        PATTERN_MOSAIC_5_2P_3L_BALANCED,
        window,
        aspects,
        assets_map,
        burst_seconds=3600,
        median_sharp=0.5,
    )
    assert ordered is not None
    assert ordered[0] in {"l0", "l1", "l2"}
    assert ordered[1] in {"l0", "l1", "l2"}
    assert ordered[2] in {"p0", "p1"}
    assert ordered[3] in {"p0", "p1"}
    assert ordered[4] in {"l0", "l1", "l2"}

    pat = default_registry()[PATTERN_MOSAIC_5_2P_3L_BALANCED]
    screen = build_screen(pat, ordered, assets_map=assets_map)
    assert screen_slots_geometry_ok(screen, aspects)
    specs = EXPLICIT_GRID_SPECS[PATTERN_MOSAIC_5_2P_3L_BALANCED]
    for slot in screen["slots"]:
        idx = int(slot["slot"])
        aid = slot["assetId"]
        cell_ar = slot_cell_aspect_ratio(specs[idx])
        if idx in (0, 1):
            assert asset_fits_cell(aid, aspects, cell_ar)
        if idx == 2:
            assert _is_std_portrait_id(aid, aspects)
