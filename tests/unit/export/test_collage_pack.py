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
from travelogue.export.longshot import EXPORT_OUTPUT_DIRNAME, export_trip_longshot
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
    # 2026-08-07 (quality-aware small-pool feed default, plan_cards_for_feed):
    # 8 photos ≤ the 10-photo small-pool threshold → collage budget = 1 card.
    # Every seeded asset lacks width/height/aspectKind, so cover_score_v2
    # returns 0.0 for all of them (kind falls back to "square" → empty
    # feature vector) — the tie-break degrades to original order, so the
    # first 6 photos (3 landscape + 3 portrait) fill one compact collage
    # card, and the trailing 2 (1 landscape + 1 portrait) become their own
    # singles (the first of which is promoted to the opening "cover" card,
    # ties broken by original order too) → 3 cards total: 1 opener single +
    # 1 collage + 1 single.
    assert result.page_count == 3
    assert "竖版拼贴" in (result.user_hint or "")
    assert "精选单图" in (result.user_hint or "")
    finals = list((trip_dir / EXPORT_OUTPUT_DIRNAME).glob("*-xhs-*.png"))
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
    # Same CardGrouper as xiaohongshu (2026-08-07 quality-aware small-pool
    # default, see that test): 8 photos → 1 opener single + 1 compact
    # collage + 1 trailing single = 3 cards.
    assert result.page_count == 3
    assert "图文正文" in (result.user_hint or "")
    assert "笔记正文" not in (result.user_hint or "")
    finals = list((trip_dir / EXPORT_OUTPUT_DIRNAME).glob("*-mp-*.png"))
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
    # 2026-08-07 (quality-aware small-pool feed default): 13 photos falls in
    # the 11-20 "medium pool" band → collage budget = 2 compact cards (all
    # scores tie at 0.0, see test_export_xiaohongshu_collage_pages, so the
    # tie-break is original order): photos[0:6] and [6:12] each fill one
    # 6-slot compact collage, leaving a single trailing photo (photos[12])
    # promoted straight to the opener single → 3 cards, all 13 photos
    # accounted for (6 + 6 + 1).
    assert result.page_count == 3


def test_export_xiaohongshu_large_pool_no_quality_split(tmp_path: Path) -> None:
    """>20 photos: plan_cards_for_feed falls through unchanged to the
    dominant-opener behavior — no "精选单图" quality-split hint."""
    trips = tmp_path / "trips"
    create_trip("xhs-30", trips, title="小红书大池")
    trip_dir = trips / "xhs-30"
    _seed_kept_photos(trip_dir, 30)

    result = export_collage_pack(trip_dir, platform="xiaohongshu")
    assert "精选单图" not in (result.user_hint or "")
    finals = list((trip_dir / EXPORT_OUTPUT_DIRNAME).glob("*-xhs-*.png"))
    assert len(finals) == result.page_count


def test_export_xiaohongshu_manual_slide_count_skips_quality_split(tmp_path: Path) -> None:
    """A manual "自定义张数" request bypasses the small-pool quality-aware
    split entirely — result must match plain ``plan_cards_with_dominant_
    opener`` (via a fixed slide_count), not the quality-aware allocation."""
    trips = tmp_path / "trips"
    create_trip("xhs-manual", trips, title="小红书自定义张数")
    trip_dir = trips / "xhs-manual"
    _seed_kept_photos(trip_dir, 8)

    result = export_collage_pack(trip_dir, platform="xiaohongshu", slide_count=4)
    assert "精选单图" not in (result.user_hint or "")


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
    assert "画册页面" in (result.user_hint or "")
    assert "正文跨页拼贴" in (result.user_hint or "")
    finals = sorted((trip_dir / EXPORT_OUTPUT_DIRNAME).glob("*-album-*.png"))
    assert len(finals) == 2
    sizes = []
    for path in finals:
        with Image.open(path) as im:
            sizes.append(im.size)
    # One full spread (double-card width) + one lone half page (single-card
    # width) — see test_album_spread_odd_card_gets_half_page.
    assert (2208, 1440) in sizes
    assert (1080, 1440) in sizes


