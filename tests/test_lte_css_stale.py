"""Layout CSS stale detection (AC-P16-11)."""

from __future__ import annotations

import pytest

from travelogue.curation.mosaic.constants import PATTERN_MOSAIC_5_2P3L_EQUAL
from travelogue.layout_templates.css_stale import (
    required_grid_classes_from_trip,
    trip_layout_css_stale,
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
