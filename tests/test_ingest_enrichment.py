"""Ingest enrichment: low-res marks, tags, dedupe keep-sharper."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from PIL import Image, ImageFilter

from travelogue.config import IngestConfig
from travelogue.media.ingest import ingest_into_trip
from travelogue.media.sharpness import sharpness_score
from travelogue.services.trip_factory import create_trip


def _album_base(tmp_path: Path, n: int = 4, *, size: tuple[int, int] = (2400, 3200)) -> Path:
    album = tmp_path / "album"
    album.mkdir()
    base_t = time.time() - 3600
    for i in range(n):
        Image.new("RGB", size, (30 + i * 17, 50 + i * 11, 70 + i * 13)).save(
            album / f"p{i:02d}.jpg", quality=95
        )
        ts = base_t + i * 60
        os.utime(album / f"p{i:02d}.jpg", (ts, ts))
    return album


def test_ingest_marks_low_resolution(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("low-res-ingest", trips, title="低分辨率标记")
    trip_dir = trips / "low-res-ingest"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    album = _album_base(tmp_path, 5, size=(2400, 3200))
    Image.new("RGB", (640, 480), (200, 100, 50)).save(album / "tiny.jpg", quality=95)

    ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=False)

    tiny = next(a for a in trip["assets"] if a["id"].endswith("006") or "tiny" in a["sourceFile"])
    # last asset is tiny - find by native size
    tiny = next(a for a in trip["assets"] if a.get("nativeWidth") == 640)
    assert tiny["layoutEligible"] is False
    assert tiny["excludeReason"] == "low_resolution"
    assert tiny["id"] in trip["curation"]["excludedLowResAssetIds"]
    eligible = [a for a in trip["assets"] if a.get("layoutEligible", True)]
    assert len(eligible) == 5


def test_ingest_writes_quality_and_tags(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("tags-ingest", trips, title="标签")
    trip_dir = trips / "tags-ingest"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    album = _album_base(tmp_path, 4)

    ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=False)
    a0 = trip["assets"][0]
    assert "quality" in a0
    assert a0["quality"]["sharpness"] > 0
    assert "meanLuma" in a0["quality"]
    assert 0.0 <= a0["quality"]["meanLuma"] <= 1.0
    assert a0.get("dominantTone", "").startswith("#")
    assert "tags" in a0
    assert a0["tagsSource"] == "heuristic"
    assert a0.get("burstGroupId", "").startswith("burst-")


def test_burst_dedupe_keeps_sharper_frame(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("burst-sharp", trips, title="连拍清晰")
    trip_dir = trips / "burst-sharp"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    album = _album_base(tmp_path, 4)
    base = Image.effect_noise((1200, 1600), 80).convert("RGB")
    blur_path = album / "burst_blur.jpg"
    sharp_path = album / "burst_sharp.jpg"
    base.filter(ImageFilter.GaussianBlur(radius=10)).save(blur_path, quality=95)
    base.save(sharp_path, quality=95)
    t0 = time.time()
    os.utime(blur_path, (t0, t0))
    os.utime(sharp_path, (t0 + 1, t0 + 1))

    cfg = IngestConfig(dedupe_burst=True, dedupe_phash=False, burst_seconds=3.0)
    result = ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=True, cfg=cfg)

    assert result.stats.get("deduped_burst_replaced") == 1
    assert len(trip["assets"]) == 5
    kept = max(a["quality"]["sharpness"] for a in trip["assets"])
    blur_only = sharpness_score(base.filter(ImageFilter.GaussianBlur(radius=10)))
    assert kept > blur_only
    for asset in trip["assets"]:
        display = trip_dir / asset["displayFile"]
        assert display.is_file(), f"missing derivative {display} for {asset['id']}"
        for entry in asset.get("srcset") or []:
            assert (trip_dir / entry["file"]).is_file()


def test_phash_dedupe_keeps_sharper_frame_and_derivatives(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("phash-sharp", trips, title="近重复清晰")
    trip_dir = trips / "phash-sharp"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    album = _album_base(tmp_path, 4)
    base = Image.effect_noise((1200, 1600), 80).convert("RGB")
    blur_path = album / "dup_blur.jpg"
    sharp_path = album / "dup_sharp.jpg"
    base.filter(ImageFilter.GaussianBlur(radius=10)).save(blur_path, quality=95)
    base.save(sharp_path, quality=95)
    t0 = time.time()
    os.utime(blur_path, (t0, t0))
    os.utime(sharp_path, (t0 + 120, t0 + 120))

    cfg = IngestConfig(dedupe_burst=False, dedupe_phash=True, phash_threshold=12, burst_seconds=3.0)
    result = ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=True, cfg=cfg)

    assert result.stats.get("deduped_phash_replaced", 0) >= 1
    assert len(trip["assets"]) >= 4
    for asset in trip["assets"]:
        assert (trip_dir / asset["displayFile"]).is_file(), asset["id"]
        for entry in asset.get("srcset") or []:
            assert (trip_dir / entry["file"]).is_file(), asset["id"]


def test_reingest_same_album_skips_existing_md5(tmp_path: Path) -> None:
    import shutil

    trips = tmp_path / "trips"
    trip_json = create_trip("reingest-md5", trips, title="二次导入")
    trip_dir = trips / "reingest-md5"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    album = _album_base(tmp_path, 4)

    cfg = IngestConfig(dedupe_burst=False, dedupe_phash=False)
    ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=True, cfg=cfg)
    count_after_first = len(trip["assets"])
    assert count_after_first == 4
    assert all(a.get("contentSig") for a in trip["assets"])

    shutil.copy2(album / "p00.jpg", album / "rescan_p00.jpg")
    result = ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=True, cfg=cfg)
    assert result.stats.get("deduped", 0) >= 1
    assert len(trip["assets"]) == count_after_first


def test_burst_replace_registers_md5_within_same_ingest(tmp_path: Path) -> None:
    import shutil

    trips = tmp_path / "trips"
    trip_json = create_trip("burst-md5", trips, title="连拍 MD5")
    trip_dir = trips / "burst-md5"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    album = _album_base(tmp_path, 4)
    base = Image.effect_noise((1200, 1600), 80).convert("RGB")
    blur_path = album / "burst_blur.jpg"
    sharp_path = album / "burst_sharp.jpg"
    base.filter(ImageFilter.GaussianBlur(radius=10)).save(blur_path, quality=95)
    base.save(sharp_path, quality=95)
    t0 = time.time()
    os.utime(blur_path, (t0, t0))
    os.utime(sharp_path, (t0 + 1, t0 + 1))
    shutil.copy2(sharp_path, album / "dup_same_sharp.jpg")
    os.utime(album / "dup_same_sharp.jpg", (t0 + 2, t0 + 2))

    cfg = IngestConfig(dedupe_burst=True, dedupe_phash=False, burst_seconds=3.0)
    result = ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=True, cfg=cfg)
    assert result.stats.get("deduped", 0) >= 1
    assert len(trip["assets"]) == 5
