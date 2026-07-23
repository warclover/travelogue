"""Studio homepage v2 · user trip Bento preview API."""

from __future__ import annotations

import os
import time
from pathlib import Path
from urllib.parse import quote

from PIL import Image

from travelogue.export.longshot import write_longshot_current
from travelogue.web.studio_bento_preview import build_trip_bento_preview


def _write_png(path: Path, width: int, height: int) -> None:
    Image.new("RGB", (width, height), color="#808080").save(path)


def test_build_trip_bento_preview_from_preview_jpg(tmp_path: Path) -> None:
    trip_id = "kyoto-rain"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    (trip_dir / "trip.json").write_text(
        '{"meta":{"title":"京都 · 雨后"},"chapters":[{"id":"c1","title":"第一章"}],"assets":[{"type":"image"}]}',
        encoding="utf-8",
    )
    trip = __import__("json").loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    assert payload["source"] == "user"
    assert payload["title"] == "京都 · 雨后"
    assert payload["pages"][0]["role"] == "cover"
    assert payload["pages"][0]["url"] == f"/{trip_id}/preview.jpg"
    assert len(payload["pages"]) >= 3


def test_build_trip_bento_preview_with_chapter_pngs(tmp_path: Path) -> None:
    trip_id = "demo-trip"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    _write_png(trip_dir / "demo-ch01.png", 1600, 900)
    _write_png(trip_dir / "demo-ch02.png", 1600, 900)
    (trip_dir / "demo-longshot.png").write_bytes(b"png")
    (trip_dir / "trip.json").write_text(
        '{"meta":{"title":"Demo"},"chapters":[{"id":"c1","title":"第一章"},{"id":"c2","title":"第二章"}]}',
        encoding="utf-8",
    )
    trip = __import__("json").loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    assert payload["assets"]["longshot"] == f"/{trip_id}/demo-longshot.png"
    chapter_pages = [p for p in payload["pages"] if p["role"] == "chapter"]
    assert len(chapter_pages) == 2
    assert chapter_pages[0]["url"] == f"/{trip_id}/demo-ch01.png"
    assert chapter_pages[1]["url"] == f"/{trip_id}/demo-ch02.png"


def test_build_trip_bento_preview_none_without_preview(tmp_path: Path) -> None:
    trip_id = "empty"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text("{}", encoding="utf-8")
    payload = build_trip_bento_preview(trip_dir, {}, trip_id)
    assert payload is None


def test_build_trip_bento_preview_chapter_urls_from_trip_assets(tmp_path: Path) -> None:
    """无 *-ch*.png 时，各章应从 trip.json 首图派生不同 carousel URL。"""
    trip_id = "kyoto-rain"
    trip_dir = tmp_path / trip_id
    assets_dir = trip_dir / "assets"
    assets_dir.mkdir(parents=True)
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    for name in ("cover.webp", "a.webp", "b.webp", "c.webp"):
        (assets_dir / name).write_bytes(b"webp")
    trip = {
        "meta": {"title": "京都 · 雨后"},
        "assets": [
            {"id": "a0", "type": "image", "displayFile": "assets/cover.webp", "aspectKind": "landscape", "width": 1600, "height": 900, "layoutEligible": True},
            {"id": "a1", "type": "image", "displayFile": "assets/a.webp", "aspectKind": "landscape", "width": 1600, "height": 900, "layoutEligible": True},
            {"id": "a2", "type": "image", "displayFile": "assets/b.webp", "aspectKind": "landscape", "width": 1600, "height": 900, "layoutEligible": True},
            {"id": "a3", "type": "image", "displayFile": "assets/c.webp", "aspectKind": "landscape", "width": 1600, "height": 900, "layoutEligible": True},
        ],
        "chapters": [
            {
                "id": "c1",
                "title": "第一章",
                "screens": [{"screenId": "s1", "slots": [{"assetId": "a1"}]}],
            },
            {
                "id": "c2",
                "title": "第二章",
                "screens": [{"screenId": "s2", "slots": [{"assetId": "a2"}]}],
            },
            {
                "id": "c3",
                "title": "第三章",
                "screens": [{"screenId": "s3", "slots": [{"assetId": "a3"}]}],
            },
        ],
    }
    (trip_dir / "trip.json").write_text(__import__("json").dumps(trip), encoding="utf-8")

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    # 封面用横图（专属封面资产），绝不用竖版 preview.jpg（封面卡下半为深色标题带 → 16:9 框内黑块）
    assert payload["pages"][0]["url"] == f"/{trip_id}/assets/cover.webp"
    chapter_urls = [p["url"] for p in payload["pages"] if p["role"] == "chapter"]
    assert chapter_urls == [
        f"/{trip_id}/assets/a.webp",
        f"/{trip_id}/assets/b.webp",
        f"/{trip_id}/assets/c.webp",
    ]
    # 轮播页一律横图，preview.jpg 不得出现
    assert f"/{trip_id}/preview.jpg" not in [p["url"] for p in payload["pages"]]
    assert payload["pages"][-1]["url"] != chapter_urls[-1]


