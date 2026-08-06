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
    # 2026-08-05 (orientation-supply-aware CardGrouper fix): the 8 seeded
    # photos are 4 landscape + 4 portrait (_seed_kept_photos alternates), so
    # the pure count-based chunk [8] → card-8-grid-equal (100% landscape
    # demand) would force 4 borrowed portrait photos into landscape-shaped
    # slots. plan_cards now tracks real orientation supply and instead
    # produces [7, 1] (card-7-triband-hero-mid's 3/4 split fits the actual
    # 4/4 supply almost exactly) → 2 cards, only the unavoidable trailing
    # single photo mismatched.
    assert result.page_count == 2
    assert "竖版拼贴" in (result.user_hint or "")
    finals = list(trip_dir.glob("*-xhs-*.png"))
    assert len(finals) == result.page_count
    for path in finals:
        with Image.open(path) as im:
            assert im.size == (1080, 1440)


def test_export_wechat_official_collage_pages(tmp_path: Path) -> None:
    """wechat_official (公众号) 与 xiaohongshu 复用同一条 3:4 Card 渲染管线，

    仅平台身份 / 文件名前缀 / 文案（图文正文 vs 笔记正文）不同。
    """
    trips = tmp_path / "trips"
    create_trip("mp-8", trips, title="公众号拼贴")
    trip_dir = trips / "mp-8"
    _seed_kept_photos(trip_dir, 8)

    with patch("travelogue.export.platform_longshot.export_platform_longshot") as mock_b:
        result = export_collage_pack(trip_dir, platform="wechat_official")
    mock_b.assert_not_called()

    assert result.platform == "wechat_official"
    assert result.capture_method == "collage_pages"
    # Same CardGrouper as xiaohongshu (2026-08-05 fix, see that test): 4
    # landscape + 4 portrait supply → [7, 1] → 2 cards.
    assert result.page_count == 2
    assert "图文正文" in (result.user_hint or "")
    assert "笔记正文" not in (result.user_hint or "")
    finals = list(trip_dir.glob("*-mp-*.png"))
    assert len(finals) == result.page_count
    for path in finals:
        with Image.open(path) as im:
            # Render-identical canvas to xiaohongshu.
            assert im.size == (1080, 1440)


def test_export_xiaohongshu_covers_every_photo(tmp_path: Path) -> None:
    """AC-ECC-01 · 每张照片都进入某个 Card，没有被 CardGrouper 丢弃。"""
    trips = tmp_path / "trips"
    create_trip("xhs-13", trips, title="小红书13张")
    trip_dir = trips / "xhs-13"
    _seed_kept_photos(trip_dir, 13)

    result = export_collage_pack(trip_dir, platform="xiaohongshu")
    # 2026-08-05 (orientation-supply-aware CardGrouper fix): 13 seeded photos
    # are 7 landscape + 6 portrait. The pure count-based [13] chunk would
    # land on card-13-hero-center-stack/top-stack — both 0% landscape —
    # forcing all 7 landscape photos into portrait-shaped cells. plan_cards
    # now picks [7, 6] instead (card-7-triband-hero-mid's 3 landscape-shaped
    # slots + card-6-sandwich-bands' 4 fit the 7/6 supply with zero forced
    # mismatches) → 2 cards.
    assert result.page_count == 2