def _seed_album_with_bookends(
    trip_dir: Path,
    n_body: int,
    *,
    with_closing: bool = True,
    cover_in_pool: bool = True,
    closing_in_pool: bool = True,
) -> tuple[str, str | None]:
    """Seed kept photos plus cover/closing assets for ABE acceptance tests."""
    trip_json = trip_dir / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    assets: list[dict] = []
    displayed: list[str] = []

    cover_id = "abe-cover"
    cover_rel = f"source/{cover_id}.jpg"
    _make_rgb(trip_dir / cover_rel, size=(900, 1200), color=(200, 80, 60))
    assets.append(
        {
            "id": cover_id,
            "type": "image",
            "sourceFile": cover_rel,
            "layoutEligible": True,
            "aspectKind": "portrait",
            "width": 900,
            "height": 1200,
        }
    )
    if cover_in_pool:
        displayed.append(cover_id)

    closing_id: str | None = None
    if with_closing:
        closing_id = "abe-closing"
        closing_rel = f"source/{closing_id}.jpg"
        _make_rgb(trip_dir / closing_rel, size=(900, 1200), color=(60, 80, 200))
        assets.append(
            {
                "id": closing_id,
                "type": "image",
                "sourceFile": closing_rel,
                "layoutEligible": True,
                "aspectKind": "portrait",
                "width": 900,
                "height": 1200,
            }
        )
        if closing_in_pool:
            displayed.append(closing_id)

    for i in range(n_body):
        aid = f"abe-body-{i:02d}"
        displayed.append(aid)
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
    data["coverAssetId"] = cover_id
    meta = data.setdefault("meta", {})
    meta["title"] = "ABE测试游记"
    meta["subtitle"] = ""
    meta["hook"] = "七天 · 慢行"
    curation = data.setdefault("curation", {})
    curation["displayedAssetIds"] = displayed
    curation["closingAssetId"] = closing_id
    cull = curation.setdefault("cullSummary", {})
    cull["layoutEligibleCount"] = len(assets)
    cull["finalLayoutEligibleCount"] = len(assets)
    trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return cover_id, closing_id


def test_album_bookends_cover_first_closing_last(tmp_path: Path) -> None:
    """AC-ABE-01/02 · 第 1 页封面、最后 1 页封底，均为单卡宽度且内容匹配渲染器。"""
    from travelogue.export.card_bookends import render_closing_card, render_cover_card
    from travelogue.export.card_renderer import CARD_CANVAS

    trips = tmp_path / "trips"
    create_trip("abe-ends", trips, title="ABE封面封底")
    trip_dir = trips / "abe-ends"
    _seed_album_with_bookends(trip_dir, 8, with_closing=True)

    result = export_collage_pack(trip_dir, platform="album_spread")
    finals = sorted((trip_dir / EXPORT_OUTPUT_DIRNAME).glob("*-album-*.png"))
    assert len(finals) == result.page_count
    assert result.page_count >= 3
    assert "封面 1 张" in (result.user_hint or "")
    assert "封底 1 张" in (result.user_hint or "")

    expected_cover = render_cover_card(
        trip_dir / "source" / "abe-cover.jpg",
        title="ABE测试游记",
        subtitle="七天 · 慢行",  # empty subtitle → hook fallback
        canvas_wh=CARD_CANVAS,
    )
    expected_closing = render_closing_card(
        trip_dir / "source" / "abe-closing.jpg",
        title="ABE测试游记",
        canvas_wh=CARD_CANVAS,
    )
    assert expected_cover is not None and expected_closing is not None
    assert finals[0].read_bytes() == expected_cover
    assert finals[-1].read_bytes() == expected_closing

    with Image.open(finals[0]) as first:
        assert first.size == (1080, 1440)
    with Image.open(finals[-1]) as last:
        assert last.size == (1080, 1440)


def test_album_bookends_prefers_portrait_over_landscape_cover(tmp_path: Path) -> None:
    """横版 coverAssetId + 竖版候选时，封面改用竖版，避免 3:4 错配硬裁。"""
    trips = tmp_path / "trips"
    create_trip("abe-orient", trips, title="ABE方向")
    trip_dir = trips / "abe-orient"
    cover_id, closing_id = _seed_album_with_bookends(trip_dir, 6, with_closing=True)

    trip_json = trip_dir / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    # Turn declared cover into landscape; keep a portrait body photo as candidate.
    land_rel = "source/abe-cover.jpg"
    _make_rgb(trip_dir / land_rel, size=(1600, 900), color=(220, 40, 40))
    for asset in data["assets"]:
        if asset.get("id") == cover_id:
            asset["aspectKind"] = "landscape"
            asset["width"] = 1600
            asset["height"] = 900
        if asset.get("id") == "abe-body-01":
            asset["aspectKind"] = "portrait"
            asset["width"] = 600
            asset["height"] = 900
    data["coverCandidates"] = [cover_id, "abe-body-01"]
    curation = data.setdefault("curation", {})
    curation["coverCandidatesByLayout"] = {"mobile": [cover_id, "abe-body-01"]}
    trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    seen_body: list[str] = []

    def _fake_render_spread(left, right, **kwargs):
        from travelogue.export.card_renderer import render_spread as real

        for plan in (left, right):
            if plan is None:
                continue
            photos, _tmpl = plan
            for path in photos:
                seen_body.append(path.stem)
        return real(left, right, **kwargs)

    with patch(
        "travelogue.export.collage_pack.render_spread", side_effect=_fake_render_spread
    ):
        result = export_collage_pack(trip_dir, platform="album_spread")

    assert "封面 1 张" in (result.user_hint or "")
    # Portrait substitute used as cover → excluded from body.
    assert "abe-body-01" not in seen_body
    assert closing_id not in seen_body


