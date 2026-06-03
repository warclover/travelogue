"""Stable template router reason codes (PRD §8.1)."""

from __future__ import annotations

ROUTER_REASON_CODES = (
    "R_MANUAL_OVERRIDE",
    "R_ROUTE_MULTI_DAY",
    "R_EVENT_VIDEO_HEAVY",
    "R_LOW_CONFIDENCE_FALLBACK",
    "R_TEMPLATE_DISABLED_FALLBACK",
    "R_PERSON_RATIO_HIGH",
    "R_CAPTION_EVENT_KEYWORDS",
    "R_GEO_CONTINUITY_LOW",
    "R_SHADOW_RECORD_ONLY",
)
