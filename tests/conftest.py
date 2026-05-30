"""Shared pytest fixtures and resource hygiene for the test suite."""

from __future__ import annotations

import gc
import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip
from tests.studio_test_helpers import IngestedTripWorkspace, make_test_album


@pytest.fixture(autouse=True)
def _release_resources_before_playwright(request: pytest.FixtureRequest):
    """Reduce open_clip/torch ↔ Playwright contention for longshot capture."""
    if request.node.get_closest_marker("playwright_serial") is None:
        yield
        return

    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass

    gc.collect()
    yield
    gc.collect()


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
