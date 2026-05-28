"""Trip JSON load-time migrations (Phase 3 M14)."""

from __future__ import annotations


def strip_legacy_curation_fields(trip: dict) -> dict:
    """Remove deprecated curation.insights (ADR-007 · PRD §11)."""
    curation = trip.get("curation")
    if isinstance(curation, dict) and "insights" in curation:
        cleaned = dict(curation)
        cleaned.pop("insights", None)
        trip["curation"] = cleaned
    return trip
