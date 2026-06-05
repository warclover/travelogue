"""Expected grid cell placements for mosaic / composite layout patterns.

Used by tests to detect slot overlap and unintended empty cells on fixed grids.
Auto-flow grids (3col, 2x2, 3x2, 3x3, portrait-2x4) rely on DOM order; they
fill completely when every slot renders (see build_layout_screen slot retention).
"""

from __future__ import annotations

from travelogue.curation.mosaic.constants import (
    MOSAIC_3_PATTERN_IDS,
    MOSAIC_4_PATTERN_IDS,
    MOSAIC_5_PATTERN_IDS,
    MOSAIC_6_PATTERN_IDS,
    MOSAIC_8_PATTERN_IDS,
    MOSAIC_9_PATTERN_IDS,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
    PATTERN_PORTRAIT_1_LANDSCAPE_2,
)

# (col_start, col_end, row_start, row_end) — 1-based inclusive
EXPLICIT_GRID_SPECS: dict[str, list[tuple[int, int, int, int]]] = {
    "screen-mosaic-5-main-portrait-3land": [
        (1, 2, 1, 2),
        (3, 3, 1, 2),
        (1, 1, 3, 3),
        (2, 2, 3, 3),
        (3, 3, 3, 3),
    ],
    "screen-mosaic-5-main-landscape-2portrait-2land": [
        (1, 2, 1, 2),
        (3, 3, 1, 2),
        (1, 1, 3, 3),
        (2, 2, 3, 3),
        (3, 3, 3, 3),
    ],
    "screen-mosaic-5-2portrait-3land-balanced": [
        (1, 1, 1, 1),
        (2, 2, 1, 1),
        (1, 1, 2, 3),
        (2, 2, 2, 2),
        (2, 3, 3, 3),
    ],
    "screen-mosaic-5-3portrait-2land-balanced": [
        (1, 1, 1, 2),
        (2, 2, 1, 2),
        (3, 3, 1, 2),
        (1, 2, 3, 3),
        (3, 3, 3, 3),
    ],
    "screen-mosaic-5-main-hero-plus-4": [
        (1, 2, 1, 2),
        (3, 3, 1, 1),
        (3, 3, 2, 2),
        (1, 1, 3, 3),
        (2, 2, 3, 3),
        (3, 3, 3, 3),
    ],
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5: [
        (1, 2, 1, 2),
        (3, 3, 1, 1),
        (3, 3, 2, 2),
        (1, 1, 3, 3),
        (2, 2, 3, 3),
        (3, 3, 3, 3),
    ],
    PATTERN_PORTRAIT_1_LANDSCAPE_2: [
        (1, 1, 1, 2),
        (2, 2, 1, 1),
        (2, 2, 2, 2),
    ],
}

# cols × rows — slots fill left-to-right, top-to-bottom in DOM order
AUTO_FLOW_GRIDS: dict[str, tuple[int, int, int]] = {
    # pattern_id -> (cols, rows, slot_count)
    "screen-portrait-3": (3, 1, 3),
    "screen-portrait-4": (2, 2, 4),
    "screen-portrait-6": (3, 2, 6),
    "screen-portrait-9": (3, 3, 9),
    "screen-landscape-4": (2, 2, 4),
    "screen-landscape-6": (3, 2, 6),
    "screen-landscape-9": (3, 3, 9),
    "screen-portrait-2-landscape-2": (2, 2, 4),
    "screen-portrait-grid-8": (4, 2, 8),
}

# Single-column stacks — no fixed cell grid; height follows aspect ratios
STACK_PATTERNS: frozenset[str] = frozenset(
    {
        "screen-landscape-2",
        "screen-landscape-3",
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

    for pid, specs in EXPLICIT_GRID_SPECS.items():
        cols = 3 if "portrait-1-landscape" not in pid else 2
        rows = 3 if "portrait-1-landscape" not in pid else 2
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
