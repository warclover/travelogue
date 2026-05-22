"""Curate rules: day grouping and chapters."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from travelogue.curation.curate import _date_span_warning, _pick_cover_asset_id, run_curate
from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip
from tests.test_ingest import _album


def _asset(aid: str, w: int, h: int, kind: str) -> dict:
    return {
        "id": aid,
        "type": "image",
        "width": w,
        "height": h,
        "aspectKind": kind,
    }


def test_web_cover_prefers_landscape() -> None:
    assets = [
        _asset("tall", 900, 2400, "tall"),
        _asset("port", 900, 1600, "portrait"),
        _asset("land", 1600, 900, "landscape"),
        _asset("pano", 2400, 800, "panorama"),
    ]
    cover = _pick_cover_asset_id(assets, export_layout="web")
    assert cover in ("land", "pano")
    mobile = _pick_cover_asset_id(assets, export_layout="mobile")
    assert mobile in ("tall", "port")


def test_curate_builds_three_plus_chapters(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("curate-test", trips)
    trip_dir = trips / "curate-test"
    import json

    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    ingest_into_trip(trip, trip_dir, from_dir=_album(tmp_path, 8), dedupe=False)
    for i, a in enumerate(trip["assets"]):
        day = 2 + (i % 3)
        a["takenAt"] = f"2025-04-0{day}T12:00:00Z"
    result = run_curate(trip, export_layout="mobile")
    from travelogue.services.manifest_limits import chapter_limits

    min_c, max_c = chapter_limits()
    assert result.chapter_count >= min_c
    assert trip["pipeline"]["status"] == "structure_draft"
    assert trip["pipeline"]["layoutStatus"] == "layout_draft"
    rows = [it for ch in trip["chapters"] for it in ch["items"] if it.get("type") == "media-row"]
    assert not rows
    assert min_c <= len(trip["chapters"]) <= max_c


def test_date_span_warning_for_mixed_years() -> None:
    assets = [
        {"takenAt": "2010-07-11T07:28:17Z"},
        {"takenAt": "2026-05-20T09:53:14Z"},
    ]
    msg = _date_span_warning(assets)
    assert msg is not None
    assert "跨度" in msg
    assert "过滤旧图" not in msg


def test_curate_writes_segments_for_multi_month_album(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("seg-test", trips)
    trip_dir = trips / "seg-test"
    import json

    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    ingest_into_trip(trip, trip_dir, from_dir=_album(tmp_path, 8), dedupe=False)
    for i, a in enumerate(trip["assets"]):
        month = 3 if i < 4 else 10
        a["takenAt"] = f"2025-{month:02d}-{(i % 5) + 10:02d}T12:00:00Z"
        a["dateSource"] = "exif"
        a["dateConfidence"] = "high"
        a["mediaClass"] = "photo"
    run_curate(trip, export_layout="mobile")
    from travelogue.services.manifest_limits import chapter_limits

    min_c, max_c = chapter_limits()
    segs = (trip.get("curation") or {}).get("segments") or []
    assert len(segs) >= 2
    assert min_c <= len(trip["chapters"]) <= max_c
    assert trip["chapters"][0].get("curation", {}).get("segmentId")


def test_curate_caps_chapters_for_wide_span_album(tmp_path: Path) -> None:
    """Many calendar buckets across years → still 3–5 chapters (manifest)."""
    from travelogue.services.manifest_limits import chapter_limits

    trips = tmp_path / "trips"
    trip_json = create_trip("wide-span", trips)
    trip_dir = trips / "wide-span"
    import json

    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    ingest_into_trip(trip, trip_dir, from_dir=_album(tmp_path, 12), dedupe=False)
    day_starts = [
        "2010-07-11",
        "2010-08-03",
        "2014-10-04",
        "2020-01-15",
        "2022-06-01",
        "2026-05-20",
    ]
    for i, a in enumerate(trip["assets"]):
        day = day_starts[i % len(day_starts)]
        a["takenAt"] = f"{day}T12:00:00Z"
        a["dateSource"] = "exif"
        a["dateConfidence"] = "high"
        a["mediaClass"] = "photo"
        a["width"] = 1200
        a["height"] = 800
    run_curate(trip, export_layout="auto", layout_engine="screens")
    min_c, max_c = chapter_limits()
    assert min_c <= len(trip["chapters"]) <= max_c
