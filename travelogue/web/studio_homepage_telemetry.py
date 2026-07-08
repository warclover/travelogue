"""Local Studio homepage funnel events (web re-export shim)."""

from __future__ import annotations

from travelogue.services.studio_homepage_telemetry import (
    ALLOWED_STUDIO_HOMEPAGE_EVENTS,
    MAX_META_BYTES,
    append_studio_homepage_event,
    studio_homepage_events_path,
)

__all__ = [
    "ALLOWED_STUDIO_HOMEPAGE_EVENTS",
    "MAX_META_BYTES",
    "append_studio_homepage_event",
    "studio_homepage_events_path",
]
