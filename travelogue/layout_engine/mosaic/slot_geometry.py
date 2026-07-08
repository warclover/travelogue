"""Match mosaic slot grid cells to portrait / landscape assets."""

from __future__ import annotations

from travelogue.curation.layout_planner import AspectKind
from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_5_HERO_3_2_PLUS_4
from travelogue.layout_engine.mosaic.legacy_specs import (
    auto_flow_grids,
    explicit_grid_specs,
    landscape_forbidden_tall,
    portrait_forbidden_wide,
)
from travelogue.layout_engine.planner.screen_planner import _is_landscape_id, _is_std_portrait_id

_STAGE_ASPECT = 16 / 9
_PORTRAIT_STAGE_ASPECT = 9 / 16
_WIDE_CELL_AR = 1.25
_TALL_CELL_AR = 0.92

# Pure portrait auto-flow grids are laid out on a portrait stage, not 16:9 landscape.
from travelogue.layout_engine.mosaic._legacy_generated import PORTRAIT_DOMINANT_AUTO_FLOW

_PORTRAIT_DOMINANT_AUTO_FLOW = PORTRAIT_DOMINANT_AUTO_FLOW

# Slots where portrait-in-wide was the user-visible defect (main tile, etc.)
from travelogue.layout_engine.mosaic._legacy_generated import (
    _LANDSCAPE_FORBIDDEN_TALL as _LANDSCAPE_FORBIDDEN_TALL,
)
from travelogue.layout_engine.mosaic._legacy_generated import (
    _PORTRAIT_FORBIDDEN_WIDE as _PORTRAIT_FORBIDDEN_WIDE,
)


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


def _cell_aspect_for_slot(
    pattern_id: str,
    slot: dict,
    idx: int,
    specs: list[tuple[int, int, int, int]],
) -> float:
    raw = slot.get("displayAspect")
    if raw is not None:
        try:
            return float(raw)
        except (TypeError, ValueError):
            pass
    geo = slot.get("rect")
    if isinstance(geo, (list, tuple)) and len(geo) == 4:
        try:
            from travelogue.layout_templates.geometry import slot_display_aspect
            from travelogue.layout_templates.registry import get_engine

            template = get_engine().get(pattern_id)
            rect = (int(geo[0]), int(geo[1]), int(geo[2]), int(geo[3]))
            return slot_display_aspect(rect, template.stage)
        except (KeyError, TypeError, ValueError):
            pass
    if idx < len(specs):
        return slot_cell_aspect_ratio(specs[idx])
    return _STAGE_ASPECT


def _explicit_geometry_ok(
    pattern_id: str,
    specs: list[tuple[int, int, int, int]],
    screen: dict,
    aspects: dict[str, AspectKind],
) -> bool:
    forbid_wide = portrait_forbidden_wide().get(pattern_id, frozenset())
    forbid_tall = landscape_forbidden_tall().get(pattern_id, frozenset())
    if pattern_id == PATTERN_MOSAIC_5_HERO_3_2_PLUS_4:
        from travelogue.layout_engine.mosaic.runtime import get_effective_mosaic_config

        if not get_effective_mosaic_config().hero_weighted_geometry_guard:
            forbid_tall = frozenset()
    for slot in screen.get("slots") or []:
        idx = int(slot.get("slot", -1))
        aid = slot.get("assetId")
        if not aid or idx < 0 or idx >= len(specs):
            continue
        cell_ar = _cell_aspect_for_slot(pattern_id, slot, idx, specs)
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
    specs = explicit_grid_specs().get(pattern_id)
    if specs:
        return _explicit_geometry_ok(pattern_id, specs, screen, aspects)
    auto = auto_flow_grids().get(pattern_id)
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
