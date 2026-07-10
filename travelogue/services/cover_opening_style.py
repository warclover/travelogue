"""Web cover opening style · thin shim over Cover Style Engine (V6).

Prefer importing from ``travelogue.cover_engine``. This module remains for
call sites that still use the V5 path names.
"""

from __future__ import annotations

from travelogue.cover_engine import (
    assignable_style_ids,
    get_default_style_id,
    is_assignable,
    resolve_cover_opening_style,
    resolve_style_id,
)

# Assignable V6 ids only (write-path truth). Not a second catalog — derived from Registry.
COVER_OPENING_STYLES: tuple[str, ...] = assignable_style_ids()


def assign_cover_opening_style(trip_id: str) -> str:
    """Create-time placeholder (D-CSV6-11/16). Hash 1:1:1 path removed in V6."""
    _ = trip_id  # retained for call-site compatibility
    return get_default_style_id()


def record_cover_opening_style_assigned(trip_id: str, style: str) -> None:
    """G-CSV-09 · log cover style once at trip create (server-side jsonl)."""
    if not is_assignable(style):
        return
    try:
        from travelogue.services.studio_homepage_telemetry import append_studio_homepage_event

        append_studio_homepage_event(
            "cover_opening_style_assigned",
            {"tripId": trip_id, "coverOpeningStyle": style},
        )
    except Exception:
        pass


__all__ = [
    "COVER_OPENING_STYLES",
    "assign_cover_opening_style",
    "record_cover_opening_style_assigned",
    "resolve_cover_opening_style",
    "resolve_style_id",
    "get_default_style_id",
    "is_assignable",
]
