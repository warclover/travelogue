"""Layout CSS stale detection (AC-P16-11)."""

from __future__ import annotations

import pytest

from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_5_2P3L_EQUAL
from travelogue.layout_templates.css_stale import (
    required_grid_classes_from_trip,
    trip_css_import_stale,
    trip_layout_css_stale,
    trip_render_bundle_stale,
)


@pytest.mark.unit
def test_required_grid_classes_prefers_layout_geometry() -> None:
    data = {
        "chapters": [
            {
                "screens": [
                    {
                        "patternId": PATTERN_MOSAIC_5_2P3L_EQUAL,
                        "layoutGeometry": {"gridClass": "layout-screen__grid--mosaic-5-2p3l-equal"},
                    }
                ]
            }
        ]
    }
    classes = required_grid_classes_from_trip(data)
    assert "layout-screen__grid--mosaic-5-2p3l-equal" in classes


@pytest.mark.unit
def test_trip_layout_css_stale_when_class_missing(tmp_path) -> None:
    trip_dir = tmp_path / "demo"
    trip_dir.mkdir()
    data = {
        "chapters": [
            {
                "screens": [
                    {
                        "patternId": PATTERN_MOSAIC_5_2P3L_EQUAL,
                        "layoutGeometry": {"gridClass": "layout-screen__grid--mosaic-5-2p3l-equal"},
                    }
                ]
            }
        ]
    }
    (trip_dir / "trip.json").write_text("{}", encoding="utf-8")
    (trip_dir / "journal-screens.css").write_text(".layout-screen__grid--3col {}", encoding="utf-8")
    assert trip_layout_css_stale(trip_dir, data) is True


@pytest.mark.unit
def test_trip_css_import_stale_when_portfolio_points_at_journal(tmp_path) -> None:
    trip_dir = tmp_path / "demo"
    trip_dir.mkdir()
    (trip_dir / "journal.css").write_text('@import url("journal-screens.css");\n', encoding="utf-8")
    data = {"studio": {"edition": "portfolio"}}
    assert trip_css_import_stale(trip_dir, data) is True
    assert trip_layout_css_stale(trip_dir, data) is True


@pytest.mark.unit
def test_trip_css_import_fresh_when_portfolio_loads_own_file(tmp_path) -> None:
    trip_dir = tmp_path / "demo"
    trip_dir.mkdir()
    (trip_dir / "journal.css").write_text('@import url("portfolio-pages.css?v=ls1");\n', encoding="utf-8")
    (trip_dir / "portfolio-pages.css").write_text("/* pages */\n", encoding="utf-8")
    data = {
        "studio": {"edition": "portfolio"},
        "chapters": [
            {
                "screens": [
                    {
                        "patternId": "page-1-hero-port",
                        "layoutGeometry": {"cols": [1], "rows": [1], "gridClass": "x"},
                    }
                ]
            }
        ],
    }
    assert trip_css_import_stale(trip_dir, data) is False
    assert trip_layout_css_stale(trip_dir, data) is False


@pytest.mark.unit
def test_trip_layout_css_not_stale_without_local_copy(tmp_path) -> None:
    trip_dir = tmp_path / "demo"
    trip_dir.mkdir()
    data = {
        "chapters": [
            {
                "screens": [
                    {"patternId": "screen-portrait-3"},
                ]
            }
        ]
    }
    assert trip_layout_css_stale(trip_dir, data) is False


@pytest.mark.unit
def test_trip_render_bundle_stale_when_index_older_than_trip_json(tmp_path) -> None:
    import time

    trip_dir = tmp_path / "demo"
    trip_dir.mkdir()
    trip_json = trip_dir / "trip.json"
    index_html = trip_dir / "index.html"
    trip_json.write_text('{"tripId":"demo","updatedAt":"2099-01-01T00:00:00Z"}', encoding="utf-8")
    index_html.write_text("<html></html>", encoding="utf-8")
    past = time.time() - 3600
    import os

    os.utime(index_html, (past, past))
    data = {"tripId": "demo", "updatedAt": "2099-01-01T00:00:00Z"}
    assert trip_render_bundle_stale(trip_dir, data) is True