def test_build_trip_bento_preview_epilogue_differs_from_last_chapter(tmp_path: Path) -> None:
    """尾声页不得与最后一章 carousel 使用同一 URL。"""
    trip_id = "dedupe-epilogue"
    trip_dir = tmp_path / trip_id
    assets_dir = trip_dir / "assets"
    assets_dir.mkdir(parents=True)
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    for name in ("a.webp", "b.webp", "c.webp", "d.webp"):
        (assets_dir / name).write_bytes(b"webp")
    trip = {
        "meta": {"title": "去重测试"},
        "assets": [
            {"id": "a1", "type": "image", "displayFile": "assets/a.webp", "aspectKind": "landscape", "width": 1600, "height": 900, "layoutEligible": True},
            {"id": "a2", "type": "image", "displayFile": "assets/b.webp", "aspectKind": "landscape", "width": 1600, "height": 900, "layoutEligible": True},
            {"id": "a3", "type": "image", "displayFile": "assets/c.webp", "aspectKind": "landscape", "width": 1600, "height": 900, "layoutEligible": True},
            {"id": "a4", "type": "image", "displayFile": "assets/d.webp", "aspectKind": "landscape", "width": 1600, "height": 900, "layoutEligible": True},
        ],
        "chapters": [
            {
                "id": "c1",
                "title": "第一章",
                "screens": [{"screenId": "s1", "slots": [{"assetId": "a1"}]}],
            },
            {
                "id": "c2",
                "title": "第二章",
                "screens": [{"screenId": "s2", "slots": [{"assetId": "a2"}]}],
            },
            {
                "id": "c3",
                "title": "第三章",
                "screens": [{"screenId": "s3", "slots": [{"assetId": "a3"}]}],
            },
        ],
    }
    (trip_dir / "trip.json").write_text(__import__("json").dumps(trip), encoding="utf-8")

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    chapter_urls = [p["url"] for p in payload["pages"] if p["role"] == "chapter"]
    epilogue_url = payload["pages"][-1]["url"]
    assert epilogue_url != chapter_urls[-1]


def test_build_trip_bento_preview_carousel_page_urls_unique(tmp_path: Path) -> None:
    """Web carousel 各页 URL 互不重复（含封面 vs 第三章）。"""
    trip_id = "carousel-dedupe"
    trip_dir = tmp_path / trip_id
    assets_dir = trip_dir / "assets"
    assets_dir.mkdir(parents=True)
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    for name in ("hero.webp", "ch1.webp", "ch2.webp", "ch3a.webp", "ch3b.webp", "epi.webp"):
        (assets_dir / name).write_bytes(b"webp")
    trip = {
        "meta": {"title": "去重轮播"},
        "coverAssetId": "hero",
        "assets": [
            {
                "id": "hero",
                "type": "image",
                "displayFile": "assets/hero.webp",
                "aspectKind": "landscape",
                "width": 1600,
                "height": 900,
                "layoutEligible": True,
            },
            {
                "id": "a1",
                "type": "image",
                "displayFile": "assets/ch1.webp",
                "aspectKind": "landscape",
                "width": 1600,
                "height": 900,
                "layoutEligible": True,
            },
            {
                "id": "a2",
                "type": "image",
                "displayFile": "assets/ch2.webp",
                "aspectKind": "landscape",
                "width": 1600,
                "height": 900,
                "layoutEligible": True,
            },
            {
                "id": "a3",
                "type": "image",
                "displayFile": "assets/hero.webp",
                "aspectKind": "landscape",
                "width": 1600,
                "height": 900,
                "layoutEligible": True,
            },
            {
                "id": "a3b",
                "type": "image",
                "displayFile": "assets/ch3b.webp",
                "aspectKind": "landscape",
                "width": 1600,
                "height": 900,
                "layoutEligible": True,
            },
            {
                "id": "epi",
                "type": "image",
                "displayFile": "assets/epi.webp",
                "aspectKind": "landscape",
                "width": 1600,
                "height": 900,
                "layoutEligible": True,
            },
        ],
        "chapters": [
            {
                "id": "c1",
                "title": "第一章",
                "screens": [{"screenId": "s1", "slots": [{"assetId": "a1"}]}],
            },
            {
                "id": "c2",
                "title": "第二章",
                "screens": [{"screenId": "s2", "slots": [{"assetId": "a2"}]}],
            },
            {
                "id": "c3",
                "title": "第三章",
                "screens": [{"screenId": "s3", "slots": [{"assetId": "a3"}, {"assetId": "a3b"}]}],
            },
        ],
    }
    (trip_dir / "trip.json").write_text(__import__("json").dumps(trip), encoding="utf-8")

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    urls = [p["url"] for p in payload["pages"]]
    assert len(urls) == len(set(urls))
    assert payload["pages"][0]["url"] == f"/{trip_id}/assets/hero.webp"
    chapter_urls = [p["url"] for p in payload["pages"] if p["role"] == "chapter"]
    assert chapter_urls[0] == f"/{trip_id}/assets/ch1.webp"
    assert chapter_urls[2] == f"/{trip_id}/assets/ch3b.webp"
    assert chapter_urls[2] != payload["pages"][0]["url"]