def test_export_album_spread_geometry(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("album-12", trips, title="相册跨页")
    trip_dir = trips / "album-12"
    _seed_kept_photos(trip_dir, 12)

    result = export_collage_pack(trip_dir, platform="album_spread")
    assert result.platform == "album_spread"
    assert result.capture_method == "collage_pages"
    # 2026-08-05 (orientation-supply-aware CardGrouper fix): 12 seeded photos
    # are 6 landscape + 6 portrait. The pure count-based [12] chunk would
    # land on a 33%-landscape 12-slot template (4 landscape-shaped slots),
    # stranding 2 real landscape photos with no home but a portrait cell.
    # plan_cards now produces 3 cards (2026-08-06 diversity-fix tie-break:
    # [7, 3, 2], zero forced mismatches — an odd count, unlike the earlier
    # [7, 2, 2, 1] chunking this comment used to document, but still 2
    # spreads: one full spread (cards 1+2) + one lone trailing card
    # rendered as a single-card-width half page per OQ-ECC-02).
    assert result.page_count == 2
    assert "3:4" in (result.user_hint or "")
    finals = sorted(trip_dir.glob("*-album-*.png"))
    assert len(finals) == 2
    sizes = []
    for path in finals:
        with Image.open(path) as im:
            sizes.append(im.size)
    # One full spread (double-card width) + one lone half page (single-card
    # width) — see test_album_spread_odd_card_gets_half_page.
    assert (2208, 1440) in sizes
    assert (1080, 1440) in sizes


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


def test_album_spread_manual_slide_count_targets_requested_spreads(tmp_path: Path) -> None:
    """P2 · 用户可指定「跨页数」，语义与小红书「张数」控件一致（一跨页≈两张 3:4 卡）——
    但 2026-08-06「自定义张数=软目标」决策后，请求的跨页数只是引导而非硬约束：
    当 20 张照片按「跨页数=2」反推出的单卡张数（5）恰好只对应一套 100% 横版模板
    （card-5-hero-mid-landscape）、而实际供给是 10 横/10 竖对半分时，硬凑 4 张
    size=5 的卡会强制把竖版照片塞进全横版槙位（AC-ECC-04 违规）。CardGrouper 改为
    优先保正确、贴近目标张数退居其次，实际落地页数会略多于用户请求（这里是 3
    而不是 2），但 0 处错配——这是设计意图内的取舍，不是回归。"""
    trips = tmp_path / "trips"
    create_trip("album-count", trips, title="画册指定跨页数")
    trip_dir = trips / "album-count"
    _seed_kept_photos(trip_dir, 20)

    result = export_collage_pack(trip_dir, platform="album_spread", slide_count=2)
    assert result.page_count == 3
    assert "被迫裁切" not in result.user_hint  # 0 处结构性错配，不应出现兜底提示
    finals = list(trip_dir.glob("*-album-*.png"))
    assert len(finals) == 3


def test_album_spread_slide_count_none_stays_auto_greedy(tmp_path: Path) -> None:
    """slide_count=None（自动）不受本次改动影响 — 沿用既有自动分页结果。

    2026-08-05 note: the *result* here is 2 spreads (see
    test_export_album_spread_geometry for why — 12 seeded photos are 6
    landscape + 6 portrait, and the orientation-supply-aware CardGrouper
    fix now avoids stranding 2 landscape photos in portrait-shaped cells);
    the behavior under test (auto mode has no externally-fixed page-count
    target, unaffected by the slide_count P2 feature) is unchanged.
    """
    trips = tmp_path / "trips"
    create_trip("album-auto", trips, title="画册自动分页")
    trip_dir = trips / "album-auto"
    _seed_kept_photos(trip_dir, 12)

    auto_result = export_collage_pack(trip_dir, platform="album_spread")
    assert auto_result.page_count == 2


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


def test_route_wechat_official_via_export_trip_longshot(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    create_trip("mp-route", trips, title="路由公众号")
    trip_dir = trips / "mp-route"
    _seed_kept_photos(trip_dir, 8)

    with patch("travelogue.export.platform_longshot.export_platform_longshot") as mock_b:
        result = export_trip_longshot(trip_dir, platform="wechat_official")
    mock_b.assert_not_called()
    assert result.platform == "wechat_official"
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


def test_export_collage_pack_passes_asset_lookup_to_renderer(tmp_path: Path) -> None:
    """AC-ECC-06 wiring · collage 必须把 trip 资产元数据注入 CardRenderer。"""
    trips = tmp_path / "trips"
    create_trip("xhs-lookup", trips, title="lookup")
    trip_dir = trips / "xhs-lookup"
    _seed_kept_photos(trip_dir, 4)

    seen: list[object] = []

    def _fake_render_card(photos, template, *, canvas_wh, asset_lookup=None, **_kw):
        seen.append(asset_lookup)
        from travelogue.export.card_renderer import render_card as real_render

        return real_render(
            photos, template, canvas_wh=canvas_wh, asset_lookup=asset_lookup
        )

    with patch("travelogue.export.collage_pack.render_card", side_effect=_fake_render_card):
        export_collage_pack(trip_dir, platform="xiaohongshu")

    assert seen, "render_card was not called"
    assert all(callable(lookup) for lookup in seen)
    any_hit = False
    for path in (trip_dir / "source").glob("*.jpg"):
        asset = seen[0](path)
        if asset is not None:
            any_hit = True
            assert isinstance(asset, dict)
            assert asset.get("id")
    assert any_hit, "asset_lookup should resolve at least one collage photo path"


def test_collage_photo_limit_album_250_others_72() -> None:
    """画册单独放大到 250；小红书/公众号仍 72（发布页数不宜过多）。"""
    from travelogue.export.collage_pack import (
        _ALBUM_PHOTO_LIMIT,
        _COLLAGE_PHOTO_LIMIT,
        collage_photo_limit_for_platform,
    )

    assert _COLLAGE_PHOTO_LIMIT == 72
    assert _ALBUM_PHOTO_LIMIT == 250
    assert collage_photo_limit_for_platform("album_spread") == 250
    assert collage_photo_limit_for_platform("xiaohongshu") == 72
    assert collage_photo_limit_for_platform("wechat_official") == 72


def test_album_pool_uses_more_than_xhs_cap(tmp_path: Path) -> None:
    """精选超过 72 时：小红书仍截断到 72，画册可继续吃到更高上限。"""
    from travelogue.export.collage_pack import list_collage_photo_paths

    trips = tmp_path / "trips"
    create_trip("pool-80", trips, title="池子80")
    trip_dir = trips / "pool-80"
    _seed_kept_photos(trip_dir, 80)

    xhs = list_collage_photo_paths(trip_dir, platform="xiaohongshu")
    album = list_collage_photo_paths(trip_dir, platform="album_spread")
    assert len(xhs) == 72
    assert len(album) == 80
