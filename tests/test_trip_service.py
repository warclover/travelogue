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


def test_resolve_trip_json_accepts_trip_dir_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    trip_dir = tmp_path / "trips" / "demo"
    trip_dir.mkdir(parents=True)
    trip_json = trip_dir / "trip.json"
    trip_json.write_text('{"tripId":"demo"}', encoding="utf-8")
    svc = TripService(root=tmp_path)
    assert svc.resolve_trip_json("linzhi".replace("linzhi", "demo")) == trip_json.resolve()
    assert svc.resolve_trip_json("trips/demo") == trip_json.resolve()
    assert svc.resolve_trip_json("trips/demo/trip.json") == trip_json.resolve()
