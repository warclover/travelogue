"""TripService load/save."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.services.trip import TripService


def test_save_writes_valid_json(tmp_path: Path) -> None:
    path = tmp_path / "trip.json"
    trip = {"tripId": "t1", "version": "0.2", "meta": {"title": "测"}}
    TripService().save(trip, path)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["tripId"] == "t1"
