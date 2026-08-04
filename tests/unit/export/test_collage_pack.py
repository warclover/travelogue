"""Unit tests · collage_pack (xiaohongshu / album_spread)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from travelogue.export.collage_pack import export_collage_pack
from travelogue.export.longshot import export_trip_longshot
from travelogue.export.platform_profiles import clear_platform_profiles_cache
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.unit


def _make_rgb(path: Path, *, size: tuple[int, int] = (800, 600), color=(40, 120, 200)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, format="JPEG", quality=90)


def _seed_kept_photos(trip_dir: Path, n: int) -> list[str]:
    trip_json = trip_dir / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    assets = []
    ids: list[str] = []
    for i in range(n):
        aid = f"collage-{i:02d}"
        ids.append(aid)
        rel = f"source/{aid}.jpg"
        size = (900, 600) if i % 2 == 0 else (600, 900)
        _make_rgb(trip_dir / rel, size=size, color=(30 + i * 10, 80, 160))
        assets.append(
            {
                "id": aid,
                "type": "image",
                "sourceFile": rel,
                "layoutEligible": True,
            }
        )
    data["assets"] = assets
    curation = data.setdefault("curation", {})
    curation["displayedAssetIds"] = ids
    cull = curation.setdefault("cullSummary", {})
    cull["layoutEligibleCount"] = n
    cull["finalLayoutEligibleCount"] = n
    trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return ids


@pytest.fixture(autouse=True)
def _clear_profiles_cache() -> None:
    clear_platform_profiles_cache()
    yield
    clear_platform_profiles_cache()


def test_export_xiaohongshu_collage_pages(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("xhs-8", trips, title="小红书拼贴")
    trip_dir = trips / "xhs-8"
    _seed_kept_photos(trip_dir, 8)

    with patch("travelogue.export.platform_longshot.export_platform_longshot") as mock_b:
        result = export_collage_pack(trip_dir, platform="xiaohongshu")
    mock_b.assert_not_called()

    assert result.platform == "xiaohongshu"
    assert result.capture_method == "collage_pages"
    assert result.page_count >= 2
    assert "竖版拼贴" in (result.user_hint or "")
    finals = list(trip_dir.glob("*-xhs-*.png"))
    assert len(finals) == result.page_count
    for path in finals:
        with Image.open(path) as im:
            assert im.size == (1080, 1440)


def test_export_album_spread_aspect(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("album-12", trips, title="相册跨页")
    trip_dir = trips / "album-12"
    _seed_kept_photos(trip_dir, 12)

    result = export_collage_pack(trip_dir, platform="album_spread")
    assert result.platform == "album_spread"
    assert result.capture_method == "collage_pages"
    assert result.page_count == 2
    assert "2.8:1" in (result.user_hint or "")
    finals = list(trip_dir.glob("*-album-*.png"))
    assert len(finals) == 2
    for path in finals:
        with Image.open(path) as im:
            assert im.size == (2800, 1000)
            assert abs(im.size[0] / im.size[1] - 2.8) < 0.01


def test_album_pack_by_chapter(tmp_path: Path) -> None:
    """两章各 3 张 → 两页 spread（章边界优先，非扁平 6+）。"""
    from travelogue.export.collage_pack import pack_album_pages_by_chapter

    trips = tmp_path / "trips"
    create_trip("album-ch", trips, title="按章画册")
    trip_dir = trips / "album-ch"
    ids = _seed_kept_photos(trip_dir, 6)
    trip_json = trip_dir / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    data["chapters"] = [
        {
            "id": "ch1",
            "screens": [{"id": "s1", "assetIds": ids[:3]}],
        },
        {
            "id": "ch2",
            "screens": [{"id": "s2", "assetIds": ids[3:]}],
        },
    ]
    trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    pages = pack_album_pages_by_chapter(trip_dir)
    assert len(pages) == 2
    assert len(pages[0]) == 3
    assert len(pages[1]) == 3

    result = export_collage_pack(trip_dir, platform="album_spread")
    assert result.page_count == 2
    assert "按章分页" in (result.user_hint or "")


def test_route_xiaohongshu_via_export_trip_longshot(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("xhs-route", trips, title="路由小红书")
    trip_dir = trips / "xhs-route"
    _seed_kept_photos(trip_dir, 8)

    with patch("travelogue.export.platform_longshot.export_platform_longshot") as mock_b:
        result = export_trip_longshot(trip_dir, platform="xiaohongshu")
    mock_b.assert_not_called()
    assert result.platform == "xiaohongshu"
    assert result.capture_method == "collage_pages"
    assert result.page_count >= 2


def test_route_album_via_export_trip_longshot(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("album-route", trips, title="路由相册")
    trip_dir = trips / "album-route"
    _seed_kept_photos(trip_dir, 6)

    with patch("travelogue.export.platform_longshot.export_platform_longshot") as mock_b:
        result = export_trip_longshot(trip_dir, platform="album_spread")
    mock_b.assert_not_called()
    assert result.platform == "album_spread"
    assert result.capture_method == "collage_pages"
    assert result.page_count == 1
