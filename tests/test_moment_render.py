"""Phase 23 · moment-screen render integration."""

from __future__ import annotations

from travelogue.render.engine import render_html
from travelogue.render.moment_screen import build_moment_screen_context


def _moment_trip() -> dict:
    return {
        "tripId": "moment-render",
        "title": "最佳时刻",
        "meta": {"title": "最佳时刻", "place": "林芝"},
        "coverAssetId": "cover",
        "momentAssetId": "moment",
        "exportLayout": "web",
        "layoutEngine": "screens",
        "assets": [
            {
                "id": "cover",
                "type": "image",
                "layoutEligible": True,
                "width": 1600,
                "height": 900,
                "paths": {"w800": "assets/cover-w800.webp", "w1600": "assets/cover-w1600.webp"},
            },
            {
                "id": "moment",
                "type": "image",
                "layoutEligible": True,
                "width": 2048,
                "height": 1365,
                "takenAt": "2024-06-14T07:15:00+08:00",
                "place": {"city": "林芝"},
                "exif": {
                    "model": "iPhone 15 Pro",
                    "focalLengthMm": 24,
                    "aperture": 1.8,
                    "shutter": "1/200",
                    "iso": 64,
                },
                "paths": {"w800": "assets/moment-w800.webp", "w1600": "assets/moment-w1600.webp"},
            },
            {
                "id": "closing",
                "type": "image",
                "layoutEligible": True,
                "width": 2048,
                "height": 1365,
                "paths": {"w800": "assets/closing-w800.webp", "w1600": "assets/closing-w1600.webp"},
            },
        ],
        "chapters": [
            {
                "id": "ch-01",
                "title": "第一章",
                "screens": [{"slots": [{"assetId": "cover"}]}, {"slots": [{"assetId": "closing"}]}],
            }
        ],
        "curation": {
            "momentPoolIds": ["moment"],
            "momentSecondaryIds": [],
            "momentPoolSize": 1,
        },
        "epilogue": "尾声一句",
    }


def test_build_moment_screen_context() -> None:
    trip = _moment_trip()
    assets = {a["id"]: a for a in trip["assets"]}
    ctx = build_moment_screen_context(
        trip,
        assets,
        export_layout="web",
        meta_title=trip["meta"]["title"],
    )
    assert ctx
    assert ctx["assetId"] == "moment"
    assert ctx["hasExifLine"] is True
    assert "林芝" in ctx["exifLine"]
    assert ctx["label"] == "决定性瞬间"


def test_english_moment_label() -> None:
    trip = _moment_trip()
    trip["meta"]["locale"] = "en-US"
    assets = {a["id"]: a for a in trip["assets"]}
    ctx = build_moment_screen_context(
        trip,
        assets,
        export_layout="web",
        meta_title=trip["meta"]["title"],
    )
    assert ctx
    assert ctx["label"] == "Moment"


def test_web_render_emits_single_moment_screen() -> None:
    trip = _moment_trip()
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
    )
    assert html.count('data-block="moment-screen"') == 1
    assert 'data-asset-id="moment"' in html
    assert "moment-exif-line" in html
    moment_pos = html.index('data-block="moment-screen"')
    closing_pos = html.index('data-block="cover-closing"')
    assert moment_pos < closing_pos


def test_skipped_moment_not_rendered() -> None:
    trip = _moment_trip()
    trip["curation"]["momentSkipped"] = "small_trip"
    trip.pop("momentAssetId", None)
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
    )
    assert 'data-block="moment-screen"' not in html