def test_build_trip_bento_preview_web_carousel_landscape_only(tmp_path: Path) -> None:
    """Web 轮播 · 章内仅有竖图时回退 preview.jpg，不选 portrait。"""
    trip_id = "portrait-only-ch"
    trip_dir = tmp_path / trip_id
    assets_dir = trip_dir / "assets"
    assets_dir.mkdir(parents=True)
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    for name in ("portrait.webp", "landscape.webp"):
        (assets_dir / name).write_bytes(b"webp")
    trip = {
        "meta": {"title": "竖图章节"},
        "assets": [
            {
                "id": "p1",
                "type": "image",
                "displayFile": "assets/portrait.webp",
                "aspectKind": "portrait",
                "width": 900,
                "height": 1600,
                "layoutEligible": True,
            },
            {
                "id": "l1",
                "type": "image",
                "displayFile": "assets/landscape.webp",
                "aspectKind": "landscape",
                "width": 1600,
                "height": 900,
                "layoutEligible": True,
            },
        ],
        "chapters": [
            {
                "id": "c1",
                "title": "第一章",
                "screens": [{"screenId": "s1", "slots": [{"assetId": "p1"}]}],
            },
        ],
    }
    (trip_dir / "trip.json").write_text(__import__("json").dumps(trip), encoding="utf-8")

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    web_urls = [p["url"] for p in payload["pages"]]
    assert f"/{trip_id}/assets/portrait.webp" not in web_urls
    # 封面优先横图；无横图时才回退 preview.jpg（此处有横图，故用 landscape.webp）
    assert payload["pages"][0]["url"] == f"/{trip_id}/assets/landscape.webp"
    assert f"/{trip_id}/preview.jpg" not in web_urls
    chapter_urls = [p["url"] for p in payload["pages"] if p["role"] == "chapter"]
    assert chapter_urls == [f"/{trip_id}/assets/landscape.webp"]


def test_build_trip_bento_preview_prefers_landscape_for_web(tmp_path: Path) -> None:
    """Web 轮播 · 章内有多张图时优先横版。"""
    trip_id = "mixed-aspect"
    trip_dir = tmp_path / trip_id
    assets_dir = trip_dir / "assets"
    assets_dir.mkdir(parents=True)
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    for name in ("portrait.webp", "landscape.webp"):
        (assets_dir / name).write_bytes(b"webp")
    trip = {
        "meta": {"title": "混合构图"},
        "assets": [
            {
                "id": "p1",
                "type": "image",
                "displayFile": "assets/portrait.webp",
                "aspectKind": "portrait",
                "width": 900,
                "height": 1600,
                "layoutEligible": True,
            },
            {
                "id": "l1",
                "type": "image",
                "displayFile": "assets/landscape.webp",
                "aspectKind": "landscape",
                "width": 1600,
                "height": 900,
                "layoutEligible": True,
            },
        ],
        "chapters": [
            {
                "id": "c1",
                "title": "第一章",
                "screens": [
                    {
                        "screenId": "s1",
                        "slots": [{"assetId": "p1"}, {"assetId": "l1"}],
                    }
                ],
            },
        ],
    }
    (trip_dir / "trip.json").write_text(__import__("json").dumps(trip), encoding="utf-8")

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    # 有横图时封面/背景用横图，不用竖版 preview.jpg
    assert payload["pages"][0]["url"] == f"/{trip_id}/assets/landscape.webp"
    chapter_urls = [p["url"] for p in payload["pages"] if p["role"] == "chapter"]
    assert chapter_urls == [f"/{trip_id}/assets/landscape.webp"]
    assert payload["assets"]["background"] == f"/{trip_id}/assets/landscape.webp"


