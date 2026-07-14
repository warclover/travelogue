"""Unit tests for Studio trip_handlers (no HTTP server)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.studio_test_helpers import MockStudioHandler
from travelogue.services.trip import TripService
from travelogue.services.trip_factory import create_trip
from travelogue.web.studio_handlers.trip_handlers import (
    handle_aesthetic,
    handle_chapter_layout,
    handle_entry,
    handle_patch_copy_intent,
    handle_patch_intent,
    handle_patch_pipeline,
    handle_patch_stratum_preference,
    handle_rerender,
    handle_trips,
)
from travelogue.web.studio_jobs import reset_job_store

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
    assert "aesthetic" in body
    assert body["aesthetic"]["enabled"] is True


def test_handle_aesthetic_not_found(tmp_path: Path) -> None:
    handler = MockStudioHandler(tmp_path / "trips")
    handle_aesthetic(handler, "missing-trip")
    assert handler.response == (404, {"ok": False, "error": "trip not found"})


def test_handle_aesthetic_success(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = create_trip("demo-ae", trips_dir, title="审美", place="京都")
    trip = TripService(root=trips_dir.parent).load(trip_json)
    trip["assets"] = [
        {
            "id": "img-1",
            "type": "image",
            "displayFile": "media/img-1.webp",
            "quality": {
                "aesthetic": {
                    "version": "pa-v0.1",
                    "source": "rules",
                    "overall": 0.6,
                    "confidence": 0.8,
                    "dims": {
                        "composition": 0.7,
                        "exposure": 0.5,
                        "color": 0.6,
                        "lighting": 0.4,
                        "subjectClarity": 0.55,
                    },
                    "signals": {},
                    "critique": None,
                }
            },
        }
    ]
    trip["chapters"] = [{"screens": [{"slots": [{"assetId": "img-1"}]}]}]
    TripService(root=trips_dir.parent).save(trip, trip_json)

    handler = MockStudioHandler(trips_dir, path="/__travelogue/trips/demo-ae/aesthetic")
    handle_aesthetic(handler, "demo-ae")
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["ok"] is True
    assert body["scoredCount"] == 1
    assert len(body["assets"]) == 1
    assert body["assets"][0]["id"] == "img-1"
    assert len(body["assets"][0]["explain"]) == 3


def test_handle_patch_stratum_preference_success(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = create_trip("demo-pref", trips_dir, title="偏好", place="京都")
    trip = TripService(root=trips_dir.parent).load(trip_json)
    trip["assets"] = [{"id": "img-1", "type": "image"}]
    TripService(root=trips_dir.parent).save(trip, trip_json)

    handler = MockStudioHandler(
        trips_dir,
        path="/__travelogue/trips/demo-pref/aesthetic/preference",
        json_body={"stratumPreference": "portrait"},
    )
    handle_patch_stratum_preference(handler, "demo-pref")
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["ok"] is True
    assert body["stratumPreference"]["value"] == "portrait"

    saved = TripService(root=trips_dir.parent).load(trip_json)
    assert saved["curation"]["stratumPreference"] == "portrait"


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
    with patch("travelogue.web.studio_handlers.trip_pipeline_handlers.run_g1_continue_job"):
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
    with patch("travelogue.web.studio_handlers.trip_pipeline_handlers.run_g1_continue_job"):
        handle_trip_curate(handler, "demo-curate")
    assert handler.response is not None
    status, body = handler.response
    assert status == 202
    assert body["ok"] is True
    assert body.get("jobId")
    assert body.get("scope") == "full"


def test_handle_trip_curate_tier_requires_chapters(tmp_path: Path) -> None:
    from travelogue.web.studio_handlers.trip_handlers import handle_trip_curate

    trips_dir = tmp_path / "trips"
    create_trip("demo-tier-empty", trips_dir)
    handler = MockStudioHandler(
        trips_dir,
        json_body={"scope": "tier", "force": True, "reason": "tier_rerank"},
    )
    handle_trip_curate(handler, "demo-tier-empty")
    assert handler.response is not None
    status, body = handler.response
    assert status == 409
    assert body.get("error") == "E_CURATE_NO_STRUCTURE"


def test_handle_trip_curate_tier_skips_unlock(tmp_path: Path) -> None:
    from travelogue.domain.pipeline_view import lock_structure
    from travelogue.web.studio_handlers.trip_handlers import handle_trip_curate

    trips_dir = tmp_path / "trips"
    trip_json = create_trip("demo-tier-lock", trips_dir)
    svc = TripService(root=trips_dir.parent)
    trip = svc.load(trip_json)
    trip["chapters"] = [
        {"id": "ch-01", "index": 1, "patternId": "open", "title": "一", "items": []}
    ]
    lock_structure(trip)
    svc.save(trip, trip_json)

    handler = MockStudioHandler(
        trips_dir,
        json_body={"scope": "tier", "force": True, "reason": "tier_rerank"},
    )
    captured: list = []

    def _sync_job(_job, *, runner=None):
        if runner is not None:
            captured.append(runner)
        return {}

    with patch(
        "travelogue.web.studio_handlers.trip_pipeline_handlers.run_g1_continue_job",
        side_effect=_sync_job,
    ):
        with patch(
            "travelogue.domain.pipeline_view.unlock_structure_for_replan"
        ) as unlock_fn:
            with patch("travelogue.curation.curate.run_curate") as run_fn:
                with patch("travelogue.render.engine.render_trip_surfaces"):
                    with patch("travelogue.render.preview.render_preview_jpg"):
                        handle_trip_curate(handler, "demo-tier-lock")
                        assert captured
                        result = captured[0]()
                        unlock_fn.assert_not_called()
                        run_fn.assert_called_once()
                        kwargs = run_fn.call_args.kwargs
                        assert kwargs.get("scope") == "tier"
                        assert kwargs.get("cover_force") is True
                        assert kwargs.get("refresh_algorithms") is False
                        assert result.get("scope") == "tier"
                        assert result.get("pipelineStatus") == "structure_locked"
    assert handler.response is not None
    assert handler.response[0] == 202
    assert handler.response[1].get("scope") == "tier"


def test_handle_trip_curate_runner_regenerates_preview_jpg(tmp_path: Path) -> None:
    from travelogue.web.studio_handlers.trip_handlers import handle_trip_curate

    trips_dir = tmp_path / "trips"
    trip_json = create_trip("demo-curate-preview", trips_dir)
    handler = MockStudioHandler(trips_dir, json_body={})
    captured: list = []

    def _sync_job(_job, *, runner=None):
        if runner is not None:
            captured.append(runner)
        return {}

    with patch(
        "travelogue.web.studio_handlers.trip_pipeline_handlers.run_g1_continue_job",
        side_effect=_sync_job,
    ):
        with patch("travelogue.curation.curate.run_curate"):
            with patch("travelogue.render.engine.render_trip_surfaces"):
                with patch(
                    "travelogue.render.preview.render_preview_jpg"
                ) as mock_preview:
                    handle_trip_curate(handler, "demo-curate-preview")
                    assert captured
                    captured[0]()
                    mock_preview.assert_called_once()
                    args, kwargs = mock_preview.call_args
                    assert args[0] == trip_json
                    assert kwargs.get("trip_root") == trip_json.parent


def _trip_with_chapter(trips_dir: Path, trip_id: str = "demo-copy-intent") -> Path:
    trip_json = create_trip(trip_id, trips_dir, title="意图测试", place="京都")
    svc = TripService(root=trips_dir.parent)
    trip = svc.load(trip_json)
    trip["chapters"] = [
        {
            "id": "ch-01",
            "index": 1,
            "patternId": "open",
            "title": "雨后",
            "items": [],
        }
    ]
    svc.save(trip, trip_json)
    return trip_json


def test_handle_patch_copy_intent_success(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = _trip_with_chapter(trips_dir)
    handler = MockStudioHandler(
        trips_dir,
        json_body={"mood": "松弛", "focus": "地方", "note": "鸭川边"},
        path="/__travelogue/trips/demo-copy-intent/chapters/ch-01/copy-intent",
    )
    handle_patch_copy_intent(handler, "demo-copy-intent", "ch-01")
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["copyIntent"] == {"mood": "松弛", "focus": "地方", "note": "鸭川边"}
    saved = TripService(root=trips_dir.parent).load(trip_json)
    assert saved["chapters"][0]["curation"]["copyIntent"] == body["copyIntent"]


def test_handle_patch_copy_intent_invalid_enum(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    _trip_with_chapter(trips_dir)
    handler = MockStudioHandler(
        trips_dir,
        json_body={"mood": "不存在"},
        path="/__travelogue/trips/demo-copy-intent/chapters/ch-01/copy-intent",
    )
    handle_patch_copy_intent(handler, "demo-copy-intent", "ch-01")
    assert handler.response is not None
    status, body = handler.response
    assert status == 400
    assert body["error"] == "E_COPY_INTENT_INVALID"


def test_handle_patch_copy_intent_chapter_not_found(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    _trip_with_chapter(trips_dir)
    handler = MockStudioHandler(
        trips_dir,
        json_body={"mood": "松弛"},
        path="/__travelogue/trips/demo-copy-intent/chapters/missing/copy-intent",
    )
    handle_patch_copy_intent(handler, "demo-copy-intent", "missing")
    assert handler.response == (
        404,
        {"ok": False, "error": "E_CHAPTER_NOT_FOUND", "message": "chapter not found"},
    )


def test_handle_patch_copy_intent_apply_to_subsequent(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_json = _trip_with_chapter(trips_dir)
    svc = TripService(root=trips_dir.parent)
    trip = svc.load(trip_json)
    trip["chapters"] = [
        {"id": "ch-01", "index": 1, "patternId": "open", "title": "一", "items": []},
        {"id": "ch-02", "index": 2, "patternId": "open", "title": "二", "items": []},
        {"id": "ch-03", "index": 3, "patternId": "open", "title": "三", "items": []},
    ]
    svc.save(trip, trip_json)
    handler = MockStudioHandler(
        trips_dir,
        json_body={
            "mood": "松弛",
            "focus": "地方",
            "note": "鸭川",
            "applyToSubsequent": True,
        },
        path="/__travelogue/trips/demo-copy-intent/chapters/ch-02/copy-intent",
    )
    handle_patch_copy_intent(handler, "demo-copy-intent", "ch-02")
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["chapterIds"] == ["ch-02", "ch-03"]
    saved = svc.load(trip_json)
    assert "copyIntent" not in saved["chapters"][0].get("curation", {})
    assert saved["chapters"][1]["curation"]["copyIntent"]["note"] == "鸭川"
    assert saved["chapters"][2]["curation"]["copyIntent"]["focus"] == "地方"


def test_handle_post_copy_telemetry(tmp_path: Path) -> None:
    from travelogue.layout_templates.css_stale import trip_render_bundle_stale
    from travelogue.services.trip import mark_render_bundle_current, meta_revision
    from travelogue.web.studio_handlers.trip_intent_handlers import handle_post_copy_telemetry

    trips_dir = tmp_path / "trips"
    trip_json = _trip_with_chapter(trips_dir)
    trip_dir = trip_json.parent
    (trip_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    svc = TripService(root=trips_dir.parent)

    def stamp(t: dict) -> None:
        mark_render_bundle_current(t)

    svc.update(trip_json, stamp)
    before = svc.load(trip_json)
    assert before["meta"]["renderedRevision"] == meta_revision(before)
    assert trip_render_bundle_stale(trip_dir, before) is False

    updated_before = before.get("updatedAt")
    handler = MockStudioHandler(
        trips_dir,
        json_body={"event": "photos_only_on"},
        path="/__travelogue/trips/demo-copy-intent/copy-telemetry",
    )
    handle_post_copy_telemetry(handler, "demo-copy-intent")
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["event"] == "photos_only_on"
    saved = svc.load(trip_json)
    metrics = saved["curation"]["copyMetrics"]
    assert metrics["clientEventCounts"]["photos_only_on"] == 1
    assert saved["meta"]["renderedRevision"] == meta_revision(saved)
    assert trip_render_bundle_stale(trip_dir, saved) is False
    assert saved.get("updatedAt") == updated_before


def test_handle_post_copy_telemetry_keeps_true_stale(tmp_path: Path) -> None:
    """Telemetry must not clear a real content-ahead-of-preview watermark gap."""
    from travelogue.layout_templates.css_stale import trip_render_bundle_stale
    from travelogue.services.trip import meta_revision
    from travelogue.web.studio_handlers.trip_intent_handlers import handle_post_copy_telemetry

    trips_dir = tmp_path / "trips"
    trip_json = _trip_with_chapter(trips_dir)
    trip_dir = trip_json.parent
    (trip_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    svc = TripService(root=trips_dir.parent)

    # Bypass CAS stamp path: write a known stale watermark directly.
    trip = svc.load(trip_json)
    trip.setdefault("meta", {})["revision"] = 3
    trip["meta"]["renderedRevision"] = 1
    trip["meta"]["title"] = "edited after render"
    trip["updatedAt"] = "2025-01-01T00:00:00Z"
    svc.save(trip, trip_json)
    assert trip_render_bundle_stale(trip_dir, svc.load(trip_json)) is True

    handler = MockStudioHandler(
        trips_dir,
        json_body={"event": "preview_open"},
        path="/__travelogue/trips/demo-copy-intent/copy-telemetry",
    )
    handle_post_copy_telemetry(handler, "demo-copy-intent")
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    after = svc.load(trip_json)
    assert trip_render_bundle_stale(trip_dir, after) is True
    assert after["meta"]["renderedRevision"] == 1
    assert meta_revision(after) == 4
    assert after.get("updatedAt") == "2025-01-01T00:00:00Z"


def test_copy_telemetry_does_not_reflag_preview_stale(tmp_path: Path) -> None:
    """Opening preview after curate must not revive algorithmStale via updatedAt."""
    import os
    from datetime import datetime

    from travelogue.curation.algorithm_profile import assess_algorithm_freshness, expected_profile
    from travelogue.services.trip import mark_render_bundle_current
    from travelogue.web.studio_handlers.trip_intent_handlers import handle_post_copy_telemetry

    trips_dir = tmp_path / "trips"
    trip_json = _trip_with_chapter(trips_dir)
    trip_dir = trip_json.parent
    (trip_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    preview = trip_dir / "preview.jpg"
    preview.write_bytes(b"jpeg")
    svc = TripService(root=trips_dir.parent)
    curated_at = "2025-06-01T12:00:00Z"
    curated_ts = datetime.fromisoformat(curated_at.replace("Z", "+00:00")).timestamp()

    def seed(t: dict) -> None:
        mark_render_bundle_current(t)
        profile = expected_profile()
        profile["curatedAt"] = curated_at
        t.setdefault("curation", {})["algorithmProfile"] = profile
        t["assets"] = [
            {
                "id": "a1",
                "type": "image",
                "quality": {
                    "aesthetic": {
                        "version": profile["aestheticVersion"],
                        "overall": 0.5,
                        "confidence": 0.6,
                        "source": "rules",
                        "dims": {},
                        "signals": {},
                    }
                },
            }
        ]

    svc.update(trip_json, seed)
    os.utime(preview, (curated_ts + 2, curated_ts + 2))
    before = assess_algorithm_freshness(svc.load(trip_json), trip_dir)
    assert before["previewStale"] is False

    handler = MockStudioHandler(
        trips_dir,
        json_body={"event": "preview_open"},
        path="/__travelogue/trips/demo-copy-intent/copy-telemetry",
    )
    handle_post_copy_telemetry(handler, "demo-copy-intent")
    assert handler.response is not None
    assert handler.response[0] == 200
    after = assess_algorithm_freshness(svc.load(trip_json), trip_dir)
    assert after["previewStale"] is False
    assert after["algorithmStale"] is False
