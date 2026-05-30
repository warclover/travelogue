"""Concurrent trip.json writes stay atomic and parseable."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from travelogue.services.trip import TripSaveError, TripService


def test_concurrent_save_leaves_valid_trip_json(tmp_path: Path) -> None:
    path = tmp_path / "trip.json"
    path.write_text(
        json.dumps({"tripId": "race", "version": "0.2", "meta": {"title": "init"}}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    svc = TripService()
    errors: list[BaseException] = []

    def _save(run_id: int) -> None:
        try:
            trip = json.loads(path.read_text(encoding="utf-8"))
            trip.setdefault("meta", {})["title"] = f"writer-{run_id}"
            trip["updatedAt"] = f"2026-05-30T12:00:{run_id:02d}Z"
            svc.save(trip, path)
        except (TripSaveError, OSError, json.JSONDecodeError) as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(_save, range(12)))

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["tripId"] == "race"
    assert str(data["meta"]["title"]).startswith("writer-")
    leftovers = list(tmp_path.glob(".trip-*.json"))
    assert leftovers == []


def test_concurrent_save_no_temp_file_leaks(tmp_path: Path) -> None:
    path = tmp_path / "trip.json"
    path.write_text('{"tripId":"t2","version":"0.2"}\n', encoding="utf-8")
    svc = TripService()
<<<<<<< HEAD

    def _save(i: int) -> None:
        trip = json.loads(path.read_text(encoding="utf-8"))
        trip["batch"] = i
        svc.save(trip, path)
=======
    busy_errors: list[TripSaveError] = []

    def _save(i: int) -> None:
        try:
            trip = json.loads(path.read_text(encoding="utf-8"))
            trip["batch"] = i
            svc.save(trip, path)
        except (TripSaveError, PermissionError, OSError, json.JSONDecodeError) as exc:
            if isinstance(exc, TripSaveError):
                busy_errors.append(exc)
>>>>>>> e02f24c (test: concurrent trip save and longshot page cleanup on goto failure)

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(_save, range(20)))

    assert list(tmp_path.glob(".trip-*.json")) == []
<<<<<<< HEAD
=======
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["tripId"] == "t2"
    assert "batch" in data
>>>>>>> e02f24c (test: concurrent trip save and longshot page cleanup on goto failure)
