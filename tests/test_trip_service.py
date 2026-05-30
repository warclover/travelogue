"""TripService load/save."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.services.trip import TripService


def test_save_removes_temp_file_on_replace_failure(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "trip.json"
    trip = {"tripId": "t1", "version": "0.2"}
    svc = TripService()

    def boom_replace(src: str, dst: str) -> None:
        raise OSError("simulated failure")

    monkeypatch.setattr("travelogue.services.trip.os.replace", boom_replace)
    with pytest.raises(OSError):
        svc.save(trip, path)
    leftovers = list(tmp_path.glob(f".trip-*.json"))
    assert leftovers == []


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
    assert svc.resolve_trip_json("demo") == trip_json.resolve()
    assert svc.resolve_trip_json("trips/demo") == trip_json.resolve()
    assert svc.resolve_trip_json("trips/demo/trip.json") == trip_json.resolve()


def test_resolve_trip_json_from_inside_trip_dir(tmp_path: Path, monkeypatch) -> None:
    """When cwd is trips/demo, trips/demo and . should still resolve."""
    trip_dir = tmp_path / "trips" / "demo"
    trip_dir.mkdir(parents=True)
    trip_json = trip_dir / "trip.json"
    trip_json.write_text('{"tripId":"demo"}', encoding="utf-8")
    monkeypatch.chdir(trip_dir)
    svc = TripService()
    assert svc.resolve_trip_json("trips/demo") == trip_json.resolve()
    assert svc.resolve_trip_json(".") == trip_json.resolve()
    assert svc.resolve_trip_json("demo") == trip_json.resolve()


def test_app_context_for_trip_json_root(tmp_path: Path, monkeypatch) -> None:
    from travelogue.runtime import app_context_for_trip_json, app_context_for_trips_dir

    monkeypatch.chdir(tmp_path)
    trip_json = tmp_path / "trips" / "demo" / "trip.json"
    trip_json.parent.mkdir(parents=True, exist_ok=True)
    trip_json.write_text('{"tripId":"demo"}', encoding="utf-8")
    ctx = app_context_for_trip_json(trip_json)
    assert ctx.trips_root == (tmp_path / "trips").resolve()
    assert ctx.trip_service().root == tmp_path.resolve()
    ctx2 = app_context_for_trips_dir(tmp_path / "trips")
    assert ctx2.trip_service().resolve_trip_json("demo", trips_dir=ctx2.trips_root) == trip_json.resolve()