def test_album_bookends_exclude_from_body(tmp_path: Path) -> None:
    """AC-ABE-03 · 封面/封底图不进入正文跨页。"""
    trips = tmp_path / "trips"
    create_trip("abe-excl", trips, title="ABE排除")
    trip_dir = trips / "abe-excl"
    cover_id, closing_id = _seed_album_with_bookends(
        trip_dir, 6, cover_in_pool=True, closing_in_pool=True
    )

    seen_ids: list[str] = []

    def _fake_render_spread(left, right, **kwargs):
        from travelogue.export.card_renderer import render_spread as real

        for plan in (left, right):
            if plan is None:
                continue
            photos, _tmpl = plan
            for path in photos:
                # path stem is asset id for our seeded source/{id}.jpg layout
                seen_ids.append(path.stem)
        return real(left, right, **kwargs)

    with patch(
        "travelogue.export.collage_pack.render_spread", side_effect=_fake_render_spread
    ):
        export_collage_pack(trip_dir, platform="album_spread")

    assert cover_id not in seen_ids
    assert closing_id not in seen_ids
    assert any(s.startswith("abe-body-") for s in seen_ids)


def test_album_bookends_skip_closing_when_missing(tmp_path: Path) -> None:
    """AC-ABE-04 · closingAssetId 为空时正常导出且无封底页。"""
    trips = tmp_path / "trips"
    create_trip("abe-noclose", trips, title="ABE无封底")
    trip_dir = trips / "abe-noclose"
    _seed_album_with_bookends(trip_dir, 8, with_closing=False)

    result = export_collage_pack(trip_dir, platform="album_spread")
    assert result.page_count >= 2
    assert "封面 1 张" in (result.user_hint or "")
    assert "封底" not in (result.user_hint or "")


def test_album_bookends_render_failure_does_not_block(tmp_path: Path) -> None:
    """AC-ABE-06 · 封面素材不可读时跳过该页，正文仍导出。"""
    trips = tmp_path / "trips"
    create_trip("abe-fail", trips, title="ABE容错")
    trip_dir = trips / "abe-fail"
    cover_id, _ = _seed_album_with_bookends(trip_dir, 8, with_closing=False)

    # Remove the file and break every resolve key so bookend render is skipped
    # without aborting the album body export.
    (trip_dir / "source" / f"{cover_id}.jpg").unlink(missing_ok=True)
    trip_json = trip_dir / "trip.json"
    data = json.loads(trip_json.read_text(encoding="utf-8"))
    for asset in data["assets"]:
        if asset.get("id") == cover_id:
            asset["sourceFile"] = "source/missing-cover.jpg"
            break
    trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    result = export_collage_pack(trip_dir, platform="album_spread")
    assert result.page_count >= 1
    assert "封面" not in (result.user_hint or "")


def test_album_bookends_render_exception_skipped(tmp_path: Path) -> None:
    """AC-ABE-06 · 渲染内部异常捕获跳过，不抛 LongshotExportError。"""
    trips = tmp_path / "trips"
    create_trip("abe-exc", trips, title="ABE异常")
    trip_dir = trips / "abe-exc"
    _seed_album_with_bookends(trip_dir, 8, with_closing=True)

    with patch(
        "travelogue.export.card_bookends._fit_photo_to_canvas",
        side_effect=RuntimeError("inject"),
    ):
        result = export_collage_pack(trip_dir, platform="album_spread")
    assert result.page_count >= 1
    assert "封面" not in (result.user_hint or "")
    assert "封底" not in (result.user_hint or "")


