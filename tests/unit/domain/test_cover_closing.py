"""Cover closing render helpers and integration."""

from __future__ import annotations

import json

from travelogue.paths import FIXTURES_DIR, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.copy_display import COPY_DISPLAY_PHOTOS
from travelogue.render.cover_closing import (
    last_chapter_curated_asset_id,
    last_screen_asset_id,
    resolve_closing_asset_id,
    show_closing_title,
)
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import render_html


def test_last_screen_asset_id() -> None:
    trip = {
        "chapters": [
            {"screens": [{"slots": [{"assetId": "a1"}]}]},
            {"screens": [{"slots": [{"assetId": "a2"}]}, {"slots": [{"assetId": "a3"}]}]},
        ]
    }
    assert last_screen_asset_id(trip) == "a3"


def test_resolve_closing_prefers_last_screen() -> None:
    trip = {
        "chapters": [
            {"screens": [{"slots": [{"assetId": "a1"}]}]},
            {"screens": [{"slots": [{"assetId": "last"}]}]},
        ]
    }
    assets = {
        "a1": {"id": "a1", "type": "image", "layoutEligible": True, "width": 1600, "height": 900},
        "last": {"id": "last", "type": "image", "layoutEligible": True, "width": 1600, "height": 900},
    }
    assert resolve_closing_asset_id(trip, assets) == "last"
    assert resolve_closing_asset_id(trip, assets, prefer_landscape=True) == "last"


def test_web_prefers_landscape_over_newer_portrait() -> None:
    trip = {
        "chapters": [
            {
                "screens": [
                    {"slots": [{"assetId": "wide"}]},
                    {"slots": [{"assetId": "portrait-last"}]},
                ]
            }
        ]
    }
    assets = {
        "wide": {
            "id": "wide",
            "type": "image",
            "layoutEligible": True,
            "width": 2048,
            "height": 1365,
        },
        "portrait-last": {
            "id": "portrait-last",
            "type": "image",
            "layoutEligible": True,
            "width": 1365,
            "height": 2048,
        },
    }
    assert resolve_closing_asset_id(trip, assets) == "portrait-last"
    assert resolve_closing_asset_id(trip, assets, prefer_landscape=True) == "wide"


def test_web_landscape_fallback_to_portrait_when_none() -> None:
    trip = {"chapters": [{"screens": [{"slots": [{"assetId": "portrait"}]}]}]}
    assets = {
        "portrait": {
            "id": "portrait",
            "type": "image",
            "layoutEligible": True,
            "width": 1200,
            "height": 1600,
        },
    }
    assert resolve_closing_asset_id(trip, assets, prefer_landscape=True) == "portrait"


def test_resolve_closing_falls_back_to_cover_when_only_cover_exists() -> None:
    trip = {
        "coverAssetId": "cover",
        "assets": [
            {"id": "cover", "type": "image", "layoutEligible": True, "width": 1600, "height": 900},
        ],
        "chapters": [{"screens": [{"slots": [{"assetId": "cover"}]}]}],
    }
    assets = {a["id"]: a for a in trip["assets"]}
    assert resolve_closing_asset_id(trip, assets) == "cover"


def test_render_keeps_cover_closing_when_only_cover_asset() -> None:
    trip = {
        "tripId": "closing-only-cover",
        "title": "仅封面",
        "meta": {"title": "仅封面", "place": "旅途"},
        "coverAssetId": "cover",
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
        ],
        "chapters": [
            {
                "id": "ch-01",
                "title": "第一章",
                "screens": [{"slots": [{"assetId": "cover"}]}],
            }
        ],
        "epilogue": "尾声一句",
    }
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
    )
    assert 'data-block="cover-closing"' in html


def test_resolve_closing_excludes_cover_even_when_last_screen() -> None:
    trip = {
        "coverAssetId": "cover",
        "assets": [
            {"id": "cover", "type": "image", "layoutEligible": True, "width": 1600, "height": 900},
            {"id": "first", "type": "image", "layoutEligible": True, "width": 1600, "height": 900},
        ],
        "chapters": [
            {"screens": [{"slots": [{"assetId": "first"}]}]},
            {"screens": [{"slots": [{"assetId": "cover"}]}]},
        ],
    }
    assets = {a["id"]: a for a in trip["assets"]}
    assert resolve_closing_asset_id(trip, assets) == "first"


def test_resolve_closing_excludes_cover_by_layout() -> None:
    trip = {
        "coverAssetId": "mobile-cover",
        "curation": {"coverByLayout": {"mobile": "mobile-cover", "web": "web-cover"}},
        "assets": [
            {"id": "mobile-cover", "type": "image", "layoutEligible": True, "width": 1200, "height": 1600},
            {"id": "web-cover", "type": "image", "layoutEligible": True, "width": 2048, "height": 1365},
            {"id": "alt-wide", "type": "image", "layoutEligible": True, "width": 2048, "height": 1365},
        ],
        "chapters": [{"screens": [{"slots": [{"assetId": "web-cover"}]}]}],
    }
    assets = {a["id"]: a for a in trip["assets"]}
    assert resolve_closing_asset_id(trip, assets, prefer_landscape=True) == "alt-wide"