def test_build_trip_bento_preview_prefers_portrait_for_longshot(tmp_path: Path) -> None:
    """手机框 · 无 longshot PNG 时优先竖版。"""
    trip_id = "mixed-aspect"
    trip_dir = tmp_path / trip_id
    assets_dir = trip_dir / "assets"
    assets_dir.mkdir(parents=True)
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    for name in ("portrait.webp", "landscape.webp"):
        (assets_dir / name).write_bytes(b"webp")
    trip = {
        "meta": {"title": "混合构图"},
        "coverAssetId": "l1",
        "assets": [
            {
                "id": "p1",
                "type": "image",
                "displayFile": "assets/portrait.webp",
                "aspectKind": "portrait",
                "width": 900,
                "height": 1600,
                "layoutEligible": True,
            },
            {
                "id": "l1",
                "type": "image",
                "displayFile": "assets/landscape.webp",
                "aspectKind": "landscape",
                "width": 1600,
                "height": 900,
                "layoutEligible": True,
            },
        ],
        "chapters": [
            {
                "id": "c1",
                "title": "第一章",
                "screens": [{"screenId": "s1", "slots": [{"assetId": "l1"}]}],
            },
        ],
    }
    (trip_dir / "trip.json").write_text(__import__("json").dumps(trip), encoding="utf-8")

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    assert len(payload["longshotPages"]) == 1
    assert payload["longshotPages"][0]["url"] == f"/{trip_id}/assets/landscape.webp"
    assert payload["longshotPages"][0]["scrollPreview"] is True
    assert payload["assets"]["longshot"] == payload["longshotPages"][0]["url"]


def test_build_trip_bento_preview_longshot_pages_from_vertical_ch_pngs(tmp_path: Path) -> None:
    """手机框 · 竖条 *-ch*.png 按章堆叠为 longshotPages。"""
    trip_id = "mobile-strips"
    trip_dir = tmp_path / trip_id
    assets_dir = trip_dir / "assets"
    assets_dir.mkdir(parents=True)
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    _write_png(trip_dir / "trip-ch01.png", 390, 8000)
    _write_png(trip_dir / "trip-ch02.png", 390, 6000)
    (assets_dir / "landscape.webp").write_bytes(b"webp")
    trip = {
        "meta": {"title": "竖条章节"},
        "assets": [
            {
                "id": "l1",
                "type": "image",
                "displayFile": "assets/landscape.webp",
                "aspectKind": "landscape",
                "layoutEligible": True,
            },
        ],
        "chapters": [
            {"id": "c1", "title": "第一章"},
            {"id": "c2", "title": "第二章"},
        ],
    }
    (trip_dir / "trip.json").write_text(__import__("json").dumps(trip), encoding="utf-8")

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    assert len(payload["longshotPages"]) == 2
    assert payload["longshotPages"][0]["url"] == f"/{trip_id}/trip-ch01.png"
    assert payload["longshotPages"][1]["url"] == f"/{trip_id}/trip-ch02.png"
    assert payload["longshotPages"][0]["scrollPreview"] is True
    assert payload["longshotPages"][0]["label"] == "第一章"
    chapter_urls = [p["url"] for p in payload["pages"] if p["role"] == "chapter"]
    # 仅一张横图时，横图耗尽后复用横图，而非把竖版 preview.jpg 塞进 16:9 轮播
    assert chapter_urls == [
        f"/{trip_id}/assets/landscape.webp",
        f"/{trip_id}/assets/landscape.webp",
    ]
    assert f"/{trip_id}/preview.jpg" not in [p["url"] for p in payload["pages"]]


