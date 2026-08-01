"""GCS Track B · bric_compose layout (TPC W4).

Uses vendored MIT BRIC (stefanwayon/collage @ pinned commit) when available.
Falls back to a deterministic shelf packer if the vendor import fails.
Call signature stays stable (D-GCS-05).
"""

from __future__ import annotations

import logging
import math
from collections.abc import Sequence

_log = logging.getLogger(__name__)


def _shelf_compose(
    sizes: Sequence[tuple[float, float]],
    *,
    width: int,
    border: int,
    spacing: int,
    round_result: bool,
) -> tuple[list[tuple[float, float]], list[tuple[float, float]], tuple[float, float]]:
    n = len(sizes)
    if n == 0:
        canvas = (float(width), float(2 * border))
        return [], [], canvas

    width = max(64, int(width))
    border = max(0, int(border))
    spacing = max(0, int(spacing))
    inner_w = max(1.0, float(width - 2 * border))

    cols = max(1, min(4, int(round(math.sqrt(n)))))
    rows_plan: list[int] = []
    remaining = n
    while remaining > 0:
        take = min(cols, remaining)
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
        aspects = [max(0.05, float(w) / max(1e-6, float(h))) for w, h in row_sizes]
        unit_widths = aspects
        gaps = spacing * max(0, row_count - 1)
        scale = (inner_w - gaps) / max(1e-6, sum(unit_widths))
        row_h = scale
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


def _bric_vendor_compose(
    sizes: Sequence[tuple[float, float]],
    *,
    width: int,
    border: int,
    spacing: int,
    round_result: bool,
) -> tuple[list[tuple[float, float]], list[tuple[float, float]], tuple[float, float]]:
    """Call vendored fit_pictures_balanced (float path; round locally)."""
    from travelogue.export._vendor.collage import fit_pictures_balanced

    # Upstream integer path pulls python-mip; keep float solve + local round.
    fitted_raw, positions_raw, canvas_raw = fit_pictures_balanced(
        list(sizes),
        layout="horizontal",
        width=width,
        border=border,
        spacing=spacing,
        round_result=False,
    )
    fitted: list[tuple[float, float]] = []
    positions: list[tuple[float, float]] = []
    for (fw, fh), (x, y) in zip(fitted_raw, positions_raw, strict=True):
        if round_result:
            fitted.append((float(round(fw)), float(round(fh))))
            positions.append((float(round(x)), float(round(y))))
        else:
            fitted.append((float(fw), float(fh)))
            positions.append((float(x), float(y)))
    cw, ch = canvas_raw
    if round_result:
        canvas = (float(round(cw)), float(round(ch)))
    else:
        canvas = (float(cw), float(ch))
    return fitted, positions, canvas


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

    try:
        return _bric_vendor_compose(
            sizes,
            width=width,
            border=border,
            spacing=spacing,
            round_result=round_result,
        )
    except Exception:
        _log.debug("bric vendor compose failed; using shelf packer", exc_info=True)
        return _shelf_compose(
            sizes,
            width=width,
            border=border,
            spacing=spacing,
            round_result=round_result,
        )
