"""Persist LTE geometry on curated screens (PRD §4.5, W3)."""

from __future__ import annotations

from typing import Any

from travelogue.layout_templates.geometry import slot_display_aspect
from travelogue.layout_templates.registry import get_engine


def solidify_screen_geometry(
    screen: dict[str, Any],
    pattern_id: str,
    *,
    assets_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write layoutGeometry + per-slot rect/displayAspect from LTE YAML.

    ``assets_map`` must be supplied so per-slot fit is re-resolved against the
    real asset (tags/person/face). Without it, ``resolve_slot_fit`` only sees a
    stub ``{"id": assetId}`` and silently downgrades person portraits from the
    face-safe ``contain`` to ``cover``.
    """
    assets_map = assets_map or {}
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
        from travelogue.layout_engine.mosaic.lte_adapter import resolve_slot_fit

        aid = slot.get("assetId")
        asset = assets_map.get(aid) if aid else None
        if asset is None and aid:
            asset = {"id": aid}
        slot["fit"] = resolve_slot_fit(
            pattern_id,
            idx,
            meta.role,
            asset or {},
        )
        # CSS-primary landscape stacks: rendered --slot-aspect follows the asset,
        # not YAML stage×rows (~3.56). Align displayAspect before crop solve.
        from travelogue.layout_engine.crop_solver import css_native_slot_aspect

        native_ar = css_native_slot_aspect(pattern_id, asset if isinstance(asset, dict) else None)
        if native_ar is not None and native_ar > 0:
            slot["displayAspect"] = round(float(native_ar), 4)

    # Person-safe cover object-position for every solidified screen (MSA re-solves
    # after track overrides when whitelisted).
    from travelogue.layout_engine.crop_solver import apply_slot_crop_focals

    apply_slot_crop_focals(screen, assets_map=assets_map)

    return screen