def test_build_trip_bento_preview_longshot_pages_single_export_png(tmp_path: Path) -> None:
    trip_id = "exported"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    _write_png(trip_dir / "trip-longshot.png", 1080, 12000)
    (trip_dir / "trip.json").write_text('{"meta":{"title":"导出长图"}}', encoding="utf-8")
    trip = __import__("json").loads((trip_dir / "trip.json").read_text(encoding="utf-8"))

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    assert payload["longshotPages"] == [
        {
            "id": "longshot",
            "label": "微信长图",
            "url": f"/{trip_id}/trip-longshot.png",
            "scrollPreview": True,
        }
    ]


def test_build_trip_bento_preview_longshot_pages_single_export_jpg(tmp_path: Path) -> None:
    trip_id = "exported-jpg"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    Image.new("RGB", (1080, 12000), color="#808080").save(trip_dir / "trip-longshot.jpg")
    (trip_dir / "trip.json").write_text('{"meta":{"title":"导出长图"}}', encoding="utf-8")
    trip = __import__("json").loads((trip_dir / "trip.json").read_text(encoding="utf-8"))

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    assert payload["longshotPages"] == [
        {
            "id": "longshot",
            "label": "微信长图",
            "url": f"/{trip_id}/trip-longshot.jpg",
            "scrollPreview": True,
        }
    ]


def test_build_trip_bento_preview_longshot_pages_sfi_display_name(tmp_path: Path) -> None:
    """SFI D-SFI-07 · 整卷 ``*-长图.png`` 须进入手机框可滚预览。"""
    trip_id = "sfi-whole"
    trip_dir = tmp_path / trip_id
    assets_dir = trip_dir / "assets"
    assets_dir.mkdir(parents=True)
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    filename = "京都雨季漫游-长图.png"
    _write_png(trip_dir / filename, 1080, 16000)
    # Portrait assets must not win over the real export.
    _write_png(assets_dir / "portrait-w1600.webp", 900, 1600)
    trip = {
        "meta": {"title": "京都雨季漫游"},
        "assets": [
            {
                "id": "p1",
                "type": "image",
                "displayFile": "assets/portrait-w1600.webp",
                "aspectKind": "portrait",
                "width": 900,
                "height": 1600,
                "layoutEligible": True,
            }
        ],
        "chapters": [{"id": "c1", "title": "第一章", "items": [{"type": "media-card", "assetId": "p1"}]}],
    }
    (trip_dir / "trip.json").write_text(__import__("json").dumps(trip), encoding="utf-8")

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    assert payload["longshotPages"] == [
        {
            "id": "longshot",
            "label": "微信长图",
            "url": f"/{trip_id}/{quote(filename)}",
            "scrollPreview": True,
        }
    ]
    assert payload["assets"]["longshot"] == payload["longshotPages"][0]["url"]


def test_build_trip_bento_preview_longshot_pages_sfi_segments(tmp_path: Path) -> None:
    """SFI 分段 ``*-长图-NN.jpg`` 按序进入手机框。"""
    trip_id = "sfi-segments"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    Image.new("RGB", (1284, 20000), color="#808080").save(trip_dir / "精选册-长图-01.jpg")
    Image.new("RGB", (1284, 18000), color="#808080").save(trip_dir / "精选册-长图-02.jpg")
    Image.new("RGB", (1284, 15000), color="#808080").save(trip_dir / "精选册-长图-03.jpg")
    (trip_dir / "trip.json").write_text(
        '{"meta":{"title":"精选册"},"chapters":[{"id":"c1","title":"第一章"},{"id":"c2","title":"第二章"},{"id":"c3","title":"第三章"}]}',
        encoding="utf-8",
    )
    trip = __import__("json").loads((trip_dir / "trip.json").read_text(encoding="utf-8"))

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    assert len(payload["longshotPages"]) == 3
    assert payload["longshotPages"][0]["url"] == f"/{trip_id}/{quote('精选册-长图-01.jpg')}"
    assert payload["longshotPages"][1]["url"] == f"/{trip_id}/{quote('精选册-长图-02.jpg')}"
    assert payload["longshotPages"][2]["url"] == f"/{trip_id}/{quote('精选册-长图-03.jpg')}"
    assert all(p.get("scrollPreview") is True for p in payload["longshotPages"])


