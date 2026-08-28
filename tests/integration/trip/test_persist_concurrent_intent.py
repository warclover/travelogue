"""Import / render must not replay stale title or notes over HTTP edits."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from tests.studio_test_helpers import make_test_album
from travelogue.orchestrator.run import run_trip
from travelogue.render.engine import render_trip
from travelogue.services.trip import (
    TripConflictError,
    TripSaveError,
    TripService,
    apply_intent,
)
from travelogue.services.trip_factory import create_trip
from travelogue.web.copy_patch import CopyPatchError, apply_copy_patch

pytestmark = pytest.mark.integration


def _patch_intent_loop(trip_json: Path, stop: threading.Event, counts: dict[str, int]) -> None:
    local = TripService()
    while not stop.is_set():
        try:

            def mutator(disk: dict) -> None:
                apply_intent(
                    disk,
                    title="HTTP补丁标题",
                    user_notes="并发笔记",
                )

            local.update(trip_json, mutator, max_retries=8)
            counts["ok"] += 1
        except (TripConflictError, TripSaveError):
            counts["err"] += 1
        time.sleep(0.01)


def test_run_trip_keeps_http_title_and_notes(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("run-intent", trips, title="初始")
    album = make_test_album(tmp_path, 6)
    stop = threading.Event()
    counts = {"ok": 0, "err": 0}

    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_patch_intent_loop, trip_json, stop, counts)
        try:
            result = run_trip(
                trip_json,
                from_stage="ingest",
                until="structure",
                album_dir=album,
                validate=False,
                dedupe=False,
            )
        finally:
            stop.set()
            fut.result(timeout=15)

    assert "ingest" in result.stages
    assert "curate" in result.stages
    assert counts["ok"] >= 1
    loaded = TripService().load(trip_json)
    assert loaded["intent"]["title"] == "HTTP补丁标题"
    assert loaded["userNotes"] == "并发笔记"
    assert len(loaded.get("assets") or []) >= 1


def test_render_trip_keeps_http_title_and_notes(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("render-intent", trips, title="初始")
    album = make_test_album(tmp_path, 6)
    run_trip(
        trip_json,
        from_stage="ingest",
        until="structure",
        album_dir=album,
        validate=False,
        dedupe=False,
    )

    stop = threading.Event()
    counts = {"ok": 0, "err": 0}
    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_patch_intent_loop, trip_json, stop, counts)
        try:
            render_trip(
                trip_json,
                trip_json.parent,
                export_mode="draft",
                validate=False,
                update_pipeline=True,
            )
        finally:
            stop.set()
            fut.result(timeout=15)

    assert counts["ok"] >= 1
    loaded = TripService().load(trip_json)
    assert loaded["intent"]["title"] == "HTTP补丁标题"
    assert loaded["userNotes"] == "并发笔记"


def _patch_lead_loop(
    trip_json: Path, chapter_id: str, stop: threading.Event, counts: dict[str, int]
) -> None:
    local = TripService()
    while not stop.is_set():
        try:

            def mutator(disk: dict) -> None:
                apply_copy_patch(disk, f"chapters.{chapter_id}.lead", "用户改过的章导语")

            local.update(trip_json, mutator, max_retries=8)
            counts["ok"] += 1
        except (TripConflictError, TripSaveError, CopyPatchError):
            counts["err"] += 1
        time.sleep(0.01)


def test_narrate_keeps_http_chapter_lead(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("narrate-lead", trips, title="初始")
    album = make_test_album(tmp_path, 6)
    run_trip(
        trip_json,
        from_stage="ingest",
        until="structure",
        album_dir=album,
        validate=False,
        dedupe=False,
    )
    structured = TripService().load(trip_json)
    chapters = structured.get("chapters") or []
    assert chapters, "until=structure must produce chapters"
    chapter_id = str(chapters[0]["id"])

    stop = threading.Event()
    counts = {"ok": 0, "err": 0}
    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_patch_lead_loop, trip_json, chapter_id, stop, counts)
        try:
            result = run_trip(
                trip_json,
                from_stage="lock_structure",
                until="copy",
                validate=False,
            )
        finally:
            stop.set()
            fut.result(timeout=15)

    assert "narrate" in result.stages
    assert counts["ok"] >= 1
    loaded = TripService().load(trip_json)
    patched = next(ch for ch in loaded["chapters"] if ch.get("id") == chapter_id)
    assert patched["lead"] == "用户改过的章导语"
    assert patched.get("leadOrigin") == "user"
