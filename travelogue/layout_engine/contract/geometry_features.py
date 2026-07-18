"""TPC · raw geometric features for decision log (AC-TPC-10 / MGQ BLK-13).

Record-only: never used as soft penalties in TPC V1 (D-TPC-05).
Area口径 = col_frac × row_frac using weighted tracks (MGQ BLK-09 /
``layout_templates.geometry``).
"""

from __future__ import annotations

import math
import statistics
from typing import Any


def _slot_area_frac(rect: tuple[int, int, int, int], stage: Any) -> float | None:
    from travelogue.layout_templates.geometry import _track_weights

    c0, c1, r0, r1 = rect
    cols, rows = _track_weights(stage)
    col_sum = sum(cols)
    row_sum = sum(rows)
    if col_sum <= 0 or row_sum <= 0:
        return None
    col_frac = sum(cols[c0 - 1 : c1]) / col_sum
    row_frac = sum(rows[r0 - 1 : r1]) / row_sum
    return float(col_frac * row_frac)


def compute_raw_geometry_features(pattern_id: str) -> dict[str, float | None]:
    """Return heroProminenceRatio / heroCoverageRatio / cellAreaCv (None = skipped)."""
    empty: dict[str, float | None] = {
        "heroProminenceRatio": None,
        "heroCoverageRatio": None,
        "cellAreaCv": None,
    }
    try:
        from travelogue.layout_templates.registry import get_engine

        template = get_engine().get(pattern_id)
    except (KeyError, AttributeError, TypeError):
        return empty

    stage = getattr(template, "stage", None)
    if stage is None:
        return empty
    slots = list(template.slots or [])
    if not slots:
        return empty

    areas: list[tuple[str, float]] = []
    for slot in slots:
        rect = getattr(slot, "rect", None)
        if not rect or len(rect) != 4:
            continue
        area = _slot_area_frac(
            (int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])), stage
        )
        if area is None:
            continue
        role = str(getattr(slot, "role", "") or "").lower()
        areas.append((role, area))

    if not areas:
        return empty

    main_areas = [a for role, a in areas if role == "main"]
    content_areas = [a for role, a in areas if role != "main"]
    hero_prominence: float | None = None
    hero_coverage: float | None = None
    if main_areas:
        hero = max(main_areas)
        hero_coverage = float(hero)
        if content_areas:
            hero_prominence = float(hero / max(content_areas))

    cell_cv: float | None = None
    if len(content_areas) >= 3:
        mean = statistics.fmean(content_areas)
        if mean > 1e-12:
            var = statistics.pvariance(content_areas)
            cell_cv = float(math.sqrt(var) / mean)

    return {
        "heroProminenceRatio": (
            round(hero_prominence, 6) if hero_prominence is not None else None
        ),
        "heroCoverageRatio": (
            round(hero_coverage, 6) if hero_coverage is not None else None
        ),
        "cellAreaCv": round(cell_cv, 6) if cell_cv is not None else None,
    }
