"""Unit tests for Studio trip_handlers (no HTTP server)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from travelogue.services.trip import TripService
from travelogue.services.trip_factory import create_trip
from travelogue.web.studio_handlers.trip_handlers import (
    handle_chapter_layout,
    handle_entry,
    handle_patch_intent,
    handle_patch_pipeline,
    handle_rerender,
    handle_trips,
)
from travelogue.web.studio_jobs import get_job_store, reset_job_store
from tests.studio_test_helpers import MockStudioHandler

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


def _structure_draft_trip(trips_dir: Path, trip_id: str = "demo-g1") -> Path:
    trip_json = create_trip(trip_id, trips_dir, title="G1测试", place="京都")
    trip = TripService(root=trips_dir.parent).load(trip_json)
    trip["pipeline"] = {"status": "structure_draft", "locks": {"structure": False}}
    TripService(root=trips_dir.parent).save(trip, trip_json)
    return trip_json


def test_handle_trips_empty_list(tmp_path: Path) -> None:
    handler = MockStudioHandler(tmp_path / "trips", path="/__travelogue/trips")
    handle_trips(handler)
    assert handler.response == (200, {"ok": True, "trips": [], "total": 0})


def test_handle_trips_clamps_limit(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    create_trip("demo-01", trips_dir, title="A", place="京都")
    handler = MockStudioHandler(trips_dir, path="/__travelogue/trips?limit=999")
    handle_trips(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["total"] == 1
    assert len(body["trips"]) == 1


def test_handle_trips_offset_and_limit(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    for i in range(3):
        create_trip(f"demo-{i:02d}", trips_dir, title=f"T{i}", place="京都")
    handler0 = MockStudioHandler(trips_dir, path="/__travelogue/trips?limit=2&offset=0")
    handle_trips(handler0)
    assert handler0.response is not None
    assert handler0.response[1]["total"] == 3
    assert len(handler0.response[1]["trips"]) == 2
    handler1 = MockStudioHandler(trips_dir, path="/__travelogue/trips?limit=2&offset=2")
    handle_trips(handler1)
    assert handler1.response is not None
    assert len(handler1.response[1]["trips"]) == 1


def test_handle_entry_not_found(tmp_path: Path) -> None:
    handler = MockStudioHandler(tmp_path / "trips")
    handle_entry(handler, "missing-trip")
    assert handler.response == (404, {"ok": False, "error": "trip not found"})


def test_handle_entry_success(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    create_trip("demo-entry", trips_dir, title="入口", place="京都")
    handler = MockStudioHandler(trips_dir)
    handle_entry(handler, "demo-entry")
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["ok"] is True
    assert body.get("previewUrl") == "/demo-entry/index.html"


def test_handle_chapter_layout_requires_trip_id(tmp_path: Path) -> None:
    handler = MockStudioHandler(tmp_path / "trips", path="/__travelogue/chapter-layout")
    handle_chapter_layout(handler)
    assert handler.response == (400, {"ok": False, "error": "tripId required"})


def test_handle_chapter_layout_not_found(tmp_path: Path) -> None:
    handler = MockStudioHandler(
        tmp_path / "trips",
        path="/__travelogue/chapter-layout?tripId=missing",
    )
    handle_chapter_layout(handler)
    assert handler.response == (404, {"ok": False, "error": "trip not found"})


def test_handle_chapter_layout_success(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = create_trip("demo-layout", trips_dir, title="分章", place="京都")
    trip = TripService(root=trips_dir.parent).load(trip_json)
    trip["curation"] = {
        "clustering": {
            "userSummary": {"summary": "按天分组", "chapters": []},
        },
    }
    TripService(root=trips_dir.parent).save(trip, trip_json)

    handler = MockStudioHandler(
        trips_dir,
        path="/__travelogue/chapter-layout?tripId=demo-layout",
    )
    handle_chapter_layout(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["ok"] is True
    assert body.get("summary") == "按天分组"


def test_handle_patch_intent_no_fields(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    create_trip("demo-intent", trips_dir)
    handler = MockStudioHandler(trips_dir, json_body={"unknown": True})
    handle_patch_intent(handler, "demo-intent")
    assert handler.response == (400, {"ok": False, "error": "no intent fields"})


def test_handle_patch_intent_updates_title(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = create_trip("demo-intent", trips_dir, title="旧标题", place="京都")
    handler = MockStudioHandler(trips_dir, json_body={"title": "新标题"})
    handle_patch_intent(handler, "demo-intent")
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["intent"]["title"] == "新标题"
    saved = json.loads(trip_json.read_text(encoding="utf-8"))
    assert saved["meta"]["title"] == "新标题"
    assert saved["intent"]["title"] == "新标题"


def test_handle_patch_intent_not_found(tmp_path: Path) -> None:
    handler = MockStudioHandler(tmp_path / "trips", json_body={"title": "x"})
    handle_patch_intent(handler, "missing")
    assert handler.response == (404, {"ok": False, "error": "trip not found"})


def test_handle_patch_pipeline_rejects_non_draft(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = create_trip("demo-locked", trips_dir)
    trip = TripService(root=trips_dir.parent).load(trip_json)
    trip["pipeline"]["status"] = "rendered"
    TripService(root=trips_dir.parent).save(trip, trip_json)

    handler = MockStudioHandler(trips_dir, json_body={"continuePipeline": False})
    handle_patch_pipeline(handler, "demo-locked")
    assert handler.response is not None
    status, body = handler.response
    assert status == 409
    assert body["error"] == "E_PIPELINE_ORDER"


def test_handle_patch_pipeline_lock_without_continue(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    _structure_draft_trip(trips_dir, "demo-g1-lock")
    handler = MockStudioHandler(trips_dir, json_body={"continuePipeline": False})
    handle_patch_pipeline(handler, "demo-g1-lock")
    assert handler.response == (200, {"ok": True, "pipelineStatus": "structure_locked"})


def test_handle_patch_pipeline_starts_continue_job(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    _structure_draft_trip(trips_dir, "demo-g1-go")
    handler = MockStudioHandler(trips_dir, json_body={"continuePipeline": True})
    with patch("travelogue.web.studio_handlers.trip_handlers.run_g1_continue_job"):
        handle_patch_pipeline(handler, "demo-g1-go")
    assert handler.response is not None
    status, body = handler.response
    assert status == 202
    assert body["ok"] is True
    assert body.get("jobId")
    assert body["pipelineStatus"] == "structure_locked"


def test_handle_rerender_missing_trip(tmp_path: Path) -> None:
    handler = MockStudioHandler(tmp_path / "trips")
    handler.trip_json_path = tmp_path / "missing" / "trip.json"
    handle_rerender(handler)
    assert handler.response == (404, {"ok": False, "error": "trip not found"})


def test_handle_rerender_success(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = create_trip("demo-rerender", trips_dir)
    handler = MockStudioHandler(trips_dir)
    handler.trip_json_path = trip_json
    with patch(
        "travelogue.web.rerender.rerender_draft_trip",
        return_value=["index.html"],
    ):
        handle_rerender(handler)
    assert handler.response == (200, {"ok": True, "rendered": ["index.html"]})


def test_handle_rerender_hides_internal_error(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = create_trip("demo-rerender-err", trips_dir)
    handler = MockStudioHandler(trips_dir)
    handler.trip_json_path = trip_json
    with patch(
        "travelogue.web.rerender.rerender_draft_trip",
        side_effect=RuntimeError("/secret/path failed"),
    ):
        handle_rerender(handler)
    assert handler.response == (
        500,
        {"ok": False, "error": "E_SERVER", "message": "服务内部错误，请稍后重试"},
    )


def test_handle_trip_curate_starts_job(tmp_path: Path) -> None:
    from travelogue.web.studio_handlers.trip_handlers import handle_trip_curate

    trips_dir = tmp_path / "trips"
    create_trip("demo-curate", trips_dir)
    handler = MockStudioHandler(trips_dir, json_body={})
    with patch("travelogue.web.studio_handlers.trip_handlers.run_g1_continue_job"):
        handle_trip_curate(handler, "demo-curate")
    assert handler.response is not None
    status, body = handler.response
    assert status == 202
    assert body["ok"] is True
    assert body.get("jobId")
