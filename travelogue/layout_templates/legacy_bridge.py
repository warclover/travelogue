"""Reverse / export between LTE YAML and legacy mosaic sources (PRD §7, V-P16-11)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from travelogue.curation.mosaic.constants import (
    MOSAIC_3_PATTERN_IDS,
    MOSAIC_4_PATTERN_IDS,
    MOSAIC_5_PATTERN_IDS,
    MOSAIC_6_PATTERN_IDS,
    MOSAIC_8_PATTERN_IDS,
    MOSAIC_9_PATTERN_IDS,
    PATTERN_GRID_CLASS,
    PATTERN_MOSAIC_5_2P_3L_BALANCED,
    PATTERN_MOSAIC_5_3P_2L_BALANCED,
    PATTERN_MOSAIC_5_MAIN_LAND_2P_2L,
    PATTERN_PORTRAIT_1_LANDSCAPE_2,
)
from travelogue.curation.mosaic.grid_specs import (
    AUTO_FLOW_GRIDS,
    EXPLICIT_GRID_SPECS,
    STACK_PATTERNS,
)
from travelogue.curation.mosaic.pattern_catalog import (
    AspectProfile,
    MosaicPattern,
    default_registry,
)
from travelogue.curation.mosaic.slot_geometry import (
    _LANDSCAPE_FORBIDDEN_TALL,
    _PORTRAIT_DOMINANT_AUTO_FLOW,
    _PORTRAIT_FORBIDDEN_WIDE,
)

_DEPRECATED_IDS = frozenset(
    {
        PATTERN_MOSAIC_5_3P_2L_BALANCED,
        PATTERN_MOSAIC_5_2P_3L_BALANCED,
        PATTERN_MOSAIC_5_MAIN_LAND_2P_2L,
    }
)

_EXTRA_ROLES: dict[str, tuple[str, ...]] = {
    PATTERN_MOSAIC_5_2P_3L_BALANCED: (
        "portrait",
        "portrait",
        "portrait",
        "landscape",
        "landscape",
    ),
    PATTERN_MOSAIC_5_MAIN_LAND_2P_2L: (
        "main",
        "portrait",
        "landscape",
        "landscape",
        "landscape",
    ),
}

_PORTRAIT_STAGE = frozenset(_PORTRAIT_DOMINANT_AUTO_FLOW)


def all_legacy_pattern_ids() -> set[str]:
    ids: set[str] = set()
    ids.update(default_registry())
    ids.update(EXPLICIT_GRID_SPECS)
    ids.update(AUTO_FLOW_GRIDS)
    ids.update(STACK_PATTERNS)
    ids.update(PATTERN_GRID_CLASS)
    return ids


def legacy_lifecycle_status(pattern_id: str) -> str:
    if pattern_id in _DEPRECATED_IDS:
        return "deprecated"
    return "ga"


def legacy_kind(pattern_id: str) -> str:
    if pattern_id in STACK_PATTERNS:
        return "stack"
    if pattern_id in EXPLICIT_GRID_SPECS or "mosaic-" in pattern_id:
        return "composite"
    return "primitive"


def legacy_stage_aspect(pattern_id: str) -> str:
    if pattern_id in _PORTRAIT_STAGE:
        return "9:16"
    return "16:9"


def _grid_class(pattern_id: str) -> str:
    if pattern_id in PATTERN_GRID_CLASS:
        return PATTERN_GRID_CLASS[pattern_id]
    from travelogue.curation.screen_planner import PATTERN_GRID_CLASS as planner_classes

    return planner_classes[pattern_id]


def _roles_for(pattern_id: str) -> tuple[str, ...]:
    reg = default_registry()
    if pattern_id in reg:
        return reg[pattern_id].roles
    if pattern_id in _EXTRA_ROLES:
        return _EXTRA_ROLES[pattern_id]
    if pattern_id in AUTO_FLOW_GRIDS:
        _cols, _rows, n = AUTO_FLOW_GRIDS[pattern_id]
        if "portrait" in pattern_id and "landscape" not in pattern_id:
            return ("portrait",) * n
        if "landscape" in pattern_id:
            return ("landscape",) * n
        if pattern_id == "screen-portrait-2-landscape-2":
            return ("portrait", "landscape", "landscape", "portrait")
    if pattern_id in STACK_PATTERNS:
        n = int(pattern_id.rsplit("-", 1)[-1])
        return ("landscape",) * n
    raise KeyError(f"no role inference for {pattern_id}")


def _accepts_for(pattern_id: str, roles: tuple[str, ...]) -> AspectProfile:
    reg = default_registry()
    if pattern_id in reg:
        return reg[pattern_id].accepts
    p = sum(1 for r in roles if r == "portrait")
    n_land = sum(1 for r in roles if r in ("landscape", "main", "tile"))
    return AspectProfile(
        min_portrait=p,
        min_landscape=n_land,
        max_portrait=max(p, 9),
        max_landscape=max(n_land, 9),
    )


def _slot_count(pattern_id: str, roles: tuple[str, ...]) -> int:
    reg = default_registry()
    if pattern_id in reg:
        return reg[pattern_id].slot_count
    if pattern_id in EXPLICIT_GRID_SPECS:
        return len(EXPLICIT_GRID_SPECS[pattern_id])
    if pattern_id in AUTO_FLOW_GRIDS:
        return AUTO_FLOW_GRIDS[pattern_id][2]
    if pattern_id in STACK_PATTERNS:
        return int(pattern_id.rsplit("-", 1)[-1])
    return len(roles)


def _explicit_grid_size(pattern_id: str) -> tuple[int, int]:
    if "portrait-1-landscape" in pattern_id:
        return 2, 2
    return 3, 3


def _stage_grid(pattern_id: str) -> dict[str, Any]:
    if pattern_id == PATTERN_PORTRAIT_1_LANDSCAPE_2:
        return {"aspect": "16:9", "cols": [1, 2], "rows": [1, 1]}
    if pattern_id in EXPLICIT_GRID_SPECS:
        cols, rows = _explicit_grid_size(pattern_id)
        return {"aspect": legacy_stage_aspect(pattern_id), "grid": [cols, rows]}
    if pattern_id in AUTO_FLOW_GRIDS:
        cols, rows, _n = AUTO_FLOW_GRIDS[pattern_id]
        return {"aspect": legacy_stage_aspect(pattern_id), "grid": [cols, rows]}
    if pattern_id in STACK_PATTERNS:
        n = int(pattern_id.rsplit("-", 1)[-1])
        return {"aspect": legacy_stage_aspect(pattern_id), "cols": [1], "rows": [1] * n}
    cols, rows = 3, 3
    return {"aspect": legacy_stage_aspect(pattern_id), "grid": [cols, rows]}


def _slots_yaml(pattern_id: str, roles: tuple[str, ...]) -> list[dict[str, Any]]:
    specs = EXPLICIT_GRID_SPECS.get(pattern_id)
    if specs:
        return [
            {
                "index": i,
                "rect": [c0, c1, r0, r1],
                "role": roles[i],
                "fit": "auto" if roles[i] in ("portrait", "main") else "cover",
            }
            for i, (c0, c1, r0, r1) in enumerate(specs)
        ]
    if pattern_id in AUTO_FLOW_GRIDS:
        cols, rows, n = AUTO_FLOW_GRIDS[pattern_id]
        slots: list[dict[str, Any]] = []
        for i in range(n):
            col = (i % cols) + 1
            row = (i // cols) + 1
            slots.append(
                {
                    "index": i,
                    "rect": [col, col, row, row],
                    "role": roles[i],
                    "fit": "auto" if roles[i] == "portrait" else "cover",
                }
            )
        return slots
    if pattern_id in STACK_PATTERNS:
        return [
            {
                "index": i,
                "rect": [1, 1, i + 1, i + 1],
                "role": roles[i],
                "fit": "cover",
            }
            for i in range(len(roles))
        ]
    raise KeyError(pattern_id)


def _mix_counts(roles: tuple[str, ...]) -> dict[str, int]:
    return {
        "portrait": sum(1 for r in roles if r == "portrait"),
        "landscape": sum(1 for r in roles if r in ("landscape", "main", "tile")),
    }


def _constraints_yaml(pattern_id: str) -> dict[str, Any]:
    wide = sorted(_PORTRAIT_FORBIDDEN_WIDE.get(pattern_id, frozenset()))
    tall = sorted(_LANDSCAPE_FORBIDDEN_TALL.get(pattern_id, frozenset()))
    return {
        "portrait_forbidden_in_wide_slots": wide,
        "landscape_forbidden_in_tall_slots": tall,
        "intentionalGaps": [],
    }


def _display_name(pattern_id: str) -> str:
    return pattern_id.removeprefix("screen-").replace("-", " · ")


def reverse_pattern_to_yaml_dict(pattern_id: str) -> dict[str, Any]:
    """Build authoritative YAML document for one legacy pattern."""
    roles = _roles_for(pattern_id)
    n = _slot_count(pattern_id, roles)
    accepts = _accepts_for(pattern_id, roles)
    doc: dict[str, Any] = {
        "id": pattern_id,
        "version": 1,
        "status": legacy_lifecycle_status(pattern_id),
        "kind": legacy_kind(pattern_id),
        "displayName": _display_name(pattern_id),
        "description": "Reverse-migrated from legacy mosaic sources (Phase 16 W1).",
        "stage": _stage_grid(pattern_id),
        "photoCount": {"min": n, "max": n},
        "mix": _mix_counts(roles),
        "slots": _slots_yaml(pattern_id, roles),
        "constraints": _constraints_yaml(pattern_id),
        "scoring": {
            "base_weight": 1.0,
            "tags": [],
        },
        "render": {
            "gridClass": _grid_class(pattern_id),
            "cssBundle": "journal-screens.css",
            "fitPolicy": "auto_delegate",
        },
        "_legacy": {
            "accepts": asdict(accepts),
            "css_verified": pattern_id in default_registry()
            and default_registry()[pattern_id].css_verified,
        },
    }
    return doc


def export_mosaic_pattern(template: Any) -> MosaicPattern:
    """TemplateDef → MosaicPattern for parity with default_registry()."""
    from travelogue.layout_templates.models import TemplateDef

    assert isinstance(template, TemplateDef)
    roles = tuple(s.role for s in template.slots)
    legacy = template.raw.get("_legacy", {})
    accepts_raw = legacy.get("accepts")
    if accepts_raw:
        accepts = AspectProfile(**accepts_raw)
    else:
        accepts = _accepts_for(template.id, roles)
    css_verified = bool(legacy.get("css_verified", True))
    return MosaicPattern(
        pattern_id=template.id,
        slot_count=len(template.slots),
        grid_class=template.render_grid_class,
        roles=roles,
        accepts=accepts,
        css_verified=css_verified,
    )


def export_explicit_grid_specs(templates: dict[str, Any]) -> dict[str, list[tuple[int, int, int, int]]]:
    out: dict[str, list[tuple[int, int, int, int]]] = {}
    for tid, t in templates.items():
        if t.kind != "composite":
            continue
        out[tid] = [tuple(s.rect) for s in t.slots]
    return out


def export_auto_flow_grids(templates: dict[str, Any]) -> dict[str, tuple[int, int, int]]:
    out: dict[str, tuple[int, int, int]] = {}
    for tid, t in templates.items():
        if t.kind != "primitive" or not t.stage.grid:
            continue
        cols, rows = t.stage.grid
        out[tid] = (cols, rows, len(t.slots))
    return out


def export_stack_patterns(templates: dict[str, Any]) -> frozenset[str]:
    return frozenset(tid for tid, t in templates.items() if t.kind == "stack")


def export_pattern_grid_class(templates: dict[str, Any]) -> dict[str, str]:
    from travelogue.curation.mosaic.constants import PATTERN_GRID_CLASS

    return {
        tid: templates[tid].render_grid_class
        for tid in PATTERN_GRID_CLASS
        if tid in templates
    }


def export_forbidden_maps(templates: dict[str, Any]) -> tuple[dict[str, frozenset[int]], dict[str, frozenset[int]]]:
    wide: dict[str, frozenset[int]] = {}
    tall: dict[str, frozenset[int]] = {}
    for tid, t in templates.items():
        c = t.constraints or {}
        w = c.get("portrait_forbidden_in_wide_slots") or []
        h = c.get("landscape_forbidden_in_tall_slots") or []
        if w:
            wide[tid] = frozenset(int(x) for x in w)
        if h:
            tall[tid] = frozenset(int(x) for x in h)
    return wide, tall


def mosaic_pattern_id_groups() -> dict[str, tuple[str, ...]]:
    from travelogue.layout_templates.mosaic_groups import build_mosaic_unified_groups
    from travelogue.layout_templates.registry import get_engine

    return build_mosaic_unified_groups(get_engine())
