"""TripService.update CAS / revision tests (M-A1a)."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from travelogue.services.trip import (
    TripConflictError,
    TripService,
    _get_trip_write_lock,
    _trip_lock_key,
    meta_revision,
)


def _minimal_trip() -> dict:
    return {
        "version": "0.2",
        "tripId": "update-test",
        "templateId": "visual-journal",
        "exportLayout": "auto",
        "meta": {
            "title": "测试",
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


@pytest.fixture
def trip_path(tmp_path: Path) -> Path:
    path = tmp_path / "trip.json"
    TripService().save(_minimal_trip(), path)
    return path


def test_update_increments_revision_monotonically(trip_path: Path) -> None:
    svc = TripService()

    def bump_title(trip: dict) -> None:
        trip["meta"]["title"] = "一次"

    svc.update(trip_path, bump_title)
    assert meta_revision(svc.load(trip_path)) == 1

    def bump_again(trip: dict) -> None:
        trip["meta"]["title"] = "两次"

    svc.update(trip_path, bump_again)
    loaded = svc.load(trip_path)
    assert meta_revision(loaded) == 2
    assert loaded["meta"]["title"] == "两次"
    assert loaded["updatedAt"].endswith("Z")


def test_update_replays_mutator_on_revision_conflict(trip_path: Path) -> None:
    svc = TripService()
    attempts: list[int] = []

    def mutator(trip: dict) -> str:
        attempts.append(meta_revision(trip))
        if len(attempts) == 1:
            external = svc.load(trip_path)
            external.setdefault("meta", {})["revision"] = 1
            external["meta"]["title"] = "外部写入"
            svc.save(external, trip_path)
        trip["meta"]["title"] = f"attempt-{len(attempts)}"
        return trip["meta"]["title"]

    result = svc.update(trip_path, mutator, max_retries=3)
    assert result == "attempt-2"
    assert attempts == [0, 1]
    loaded = svc.load(trip_path)
    assert meta_revision(loaded) == 2
    assert loaded["meta"]["title"] == "attempt-2"


def test_update_raises_after_retries_exhausted(trip_path: Path, monkeypatch) -> None:
    svc = TripService()

    def mutator(trip: dict) -> None:
        trip["meta"]["title"] = "never"

    def always_stale(_path: Path) -> int:
        return 999

    monkeypatch.setattr("travelogue.services.trip._read_disk_revision", always_stale)
    with pytest.raises(TripConflictError) as exc:
        svc.update(trip_path, mutator, max_retries=2)
    assert exc.value.code == "E_TRIP_CONFLICT"


def test_trip_lock_key_normalizes_path_case(tmp_path: Path) -> None:
    nested = tmp_path / "TripCase"
    nested.mkdir()
    lower = nested / "trip.json"
    upper = tmp_path / "tripcase" / "TRIP.JSON"
    lower.write_text("{}", encoding="utf-8")
    assert _trip_lock_key(lower) == _trip_lock_key(upper)


def test_lock_registry_concurrent_insert_uses_single_lock(trip_path: Path) -> None:
    keys: list[str] = []
    locks: list[threading.Lock] = []
    barrier = threading.Barrier(8)

    def worker() -> None:
        barrier.wait()
        lock = _get_trip_write_lock(trip_path)
        locks.append(lock)
        keys.append(_trip_lock_key(trip_path))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)
        assert not thread.is_alive()

    assert len(set(keys)) == 1
    assert len(set(id(lock) for lock in locks)) == 1


def test_update_returns_mutator_result(trip_path: Path) -> None:
    svc = TripService()
    out = svc.update(trip_path, lambda trip: trip["meta"]["title"])
    assert out == "测试"


def test_save_without_revision_leaves_meta_revision_absent(trip_path: Path) -> None:
    svc = TripService()
    trip = svc.load(trip_path)
    assert "revision" not in trip.get("meta", {})
    svc.save(trip, trip_path)
    assert meta_revision(svc.load(trip_path)) == 0
