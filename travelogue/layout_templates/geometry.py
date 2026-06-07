"""Weighted-track slot geometry (PRD §4.3, §4.6)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from travelogue.layout_templates.models import TemplateDef, TemplateStage


@dataclass(frozen=True)
class SlotAspect:
    index: int
    display_aspect: float
    role: str


def parse_aspect_ratio(text: str) -> float:
    left, right = text.split(":", 1)
    return float(left) / float(right)


def _track_weights(stage: TemplateStage) -> tuple[tuple[float, ...], tuple[float, ...]]:
    if stage.cols and stage.rows:
        return stage.cols, stage.rows
    if stage.grid:
        cols_n, rows_n = stage.grid
        return (1.0,) * cols_n, (1.0,) * rows_n
    return (1.0, 1.0, 1.0), (1.0, 1.0, 1.0)


def slot_display_aspect(
    rect: tuple[int, int, int, int],
    stage: TemplateStage,
) -> float:
    """Display aspect (width/height) relative to template stage (§4.3)."""
    c0, c1, r0, r1 = rect
    cols, rows = _track_weights(stage)
    stage_ar = parse_aspect_ratio(stage.aspect)
    col_sum = sum(cols)
    row_sum = sum(rows)
    col_frac = sum(cols[c0 - 1 : c1]) / col_sum
    row_frac = sum(rows[r0 - 1 : r1]) / row_sum
    if row_frac <= 0:
        return stage_ar
    return (col_frac * stage_ar) / row_frac


def auto_flow_cell_aspect_ratio(
    cols: int,
    rows: int,
    *,
    stage_aspect: str = "16:9",
) -> float:
    """Uniform auto-flow cell AR (legacy slot_geometry parity)."""
    if cols <= 0 or rows <= 0:
        return parse_aspect_ratio(stage_aspect)
    stage = TemplateStage(aspect=stage_aspect, grid=(cols, rows))
    return slot_display_aspect((1, 1, 1, 1), stage)


def slot_aspect_table(template: TemplateDef) -> list[SlotAspect]:
    return [
        SlotAspect(
            index=s.index,
            display_aspect=s.display_aspect
            if s.display_aspect is not None
            else slot_display_aspect(s.rect, template.stage),
            role=s.role,
        )
        for s in template.slots
    ]


def solve_tracks(
    targets: Sequence[tuple[float, float]],
    *,
    stage_aspect: str = "16:9",
    rects: Sequence[tuple[int, int, int, int]] | None = None,
) -> tuple[list[float], list[float]]:
    """Inverse-design column/row weights (R-P16-15).

    Each target is ``(desired_display_aspect, weight)``. When ``rects`` is
    provided (one rect per target), coordinate descent minimizes weighted AR error.
    """
    if not targets:
        return [1.0, 1.0, 1.0], [1.0, 1.0, 1.0]
    if rects is None or len(rects) != len(targets):
        n = len(targets)
        cols_n = max(3, int(n**0.5) + 1)
        rows_n = max(3, (n + cols_n - 1) // cols_n)
        return [1.0] * cols_n, [1.0] * rows_n

    max_col = max(r[1] for r in rects)
    max_row = max(r[3] for r in rects)
    cols = [1.0] * max_col
    rows = [1.0] * max_row

    def _weighted_error(c: list[float], r: list[float]) -> float:
        stage = TemplateStage(aspect=stage_aspect, cols=tuple(c), rows=tuple(r))
        err = 0.0
        for rect, (target_ar, weight) in zip(rects, targets):
            if target_ar <= 0:
                continue
            got = slot_display_aspect(rect, stage)
            rel = (got - target_ar) / target_ar
            err += float(weight) * rel * rel
        return err

    best = _weighted_error(cols, rows)
    for _ in range(120):
        improved = False
        for i in range(len(cols)):
            for factor in (0.85, 0.92, 1.08, 1.15, 1.25, 1.5, 2.0):
                trial = list(cols)
                trial[i] *= factor
                err = _weighted_error(trial, rows)
                if err + 1e-9 < best:
                    cols = trial
                    best = err
                    improved = True
        for i in range(len(rows)):
            for factor in (0.85, 0.92, 1.08, 1.15, 1.25, 1.5, 2.0):
                trial = list(rows)
                trial[i] *= factor
                err = _weighted_error(cols, trial)
                if err + 1e-9 < best:
                    rows = trial
                    best = err
                    improved = True
        if not improved:
            break

    def _round_weight(w: float) -> float:
        for denom in (1, 2, 3, 4, 5, 6, 8):
            num = max(1, round(w * denom))
            return round(num / denom, 4)
        return round(w, 4)

    return [_round_weight(w) for w in cols], [_round_weight(w) for w in rows]


def legacy_slot_cell_aspect_ratio(
    spec: tuple[int, int, int, int],
    *,
    stage_aspect: float = 16 / 9,
    grid_cols: int = 3,
    grid_rows: int = 3,
) -> float:
    """Match mosaic.slot_geometry.slot_cell_aspect_ratio for uniform grids."""
    stage = TemplateStage(
        aspect=f"{stage_aspect:.0f}:9" if stage_aspect == 16 / 9 else "9:16",
        grid=(grid_cols, grid_rows),
    )
    if stage_aspect == 9 / 16:
        stage = TemplateStage(aspect="9:16", grid=(grid_cols, grid_rows))
    elif abs(stage_aspect - 16 / 9) < 0.01:
        stage = TemplateStage(aspect="16:9", grid=(grid_cols, grid_rows))
    else:
        stage = TemplateStage(aspect=f"{stage_aspect:g}:1", grid=(grid_cols, grid_rows))
    return slot_display_aspect(spec, stage)
