"""Ingest reports suspected thumbnails before curate."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from travelogue.media.ingest import ingest_into_trip
from travelogue.media.ingest_report import format_ingest_report
from travelogue.services.trip_factory import create_trip


def test_ingest_flags_short_edge_thumbnail(tmp_path: Path) -> None:
    album = tmp_path / "album"
    album.mkdir()
    # 438×640 style thumbnail
    Image.new("RGB", (438, 640), (40, 80, 120)).save(album / "thumb.jpg", quality=90)
    for i in range(5):
        Image.new("RGB", (2000, 1200), (i * 10, 90, 120)).save(
            album / f"wide-{i:02d}.jpg", quality=90
        )

    trips = tmp_path / "trips"
    trip_json = create_trip("thumb-hint", trips, title="测试")
    trip_dir = trips / "thumb-hint"
    trip = __import__("json").loads(trip_json.read_text(encoding="utf-8"))
    result = ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=False)
    report = format_ingest_report(result, trip)
    assert result.stats.get("suspected_thumbnail_ids")
    assert "疑似缩略图" in report
