"""GCS Track B · bric_compose layout (TPC W4).

Dogfood uses a deterministic shelf packer that preserves AR, enforces gutter
spacing, and never overlaps. Swap the body for MIT BRIC (pinned commit) later
without changing the call signature (D-GCS-05).
"""

from __future__ import annotations

import math
from typing import Sequence


def bric_compose(
    sizes: Sequence[tuple[float, float]],
    *,
    width: int = 1080,
    border: int = 16,
    spacing: int = 8,
    round_result: bool = True,
) -> tuple[list[tuple[float, float]], list[tuple[float, float]], tuple[float, float]]:
    """
    Pack photo sizes into a single collage canvas.

    Parameters
    ----------
    sizes:
        Native (w, h) per photo; must be length 3–9 for poster export.
    width:
        Target canvas width in px.
    border / spacing:
        Outer margin and inter-cell gutter (GCS contract defaults).

    Returns
    -------
    fitted_sizes, positions, canvas_size
        fitted_sizes: placed (w, h) per photo (same order as ``sizes``)
        positions: top-left (x, y) per photo
        canvas_size: (canvas_w, canvas_h)
    """
    n = len(sizes)
    if n == 0:
        canvas = (float(width), float(2 * border))
        return [], [], canvas

    width = max(64, int(width))
    border = max(0, int(border))
    spacing = max(0, int(spacing))
    inner_w = max(1.0, float(width - 2 * border))

    # Row plan: prefer ~sqrt(n) columns, capped 1..4
    cols = max(1, min(4, int(round(math.sqrt(n)))))
    rows_plan: list[int] = []
    remaining = n
    while remaining > 0:
        take = min(cols, remaining)
        # Prefer fuller last rows when leftover is 1 under a 3-col plan
        if remaining - take == 1 and take > 1:
            take -= 1
        rows_plan.append(take)
        remaining -= take

    fitted: list[tuple[float, float]] = [(0.0, 0.0)] * n
    positions: list[tuple[float, float]] = [(0.0, 0.0)] * n

    y = float(border)
    idx = 0
    for row_count in rows_plan:
        row_sizes = list(sizes[idx : idx + row_count])
        # Equal height for the row; widths follow AR; then scale to fill inner_w
        aspects = [max(0.05, float(w) / max(1e-6, float(h))) for w, h in row_sizes]
        # Unit height 1 → widths = aspects; sum + gutters → scale
        unit_widths = aspects
        gaps = spacing * max(0, row_count - 1)
        scale = (inner_w - gaps) / max(1e-6, sum(unit_widths))
        row_h = scale  # since unit height was 1
        x = float(border)
        for j, ar in enumerate(aspects):
            fw = ar * scale
            fh = row_h
            if round_result:
                fw, fh = round(fw), round(fh)
                x_r, y_r = round(x), round(y)
            else:
                x_r, y_r = x, y
            fitted[idx + j] = (float(fw), float(fh))
            positions[idx + j] = (float(x_r), float(y_r))
            x += fw + spacing
        y += row_h + spacing
        idx += row_count

    canvas_h = y - spacing + border if n else float(2 * border)
    if round_result:
        canvas_h = float(round(canvas_h))
    canvas = (float(width), float(max(canvas_h, 2 * border)))
    return fitted, positions, canvas
