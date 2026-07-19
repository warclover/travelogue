"""PRD-PIPELINE-PERF-V1 · R3.1 · scan without pixel decode (AC-PPF-08)."""

from __future__ import annotations

from pathlib import Path

import piexif
from PIL import Image

from travelogue.media.image_ops import min_edge_ok, peek_image_meta
from travelogue.media.ingest import scan_image_paths


def _jpeg_with_orientation(path: Path, *, size: tuple[int, int], orientation: int) -> None:
    img = Image.new("RGB", size, (20, 40, 60))
    exif_dict = {"0th": {piexif.ImageIFD.Orientation: orientation}, "Exif": {}, "GPS": {}, "1st": {}}
    exif_bytes = piexif.dump(exif_dict)
    img.save(path, "JPEG", quality=90, exif=exif_bytes)


def test_peek_swaps_wh_for_orientation_6(tmp_path: Path) -> None:
    photo = tmp_path / "rot.jpg"
    # Stored 400x800; orientation 6 → upright 800x400
    _jpeg_with_orientation(photo, size=(400, 800), orientation=6)
    meta = peek_image_meta(photo)
    assert meta.width == 800
    assert meta.height == 400
    assert meta.orientation_tag == 6
    assert min_edge_ok(meta.width, meta.height, 320)


def test_scan_rejects_small_after_orientation_swap(tmp_path: Path) -> None:
    photo = tmp_path / "tiny_rot.jpg"
    # Stored 500x200; orientation 6 → upright 200x500 → min edge 200 < 320
    _jpeg_with_orientation(photo, size=(500, 200), orientation=6)
    files, stats = scan_image_paths(tmp_path, max_photos=10, min_edge_px=320)
    assert files == []
    assert stats["skipped_small"] >= 1


def test_scan_accepts_upright_min_edge(tmp_path: Path) -> None:
    photo = tmp_path / "ok.jpg"
    Image.new("RGB", (640, 480), (1, 2, 3)).save(photo, "JPEG", quality=90)
    files, stats = scan_image_paths(tmp_path, max_photos=10, min_edge_px=320)
    assert files == [photo]
    assert stats["used"] == 1