@pytest.mark.unit
def test_trip_render_bundle_not_stale_when_index_newer(tmp_path) -> None:
    trip_dir = tmp_path / "demo"
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text('{"tripId":"demo"}', encoding="utf-8")
    (trip_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    assert trip_render_bundle_stale(trip_dir, {"tripId": "demo"}) is False


@pytest.mark.unit
def test_trip_render_bundle_not_stale_after_post_render_metadata_persist(tmp_path) -> None:
    """Creating a trip writes index.html then persists timings — must not false-positive."""
    from travelogue.services.trip import TripService, mark_render_bundle_current, meta_revision

    trip_dir = tmp_path / "demo"
    trip_dir.mkdir()
    trip_json = trip_dir / "trip.json"
    index_html = trip_dir / "index.html"
    svc = TripService()
    trip = {"tripId": "demo", "meta": {"revision": 0}, "pipeline": {"timings": {}}}
    svc.save(trip, trip_json)
    index_html.write_text("<html></html>", encoding="utf-8")

    def after_render(t: dict) -> None:
        mark_render_bundle_current(t)

    svc.update(trip_json, after_render)
    rendered = svc.load(trip_json)
    assert meta_revision(rendered) == 1
    assert rendered["meta"]["renderedRevision"] == 1
    assert trip_render_bundle_stale(trip_dir, rendered) is False

    def timings_only(t: dict) -> None:
        t.setdefault("pipeline", {})["timings"] = {"renderMs": 12.0, "totalMs": 99.0}
        mark_render_bundle_current(t)

    svc.update(trip_json, timings_only)
    after = svc.load(trip_json)
    assert meta_revision(after) == 2
    assert after["meta"]["renderedRevision"] == 2
    assert trip_render_bundle_stale(trip_dir, after) is False


@pytest.mark.unit
def test_mark_render_bundle_current_if_fresh_preserves_fresh_preview(tmp_path) -> None:
    from travelogue.services.trip import (
        TripService,
        mark_render_bundle_current,
        mark_render_bundle_current_if_fresh,
        meta_revision,
    )

    trip_dir = tmp_path / "demo"
    trip_dir.mkdir()
    trip_json = trip_dir / "trip.json"
    (trip_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    svc = TripService()
    svc.save({"tripId": "demo", "meta": {"revision": 0}}, trip_json)
    svc.update(trip_json, mark_render_bundle_current)
    assert trip_render_bundle_stale(trip_dir, svc.load(trip_json)) is False

    def telemetry(t: dict) -> None:
        t.setdefault("curation", {})["copyMetrics"] = {"clientEventCounts": {"preview_open": 1}}
        mark_render_bundle_current_if_fresh(t, trip_dir)

    svc.update(trip_json, telemetry)
    after = svc.load(trip_json)
    assert meta_revision(after) == 2
    assert after["meta"]["renderedRevision"] == 2
    assert trip_render_bundle_stale(trip_dir, after) is False


@pytest.mark.unit
def test_mark_render_bundle_current_if_fresh_skips_when_already_stale(tmp_path) -> None:
    from travelogue.services.trip import (
        TripService,
        mark_render_bundle_current_if_fresh,
        meta_revision,
    )

    trip_dir = tmp_path / "demo"
    trip_dir.mkdir()
    trip_json = trip_dir / "trip.json"
    (trip_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    svc = TripService()
    svc.save(
        {"tripId": "demo", "meta": {"revision": 5, "renderedRevision": 2}},
        trip_json,
    )
    assert trip_render_bundle_stale(trip_dir, svc.load(trip_json)) is True

    def telemetry(t: dict) -> None:
        mark_render_bundle_current_if_fresh(t, trip_dir)

    svc.update(trip_json, telemetry)
    after = svc.load(trip_json)
    assert meta_revision(after) == 6
    assert after["meta"]["renderedRevision"] == 2
    assert trip_render_bundle_stale(trip_dir, after) is True


@pytest.mark.unit
def test_trip_render_bundle_stale_when_revision_ahead_of_rendered(tmp_path) -> None:
    trip_dir = tmp_path / "demo"
    trip_dir.mkdir()
    (trip_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    data = {"tripId": "demo", "meta": {"revision": 5, "renderedRevision": 3}}
    (trip_dir / "trip.json").write_text("{}", encoding="utf-8")
    assert trip_render_bundle_stale(trip_dir, data) is True
