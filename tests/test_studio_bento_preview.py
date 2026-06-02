"""Studio homepage v2 · user trip Bento preview API."""

from __future__ import annotations

from pathlib import Path

from travelogue.web.studio_bento_preview import build_trip_bento_preview


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
    (trip_dir / "demo-ch01.png").write_bytes(b"png")
    (trip_dir / "demo-ch02.png").write_bytes(b"png")
    (trip_dir / "demo-longshot.png").write_bytes(b"png")
    (trip_dir / "trip.json").write_text('{"meta":{"title":"Demo"}}', encoding="utf-8")
    trip = __import__("json").loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    payload = build_trip_bento_preview(trip_dir, trip, trip_id)
    assert payload is not None
    assert payload["assets"]["longshot"] == f"/{trip_id}/demo-longshot.png"
    chapter_pages = [p for p in payload["pages"] if p["role"] == "chapter"]
    assert len(chapter_pages) == 2


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
    assert payload["assets"]["longshot"] == f"/{trip_id}/assets/portrait.webp"


def test_build_trip_bento_preview_keeps_prerendered_pngs(tmp_path: Path) -> None:
    """已有 *-ch*.png / *-longshot.png 时不从原图重选。"""
    trip_id = "rendered"
    trip_dir = tmp_path / trip_id
    assets_dir = trip_dir / "assets"
    assets_dir.mkdir(parents=True)
    (trip_dir / "preview.jpg").write_bytes(b"jpg")
    (trip_dir / "trip-ch01.png").write_bytes(b"png")
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
