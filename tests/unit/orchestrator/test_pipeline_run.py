"""Orchestrator run chain."""

from __future__ import annotations

import json
from pathlib import Path

from tests.test_ingest import _album
from travelogue.orchestrator.run import run_trip
from travelogue.services.trip_factory import create_trip


def test_run_until_structure(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("run-test", trips, title="运行测试")
    album = _album(tmp_path, 6)
    result = run_trip(
        trip_json,
        from_stage="ingest",
        until="structure",
        album_dir=album,
        validate=False,
        dedupe=False,
    )
    assert "ingest" in result.stages
    assert "curate" in result.stages
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    assert trip["pipeline"]["status"] == "structure_draft"
    assert len(trip["chapters"]) >= 3
    timings = (trip.get("pipeline") or {}).get("timings") or {}
    assert "ingestMs" in timings
    assert "curateMs" in timings
    assert timings["ingestMs"] >= 0
    assert timings["curateMs"] >= 0
