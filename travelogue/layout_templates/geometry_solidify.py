"""Persist LTE geometry on curated screens (PRD §4.5, W3)."""

from __future__ import annotations

from typing import Any

from travelogue.layout_templates.geometry import slot_display_aspect
from travelogue.layout_templates.registry import get_engine


def solidify_screen_geometry(screen: dict[str, Any], pattern_id: str) -> dict[str, Any]:
    """Write layoutGeometry + per-slot rect/displayAspect from LTE YAML."""
    try:
        template = get_engine().get(pattern_id)
    except KeyError:
        return screen

    stage = template.stage
    if stage.cols and stage.rows:
        cols = list(stage.cols)
        rows = list(stage.rows)
    elif stage.grid:
        cols = [1.0] * stage.grid[0]
        rows = [1.0] * stage.grid[1]
    else:
        cols = [1.0]
        rows = [1.0]

    geo: dict[str, Any] = {
        "stageAspect": stage.aspect,
        "cols": cols,
        "rows": rows,
        "gridClass": template.render_grid_class,
        "templateVersion": template.version,
    }
    if stage.gap:
        geo["gap"] = stage.gap
    screen["layoutGeometry"] = geo

    slot_by_index = {slot.index: slot for slot in template.slots}
    for slot in screen.get("slots") or []:
        idx = int(slot.get("slot", -1))
        meta = slot_by_index.get(idx)
        if meta is None:
            continue
        slot["rect"] = list(meta.rect)
        slot["displayAspect"] = round(slot_display_aspect(meta.rect, stage), 4)
        from travelogue.curation.mosaic.lte_adapter import resolve_slot_fit

        slot["fit"] = resolve_slot_fit(
            pattern_id,
            idx,
            meta.role,
            {"id": slot.get("assetId")} if slot.get("assetId") else {},
        )

    return screen