def test_prefers_unused_asset_over_screen_duplicate() -> None:
    trip = {
        "coverAssetId": "cover",
        "assets": [
            {"id": "cover", "type": "image", "layoutEligible": True, "width": 1600, "height": 900},
            {"id": "on-page", "type": "image", "layoutEligible": True, "width": 1600, "height": 900},
            {
                "id": "fresh-wide",
                "type": "image",
                "layoutEligible": True,
                "width": 2048,
                "height": 1365,
                "dominantTone": "#223344",
            },
        ],
        "chapters": [{"screens": [{"slots": [{"assetId": "on-page"}]}]}],
    }
    assets = {a["id"]: a for a in trip["assets"]}
    assert resolve_closing_asset_id(trip, assets, prefer_landscape=True) == "fresh-wide"


def test_reuses_screen_image_when_no_unused_available() -> None:
    trip = {
        "assets": [
            {"id": "only", "type": "image", "layoutEligible": True, "width": 1600, "height": 900},
        ],
        "chapters": [{"screens": [{"slots": [{"assetId": "only"}]}]}],
    }
    assets = {a["id"]: a for a in trip["assets"]}
    assert resolve_closing_asset_id(trip, assets, prefer_landscape=True) == "only"


def test_last_chapter_curated_prefers_low_saturation() -> None:
    trip = {
        "chapters": [
            {
                "screens": [
                    {"slots": [{"assetId": "bright"}]},
                    {"slots": [{"assetId": "dusk"}]},
                ]
            }
        ]
    }
    assets = {
        "bright": {
            "id": "bright",
            "type": "image",
            "layoutEligible": True,
            "dominantTone": "#ffee00",
        },
        "dusk": {
            "id": "dusk",
            "type": "image",
            "layoutEligible": True,
            "dominantTone": "#223344",
            "subjectTags": ["evening"],
        },
    }
    assert last_chapter_curated_asset_id(trip, assets) == "dusk"


def test_resolve_closing_falls_back_to_curated() -> None:
    trip = {"chapters": [{"screens": [{"slots": [{"assetId": "bad"}]}]}]}
    assets = {
        "bad": {"id": "bad", "type": "video"},
        "dusk": {"id": "dusk", "type": "image", "layoutEligible": True, "dominantTone": "#223344"},
    }
    trip["chapters"][0]["screens"].append({"slots": [{"assetId": "dusk"}]})
    assert resolve_closing_asset_id(trip, assets) == "dusk"


def test_show_closing_title() -> None:
    assert show_closing_title("林芝") is True
    assert show_closing_title("") is False


def test_web_render_uses_cover_closing_not_inline_epilogue() -> None:
    trip = prepare_trip_web_screens(json.loads(FIXTURES_DIR.joinpath("trip.linzhi_screens.json").read_text(encoding="utf-8")))
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
    )
    assert 'data-block="cover-closing"' in html
    assert 'data-block="epilogue-screen"' not in html
    assert 'data-block="footer-cta"' not in html


def test_mobile_render_keeps_inline_epilogue_without_cover_closing() -> None:
    trip = prepare_trip_web_screens(json.loads(FIXTURES_DIR.joinpath("trip.linzhi_screens.json").read_text(encoding="utf-8")))
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="mobile",
        reading_profile_override="default_hybrid",
    )
    assert 'data-block="cover-closing"' not in html
    assert 'data-block="epilogue-screen"' in html or 'data-block="epilogue"' in html


def test_copy_display_css_hides_closing_narrative_not_screen() -> None:
    css = (TEMPLATE_VISUAL_JOURNAL / "copy-display.css").read_text(encoding="utf-8")
    assert ".cover-closing__text" in css
    assert ".cover-closing__stats" in css
    assert 'html[data-copy-display="photos"] [data-block="cover-closing"]' not in css


def test_photos_draft_still_emits_cover_closing_for_toggle() -> None:
    trip = prepare_trip_web_screens(json.loads(FIXTURES_DIR.joinpath("trip.linzhi_screens.json").read_text(encoding="utf-8")))
    html = render_html(
        trip,
        export_mode="draft",
        layout_engine_override="screens",
        export_layout_override="web",
        reading_profile_override="default_hybrid",
        copy_display_override=COPY_DISPLAY_PHOTOS,
    )
    assert 'data-block="cover-closing"' in html
    assert 'data-copy-display="photos"' in html
