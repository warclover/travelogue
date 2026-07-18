"""Unit tests for Studio import subprocess worker."""

from __future__ import annotations

import multiprocessing as mp
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest

from travelogue.demo.build import DemoError
from travelogue.web.studio_subprocess import ImportSubprocess, _import_worker

pytestmark = pytest.mark.unit


@dataclass
class _FakePipelineResult:
    trip_id: str
    trip_dir: Path
    preview_url: str = "http://127.0.0.1:8766/trips/demo/index.html"
    cluster_notice: str = ""
    title: str = "测试"
    intent_line: str = ""
    featured_count: int = 0
    segment_count: int = 0
    tier_mode: str = "none"
    g1_pending: bool = False
    sparse_g1_suppressed: bool = False
    photo_count: int = 6
    cull_user_line: str = ""
    cull_warn: str = ""
    template_feedback_kind: str = ""
    template_feedback_message: str = ""
    resolved_template_id: str = "visual-journal"
    import_mode: str = "quick_share"
    layout_density: str = "balanced"
    layout_density_effect: str = "ignored_quick"
    date_range_warn: str = ""
    photo_cull_enabled: bool = True
    layout_eligible_count: int = 0
    keep_near_duplicates: bool = False
    assets_written: int = 0
    media_warn: str = ""
    title_noise_fallback: bool = False


def _drain_queue(queue: mp.Queue, *, timeout: float = 2.0) -> list[dict]:
    import time

    events: list[dict] = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            remaining = max(0.01, deadline - time.monotonic())
            events.append(queue.get(timeout=remaining))
        except Exception:
            break
    while True:
        try:
            events.append(queue.get_nowait())
        except Exception:
            break
    return events


def _base_payload(tmp_path: Path) -> dict:
    album = tmp_path / "album"
    album.mkdir()
    trips = tmp_path / "trips"
    trips.mkdir()
    return {
        "albumPath": str(album),
        "tripsDir": str(trips),
        "title": "子进程测试",
        "place": "京都",
        "host": "127.0.0.1",
        "port": 8766,
    }


def test_import_worker_emits_progress_and_done(tmp_path: Path) -> None:
    ctx = mp.get_context("spawn")
    queue: mp.Queue = ctx.Queue()
    cancel = ctx.Event()
    result = _FakePipelineResult(trip_id="demo-sub", trip_dir=tmp_path / "trips" / "demo-sub")

    def fake_run(*_args, progress=None, **_kwargs):
        if progress:
            progress("ingest", 1, "ingesting")
        return result

    with patch("travelogue.web.studio_pipeline.run_studio_pipeline", side_effect=fake_run):
        _import_worker(_base_payload(tmp_path), queue, cancel)

    events = _drain_queue(queue)
    assert [e["type"] for e in events] == ["progress", "done"]
    assert events[1]["result"]["tripId"] == "demo-sub"


def test_import_worker_surfaces_demo_error(tmp_path: Path) -> None:
    ctx = mp.get_context("spawn")
    queue: mp.Queue = ctx.Queue()
    cancel = ctx.Event()

    with patch(
        "travelogue.web.studio_pipeline.run_studio_pipeline",
        side_effect=DemoError("E_DEMO_TOO_FEW", "too few photos"),
    ):
        _import_worker(_base_payload(tmp_path), queue, cancel)

    events = _drain_queue(queue)
    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert events[0]["code"] == "E_DEMO_TOO_FEW"
    assert events[0]["demo"] is True


def test_import_worker_surfaces_ingest_too_few_not_demo_code(tmp_path: Path) -> None:
    """Regular album too-few must keep E_INGEST_TOO_FEW through the subprocess event."""
    ctx = mp.get_context("spawn")
    queue: mp.Queue = ctx.Queue()
    cancel = ctx.Event()

    with patch(
        "travelogue.web.studio_pipeline.run_studio_pipeline",
        side_effect=DemoError(
            "E_INGEST_TOO_FEW",
            "need at least 4 assets in trip after ingest (have 1)",
        ),
    ):
        _import_worker(_base_payload(tmp_path), queue, cancel)

    events = _drain_queue(queue)
    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert events[0]["code"] == "E_INGEST_TOO_FEW"
    assert "示例相册" not in str(events[0].get("message") or "")


def test_import_worker_surfaces_generic_error(tmp_path: Path) -> None:
    ctx = mp.get_context("spawn")
    queue: mp.Queue = ctx.Queue()
    cancel = ctx.Event()

    with patch(
        "travelogue.web.studio_pipeline.run_studio_pipeline",
        side_effect=RuntimeError("disk full"),
    ):
        _import_worker(_base_payload(tmp_path), queue, cancel)

    events = _drain_queue(queue)
    assert events[0]["type"] == "error"
    assert events[0]["code"] == "E_STUDIO_PIPELINE"
    assert events[0]["demo"] is False


def test_import_worker_honours_cancel_event(tmp_path: Path) -> None:
    ctx = mp.get_context("spawn")
    queue: mp.Queue = ctx.Queue()
    cancel = ctx.Event()
    cancel.set()

    def fake_run(*_args, progress=None, **_kwargs):
        if progress:
            progress("ingest", 1, "ingesting")
        return _FakePipelineResult("x", tmp_path / "trips" / "x")

    with patch("travelogue.web.studio_pipeline.run_studio_pipeline", side_effect=fake_run):
        _import_worker(_base_payload(tmp_path), queue, cancel)

    events = _drain_queue(queue)
    assert events[0]["type"] == "error"
    assert events[0]["code"] == "E_STUDIO_CANCELLED"


def test_import_subprocess_drain_empty_before_start(tmp_path: Path) -> None:
    payload = _base_payload(tmp_path)
    handle = ImportSubprocess(payload)
    assert handle.drain() == []
    assert handle.alive is False
