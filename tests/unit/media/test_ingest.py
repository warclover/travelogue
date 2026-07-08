"""Ingest service tests."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from tests.studio_test_helpers import make_test_album as _album
from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip


def test_ingest_preserves_aspect_without_crop(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("ingest-test", trips, title="导入测试")
    trip_dir = trips / "ingest-test"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    result = ingest_into_trip(
        trip, trip_dir, from_dir=_album(tmp_path), generate_crops=False, dedupe=False
    )
    assert result.added == 6
    assert trip["pipeline"]["status"] == "ingest_ready"
    a0 = trip["assets"][0]
    assert a0.get("cropMobile") is None
    assert a0.get("cropWeb") is None
    assert a0["aspectKind"] == "portrait"
    assert a0["width"] < a0["height"]
    display = trip_dir / a0["displayFile"]
    assert display.is_file()
    with Image.open(display) as img:
        assert img.width < img.height


def test_ingest_optional_profile_crops(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("ingest-crop-test", trips, title="裁切测试")
    trip_dir = trips / "ingest-crop-test"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    ingest_into_trip(
        trip, trip_dir, from_dir=_album(tmp_path, 4), generate_crops=True, dedupe=False
    )
    a0 = trip["assets"][0]
    assert a0.get("cropMobile", "").endswith("-m.webp")
    assert a0.get("cropWeb", "").endswith("-w.webp")
    assert (trip_dir / "assets" / f"{a0['id']}-m.webp").is_file()
