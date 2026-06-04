"""Studio PATCH screen replan handler."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from travelogue.config import AppConfig
from travelogue.curation.screen_planner import LAYOUT_ENGINE_SCREENS
from travelogue.services.trip import TripService
from travelogue.services.trip_factory import create_trip
from travelogue.web.studio_handlers.trip_handlers import handle_patch_screen_replan
from tests._golden.helpers import build_mosaic_eligible_trip, plan_mosaic_screens
from tests.studio_test_helpers import MockStudioHandler

pytestmark = pytest.mark.unit


def _trip_with_screens(trips_dir: Path, trip_id: str = "replan-demo") -> Path:
    buckets, aspects_map, assets = build_mosaic_eligible_trip()
    chapters = plan_mosaic_screens(buckets[:1], aspects_map, assets)
    trip_json = create_trip(trip_id, trips_dir, title="Replan", place="测试")
    trip = TripService(root=trips_dir.parent).load(trip_json)
    trip["assets"] = assets
    trip["chapters"] = chapters
    trip["layoutEngine"] = LAYOUT_ENGINE_SCREENS
    TripService(root=trips_dir.parent).save(trip, trip_json)
    return trip_json


@patch("travelogue.web.studio_handlers.trip_handlers.studio_ctx")
def test_handle_patch_screen_replan(mock_ctx, tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = _trip_with_screens(trips_dir)
    trip = TripService(root=trips_dir.parent).load(trip_json)
    screen_id = trip["chapters"][0]["screens"][0]["screenId"]
    cfg = AppConfig(trips_dir=trips_dir, mosaic=AppConfig().mosaic)
    mock_ctx.return_value.app_config = cfg
    mock_ctx.return_value.trip_service.return_value = TripService(root=trips_dir.parent)

    handler = MockStudioHandler(
        trips_dir,
        path=f"/__travelogue/trips/replan-demo/screens/{screen_id}/replan",
        json_body={"strategy": "alt_topk", "topK": 3},
    )
    handle_patch_screen_replan(handler, "replan-demo", screen_id)
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body.get("ok") is True
    saved = TripService(root=trips_dir.parent).load(trip_json)
    assert saved["curation"].get("displayedAssetIds")
