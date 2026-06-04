"""Studio cohort API handlers."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from travelogue.config import AppConfig, CohortConfig
from travelogue.services.trip import TripService
from travelogue.services.trip_factory import create_trip
from travelogue.web.studio_handlers.trip_handlers import (
    handle_get_cohort,
    handle_patch_cohort,
    handle_post_cohort_refresh,
)
from tests.studio_test_helpers import MockStudioHandler

pytestmark = pytest.mark.unit


def _trip_with_assets(trips_dir: Path, trip_id: str = "cohort-demo") -> Path:
    trip_json = create_trip(trip_id, trips_dir, title="同框", place="京都")
    trip = TripService(root=trips_dir.parent).load(trip_json)
    assets = []
    for i in range(3):
        aid = f"img-{i:02d}"
        assets.append(
            {
                "id": aid,
                "type": "image",
                "sourceFile": f"source/{aid}.jpg",
                "displayFile": f"assets/{aid}.webp",
                "layoutEligible": True,
                "quality": {"sharpness": 0.5 + i * 0.1, "faceCount": 2 if i < 2 else 0},
                "takenAt": f"2025-06-0{i + 1}T10:00:00Z",
            }
        )
    trip["assets"] = assets
    trip["intent"] = {
        "version": "1",
        "featuredSubjects": [
            {"id": "alice", "label": "A", "seedAssetIds": ["img-00"]},
            {"id": "bob", "label": "B", "seedAssetIds": ["img-01"]},
        ],
    }
    TripService(root=trips_dir.parent).save(trip, trip_json)
    return trip_json


@patch("travelogue.web.studio_handlers.trip_handlers.studio_ctx")
def test_handle_get_cohort(mock_ctx, tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    _trip_with_assets(trips_dir)
    cfg = AppConfig(trips_dir=trips_dir, cohort=CohortConfig(enabled=True))
    mock_ctx.return_value.app_config = cfg
    mock_ctx.return_value.trip_service.return_value = TripService(root=trips_dir.parent)

    handler = MockStudioHandler(trips_dir)
    handle_get_cohort(handler, "cohort-demo")
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert len(body["featuredSubjects"]) == 2
    assert len(body["assets"]) == 3


@patch("travelogue.web.studio_handlers.trip_handlers.studio_ctx")
@patch("travelogue.curation.cohort_faces.apply_cohort_tags")
def test_handle_patch_cohort_refresh(mock_tags, mock_ctx, tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = _trip_with_assets(trips_dir)
    mock_tags.return_value = {"version": "1", "duoCount": 1, "tagged": 3}
    cfg = AppConfig(trips_dir=trips_dir, cohort=CohortConfig(enabled=True))
    mock_ctx.return_value.app_config = cfg
    mock_ctx.return_value.trip_service.return_value = TripService(root=trips_dir.parent)

    handler = MockStudioHandler(
        trips_dir,
        json_body={
            "featuredSubjects": [
                {"id": "alice", "seedAssetIds": ["img-00"]},
                {"id": "bob", "seedAssetIds": ["img-01"]},
            ],
            "refresh": True,
        },
    )
    handle_patch_cohort(handler, "cohort-demo")
    assert handler.response is not None
    assert handler.response[0] == 200
    saved = json.loads(trip_json.read_text(encoding="utf-8"))
    assert saved["curation"]["cohort"]["duoCount"] == 1


@patch("travelogue.web.studio_handlers.trip_handlers.studio_ctx")
def test_handle_patch_cohort_disabled(mock_ctx, tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    _trip_with_assets(trips_dir)
    cfg = AppConfig(trips_dir=trips_dir, cohort=CohortConfig(enabled=False))
    mock_ctx.return_value.app_config = cfg

    handler = MockStudioHandler(trips_dir, json_body={"refresh": True})
    handle_patch_cohort(handler, "cohort-demo")
    assert handler.response == (
        400,
        {
            "ok": False,
            "error": "E_COHORT_DISABLED",
            "message": "cohort.enabled is false in config",
        },
    )


@patch("travelogue.web.studio_handlers.trip_handlers.studio_ctx")
@patch("travelogue.curation.cohort_faces.apply_cohort_tags")
def test_handle_post_cohort_refresh(mock_tags, mock_ctx, tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = _trip_with_assets(trips_dir)
    mock_tags.return_value = {"version": "1", "tagged": 2}
    cfg = AppConfig(trips_dir=trips_dir, cohort=CohortConfig(enabled=True))
    mock_ctx.return_value.app_config = cfg
    mock_ctx.return_value.trip_service.return_value = TripService(root=trips_dir.parent)

    handler = MockStudioHandler(trips_dir)
    handle_post_cohort_refresh(handler, "cohort-demo")
    assert handler.response is not None
    assert handler.response[0] == 200
    saved = json.loads(trip_json.read_text(encoding="utf-8"))
    assert saved["curation"]["cohort"]["tagged"] == 2
