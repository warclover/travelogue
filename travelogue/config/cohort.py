"""Cohort (featured-subject duo) configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CohortConfig:
    """Featured-subject duo tagging (face embed + layout coherence)."""

    enabled: bool = False
    match_threshold: float = 0.78
    min_face_area_ratio: float = 0.012
    l0_face_count_fallback: bool = True
    layout_weight: float = 0.06
    mosaic_weight: float = 0.05
