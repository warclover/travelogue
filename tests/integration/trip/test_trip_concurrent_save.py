"""Concurrent trip.json writes stay atomic and parseable (via TripService.update)."""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from travelogue.services.trip import TripConflictError, TripSaveError, TripService, meta_revision


def _minimal_trip() -> dict:
    return {
        "version": "0.2",
        "tripId": "race",
        "templateId": "visual-journal",
        "exportLayout": "auto",
        "meta": {
            "title": "init",
            "dateStart": "2025-01-01",
            "dateEnd": "2025-01-02",
            "places": ["测试"],
            "tone": "relaxed",
        },
        "assets": [],
        "chapters": [],
        "pipeline": {"status": "draft"},
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-01T00:00:00Z",
    }


def test_concurrent_update_leaves_valid_trip_json(tmp_path: Path) -> None:
    path = tmp_path / "trip.json"
    TripService().save(_minimal_trip(), path)
    svc = TripService()
    expected: set[str] = set()
    guard = threading.Lock()
    errors: list[BaseException] = []

    def _update(run_id: int) -> None:
        key = f"writer-{run_id}"
        try:

            def mutator(trip: dict, marker: str = key) -> None:
                trip.setdefault("meta", {})["title"] = marker

            svc.update(path, mutator, max_retries=5)
            with guard:
                expected.add(key)
        except (TripConflictError, TripSaveError, OSError, json.JSONDecodeError) as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(_update, range(12)))

    assert not errors
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["tripId"] == "race"
    assert data["meta"]["title"] in expected
    assert meta_revision(data) >= len(expected)
    assert list(tmp_path.glob(".trip-*.json")) == []


def test_concurrent_update_no_temp_file_leaks(tmp_path: Path) -> None:
    path = tmp_path / "trip.json"
    TripService().save(_minimal_trip(), path)
    svc = TripService()
    busy_errors: list[TripSaveError] = []

    def _update(i: int) -> None:
        try:

            def mutator(trip: dict, batch: int = i) -> None:
                trip["batch"] = batch

            svc.update(path, mutator, max_retries=5)
        except TripConflictError:
            return
        except (TripSaveError, PermissionError, OSError, json.JSONDecodeError) as exc:
            if isinstance(exc, TripSaveError):
                busy_errors.append(exc)

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(_update, range(20)))

    assert list(tmp_path.glob(".trip-*.json")) == []
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["tripId"] == "race"
    assert "batch" in data
