"""Phase 16 P2 closure: legacy reexport, primitives, studio stale, dashboard."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.curation.mosaic import _legacy_generated as legacy_gen
from travelogue.curation.mosaic.constants import (
    MOSAIC_3_PATTERN_IDS,
    PATTERN_GRID_CLASS,
)
from travelogue.curation.mosaic.grid_specs import EXPLICIT_GRID_SPECS
from travelogue.layout_templates.primitive_catalog import check_primitive_yaml_drift
from travelogue.layout_templates.registry import reset_engine_cache_for_tests
from travelogue.web.studio_trips import list_studio_trips


@pytest.fixture(autouse=True)
def _fresh() -> None:
    reset_engine_cache_for_tests()


@pytest.mark.unit
def test_grid_specs_reexports_legacy_generated() -> None:
    assert EXPLICIT_GRID_SPECS is legacy_gen.EXPLICIT_GRID_SPECS


@pytest.mark.unit
def test_constants_reexports_mosaic_pattern_ids() -> None:
    assert MOSAIC_3_PATTERN_IDS is legacy_gen.MOSAIC_3_PATTERN_IDS
    assert PATTERN_GRID_CLASS is legacy_gen.PATTERN_GRID_CLASS


@pytest.mark.unit
def test_primitive_yaml_matches_catalog() -> None:
    errors = check_primitive_yaml_drift()
    assert errors == []


@pytest.mark.unit
def test_cli_check_primitives() -> None:
    from travelogue.layout_templates import cli

    assert cli.cmd_check_primitives(cli.build_parser().parse_args(["check-primitives"])) == 0


@pytest.mark.unit
def test_list_studio_trips_layout_css_stale_without_solidified_geometry(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_dir = trips_dir / "stale-demo"
    trip_dir.mkdir(parents=True)
    data = {
        "title": "Stale demo",
        "chapters": [
            {
                "screens": [
                    {
                        "patternId": "screen-mosaic-5-2p3l-equal",
                        "layoutGeometry": {
                            "gridClass": "layout-screen__grid--mosaic-5-2p3l-equal",
                        },
                    }
                ]
            }
        ],
    }
    (trip_dir / "trip.json").write_text(json.dumps(data), encoding="utf-8")
    (trip_dir / "journal-screens.css").write_text(".layout-screen__grid--3col {}", encoding="utf-8")
    rows = list_studio_trips(trips_dir)
    assert len(rows) == 1
    assert rows[0]["layoutCssStale"] is True


@pytest.mark.unit
def test_list_studio_trips_layout_css_not_stale_when_geometry_solidified(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_dir = trips_dir / "solid-demo"
    trip_dir.mkdir(parents=True)
    data = {
        "title": "Solid demo",
        "chapters": [
            {
                "screens": [
                    {
                        "patternId": "screen-mosaic-5-2p3l-equal",
                        "layoutGeometry": {
                            "gridClass": "layout-screen__grid--mosaic-5-2p3l-equal",
                            "cols": [1, 1, 1],
                            "rows": [1, 1],
                        },
                    }
                ]
            }
        ],
    }
    (trip_dir / "trip.json").write_text(json.dumps(data), encoding="utf-8")
    (trip_dir / "journal-screens.css").write_text(".wrong {}", encoding="utf-8")
    rows = list_studio_trips(trips_dir)
    assert rows[0]["layoutCssStale"] is False


@pytest.mark.unit
def test_list_studio_trips_shelf_cover_prefers_mobile_cover(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_dir = trips_dir / "dual-cover"
    assets = trip_dir / "assets"
    assets.mkdir(parents=True)
    (assets / "port-cover.webp").write_bytes(b"webp")
    (assets / "land-cover.webp").write_bytes(b"webp")
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    data = {
        "meta": {"title": "Dual cover"},
        "coverAssetId": "port",
        "exportLayout": "auto",
        "assets": [
            {
                "id": "port",
                "type": "image",
                "width": 900,
                "height": 2000,
                "displayFile": "assets/port-cover.webp",
                "layoutEligible": True,
            },
            {
                "id": "land",
                "type": "image",
                "width": 1920,
                "height": 1080,
                "displayFile": "assets/land-cover.webp",
                "layoutEligible": True,
            },
        ],
        "curation": {"coverByLayout": {"mobile": "port", "web": "land"}},
    }
    (trip_dir / "trip.json").write_text(json.dumps(data), encoding="utf-8")

    rows = list_studio_trips(trips_dir)
    assert len(rows) == 1
    assert rows[0]["previewRelPath"] == "preview.jpg"
    assert rows[0]["shelfCoverRelPath"] == "assets/port-cover.webp"


@pytest.mark.unit
def test_list_studio_trips_shelf_cover_falls_back_to_preview(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_dir = trips_dir / "preview-only"
    trip_dir.mkdir(parents=True)
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    (trip_dir / "trip.json").write_text(
        json.dumps({"meta": {"title": "Preview only"}}),
        encoding="utf-8",
    )

    rows = list_studio_trips(trips_dir)
    assert rows[0]["shelfCoverRelPath"] == "preview.jpg"