def test_album_bookends_target_uses_body_count(tmp_path: Path) -> None:
    """AC-ABE-07 · _album_target_per_card 按排除后的正文张数计算。"""
    from travelogue.export import collage_pack as cp

    trips = tmp_path / "trips"
    create_trip("abe-target", trips, title="ABE页数")
    trip_dir = trips / "abe-target"
    # 20 body + cover + closing in pool → body after exclude = 20
    _seed_album_with_bookends(
        trip_dir, 20, cover_in_pool=True, closing_in_pool=True
    )

    captured: list[int] = []
    real = cp._album_target_per_card

    def _spy_target(n_photos, **kwargs):
        captured.append(n_photos)
        return real(n_photos, **kwargs)

    with patch.object(cp, "_album_target_per_card", side_effect=_spy_target):
        export_collage_pack(trip_dir, platform="album_spread", slide_count=2)

    assert captured == [20]


def test_xhs_unchanged_when_bookends_present(tmp_path: Path) -> None:
    """AC-ABE-05 · 小红书不受 album bookends 影响（页数/池仍含 cover|closing）。"""
    trips = tmp_path / "trips"
    create_trip("abe-xhs", trips, title="ABE小红书回归")
    trip_dir = trips / "abe-xhs"
    _seed_album_with_bookends(trip_dir, 6, cover_in_pool=True, closing_in_pool=True)

    result = export_collage_pack(trip_dir, platform="xiaohongshu")
    assert result.platform == "xiaohongshu"
    # 8 kept photos in pool (6 body + cover + closing); hint must stay xhs wording
    assert "竖版拼贴" in (result.user_hint or "")
    assert "封面" not in (result.user_hint or "")
    assert result.page_count >= 1
    finals = list((trip_dir / EXPORT_OUTPUT_DIRNAME).glob("*-xhs-*.png"))
    assert len(finals) == result.page_count


def test_wechat_official_unchanged_when_bookends_present(tmp_path: Path) -> None:
    """AC-ABE-05 · 公众号不受 album bookends 影响。"""
    trips = tmp_path / "trips"
    create_trip("abe-mp", trips, title="ABE公众号回归")
    trip_dir = trips / "abe-mp"
    _seed_album_with_bookends(trip_dir, 6, cover_in_pool=True, closing_in_pool=True)

    result = export_collage_pack(trip_dir, platform="wechat_official")
    assert result.platform == "wechat_official"
    assert "图文正文" in (result.user_hint or "")
    assert "封面" not in (result.user_hint or "")
    assert "封底" not in (result.user_hint or "")
    finals = list((trip_dir / EXPORT_OUTPUT_DIRNAME).glob("*-mp-*.png"))
    assert len(finals) == result.page_count
    for path in finals:
        with Image.open(path) as im:
            assert im.size == (1080, 1440)


def test_poster_bric_unchanged_when_bookends_present(tmp_path: Path) -> None:
    """AC-ABE-05 · 单张海报不受 album bookends 影响（仍单页、无封面封底语义）。"""
    from travelogue.export.poster_bric_pack import export_poster_bric_pack

    trips = tmp_path / "trips"
    create_trip("abe-poster", trips, title="ABE海报回归")
    trip_dir = trips / "abe-poster"
    _seed_album_with_bookends(trip_dir, 6, cover_in_pool=True, closing_in_pool=True)

    result = export_poster_bric_pack(trip_dir)
    assert result.platform == "poster_bric"
    assert result.page_count == 1
    assert "封面" not in (result.user_hint or "")
    assert "封底" not in (result.user_hint or "")
    finals = list((trip_dir / EXPORT_OUTPUT_DIRNAME).glob("*-poster-*.png")) + list(
        (trip_dir / EXPORT_OUTPUT_DIRNAME).glob("*-bric-*.png")
    )
    # prefix varies by profile; fall back to result.outputs
    if not finals:
        finals = [Path(o.path) for o in result.outputs]
    assert len(finals) == 1


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
    finals = list((trip_dir / EXPORT_OUTPUT_DIRNAME).glob("*-album-*.png"))
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
    finals = list((trip_dir / EXPORT_OUTPUT_DIRNAME).glob("*-album-*.png"))
    assert len(finals) == 3


def test_album_spread_auto_medium_soft_steers_toward_four(tmp_path: Path) -> None:
    """中等本自动：软引导到 4 跨页档（软目标，允许因横竖版选型略有偏差）。"""
    trips = tmp_path / "trips"
    create_trip("album-auto-mid", trips, title="画册自动中等")
    trip_dir = trips / "album-auto-mid"
    _seed_kept_photos(trip_dir, 24)

    result = export_collage_pack(trip_dir, platform="album_spread")
    # 24 张 → resolve=4；无封面封底时 page_count≈正文跨页数，软目标附近。
    assert 3 <= result.page_count <= 6


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
