"""Expected grid cell placements for mosaic / composite layout patterns.

Runtime data resolves through ``legacy_specs`` (LTE YAML when enabled).
CI snapshot: ``_legacy_generated.py`` — ``python scripts/lte_export_legacy.py --sync-python``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from travelogue.curation.mosaic.legacy_specs import (
    auto_flow_grids,
    explicit_grid_bounds,
    explicit_grid_specs,
    mosaic_pattern_id_groups,
    mosaic_unified_pattern_ids,
    stack_patterns,
)

_LAZY_EXPORTS: dict[str, Callable[[], Any]] = {
    "EXPLICIT_GRID_SPECS": explicit_grid_specs,
    "EXPLICIT_GRID_BOUNDS": explicit_grid_bounds,
    "AUTO_FLOW_GRIDS": auto_flow_grids,
    "STACK_PATTERNS": stack_patterns,
    "MOSAIC_3_PATTERN_IDS": lambda: mosaic_pattern_id_groups()["MOSAIC_3_PATTERN_IDS"],
    "MOSAIC_4_PATTERN_IDS": lambda: mosaic_pattern_id_groups()["MOSAIC_4_PATTERN_IDS"],
    "MOSAIC_5_PATTERN_IDS": lambda: mosaic_pattern_id_groups()["MOSAIC_5_PATTERN_IDS"],
    "MOSAIC_6_PATTERN_IDS": lambda: mosaic_pattern_id_groups()["MOSAIC_6_PATTERN_IDS"],
    "MOSAIC_8_PATTERN_IDS": lambda: mosaic_pattern_id_groups()["MOSAIC_8_PATTERN_IDS"],
    "MOSAIC_9_PATTERN_IDS": lambda: mosaic_pattern_id_groups()["MOSAIC_9_PATTERN_IDS"],
    "ALL_MOSAIC_PATTERN_IDS": mosaic_unified_pattern_ids,
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_EXPORTS:
        return _LAZY_EXPORTS[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(
        set(_LAZY_EXPORTS.keys())
        | {
            "cells_for_spec",
            "cells_for_specs",
            "gap_cells",
            "overlapping_pairs",
            "audit_all",
        }
    )


def cells_for_spec(spec: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    c0, c1, r0, r1 = spec
    return {(c, r) for c in range(c0, c1 + 1) for r in range(r0, r1 + 1)}


def cells_for_specs(specs: list[tuple[int, int, int, int]]) -> set[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    for spec in specs:
        out |= cells_for_spec(spec)
    return out


def gap_cells(
    specs: list[tuple[int, int, int, int]],
    *,
    cols: int = 3,
    rows: int = 3,
) -> set[tuple[int, int]]:
    stage = {(c, r) for c in range(1, cols + 1) for r in range(1, rows + 1)}
    return stage - cells_for_specs(specs)


def overlapping_pairs(
    specs: list[tuple[int, int, int, int]],
) -> list[tuple[int, int]]:
    hits: list[tuple[int, int]] = []
    for i, a in enumerate(specs):
        for j, b in enumerate(specs[i + 1 :], start=i + 1):
            if cells_for_spec(a) & cells_for_spec(b):
                hits.append((i, j))
    return hits


def audit_all() -> dict[str, dict]:
    """Return audit summary keyed by pattern id."""
    report: dict[str, dict] = {}
    explicit = explicit_grid_specs()
    bounds = explicit_grid_bounds()
    auto_flow = auto_flow_grids()
    stacks = stack_patterns()

    for pid, specs in explicit.items():
        cols, rows = bounds.get(pid, (3, 3))
        gaps = gap_cells(specs, cols=cols, rows=rows)
        report[pid] = {
            "kind": "explicit",
            "slot_count": len(specs),
            "grid": f"{cols}×{rows}",
            "overlaps": overlapping_pairs(specs),
            "gap_cells": sorted(gaps),
        }

    for pid, (cols, rows, n) in auto_flow.items():
        report[pid] = {
            "kind": "auto_flow",
            "slot_count": n,
            "grid": f"{cols}×{rows}",
            "overlaps": [],
            "gap_cells": [],
            "note": "满格；缺图时靠 DOM 占位，错位风险已靠 render 保留 slot 缓解",
        }

    for pid in stacks:
        report[pid] = {
            "kind": "stack",
            "slot_count": int(pid.split("-")[-1]),
            "grid": "1×N stack",
            "overlaps": [],
            "gap_cells": [],
            "note": "竖向堆叠，无固定宫格空位",
        }

    return report
