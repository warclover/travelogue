"""Bookends Studio AC-BE-20..25 semi-automated checks (B2b)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tests.studio_test_helpers import MockStudioHandler
from travelogue.cover_engine.api import (
    ClosingConflictError,
    build_bookends_studio_payload,
    repick_opening,
    resolve_closing,
)
from travelogue.services.trip import TripService
from travelogue.web.studio_handlers.bookends_handlers import (
    handle_get_bookends,
    handle_post_repick_closing,
    handle_post_restore_auto,
)

pytestmark = pytest.mark.unit


def _img(aid: str, **extra) -> dict:
    base = {
        "id": aid,
        "type": "image",
        "layoutEligible": True,
        "width": 1600,
        "height": 900,
        "userTier": "featured",
        "sharpness": 0.8,
        "aesthetic": {"overall": 0.65},
        "sourceFile": f"source/{aid}.jpg",
        "displayFile": f"assets/{aid}.webp",
    }
    base.update(extra)
    return base


def _seed_trip(trips_dir: Path, trip_id: str = "bookends-ac") -> Path:
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True, exist_ok=True)
    trip = {
        "tripId": trip_id,
        "title": "封面与封底验收",
        "exportLayout": "web",
        "layoutEngine": "screens",
        "coverAssetId": "cover",
        "meta": {"title": "封面与封底验收", "coverOpeningStyle": "veil-footer"},
        "assets": [
            _img("cover"),
            _img("body", dominantTone="#667788"),
            _img("spare", dominantTone="#334455"),
        ],
        "chapters": [
            {"id": "ch-01", "screens": [{"slots": [{"assetId": "body"}]}]},
        ],
        "curation": {},
        "epilogue": "尾声",
    }
    trip_json = trip_dir / "trip.json"
    TripService(root=trips_dir.parent).save(trip, trip_json)
    return trip_json


def test_ac_be_20_panel_copy_and_spread_payload() -> None:
    trip = {
        "tripId": "ac20",
        "exportLayout": "web",
        "coverAssetId": "cover",
        "meta": {"coverOpeningStyle": "veil-footer"},
        "assets": [_img("cover"), _img("spare"), _img("body")],
        "chapters": [{"screens": [{"slots": [{"assetId": "body"}]}]}],
        "curation": {},
    }
    resolve_closing(trip, force=True)
    payload = build_bookends_studio_payload(trip)
    assert payload["panelTitle"] == "封面与封底"
    assert "第一眼" in (payload.get("panelSubtitle") or "")
    assert payload.get("userOneLiner")
    assert "openingCandidates" in payload
    assert "closingCandidates" in payload
    assert payload.get("statusBanner") is None or isinstance(payload.get("statusBanner"), dict)
    # AC-BE-24 · no closing style switcher surface in payload
    assert "closingStyleOptions" not in payload


def test_fe_be_07_status_banner_degraded() -> None:
    trip = {
        "tripId": "status",
        "exportLayout": "web",
        "coverAssetId": "cover",
        "meta": {},
        "assets": [_img("cover")],
        "chapters": [{"screens": [{"slots": [{"assetId": "cover"}]}]}],
        "curation": {"closingAssetId": None, "bookendsDegraded": True},
    }
    payload = build_bookends_studio_payload(trip)
    banner = payload.get("statusBanner") or {}
    assert banner.get("kind") == "degraded"
    assert banner.get("code") == "E_BOOKENDS_NO_CLOSING_CANDIDATE"
    assert "省略封底图" in (banner.get("message") or "")
    assert payload.get("statusCode") == "E_BOOKENDS_NO_CLOSING_CANDIDATE"


@patch("travelogue.web.studio_handlers.bookends_handlers.studio_ctx")
def test_ac_be_21_repick_closing_sets_user_picked(mock_ctx, tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = _seed_trip(trips_dir)
    svc = TripService(root=tmp_path)
    mock_ctx.return_value.trip_service.return_value = svc
    trip = svc.load(trip_json)
    resolve_closing(trip, force=True)
    svc.save(trip, trip_json)

    handler = MockStudioHandler(trips_dir, json_body={"assetId": "spare"})
    with patch("travelogue.web.rerender.rerender_draft_trip", return_value=["index.html"]):
        handle_post_repick_closing(handler, "bookends-ac")
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["ok"] is True
    assert body["closingAssetId"] == "spare"
    trip2 = svc.load(trip_json)
    assert trip2["curation"]["closingUserPicked"] is True
    assert trip2["curation"]["closingAssetId"] == "spare"


@patch("travelogue.web.studio_handlers.bookends_handlers.studio_ctx")
def test_ac_be_22_restore_auto_requires_confirm(mock_ctx, tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    _seed_trip(trips_dir)
    mock_ctx.return_value.trip_service.return_value = TripService(root=tmp_path)

    handler = MockStudioHandler(trips_dir, json_body={"confirmed": False})
    # Force a non-empty body so MockStudioHandler returns it
    handler._json_body = {"confirmed": False}
    handle_post_restore_auto(handler, "bookends-ac")
    assert handler.response is not None
    status, body = handler.response
    assert status == 400
    assert body["error"] == "E_BOOKENDS_CONFIRM_REQUIRED"

    handler2 = MockStudioHandler(trips_dir, json_body={"confirmed": True})
    with patch("travelogue.web.rerender.rerender_draft_trip", return_value=["index.html"]):
        handle_post_restore_auto(handler2, "bookends-ac")
    assert handler2.response is not None
    status2, body2 = handler2.response
    assert status2 == 200
    assert body2["ok"] is True


def test_ac_be_23_opening_conflict_with_user_picked_closing() -> None:
    cover = _img(
        "face-cover",
        width=1200,
        height=1600,
        faceCount=1,
        faces=[{"bbox": {"x": 0.2, "y": 0.15, "w": 0.55, "h": 0.55}}],
    )
    near = _img(
        "face-near",
        width=1200,
        height=1600,
        faceCount=1,
        faces=[{"bbox": {"x": 0.25, "y": 0.2, "w": 0.5, "h": 0.5}}],
    )
    trip = {
        "tripId": "conflict",
        "exportLayout": "web",
        "coverAssetId": "other",
        "meta": {"coverOpeningStyle": "veil-footer"},
        "assets": [cover, near, _img("other"), _img("scenic", dominantTone="#223344")],
        "chapters": [{"screens": [{"slots": [{"assetId": "scenic"}]}]}],
        "curation": {
            "closingAssetId": "face-near",
            "closingUserPicked": True,
            "coverByLayout": {"web": "other"},
        },
    }
    with pytest.raises(ClosingConflictError) as exc:
        repick_opening(trip, asset_id="face-cover", style_id="veil-footer")
    assert exc.value.violations

    decision = repick_opening(
        trip,
        asset_id="face-cover",
        style_id="veil-footer",
        confirm_closing_conflict=True,
    )
    assert decision.closing_asset_id != "face-cover"
    assert trip["curation"].get("closingUserPicked") is False


def test_ac_be_25_mobile_fold_copy_in_payload_and_ui_source() -> None:
    trip = {
        "tripId": "mobile",
        "exportLayout": "web",
        "coverAssetId": "cover",
        "assets": [_img("cover"), _img("body")],
        "chapters": [{"screens": [{"slots": [{"assetId": "body"}]}]}],
        "curation": {"coverByLayout": {"web": "cover", "mobile": "cover"}},
        "meta": {},
    }
    payload = build_bookends_studio_payload(trip)
    assert payload["mobileClosingEnabled"] is False
    assert payload.get("mobileCoverAssetId") == "cover"
    assert payload.get("mobileCoverThumb")

    ui = Path("templates/studio/preview-toolbar/bookends.js").read_text(encoding="utf-8")
    assert "封面与封底" in ui
    assert "手机封面" in ui
    assert "封底目前仅网页成书" in ui
    assert "恢复自动挑选" in ui
    assert "data-bookends-status" in ui
    assert "data-bookends-opening-hero" in ui
    assert "data-bookends-mobile-thumb" in ui
    assert "data-bookends-mobile-hint" in ui
    assert "已按你的选择固定" not in ui
    assert "手选 · 可恢复自动" in ui
    assert "看封面" in ui
    assert "看封底" in ui
    assert "data-bookends-scroll-opening" in ui
    assert "applyStyleViaBookends" in ui
    assert "closingStyleOptions" not in ui
    assert "封底样式" not in ui
    assert payload.get("webCoverAssetId") == "cover"
    assert payload.get("mobileCoverHint")
    assert "orientationFallback" in payload


def test_fe_be_03_opening_candidates_top3() -> None:
    trip = {
        "tripId": "top3",
        "exportLayout": "web",
        "coverAssetId": "cover",
        "meta": {"coverOpeningStyle": "veil-footer"},
        "assets": [_img("cover"), _img("a"), _img("b"), _img("c"), _img("d")],
        "chapters": [{"screens": [{"slots": [{"assetId": "a"}]}]}],
        "curation": {},
    }
    payload = build_bookends_studio_payload(trip)
    assert len(payload.get("openingCandidates") or []) <= 3
    assert payload.get("coverThumb")
    assert "openingLocked" in payload
    assert "closingPreviewOnly" in payload


@patch("travelogue.web.studio_handlers.bookends_handlers.studio_ctx")
def test_get_bookends_http(mock_ctx, tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    _seed_trip(trips_dir)
    mock_ctx.return_value.trip_service.return_value = TripService(root=tmp_path)
    handler = MockStudioHandler(trips_dir)
    handle_get_bookends(handler, "bookends-ac")
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["panelTitle"] == "封面与封底"


@patch("travelogue.web.studio_handlers.bookends_handlers.studio_ctx")
def test_resolve_closing_locked_returns_e_bookends_locked(mock_ctx, tmp_path: Path) -> None:
    from travelogue.cover_engine.lock import set_closing_locked
    from travelogue.web.studio_handlers.bookends_handlers import handle_post_resolve_closing

    trips_dir = tmp_path / "trips"
    trip_json = _seed_trip(trips_dir)
    svc = TripService(root=tmp_path)
    mock_ctx.return_value.trip_service.return_value = svc
    trip = svc.load(trip_json)
    resolve_closing(trip, force=True)
    set_closing_locked(trip, True)
    svc.save(trip, trip_json)

    handler = MockStudioHandler(trips_dir, json_body={"force": False})
    handle_post_resolve_closing(handler, "bookends-ac")
    assert handler.response is not None
    status, body = handler.response
    assert status == 409
    assert body["error"] == "E_BOOKENDS_LOCKED"
