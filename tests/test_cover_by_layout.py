"""Dual cover: mobile portrait vs web landscape."""

from __future__ import annotations

from travelogue.curation.curate import (
    _pick_cover_asset_id,
    resolve_cover_asset_id,
    sync_trip_covers,
)
from travelogue.render.engine import render_html


def _asset(aid: str, w: int, h: int) -> dict:
    return {
        "id": aid,
        "type": "image",
        "width": w,
        "height": h,
        "displayFile": f"assets/{aid}.webp",
    }


def test_sync_cover_by_layout_auto() -> None:
    assets = [
        _asset("port", 900, 2000),
        _asset("land", 2400, 1350),
        _asset("pano", 3000, 1000),
        _asset("p2", 900, 1600),
    ]
    trip = {"exportLayout": "auto", "assets": assets, "curation": {}}
    sync_trip_covers(trip, export_layout="auto")
    by = trip["curation"]["coverByLayout"]
    assert by["mobile"] == "port"
    assert by["web"] in ("land", "pano")
    assert trip["coverAssetId"] == by["mobile"]


def test_resolve_cover_at_render_profile() -> None:
    trip = {
        "exportLayout": "auto",
        "coverAssetId": "port",
        "assets": [
            _asset("port", 900, 2000),
            _asset("land", 1920, 1080),
            _asset("x", 1000, 1000),
            _asset("y", 1000, 1000),
        ],
        "curation": {"coverByLayout": {"mobile": "port", "web": "land"}},
        "chapters": [],
        "meta": {"title": "测", "places": ["京都"]},
    }
    assert resolve_cover_asset_id(trip, export_layout="mobile") == "port"
    assert resolve_cover_asset_id(trip, export_layout="web") == "land"


def test_dual_render_cover_src_differs() -> None:
    trip = {
        "exportLayout": "auto",
        "layoutEngine": "screens",
        "coverAssetId": "port",
        "assets": [
            _asset("port", 900, 2000),
            _asset("land", 1920, 1080),
            _asset("a3", 1200, 800),
            _asset("a4", 1200, 800),
        ],
        "curation": {"coverByLayout": {"mobile": "port", "web": "land"}},
        "chapters": [],
        "meta": {"title": "测", "dateStart": "2025-04-01", "dateEnd": "2025-04-02", "places": ["京都"]},
    }
    mobile_html = render_html(
        trip, export_layout_override="mobile", layout_engine_override="legacy"
    )
    web_html = render_html(
        trip, export_layout_override="web", layout_engine_override="screens"
    )
    assert "port" in mobile_html or "900" in mobile_html
    assert "land" in web_html or "1920" in web_html
    assert mobile_html != web_html


def test_pick_cover_web_excludes_portrait() -> None:
    assets = [_asset("port", 900, 2000), _asset("land", 1600, 900)]
    assert _pick_cover_asset_id(assets, export_layout="mobile") == "port"
    assert _pick_cover_asset_id(assets, export_layout="web") == "land"


def test_mobile_cover_prefers_portrait_thumb_over_landscape_photo() -> None:
    """WeChat-style portrait thumbs should win mobile cover over sharp landscapes."""
    assets = [
        {
            **_asset("land", 1920, 962),
            "mediaClass": "photo",
            "layoutEligible": True,
            "quality": {"sharpness": 2000.0},
        },
        {
            **_asset("port-thumb", 1280, 1920),
            "mediaClass": "thumbnail",
            "layoutEligible": True,
            "nativeWidth": 1280,
            "nativeHeight": 1920,
            "quality": {"sharpness": 800.0},
        },
    ]
    assert _pick_cover_asset_id(assets, export_layout="mobile") == "port-thumb"
    assert _pick_cover_asset_id(assets, export_layout="web") == "land"
