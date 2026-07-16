"""P0 · trip.meta.title must match rendered HTML <title> (shelf/preview drift)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts.lint_trip_html_title import check_trip_html_title_consistency
from tests._repo_root import repo_root
from travelogue.paths import TEMPLATE_VISUAL_JOURNAL
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import render_trip_surfaces
from travelogue.web.studio_trips import list_studio_trips

ROOT = repo_root(__file__)
GOLDEN = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
DEMO_ASSETS = TEMPLATE_VISUAL_JOURNAL / "assets"


@pytest.mark.skipif(not DEMO_ASSETS.is_dir(), reason="demo assets not present")
def test_rendered_html_title_matches_meta_and_shelf(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_id = "title-consistency"
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True)

    trip = json.loads(GOLDEN.read_text(encoding="utf-8"))
    trip["tripId"] = trip_id
    trip.setdefault("meta", {})["title"] = "雨后京都·手测"
    trip = prepare_trip_web_screens(trip)
    shutil.copytree(DEMO_ASSETS, trip_dir / "assets")
    (trip_dir / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (trip_dir / "assets" / "demo" / "video.mp4").write_bytes(b"")
    (trip_dir / "trip.json").write_text(
        json.dumps(trip, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    web, mobile, present = render_trip_surfaces(trip_dir / "trip.json", validate=False)
    assert web.is_file() and mobile.is_file()
    assert present is not None and present.is_file()

    failures = check_trip_html_title_consistency(trip_dir)
    assert failures == [], failures

    rows = list_studio_trips(trips_dir, limit=10)
    assert rows, "expected shelf row"
    row = next(r for r in rows if r.get("tripId") == trip_id)
    assert row.get("title") == "雨后京都·手测"
    html_title = web.read_text(encoding="utf-8")
    assert "雨后京都·手测" in html_title


def test_detects_stale_html_title(tmp_path: Path) -> None:
    trip_dir = tmp_path / "stale"
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text(
        json.dumps(
            {
                "version": "0.2",
                "tripId": "stale",
                "meta": {"title": "H-A Ambiguous 手测"},
                "assets": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (trip_dir / "index.html").write_text(
        "<!doctype html><title>示例游记</title><body></body>",
        encoding="utf-8",
    )
    failures = check_trip_html_title_consistency(trip_dir)
    assert failures
    assert any("示例游记" in item and "H-A Ambiguous" in item for item in failures)
