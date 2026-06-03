"""Template decision log (AC-P13-07)."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.services.trip_factory import create_trip
from travelogue.templating.decision_log import list_decisions, log_path


def test_create_trip_writes_decision_log(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trips.mkdir()
    trip_json = create_trip("log-trip", trips)
    trip_dir = trip_json.parent
    assert log_path(trip_dir).is_file()
    rows = list_decisions(trip_dir, limit=5)
    assert len(rows) >= 1
    assert rows[-1]["action"] == "create"
    assert rows[-1]["resolvedTemplateId"] == "visual-journal"
