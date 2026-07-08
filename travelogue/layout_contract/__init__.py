"""Shared layout types and summaries (breaks curation ↔ services cycles)."""

from travelogue.layout_contract.constraints import FOCAL_EDGE_MARGIN
from travelogue.layout_contract.density import (
    LayoutDensity,
    LayoutDensityParams,
    layout_density_from_trip,
    layout_density_params,
    normalize_layout_density,
)
from travelogue.layout_contract.rhythm import (
    DEFAULT_CONSECUTIVE_BANS,
    MAX_PORTRAIT_ORIENTATION_STREAK,
    MAX_PORTRAIT_PAIR_STREAK,
    PORTRAIT_PAIR_PATTERN,
    RhythmRules,
    is_nine_grid_pattern,
    is_portrait_single_pattern,
    layout_kind_from_pattern,
    nine_grid_limits_for_trip,
    pattern_slot_count,
)
from travelogue.layout_contract.summary import (
    LAYOUT_PLAN_VERSION,
    VALID_EXPORT_LAYOUTS,
    format_layout_summary,
)

__all__ = [
    "DEFAULT_CONSECUTIVE_BANS",
    "FOCAL_EDGE_MARGIN",
    "LAYOUT_PLAN_VERSION",
    "LayoutDensity",
    "LayoutDensityParams",
    "MAX_PORTRAIT_ORIENTATION_STREAK",
    "MAX_PORTRAIT_PAIR_STREAK",
    "PORTRAIT_PAIR_PATTERN",
    "RhythmRules",
    "VALID_EXPORT_LAYOUTS",
    "format_layout_summary",
    "is_nine_grid_pattern",
    "is_portrait_single_pattern",
    "layout_density_from_trip",
    "layout_density_params",
    "layout_kind_from_pattern",
    "nine_grid_limits_for_trip",
    "normalize_layout_density",
    "pattern_slot_count",
]
