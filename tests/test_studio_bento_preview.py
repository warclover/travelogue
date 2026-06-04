"""Studio homepage v2 · user trip Bento preview API."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from PIL import Image

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
    for name in ("a.webp", "b.webp", "c.webp"):
        (assets_dir / name).write_bytes(b"webp")
    trip = {
        "meta": {"title": "京都 · 雨后"},
        "assets": [
            {"id": "a1", "type": "image", "displayFile": "assets/a.webp", "layoutEligible": True},
            {"id": "a2", "type": "image", "displayFile": "assets/b.webp", "layoutEligible": True},
            {"id": "a3", "type": "image", "displayFile": "assets/c.webp", "layoutEligible": True},
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
    assert chapter_urls == [
        f"/{trip_id}/assets/a.webp",
        f"/{trip_id}/assets/b.webp",
        f"/{trip_id}/assets/c.webp",
    ]
    assert payload["pages"][-1]["url"] == f"/{trip_id}/assets/c.webp"


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
    assert payload["assets"]["longshot"] == f"/{trip_id}/preview.jpg"
    assert len(payload["longshotPages"]) == 3
    assert payload["longshotPages"][0]["url"] == f"/{trip_id}/preview.jpg"
    assert payload["longshotPages"][0]["scrollPreview"] is True


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
    assert chapter_urls == [
        f"/{trip_id}/assets/landscape.webp",
        f"/{trip_id}/assets/landscape.webp",
    ]


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
    """无导出长图时 · longshotPages 与 carousel 同序，章内选竖版。"""
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
    assert len(payload["longshotPages"]) == len(payload["pages"])
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