def test_build_trip_bento_preview_longshot_pages_moments_segments(tmp_path: Path) -> None:
    """朋友圈 ``*-moments-NN.png`` 在无整卷/分段长图时进入手机框。"""
    trip_id = "moments-only"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    _write_png(trip_dir / "精选 · 周末-moments-01.png", 1080, 5000)
    _write_png(trip_dir / "精选 · 周末-moments-02.png", 1080, 4800)
    (trip_dir / "trip.json").write_text(
        '{"meta":{"title":"精选 · 周末"},"chapters":[{"id":"c1","title":"上"},{"id":"c2","title":"下"}]}',
        encoding="utf-8",
    )
    trip = __import__("json").loads((trip_dir / "trip.json").read_text(encoding="utf-8"))

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    assert len(payload["longshotPages"]) == 2
    assert payload["longshotPages"][0]["url"] == f"/{trip_id}/{quote('精选 · 周末-moments-01.png')}"
    assert payload["longshotPages"][1]["url"] == f"/{trip_id}/{quote('精选 · 周末-moments-02.png')}"
    assert all(p.get("scrollPreview") is True for p in payload["longshotPages"])


def test_build_trip_bento_preview_picks_newer_mtime_when_no_current(tmp_path: Path) -> None:
    """AC-QFX-11 · 无 current 时整卷选 (mtime,name) 更新者，而非名序首项。"""
    trip_id = "mtime-pick"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    old_name = "AAA-旧标题-长图.png"
    new_name = "ZZZ-新标题-长图.png"
    _write_png(trip_dir / old_name, 1080, 12000)
    time.sleep(0.02)
    _write_png(trip_dir / new_name, 1080, 12000)
    now = time.time()
    os.utime(trip_dir / old_name, (now - 100, now - 100))
    os.utime(trip_dir / new_name, (now, now))
    (trip_dir / "trip.json").write_text(
        '{"meta":{"title":"改标题"}}',
        encoding="utf-8",
    )
    trip = __import__("json").loads((trip_dir / "trip.json").read_text(encoding="utf-8"))

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    assert payload["longshotPages"][0]["url"] == f"/{trip_id}/{quote(new_name)}"
    assert payload["assets"]["longshot"] == payload["longshotPages"][0]["url"]


def test_build_trip_bento_preview_rejects_incomplete_sfi_segments(tmp_path: Path) -> None:
    """AC-QFX-25 分段 · 不完整 *-长图-NN* 批不得进入预览。"""
    trip_id = "incomplete-seg"
    trip_dir = tmp_path / trip_id
    assets_dir = trip_dir / "assets"
    assets_dir.mkdir(parents=True)
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    _write_png(trip_dir / "半批-长图-01.png", 390, 8000)
    # 缺 02 → 完整批解析失败；应回落竖版原图而非半批
    _write_png(assets_dir / "portrait-w900.webp", 900, 1600)
    trip = {
        "meta": {"title": "半批"},
        "assets": [
            {
                "id": "p1",
                "type": "image",
                "displayFile": "assets/portrait-w900.webp",
                "aspectKind": "portrait",
                "width": 900,
                "height": 1600,
                "layoutEligible": True,
            }
        ],
        "chapters": [
            {"id": "c1", "title": "第一章", "items": [{"type": "media-card", "assetId": "p1"}]}
        ],
    }
    (trip_dir / "trip.json").write_text(__import__("json").dumps(trip), encoding="utf-8")
    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    urls = [p["url"] for p in payload["longshotPages"]]
    assert not any("半批-长图-01" in u for u in urls)


def test_build_trip_bento_preview_prefers_current_over_name_order(tmp_path: Path) -> None:
    """AC-QFX-25 · 有 current 时忽略名序更前的旧文件。"""
    trip_id = "current-pick"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    old_name = "AAA-旧标题-长图.png"
    new_name = "ZZZ-新标题-长图.png"
    _write_png(trip_dir / old_name, 1080, 12000)
    _write_png(trip_dir / new_name, 1080, 12000)
    write_longshot_current(
        trip_dir,
        batch_id="batch-retitle",
        kind="whole",
        files=[new_name],
    )
    (trip_dir / "trip.json").write_text(
        '{"meta":{"title":"权威清单"}}',
        encoding="utf-8",
    )
    trip = __import__("json").loads((trip_dir / "trip.json").read_text(encoding="utf-8"))

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    assert payload["longshotPages"] == [
        {
            "id": "longshot",
            "label": "微信长图",
            "url": f"/{trip_id}/{quote(new_name)}",
            "scrollPreview": True,
        }
    ]


