"""Template summary for Studio API."""

from __future__ import annotations

from travelogue.templating.router import apply_template_selection
from travelogue.templating.summary import build_template_summary, template_source_kind


def test_legacy_trip_summary() -> None:
    trip = {"templateId": "visual-journal"}
    s = build_template_summary(trip)
    assert s["source"] == "legacy"
    assert s["resolvedTemplateId"] == "visual-journal"
    assert s["locked"] is False


def test_smart_trip_summary() -> None:
    trip = {"meta": {"dateStart": "2026-01-01", "dateEnd": "2026-01-01", "places": ["A"]}}
    apply_template_selection(trip, mode="smart")
    assert template_source_kind(trip) == "smart"
    s = build_template_summary(trip)
    assert s["source"] == "smart"
    assert s["feedbackMessage"]


def test_locked_copy_pipeline() -> None:
    trip = {
        "templateSelection": {"mode": "manual", "resolvedTemplateId": "visual-journal", "locked": False},
        "pipeline": {"locks": {"copy": True}},
    }
    s = build_template_summary(trip)
    assert s["locked"] is True
