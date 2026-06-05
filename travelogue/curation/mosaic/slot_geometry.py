"""Match mosaic slot grid cells to portrait / landscape assets."""

from __future__ import annotations

from travelogue.curation.layout_planner import AspectKind
from travelogue.curation.mosaic.constants import (
    PATTERN_MOSAIC_5_2P_3L_BALANCED,
    PATTERN_MOSAIC_5_MAIN_LAND_2P_2L,
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
)
from travelogue.curation.mosaic.grid_specs import AUTO_FLOW_GRIDS, EXPLICIT_GRID_SPECS
from travelogue.curation.screen_planner import _is_landscape_id, _is_std_portrait_id

_STAGE_ASPECT = 16 / 9
_PORTRAIT_STAGE_ASPECT = 9 / 16
_WIDE_CELL_AR = 1.25
_TALL_CELL_AR = 0.92

# Pure portrait auto-flow grids are laid out on a portrait stage, not 16:9 landscape.
_PORTRAIT_DOMINANT_AUTO_FLOW: frozenset[str] = frozenset(
    {
        "screen-portrait-3",
        "screen-portrait-4",
        "screen-portrait-6",
        "screen-portrait-9",
        "screen-portrait-grid-8",
    }
)

# Slots where portrait-in-wide was the user-visible defect (top row of 2P+3L, main tile, etc.)
_PORTRAIT_FORBIDDEN_WIDE: dict[str, frozenset[int]] = {
    PATTERN_MOSAIC_5_2P_3L_BALANCED: frozenset({0, 1}),
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND: frozenset({0}),
    PATTERN_MOSAIC_5_MAIN_LAND_2P_2L: frozenset({0, 2, 4}),
}
_LANDSCAPE_FORBIDDEN_TALL: dict[str, frozenset[int]] = {
    PATTERN_MOSAIC_5_2P_3L_BALANCED: frozenset({2}),
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND: frozenset({1}),
    PATTERN_MOSAIC_5_MAIN_LAND_2P_2L: frozenset({1}),
}


def slot_cell_aspect_ratio(
    spec: tuple[int, int, int, int],
    *,
    stage_aspect: float = _STAGE_ASPECT,
) -> float:
    """Display aspect ratio (width/height) for a 1-based grid cell on a 3×3 stage."""
    c0, c1, r0, r1 = spec
    col_frac = (c1 - c0 + 1) / 3.0
    row_frac = (r1 - r0 + 1) / 3.0
    return (col_frac * stage_aspect) / row_frac


def asset_fits_cell(
    aid: str,
    aspects: dict[str, AspectKind],
    cell_aspect: float,
) -> bool:
    kind = aspects.get(aid)
    if kind is None:
        return True
    if cell_aspect >= _WIDE_CELL_AR:
        return _is_landscape_id(aid, aspects) or kind == "square"
    if cell_aspect <= _TALL_CELL_AR:
        return _is_std_portrait_id(aid, aspects) or kind == "square"
    return True


def auto_flow_cell_aspect_ratio(
    cols: int,
    rows: int,
    *,
    stage_aspect: float = _STAGE_ASPECT,
) -> float:
    """Display aspect ratio for one cell of a uniform cols×rows auto-flow grid."""
    if cols <= 0 or rows <= 0:
        return stage_aspect
    return (rows / cols) * stage_aspect


def _explicit_geometry_ok(
    pattern_id: str,
    specs: list[tuple[int, int, int, int]],
    screen: dict,
    aspects: dict[str, AspectKind],
) -> bool:
    forbid_wide = _PORTRAIT_FORBIDDEN_WIDE.get(pattern_id, frozenset())
    forbid_tall = _LANDSCAPE_FORBIDDEN_TALL.get(pattern_id, frozenset())
    for slot in screen.get("slots") or []:
        idx = int(slot.get("slot", -1))
        aid = slot.get("assetId")
        if not aid or idx < 0 or idx >= len(specs):
            continue
        cell_ar = slot_cell_aspect_ratio(specs[idx])
        if idx in forbid_wide and cell_ar >= _WIDE_CELL_AR:
            if _is_std_portrait_id(aid, aspects):
                return False
        if idx in forbid_tall and cell_ar <= _TALL_CELL_AR:
            if _is_landscape_id(aid, aspects):
                return False
    return True


def _stage_aspect_for_auto_flow(pattern_id: str) -> float:
    if pattern_id in _PORTRAIT_DOMINANT_AUTO_FLOW:
        return _PORTRAIT_STAGE_ASPECT
    return _STAGE_ASPECT


def _auto_flow_geometry_ok(
    cols: int,
    rows: int,
    screen: dict,
    aspects: dict[str, AspectKind],
    *,
    stage_aspect: float = _STAGE_ASPECT,
) -> bool:
    """Uniform auto-flow grids: reject portrait in wide cells / landscape in tall cells."""
    cell_ar = auto_flow_cell_aspect_ratio(cols, rows, stage_aspect=stage_aspect)
    for slot in screen.get("slots") or []:
        aid = slot.get("assetId")
        if not aid:
            continue
        if cell_ar >= _WIDE_CELL_AR and _is_std_portrait_id(aid, aspects):
            return False
        if cell_ar <= _TALL_CELL_AR and _is_landscape_id(aid, aspects):
            return False
    return True


def screen_slots_geometry_ok(
    screen: dict,
    aspects: dict[str, AspectKind],
) -> bool:
    """Reject layouts with portrait in clearly wide cells (or landscape in tall cells)."""
    pattern_id = str(screen.get("patternId") or "")
    specs = EXPLICIT_GRID_SPECS.get(pattern_id)
    if specs:
        return _explicit_geometry_ok(pattern_id, specs, screen, aspects)
    auto = AUTO_FLOW_GRIDS.get(pattern_id)
    if auto:
        cols, rows, _n = auto
        return _auto_flow_geometry_ok(
            cols,
            rows,
            screen,
            aspects,
            stage_aspect=_stage_aspect_for_auto_flow(pattern_id),
        )
    return True
