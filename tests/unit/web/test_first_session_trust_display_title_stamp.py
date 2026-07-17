"""First-Session Trust · displayTitle persist must not false-flag renderBundleStale."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.layout_templates.css_stale import trip_render_bundle_stale
from travelogue.services.trip import (
    TripService,
    mark_render_bundle_current,
    meta_rendered_revision,
    meta_revision,
)
from travelogue.web.studio_pipeline import _finalize_pipeline_result

pytestmark = pytest.mark.unit


def test_finalize_display_title_persist_keeps_render_bundle_fresh(tmp_path: Path) -> None:
    """BE-FST-06 write of meta.displayTitle must re-stamp renderedRevision."""
    trips_dir = tmp_path / "trips" / "demo-fst"
    trips_dir.mkdir(parents=True)
    trip_json = trips_dir / "trip.json"
    (trips_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    svc = TripService(root=tmp_path)
    seed = {
        "tripId": "demo-fst",
        "meta": {
            "revision": 0,
            "title": "王丹昙华林2",
            "places": ["武汉"],
            "dateStart": "2026-07-01",
            "dateEnd": "2026-07-02",
        },
        "pipeline": {"status": "rendered"},
        "assets": [],
        "chapters": [],
        "intent": {"version": "1", "title": "王丹昙华林2", "places": ["武汉"]},
    }
    svc.save(seed, trip_json)
    svc.update(trip_json, mark_render_bundle_current)
    before = svc.load(trip_json)
    assert meta_rendered_revision(before) == meta_revision(before)
    assert not str((before.get("meta") or {}).get("displayTitle") or "").strip()

    result = _finalize_pipeline_result(
        svc=svc,
        trip_json=trip_json,
        trip_root=trips_dir,
        slug="demo-fst",
        host="127.0.0.1",
        port=8787,
        title="王丹昙华林2",
        photo_count=0,
        cluster_notice="",
        tier_mode="single",
    )
    after = svc.load(trip_json)
    display = str((after.get("meta") or {}).get("displayTitle") or "").strip()
    assert display
    assert display != "王丹昙华林2"
    assert result.title == display
    assert meta_rendered_revision(after) == meta_revision(after)
    assert trip_render_bundle_stale(trips_dir, after) is False
