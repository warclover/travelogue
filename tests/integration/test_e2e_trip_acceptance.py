"""Unit tests for e2e trip acceptance script."""



from __future__ import annotations

import json
from pathlib import Path

from tests._repo_root import repo_root
from travelogue.services.trip import TripService


def test_accept_trip_validates_fixture_trip(tmp_path: Path) -> None:
    from scripts.e2e_trip_acceptance import accept_trip

    fixture = repo_root(__file__) / "schemas/fixtures/trip.example.json"
    trip = json.loads(fixture.read_text(encoding="utf-8"))
    trip_dir = tmp_path / "mini"
    trip_dir.mkdir()
    trip["tripId"] = "mini"
    trip.setdefault("pipeline", {})["timings"] = {"ingestMs": 10.0}
    trip_json = trip_dir / "trip.json"
    TripService(root=tmp_path).save(trip, trip_json)

    report = accept_trip(trip_json, layout_equiv=False)
    assert report["ok"] is True
    assert report["telemetry"]["timingsMs"]["ingestMs"] == 10.0


def test_accept_trip_flags_missing_render_artifact(tmp_path: Path) -> None:
    from scripts.e2e_trip_acceptance import accept_trip

    trip_dir = tmp_path / "rendered-missing"
    trip_dir.mkdir()
    trip = json.loads(
        (repo_root(__file__) / "schemas/fixtures/trip.example.json").read_text(
            encoding="utf-8"
        )
    )
    trip["tripId"] = "rendered-missing"
    trip.setdefault("pipeline", {})["status"] = "rendered"
    trip_json = trip_dir / "trip.json"
    TripService(root=tmp_path).save(trip, trip_json)

    report = accept_trip(trip_json, layout_equiv=False)
    assert report["ok"] is False
    assert any("index.html" in i for i in report["issues"])
