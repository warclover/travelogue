"""Demo from-album importer tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from travelogue.demo.from_album import DemoError, demo_from_album, scan_album


def _make_album(tmp_path: Path, count: int = 6) -> Path:
    album = tmp_path / "album"
    album.mkdir()
    for i in range(count):
        img = Image.new("RGB", (1200, 1600), color=(40 + i * 10, 60, 80))
        img.save(album / f"img_{i:02d}.jpg", quality=90)
    return album


def test_scan_album_sorts_and_limits(tmp_path: Path) -> None:
    album = _make_album(tmp_path, 8)
    files, stats = scan_album(album, max_photos=6)
    assert len(files) == 6
    assert stats["used"] == 6


def test_scan_album_too_few(tmp_path: Path) -> None:
    album = _make_album(tmp_path, 2)
    with pytest.raises(DemoError) as exc:
        scan_album(album)
    assert exc.value.code == "E_DEMO_TOO_FEW"


def test_demo_from_album_builds_trip(tmp_path: Path) -> None:
    album = _make_album(tmp_path, 8)
    trips = tmp_path / "trips"
    result = demo_from_album(
        album,
        trips_dir=trips,
        trip_id="demo-test",
        title="测试旅途",
        place="测试",
        dedupe=False,
    )
    assert result.trip_json.is_file()
    assert result.index_html.is_file()
    import json

    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    display = trip["assets"][0]["displayFile"]
    assert (result.trip_dir / display).is_file()
    html = result.index_html.read_text(encoding="utf-8")
    assert "测试旅途" in html
    assert 'data-pattern="open"' in html

    cover = trip["coverAssetId"]
    used = {
        it.get("assetId")
        for ch in trip["chapters"]
        for it in ch["items"]
        if it.get("type") == "media-card"
    }
    assert cover not in used, "cover image must not repeat in chapter cards"
