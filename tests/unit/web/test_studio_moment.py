"""Studio · Phase 23 moment pool GET/PATCH handlers."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.studio_test_helpers import MockStudioHandler
from travelogue.services.moment_curation import (
    apply_moment_signature,
    build_moment_curation_payload,
    validate_moment_asset_id,
)
from travelogue.services.trip import TripService
from travelogue.services.trip_factory import create_trip
from travelogue.web.studio_handlers.trip_handlers import (
    handle_get_moment_curation,
    handle_patch_moment,
)

pytestmark = pytest.mark.unit


def _trip_with_moment_pool(trips_dir: Path, trip_id: str = "moment-demo") -> Path:
    trip_json = create_trip(trip_id, trips_dir, title="最佳时刻", place="仙本那")
    trip = TripService(root=trips_dir.parent).load(trip_json)
    assets = []
    for i in range(4):
        aid = f"img-{i:02d}"
        assets.append(
            {
                "id": aid,
                "type": "image",
                "sourceFile": f"source/{aid}.jpg",
                "displayFile": f"assets/{aid}.webp",
                "layoutEligible": True,
                "width": 1600,
                "height": 900,
                "quality": {"sharpness": 0.5 + i * 0.1},
            }
        )
    trip["coverAssetId"] = "img-00"
    trip["assets"] = assets
    trip["curation"] = {
        "momentPoolIds": ["img-01", "img-02", "img-03"],
        "momentSecondaryIds": ["img-02", "img-03"],
        "momentExplain": [{"factor": "featured", "weight": 0.2, "detail": "featured tier"}],
        "momentPosition": "before_closing",
    }
    trip["momentAssetId"] = "img-01"
    TripService(root=trips_dir.parent).save(trip, trip_json)
    return trip_json


def test_validate_moment_asset_id_errors() -> None:
    trip = {
        "coverAssetId": "cover",
        "assets": [
            {"id": "cover", "type": "image"},
            {"id": "vid", "type": "video"},
            {"id": "a1", "type": "image"},
        ],
        "curation": {"momentPoolIds": ["a1"], "momentSkipped": "small_trip"},
    }
    assert validate_moment_asset_id(trip, "") == "E_MOMENT_MISSING_ID"
    assert validate_moment_asset_id(trip, "missing") == "E_MOMENT_UNKNOWN_ASSET"
    assert validate_moment_asset_id(trip, "vid") == "E_MOMENT_NOT_IMAGE"
    assert validate_moment_asset_id(trip, "cover") == "E_MOMENT_COVER_CONFLICT"
    assert validate_moment_asset_id(trip, "a1") == "E_MOMENT_SKIPPED"


def test_apply_moment_signature_updates_secondary() -> None:
    trip = {
        "momentAssetId": "img-01",
        "curation": {"momentPoolIds": ["img-01", "img-02", "img-03"]},
    }
    apply_moment_signature(trip, "img-03")
    assert trip["momentAssetId"] == "img-03"
    assert trip["curation"]["momentSecondaryIds"] == ["img-01", "img-02"]


def test_build_moment_curation_payload_strip() -> None:
    trip = {
        "momentAssetId": "img-01",
        "assets": [
            {"id": "img-01", "type": "image", "userTier": "featured", "exif": {"model": "iPhone"}},
            {"id": "img-02", "type": "image"},
        ],
        "curation": {
            "momentPoolIds": ["img-01", "img-02"],
            "momentExplain": [{"factor": "score", "weight": 1.0, "detail": "0.812"}],
        },
    }
    payload = build_moment_curation_payload(trip)
    assert payload["hasMoment"] is True
    assert payload["poolStrip"][0]["isSignature"] is True
    assert payload["poolStrip"][0]["hasExif"] is True
    assert payload["momentExplain"][0]["factor"] == "score"


@patch("travelogue.web.studio_handlers.trip_moment_handlers.studio_ctx")
def test_handle_get_moment_curation(mock_ctx, tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    _trip_with_moment_pool(trips_dir)
    mock_ctx.return_value.trip_service.return_value = TripService(root=trips_dir.parent)

    handler = MockStudioHandler(trips_dir)
    handle_get_moment_curation(handler, "moment-demo")
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["ok"] is True
    assert body["momentAssetId"] == "img-01"
    assert len(body["poolStrip"]) == 3
    assert body["poolStrip"][0]["isSignature"] is True


@patch("travelogue.web.studio_handlers.trip_moment_handlers.studio_ctx")
def test_handle_get_moment_curation_not_found(mock_ctx, tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir(parents=True)
    mock_ctx.return_value.trip_service.return_value = TripService(root=trips_dir.parent)

    handler = MockStudioHandler(trips_dir)
    handle_get_moment_curation(handler, "missing")
    assert handler.response == (404, {"ok": False, "error": "trip not found"})


@patch("travelogue.web.studio_handlers.trip_moment_handlers.studio_ctx")
def test_handle_patch_moment_success(mock_ctx, tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = _trip_with_moment_pool(trips_dir)
    mock_ctx.return_value.trip_service.return_value = TripService(root=trips_dir.parent)

    handler = MockStudioHandler(trips_dir, json_body={"momentAssetId": "img-02"})
    with patch("travelogue.web.rerender.rerender_draft_trip", return_value=["index.html"]):
        handle_patch_moment(handler, "moment-demo")

    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["momentAssetId"] == "img-02"
    saved = json.loads(trip_json.read_text(encoding="utf-8"))
    assert saved["momentAssetId"] == "img-02"
    assert saved["curation"]["momentSecondaryIds"] == ["img-01", "img-03"]


@patch("travelogue.web.studio_handlers.trip_moment_handlers.studio_ctx")
def test_handle_patch_moment_rejects_cover(mock_ctx, tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    _trip_with_moment_pool(trips_dir)
    mock_ctx.return_value.trip_service.return_value = TripService(root=trips_dir.parent)

    handler = MockStudioHandler(trips_dir, json_body={"momentAssetId": "img-00"})
    handle_patch_moment(handler, "moment-demo")
    assert handler.response == (
        400,
        {
            "ok": False,
            "error": "E_MOMENT_COVER_CONFLICT",
            "message": "momentAssetId must be in pool and not cover",
        },
    )


@patch("travelogue.web.studio_handlers.trip_moment_handlers.studio_ctx")
def test_handle_patch_moment_rejects_out_of_pool(mock_ctx, tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = _trip_with_moment_pool(trips_dir)
    trip = TripService(root=trips_dir.parent).load(trip_json)
    trip["assets"].append(
        {
            "id": "img-99",
            "type": "image",
            "sourceFile": "source/img-99.jpg",
            "displayFile": "assets/img-99.webp",
            "layoutEligible": True,
        }
    )
    TripService(root=trips_dir.parent).save(trip, trip_json)
    mock_ctx.return_value.trip_service.return_value = TripService(root=trips_dir.parent)

    handler = MockStudioHandler(trips_dir, json_body={"momentAssetId": "img-99"})
    handle_patch_moment(handler, "moment-demo")
    assert handler.response is not None
    assert handler.response[0] == 400
    assert handler.response[1]["error"] == "E_MOMENT_NOT_IN_POOL"