def test_build_trip_bento_preview_longshot_pages_from_vertical_ch_jpgs(tmp_path: Path) -> None:
    trip_id = "mobile-strips-jpg"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    Image.new("RGB", (390, 8000), color="#808080").save(trip_dir / "trip-ch01.jpg")
    Image.new("RGB", (390, 6000), color="#808080").save(trip_dir / "trip-ch02.jpg")
    (trip_dir / "trip.json").write_text(
        '{"meta":{"title":"竖条章节"},"chapters":[{"id":"c1","title":"第一章"},{"id":"c2","title":"第二章"}]}',
        encoding="utf-8",
    )
    trip = __import__("json").loads((trip_dir / "trip.json").read_text(encoding="utf-8"))

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    assert len(payload["longshotPages"]) == 2
    assert payload["longshotPages"][0]["url"] == f"/{trip_id}/trip-ch01.jpg"
    assert payload["longshotPages"][1]["url"] == f"/{trip_id}/trip-ch02.jpg"


def test_build_trip_bento_preview_longshot_pages_match_carousel_chapters(tmp_path: Path) -> None:
    """无导出长图时 · longshotPages 仅含各章竖版（不含封面/尾声 preview）。"""
    trip_id = "dongao-like"
    trip_dir = tmp_path / trip_id
    assets_dir = trip_dir / "assets"
    assets_dir.mkdir(parents=True)
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    for name in ("p1.webp", "p2.webp", "l1.webp", "l2.webp"):
        (assets_dir / name).write_bytes(b"webp")
    trip = {
        "meta": {"title": "东澳岛"},
        "assets": [
            {
                "id": "p1",
                "type": "image",
                "displayFile": "assets/p1.webp",
                "aspectKind": "portrait",
                "width": 900,
                "height": 1600,
                "layoutEligible": True,
            },
            {
                "id": "p2",
                "type": "image",
                "displayFile": "assets/p2.webp",
                "aspectKind": "portrait",
                "width": 900,
                "height": 1500,
                "layoutEligible": True,
            },
            {
                "id": "l1",
                "type": "image",
                "displayFile": "assets/l1.webp",
                "aspectKind": "landscape",
                "width": 1600,
                "height": 900,
                "layoutEligible": True,
            },
            {
                "id": "l2",
                "type": "image",
                "displayFile": "assets/l2.webp",
                "aspectKind": "landscape",
                "width": 1600,
                "height": 900,
                "layoutEligible": True,
            },
        ],
        "chapters": [
            {
                "id": "c1",
                "title": "第一章",
                "screens": [{"screenId": "s1", "slots": [{"assetId": "l1"}, {"assetId": "p1"}]}],
            },
            {
                "id": "c2",
                "title": "第二章",
                "screens": [{"screenId": "s2", "slots": [{"assetId": "l2"}, {"assetId": "p2"}]}],
            },
        ],
    }
    (trip_dir / "trip.json").write_text(__import__("json").dumps(trip), encoding="utf-8")

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    assert len(payload["longshotPages"]) == 2
    assert all(p.get("scrollPreview") is True for p in payload["longshotPages"])
    chapter_longshots = [p["url"] for p in payload["longshotPages"] if p.get("chapterIndex")]
    assert chapter_longshots == [
        f"/{trip_id}/assets/p1.webp",
        f"/{trip_id}/assets/p2.webp",
    ]


def test_build_trip_bento_preview_keeps_landscape_chapter_pngs(tmp_path: Path) -> None:
    """横版 *-ch*.png 仍可直接用于 Web 轮播。"""
    trip_id = "rendered"
    trip_dir = tmp_path / trip_id
    assets_dir = trip_dir / "assets"
    assets_dir.mkdir(parents=True)
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    _write_png(trip_dir / "trip-ch01.png", 1600, 900)
    (trip_dir / "trip-longshot.png").write_bytes(b"png")
    (assets_dir / "landscape.webp").write_bytes(b"webp")
    trip = {
        "meta": {"title": "已渲染"},
        "assets": [
            {
                "id": "l1",
                "type": "image",
                "displayFile": "assets/landscape.webp",
                "aspectKind": "landscape",
                "layoutEligible": True,
            },
        ],
        "chapters": [{"id": "c1", "title": "第一章"}],
    }
    (trip_dir / "trip.json").write_text(__import__("json").dumps(trip), encoding="utf-8")

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    assert payload["pages"][1]["url"] == f"/{trip_id}/trip-ch01.png"
    assert payload["assets"]["longshot"] == f"/{trip_id}/trip-longshot.png"


