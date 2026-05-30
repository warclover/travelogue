"""Shared layout types and summaries (breaks curation ↔ services cycles)."""

from travelogue.layout_contract.summary import (
    LAYOUT_PLAN_VERSION,
    VALID_EXPORT_LAYOUTS,
    format_layout_summary,
)

__all__ = [
    "LAYOUT_PLAN_VERSION",
    "VALID_EXPORT_LAYOUTS",
    "format_layout_summary",
]
