"""PRD-P9-F2 · keepNearDuplicates skips burst/pHash dedupe on incremental ingest."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from PIL import Image, ImageFilter

from travelogue.config import IngestConfig
from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip


def _album_with_burst(tmp_path: Path) -> Path:
    album = tmp_path / "album"
    album.mkdir()
    base = Image.effect_noise((1200, 1600), 80).convert("RGB")
    blur_path = album / "burst_blur.jpg"
    sharp_path = album / "burst_sharp.jpg"
    base.filter(ImageFilter.GaussianBlur(radius=10)).save(blur_path, quality=95)
    base.save(sharp_path, quality=95)
    t0 = time.time()
    os.utime(blur_path, (t0, t0))
    os.utime(sharp_path, (t0 + 1, t0 + 1))
    for i in range(3):
        path = album / f"extra_{i:02d}.jpg"
        Image.new("RGB", (2400, 3200), (30 + i * 17, 50, 70)).save(path, quality=95)
        os.utime(path, (t0 + 120 + i * 60, t0 + 120 + i * 60))
    return album


def test_keep_near_duplicates_skips_burst_dedupe(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("keep-dupes", trips, title="保留连拍")
    trip_dir = trips / "keep-dupes"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    trip.setdefault("intent", {})["keepNearDuplicates"] = True
    album = _album_with_burst(tmp_path)
    cfg = IngestConfig(dedupe_burst=True, dedupe_phash=False, burst_seconds=3.0)

    result = ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=True, cfg=cfg)

    assert result.stats.get("deduped_burst", 0) == 0
    assert result.stats.get("deduped_burst_replaced", 0) == 0
    assert len(trip["assets"]) == 5


def test_keep_near_duplicates_false_still_dedupes_burst(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("dedupe-burst", trips, title="连拍去重")
    trip_dir = trips / "dedupe-burst"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    album = _album_with_burst(tmp_path)
    cfg = IngestConfig(dedupe_burst=True, dedupe_phash=False, burst_seconds=3.0)

    result = ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=True, cfg=cfg)

    assert result.stats.get("deduped_burst_replaced", 0) == 1
    assert len(trip["assets"]) == 4