def test_build_trip_bento_preview_skips_vertical_chapter_pngs(tmp_path: Path) -> None:
    """竖条 *-ch*.png（手机长图切条）应回退到 trip 横版资产。"""
    trip_id = "mobile-strip"
    trip_dir = tmp_path / trip_id
    assets_dir = trip_dir / "assets"
    assets_dir.mkdir(parents=True)
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    _write_png(trip_dir / "trip-ch01.png", 390, 11437)
    (assets_dir / "landscape.webp").write_bytes(b"webp")
    trip = {
        "meta": {"title": "竖条章节"},
        "assets": [
            {
                "id": "l1",
                "type": "image",
                "displayFile": "assets/landscape.webp",
                "aspectKind": "landscape",
                "width": 1600,
                "height": 900,
                "layoutEligible": True,
            },
            {
                "id": "p1",
                "type": "image",
                "displayFile": "assets/portrait.webp",
                "aspectKind": "portrait",
                "width": 900,
                "height": 1600,
                "layoutEligible": True,
            },
        ],
        "chapters": [
            {
                "id": "c1",
                "title": "第一章",
                "screens": [{"screenId": "s1", "slots": [{"assetId": "p1"}, {"assetId": "l1"}]}],
            },
        ],
    }
    (assets_dir / "portrait.webp").write_bytes(b"webp")
    (trip_dir / "trip.json").write_text(__import__("json").dumps(trip), encoding="utf-8")

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    chapter_urls = [p["url"] for p in payload["pages"] if p["role"] == "chapter"]
    assert chapter_urls == [f"/{trip_id}/assets/landscape.webp"]


def test_build_trip_bento_preview_encodes_unicode_longshot_urls(tmp_path: Path) -> None:
    """M14 分段长图中文文件名 · longshotPages URL 须 percent-encode。"""
    trip_id = "unicode-title"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    filename = "东澳岛-ch01.png"
    _write_png(trip_dir / filename, 390, 800)
    (trip_dir / "trip.json").write_text(
        '{"meta":{"title":"东澳岛"},"chapters":[{"id":"c1","title":"4月20-23日"}]}',
        encoding="utf-8",
    )
    trip = __import__("json").loads((trip_dir / "trip.json").read_text(encoding="utf-8"))

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    expected = f"/{trip_id}/{quote(filename)}"
    assert payload["longshotPages"][0]["url"] == expected
    assert payload["longshotPages"][0]["scrollPreview"] is True


def test_build_trip_bento_preview_prefers_w1600_over_w3200(tmp_path: Path) -> None:
    """Homepage Bento 应优先中档 WebP，避免一次解码多张 w3200。"""
    trip_id = "mid-size"
    trip_dir = tmp_path / trip_id
    assets_dir = trip_dir / "assets"
    assets_dir.mkdir(parents=True)
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    for stem in ("cover", "a", "b", "c"):
        for width in (800, 1600, 2400, 3200):
            (assets_dir / f"{stem}-w{width}.webp").write_bytes(b"webp")
    trip = {
        "meta": {"title": "中档预览"},
        "coverAssetId": "a0",
        "assets": [
            {
                "id": "a0",
                "type": "image",
                "displayFile": "assets/cover-w3200.webp",
                "aspectKind": "landscape",
                "width": 3200,
                "height": 1800,
                "layoutEligible": True,
            },
            {
                "id": "a1",
                "type": "image",
                "displayFile": "assets/a-w3200.webp",
                "aspectKind": "landscape",
                "width": 3200,
                "height": 1800,
                "layoutEligible": True,
            },
            {
                "id": "a2",
                "type": "image",
                "displayFile": "assets/b-w3200.webp",
                "aspectKind": "landscape",
                "width": 3200,
                "height": 1800,
                "layoutEligible": True,
            },
            {
                "id": "a3",
                "type": "image",
                "displayFile": "assets/c-w3200.webp",
                "aspectKind": "landscape",
                "width": 3200,
                "height": 1800,
                "layoutEligible": True,
            },
        ],
        "chapters": [
            {
                "id": "c1",
                "title": "第一章",
                "screens": [{"screenId": "s1", "slots": [{"assetId": "a1"}]}],
            },
            {
                "id": "c2",
                "title": "第二章",
                "screens": [{"screenId": "s2", "slots": [{"assetId": "a2"}]}],
            },
        ],
    }
    (trip_dir / "trip.json").write_text(__import__("json").dumps(trip), encoding="utf-8")

    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    urls = [p["url"] for p in payload["pages"]]
    assert all("-w1600.webp" in u for u in urls)
    assert not any("-w3200.webp" in u for u in urls)
    assert payload["assets"]["background"].endswith("cover-w1600.webp")
