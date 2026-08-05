"""Unit tests · collage_pack (xiaohongshu 3:4 Card / album_spread paired 3:4 + gutter).

PRD-EXPORT-CARD-COMPOSE-V1 v0.3.0 / ADR-021 v0.4.
"""

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
    # 8 photos greedy-chunk to [7,1] (largest available slot count ≤ 8) → 2 cards.
    assert result.page_count == 2
    assert "竖版拼贴" in (result.user_hint or "")
    finals = list(trip_dir.glob("*-xhs-*.png"))
    assert len(finals) == result.page_count
    for path in finals:
        with Image.open(path) as im:
            assert im.size == (1080, 1440)


def test_export_xiaohongshu_covers_every_photo(tmp_path: Path) -> None:
    """AC-ECC-01 · 每张照片都进入某个 Card，没有被 CardGrouper 丢弃。"""
    trips = tmp_path / "trips"
    create_trip("xhs-13", trips, title="小红书13张")
    trip_dir = trips / "xhs-13"
    _seed_kept_photos(trip_dir, 13)

    result = export_collage_pack(trip_dir, platform="xiaohongshu")
    # 13 → greedy [9,4] → 2 cards.
    assert result.page_count == 2


def test_export_album_spread_geometry(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("album-12", trips, title="相册跨页")
    trip_dir = trips / "album-12"
    _seed_kept_photos(trip_dir, 12)

    result = export_collage_pack(trip_dir, platform="album_spread")
    assert result.platform == "album_spread"
    assert result.capture_method == "collage_pages"
    # 12 → CardGrouper greedy [9,1,1,1] → 4 cards → paired spreads: 2.
    assert result.page_count == 2
    assert "3:4" in (result.user_hint or "")
    finals = list(trip_dir.glob("*-album-*.png"))
    assert len(finals) == 2
    for path in finals:
        with Image.open(path) as im:
            assert im.size == (2208, 1440)
            assert abs(im.size[0] / im.size[1] - 1.53) < 0.02


def test_album_spread_odd_card_gets_half_page(tmp_path: Path) -> None:
    """OQ-ECC-02 默认解：末尾单卡独立成半页，不强行拉伸铺满整跨页。"""
    trips = tmp_path / "trips"
    create_trip("album-odd", trips, title="奇数卡画册")
    trip_dir = trips / "album-odd"
    # 9 photos → CardGrouper greedy [9] → 1 card (odd count) → 1 spread with
    # a lone card (right half stays background, no partner to pair with).
    _seed_kept_photos(trip_dir, 9)

    result = export_collage_pack(trip_dir, platform="album_spread")
    assert result.page_count == 1
    finals = list(trip_dir.glob("*-album-*.png"))
    assert len(finals) == 1
    with Image.open(finals[0]) as im:
        bg = (245, 245, 243)
        w, h = im.size
        assert im.getpixel((w - 10, h // 2)) == bg


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
    assert result.page_count >= 1


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


def test_export_collage_pack_empty_raises(tmp_path: Path) -> None:
    from travelogue.export.longshot import LongshotExportError

    trips = tmp_path / "trips"
    create_trip("xhs-empty", trips, title="空")
    trip_dir = trips / "xhs-empty"
    _seed_kept_photos(trip_dir, 0)

    with pytest.raises(LongshotExportError) as ei:
        export_collage_pack(trip_dir, platform="xiaohongshu")
    assert getattr(ei.value, "code", None) == "E_COLLAGE_N"
