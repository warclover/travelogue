"""Phase 23 · inline moment EXIF on layout-screen."""

from __future__ import annotations

from travelogue.render.engine import render_html
from travelogue.render.moment_exif import format_moment_exif_line


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
                "screens": [
                    {"slots": [{"assetId": "cover"}]},
                    {"role": "moment", "patternId": "screen-landscape-1", "slots": [{"assetId": "moment"}]},
                    {"slots": [{"assetId": "closing"}]},
                ],
            }
        ],
        "curation": {
            "momentPoolIds": ["moment"],
            "momentSecondaryIds": [],
            "momentPoolSize": 1,
        },
        "epilogue": "尾声一句",
    }


def test_format_moment_exif_line() -> None:
    trip = _moment_trip()
    asset = next(a for a in trip["assets"] if a["id"] == "moment")
    line = format_moment_exif_line(asset)
    assert line
    assert "林芝" in line


def test_web_render_inline_moment_exif_bar() -> None:
    trip = _moment_trip()
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
    )
    assert 'data-block="moment-screen"' not in html
    assert 'data-role="moment"' in html
    assert "moment-exif-bar" in html
    assert "林芝" in html
    assert html.count("moment-exif-bar") == 1
    moment_pos = html.index('data-role="moment"')
    closing_pos = html.index('data-block="cover-closing"')
    assert moment_pos < closing_pos


def test_skipped_moment_has_no_exif_bar() -> None:
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
    assert "moment-exif-bar" not in html
