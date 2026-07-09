"""Layout CSS stale detection (AC-P16-11)."""

from __future__ import annotations

import pytest

from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_5_2P3L_EQUAL
from travelogue.layout_templates.css_stale import (
    required_grid_classes_from_trip,
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
