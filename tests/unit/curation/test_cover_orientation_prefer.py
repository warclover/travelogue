"""UX-BE-09 · soft orientation prefer + explainable fallback."""

from __future__ import annotations

from travelogue.curation.curate import sync_trip_covers
from travelogue.curation.curate_scoring import (
    pick_cover_asset_id,
    pick_cover_asset_id_with_meta,
)
from travelogue.cover_engine.api import build_bookends_studio_payload


def _asset(aid: str, w: int, h: int, *, sharp: float = 120.0, overall: float = 0.6) -> dict:
    return {
        "id": aid,
        "type": "image",
        "width": w,
        "height": h,
        "displayFile": f"assets/{aid}.webp",
        "mediaClass": "photo",
        "layoutEligible": True,
        "dateConfidence": "high",
        "quality": {"sharpness": sharp},
        "aesthetic": {"overall": overall},
    }


def test_web_prefers_landscape_when_both_exist() -> None:
    assets = [_asset("port", 900, 2000), _asset("land", 1600, 900)]
    cover_id, meta = pick_cover_asset_id_with_meta(assets, export_layout="web")
    assert cover_id == "land"
    assert meta["orientationMatched"] is True
    assert meta["orientationFallback"] is False
    assert meta["preferredOrientation"] == "landscape"


def test_mobile_prefers_portrait_when_both_exist() -> None:
    assets = [_asset("port", 900, 2000), _asset("land", 1600, 900)]
    cover_id, meta = pick_cover_asset_id_with_meta(assets, export_layout="mobile")
    assert cover_id == "port"
    assert meta["orientationMatched"] is True
    assert meta["orientationFallback"] is False
    assert meta["preferredOrientation"] == "portrait"


def test_web_falls_back_when_no_landscape() -> None:
    assets = [
        _asset("port-a", 900, 1600, sharp=200.0),
        _asset("port-b", 800, 1400, sharp=100.0),
    ]
    cover_id, meta = pick_cover_asset_id_with_meta(assets, export_layout="web")
    assert cover_id in ("port-a", "port-b")
    assert meta["orientationFallback"] is True
    assert meta["orientationFallbackReason"] == "no_preferred_orientation_in_pool"
    assert "横图" in str(meta.get("userOneLiner") or "")


def test_mobile_falls_back_when_no_portrait() -> None:
    assets = [
        _asset("land-a", 1920, 1080, sharp=200.0),
        _asset("land-b", 1600, 900, sharp=100.0),
    ]
    cover_id, meta = pick_cover_asset_id_with_meta(assets, export_layout="mobile")
    assert cover_id in ("land-a", "land-b")
    assert meta["orientationFallback"] is True
    assert meta["orientationFallbackReason"] == "no_preferred_orientation_in_pool"
    assert "竖图" in str(meta.get("userOneLiner") or "")


def test_soft_quality_override_wrong_orientation_can_win() -> None:
    """Wrong orientation may win only when quality is clearly higher."""
    assets = [
        _asset("land", 1600, 900, sharp=100.0, overall=0.5),
        _asset("port", 900, 2000, sharp=900.0, overall=0.9),
    ]
    cover_id, meta = pick_cover_asset_id_with_meta(assets, export_layout="web")
    assert cover_id == "port"
    assert meta["orientationFallback"] is True
    assert meta["orientationFallbackReason"] == "soft_quality_override"


def test_soft_override_does_not_fire_on_similar_quality() -> None:
    assets = [
        _asset("land", 1600, 900, sharp=120.0),
        _asset("port", 900, 2000, sharp=130.0),
    ]
    assert pick_cover_asset_id(assets, export_layout="web") == "land"


def test_sync_trip_covers_writes_orientation_meta() -> None:
    assets = [
        _asset("port", 900, 2000, sharp=200.0),
        _asset("land", 2400, 1350, sharp=180.0),
    ]
    trip = {"exportLayout": "auto", "assets": assets, "curation": {}}
    sync_trip_covers(trip, export_layout="auto")
    orient = trip["curation"].get("coverOrientationByLayout") or {}
    assert orient["mobile"]["preferredOrientation"] == "portrait"
    assert orient["web"]["preferredOrientation"] == "landscape"
    assert orient["mobile"]["orientationMatched"] is True
    assert orient["web"]["orientationMatched"] is True


def test_studio_payload_exposes_dual_thumbs_and_fallback_hint() -> None:
    trip = {
        "tripId": "orient",
        "exportLayout": "auto",
        "coverAssetId": "port",
        "assets": [
            _asset("port", 900, 2000),
            _asset("land", 1600, 900),
            _asset("spare", 1400, 900),
        ],
        "chapters": [],
        "meta": {},
        "curation": {
            "coverByLayout": {"mobile": "port", "web": "land"},
            "coverOrientationByLayout": {
                "mobile": {
                    "preferredOrientation": "portrait",
                    "orientationMatched": True,
                    "orientationFallback": False,
                },
                "web": {
                    "preferredOrientation": "landscape",
                    "orientationMatched": False,
                    "orientationFallback": True,
                    "orientationFallbackReason": "no_preferred_orientation_in_pool",
                    "userOneLiner": "未找到更合适的横图，先用这张适配电脑；你可手换。",
                },
            },
        },
    }
    # Force mobile fallback copy path
    trip["curation"]["coverOrientationByLayout"]["mobile"] = {
        "preferredOrientation": "portrait",
        "orientationMatched": False,
        "orientationFallback": True,
        "orientationFallbackReason": "no_preferred_orientation_in_pool",
        "userOneLiner": "未找到更合适的竖图，先用这张适配手机；你可手换。",
    }
    trip["curation"]["coverByLayout"]["mobile"] = "land"
    payload = build_bookends_studio_payload(trip)
    assert payload["webCoverAssetId"] == "land"
    assert payload["mobileCoverAssetId"] == "land"
    assert payload["coverThumb"]["assetId"] == "land"
    assert payload["orientationFallback"]["mobile"] is True
    assert "竖图" in (payload.get("mobileCoverHint") or "")
    soft = payload.get("softWarnings") or []
    assert any(
        isinstance(w, dict) and w.get("code") == "orientation_fallback_mobile" for w in soft
    )
