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


def _dual_album(tmp_path: Path, featured_n: int = 2, material_n: int = 4) -> Path:
    root = tmp_path / "album-dual"
    feat = root / "精选"
    mat = root / "素材上传"
    feat.mkdir(parents=True)
    mat.mkdir(parents=True)
    for i in range(featured_n):
        img = Image.new("RGB", (1600, 900), color=(200, 90 + i * 10, 50))
        img.save(feat / f"feat-{i:02d}.jpg", quality=90)
    for i in range(material_n):
        img = Image.new("RGB", (1600, 900), color=(60, 100 + i * 5, 140))
        img.save(mat / f"mat-{i:02d}.jpg", quality=90)
    return root


def test_demo_from_album_auto_dual_folder_user_tier(tmp_path: Path) -> None:
    album = _dual_album(tmp_path)
    trips = tmp_path / "trips"
    result = demo_from_album(
        album,
        trips_dir=trips,
        trip_id="demo-dual-auto",
        title="双源",
        dedupe=False,
        render=False,
    )
    import json

    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    featured = [a for a in trip["assets"] if a.get("userTier") == "featured"]
    material = [a for a in trip["assets"] if a.get("userTier") == "material"]
    assert len(featured) == 2
    assert len(material) == 4
    assert all(a.get("importSource") == "featured" for a in featured)
    assert result.stats.get("userTierSummary", {}).get("featured") == 2


def test_demo_from_album_explicit_tier_dirs(tmp_path: Path) -> None:
    album = tmp_path / "album-root"
    album.mkdir()
    featured = tmp_path / "my-featured"
    material = tmp_path / "my-material"
    featured.mkdir(parents=True)
    material.mkdir(parents=True)
    for i in range(2):
        Image.new("RGB", (1600, 900), color=(220, 80, 40)).save(featured / f"f-{i}.jpg", quality=90)
    for i in range(4):
        Image.new("RGB", (1600, 900), color=(50, 90, 160)).save(material / f"m-{i}.jpg", quality=90)

    from travelogue.demo.build import run_demo_from_album

    trips = tmp_path / "trips"
    result = run_demo_from_album(
        album,
        trips_dir=trips,
        trip_id="demo-dual-explicit",
        featured_dir=featured,
        material_dir=material,
        dedupe=False,
        render=False,
        force=True,
    )
    import json

    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    assert len([a for a in trip["assets"] if a.get("userTier") == "featured"]) == 2
    assert len([a for a in trip["assets"] if a.get("userTier") == "material"]) == 4
    assert result.stats.get("tier_mode") == "explicit"
