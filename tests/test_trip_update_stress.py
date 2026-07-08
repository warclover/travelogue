"""AC-ARC-01 · concurrent TripService.update stress."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from travelogue.services.trip import TripConflictError, TripSaveError, TripService, meta_revision


def _minimal_trip() -> dict:
    return {
        "version": "0.2",
        "tripId": "stress",
        "templateId": "visual-journal",
        "exportLayout": "auto",
        "meta": {
            "title": "stress",
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


@pytest.mark.integration
def test_ac_arc_01_concurrent_update_unique_keys(tmp_path: Path, pytestconfig: pytest.Config) -> None:
    iterations = int(pytestconfig.getoption("--stress-iterations"))
    path = tmp_path / "trip.json"
    TripService().save(_minimal_trip(), path)
    expected: set[str] = set()
    guard = threading.Lock()
    thread_count = 16

    def worker(thread_id: int) -> None:
        svc = TripService()
        for seq in range(iterations):
            key = f"mutations.{thread_id}.{seq}"

            def mutator(trip: dict, marker: str = key) -> None:
                trip.setdefault("mutations", {})[marker] = True

            try:
                svc.update(path, mutator, max_retries=5)
            except (TripConflictError, TripSaveError):
                continue
            with guard:
                expected.add(key)

    with ThreadPoolExecutor(max_workers=thread_count) as pool:
        list(pool.map(worker, range(thread_count)))

    loaded = TripService().load(path)
    actual = set((loaded.get("mutations") or {}).keys())
    assert actual == expected
    assert meta_revision(loaded) >= len(expected)
