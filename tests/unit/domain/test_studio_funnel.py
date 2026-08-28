"""MET-01 · four-stage funnel mapping and baseline export."""

from __future__ import annotations

import pytest

from travelogue.domain.studio_events import ALLOWED_STUDIO_HOMEPAGE_EVENTS
from travelogue.domain.studio_funnel import (
    FIRST_PREVIEW,
    FUNNEL_FIRST_PREVIEW_EVENT,
    FUNNEL_META_DENY,
    FUNNEL_STAGES,
    WIZARD_PREVIEW_EVENT,
    build_funnel_baseline,
    format_funnel_baseline,
    sanitize_funnel_meta,
)


def test_four_stages_and_preview_is_not_wizard_thumbs() -> None:
    assert [stage.id for stage in FUNNEL_STAGES] == [
        "home_enter",
        "import_success",
        "first_preview",
        "first_export",
    ]
    preview = next(stage for stage in FUNNEL_STAGES if stage.id == FIRST_PREVIEW)
    assert FUNNEL_FIRST_PREVIEW_EVENT in preview.events
    assert WIZARD_PREVIEW_EVENT not in preview.events
    assert WIZARD_PREVIEW_EVENT not in preview.historical_proxy
    assert FUNNEL_FIRST_PREVIEW_EVENT in ALLOWED_STUDIO_HOMEPAGE_EVENTS


def test_sanitize_funnel_meta_drops_content_fields() -> None:
    cleaned = sanitize_funnel_meta(
        {
            "tripId": "kyoto-2026",
            "edition": "journal",
            "source": "preview_toolbar",
            "path": "C:/Users/me/photos",
            "filename": "IMG_0001.jpg",
            "displayTitle": "京都",
            "caption": "夜景",
        }
    )
    assert cleaned == {
        "tripId": "kyoto-2026",
        "edition": "journal",
        "source": "preview_toolbar",
    }
    for key in FUNNEL_META_DENY:
        assert key not in cleaned


def test_baseline_uses_first_per_trip_and_ignores_wizard_preview() -> None:
    events = [
        {"ts": "2026-08-01T10:00:00+00:00", "event": "homepage_view"},
        {"ts": "2026-08-01T10:01:00+00:00", "event": "homepage_view"},
        {
            "ts": "2026-08-01T10:05:00+00:00",
            "event": "import_success",
            "meta": {"tripId": "trip-a"},
        },
        {
            "ts": "2026-08-01T10:06:00+00:00",
            "event": "preview_loaded",
            "meta": {"tripId": "trip-a"},
        },
        {
            "ts": "2026-08-01T10:20:00+00:00",
            "event": "funnel_first_preview",
            "meta": {"tripId": "trip-a", "edition": "journal"},
        },
        {
            "ts": "2026-08-01T10:21:00+00:00",
            "event": "funnel_first_preview",
            "meta": {"tripId": "trip-a", "edition": "journal"},
        },
        {
            "ts": "2026-08-01T10:40:00+00:00",
            "event": "longshot_export_success",
            "meta": {"tripId": "trip-a"},
        },
    ]
    baseline = build_funnel_baseline(events)
    by_id = {stage.id: stage for stage in baseline.stages}
    assert by_id["home_enter"].event_count == 2
    assert by_id["import_success"].unique_trips == 1
    assert by_id["first_preview"].unique_trips == 1
    assert by_id["first_preview"].event_count == 2
    assert by_id["first_preview"].source == "canonical"
    assert by_id["first_preview"].median_seconds_from_prev == pytest.approx(15 * 60)
    assert by_id["first_export"].unique_trips == 1
    assert by_id["first_export"].median_seconds_from_prev == pytest.approx(20 * 60)


def test_baseline_falls_back_to_historical_preview_proxy() -> None:
    events = [
        {"ts": "2026-07-01T09:00:00+00:00", "event": "homepage_view"},
        {
            "ts": "2026-07-01T09:10:00+00:00",
            "event": "import_success",
            "meta": {"tripId": "trip-b"},
        },
        {
            "ts": "2026-07-01T09:12:00+00:00",
            "event": "cover_opening_style_render",
            "meta": {"tripId": "trip-b"},
        },
    ]
    baseline = build_funnel_baseline(events)
    preview = next(stage for stage in baseline.stages if stage.id == FIRST_PREVIEW)
    assert preview.unique_trips == 1
    assert preview.source == "historical_proxy"


def test_baseline_excludes_explicit_portfolio_trips() -> None:
    events = [
        {
            "ts": "2026-08-01T10:05:00+00:00",
            "event": "import_success",
            "meta": {"tripId": "folio-1", "edition": "portfolio"},
        },
        {
            "ts": "2026-08-01T10:06:00+00:00",
            "event": "funnel_first_preview",
            "meta": {"tripId": "folio-1", "edition": "portfolio"},
        },
        {
            "ts": "2026-08-01T10:07:00+00:00",
            "event": "import_success",
            "meta": {"tripId": "journal-1", "edition": "journal"},
        },
    ]
    baseline = build_funnel_baseline(events)
    imported = next(stage for stage in baseline.stages if stage.id == "import_success")
    assert imported.unique_trips == 1


def test_format_funnel_baseline_has_no_content_fields() -> None:
    text = format_funnel_baseline(
        build_funnel_baseline([{"ts": "2026-08-01T00:00:00+00:00", "event": "homepage_view"}]),
        source_path="~/.travelogue/telemetry/studio-homepage-events.jsonl",
    )
    assert "home_enter" in text
    assert "first_preview" in text
    assert "IMG_" not in text
    assert "C:/" not in text
    assert "分享图" not in text
