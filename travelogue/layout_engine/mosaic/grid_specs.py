"""Expected grid cell placements for mosaic / composite layout patterns.

LTE-generated data lives in ``_legacy_generated.py`` (PRD R-P16-02).
Regenerate: ``python scripts/lte_export_legacy.py --sync-python``
"""

from __future__ import annotations

from travelogue.layout_engine.mosaic._legacy_generated import (
    AUTO_FLOW_GRIDS,
    EXPLICIT_GRID_BOUNDS,
    EXPLICIT_GRID_SPECS,
    MOSAIC_3_PATTERN_IDS,
    MOSAIC_4_PATTERN_IDS,
    MOSAIC_5_PATTERN_IDS,
    MOSAIC_6_PATTERN_IDS,
    MOSAIC_8_PATTERN_IDS,
    MOSAIC_9_PATTERN_IDS,
    STACK_PATTERNS,
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

    for pid, specs in EXPLICIT_GRID_SPECS.items():
        cols, rows = EXPLICIT_GRID_BOUNDS.get(pid, (3, 3))
        gaps = gap_cells(specs, cols=cols, rows=rows)
        report[pid] = {
            "kind": "explicit",
            "slot_count": len(specs),
            "grid": f"{cols}×{rows}",
            "overlaps": overlapping_pairs(specs),
            "gap_cells": sorted(gaps),
        }

    for pid, (cols, rows, n) in AUTO_FLOW_GRIDS.items():
        report[pid] = {
            "kind": "auto_flow",
            "slot_count": n,
            "grid": f"{cols}×{rows}",
            "overlaps": [],
            "gap_cells": [],
            "note": "满格；缺图时靠 DOM 占位，错位风险已靠 render 保留 slot 缓解",
        }

    for pid in STACK_PATTERNS:
        report[pid] = {
            "kind": "stack",
            "slot_count": int(pid.split("-")[-1]),
            "grid": "1×N stack",
            "overlaps": [],
            "gap_cells": [],
            "note": "竖向堆叠，无固定宫格空位",
        }

    return report


ALL_MOSAIC_PATTERN_IDS: tuple[str, ...] = (
    *MOSAIC_3_PATTERN_IDS,
    *MOSAIC_4_PATTERN_IDS,
    *MOSAIC_5_PATTERN_IDS,
    *MOSAIC_6_PATTERN_IDS,
    *MOSAIC_8_PATTERN_IDS,
    *MOSAIC_9_PATTERN_IDS,
)
