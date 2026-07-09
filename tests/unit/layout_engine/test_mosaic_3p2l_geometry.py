"""3P2L balanced mosaic: slot geometry matches portrait/landscape roles."""

from __future__ import annotations

from travelogue.layout_engine.mosaic.grid_specs import EXPLICIT_GRID_SPECS, gap_cells


def _slot_aspect(spec: tuple[int, int, int, int], stage: float = 16 / 9) -> float:
    c0, c1, r0, r1 = spec
    cw = (c1 - c0 + 1) / 3
    rh = (r1 - r0 + 1) / 3
    return (cw * stage) / rh


def test_3p2l_balanced_fills_3x3_without_gaps():
    specs = EXPLICIT_GRID_SPECS["screen-mosaic-5-3portrait-2land-balanced"]
    assert gap_cells(specs) == set()


def test_3p2l_balanced_portrait_slots_are_tall_cells():
    specs = EXPLICIT_GRID_SPECS["screen-mosaic-5-3portrait-2land-balanced"]
    for spec in specs[:3]:
        assert _slot_aspect(spec) < 1.0, spec


def test_3p2l_balanced_landscape_slots_are_wide_cells():
    specs = EXPLICIT_GRID_SPECS["screen-mosaic-5-3portrait-2land-balanced"]
    for spec in specs[3:]:
        assert _slot_aspect(spec) > 1.0, spec
