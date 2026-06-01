"""Shared pytest fixtures and resource hygiene for the test suite."""

from __future__ import annotations

import gc
import json
import shutil
import threading
from copy import deepcopy
from pathlib import Path

import pytest

_playwright_gate = threading.Lock()

from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip
from tests.studio_test_helpers import IngestedTripWorkspace, make_test_album


def _is_studio_ui_playwright(item: pytest.Item) -> bool:
    nodeid = item.nodeid.replace("\\", "/")
    return "test_studio_p9_qa_playwright" in nodeid or "test_studio_p10_layout_playwright" in nodeid


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Run Studio homepage Playwright last; other serial Playwright before them."""
    studio_ui: list[pytest.Item] = []
    serial: list[pytest.Item] = []
    other: list[pytest.Item] = []
    for item in items:
        if _is_studio_ui_playwright(item):
            studio_ui.append(item)
        elif item.get_closest_marker("playwright_serial"):
            serial.append(item)
        else:
            other.append(item)
    items[:] = other + serial + studio_ui


@pytest.fixture(autouse=True)
def _release_resources_before_playwright(request: pytest.FixtureRequest):
    """Reduce open_clip/torch ↔ Playwright contention for longshot capture."""
    if request.node.get_closest_marker("playwright_serial") is None:
        yield
        return

    with _playwright_gate:
        try:
            from travelogue.export.longshot import reset_browser_pool_for_tests

            reset_browser_pool_for_tests()
        except Exception:
            pass
        if _is_studio_ui_playwright(request.node):
            gc.collect()

        try:
            import torch  # type: ignore

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

        gc.collect()
        yield
        gc.collect()
        try:
            from travelogue.export.longshot import reset_browser_pool_for_tests

            reset_browser_pool_for_tests()
        except Exception:
            pass


@pytest.fixture(autouse=True)
def _reset_clip_encoder_singleton() -> None:
    """Avoid CLIP singleton state leaking between vision/clustering tests."""
    yield
    try:
        from travelogue.vision.clip_encoder import reset_clip_encoder_singleton

        reset_clip_encoder_singleton()
    except Exception:
        pass


@pytest.fixture(scope="session")
def session_ingested_trip(tmp_path_factory: pytest.TempPathFactory) -> IngestedTripWorkspace:
    """One ingest per session — copy into per-test tmp dirs to skip re-ingest."""
    root = tmp_path_factory.mktemp("session-pipeline")
    album = make_test_album(root, 8)
    trips_dir = root / "trips"
    trip_json = create_trip("session-ingest", trips_dir, title="Session", place="京都")
    trip_dir = trips_dir / "session-ingest"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=False)
    trip_json.write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return IngestedTripWorkspace(
        trips_dir=trips_dir,
        trip_id="session-ingest",
        trip_dir=trip_dir,
        trip_json=trip_json,
    )


@pytest.fixture
def ingested_trip(
    session_ingested_trip: IngestedTripWorkspace, tmp_path: Path
) -> tuple[IngestedTripWorkspace, dict]:
    """Mutable trip workspace + trip dict cloned from session ingest."""
    trips_dir = tmp_path / "trips"
    trip_dir = trips_dir / session_ingested_trip.trip_id
    shutil.copytree(session_ingested_trip.trip_dir, trip_dir)
    trip_json = trip_dir / "trip.json"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    workspace = IngestedTripWorkspace(
        trips_dir=trips_dir,
        trip_id=session_ingested_trip.trip_id,
        trip_dir=trip_dir,
        trip_json=trip_json,
    )
    return workspace, deepcopy(trip)
