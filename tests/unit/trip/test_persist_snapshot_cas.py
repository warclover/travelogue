"""Full-snapshot CAS vs incremental persist (lost-update guard)."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.services.trip import (
    TripConflictError,
    TripService,
    apply_intent,
    meta_revision,
    persist_pipeline_owned,
    persist_trip_snapshot,
)


def _minimal_trip() -> dict:
    return {
        "version": "0.2",
        "tripId": "snapshot-cas",
        "templateId": "visual-journal",
        "exportLayout": "auto",
        "meta": {
            "title": "old",
            "dateStart": "2025-01-01",
            "dateEnd": "2025-01-02",
            "places": ["测试"],
            "tone": "relaxed",
        },
        "intent": {"title": "old"},
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


def test_persist_trip_snapshot_rejects_stale_replay(trip_path: Path) -> None:
    svc = TripService()
    stale = svc.load(trip_path)
    base = meta_revision(stale)
    stale.setdefault("intent", {})["title"] = "old"
    stale.setdefault("meta", {})["title"] = "old"

    def patch(disk: dict) -> None:
        apply_intent(disk, title="new", user_notes="并发笔记")

    svc.update(trip_path, patch)

    with pytest.raises(TripConflictError):
        persist_trip_snapshot(svc, trip_path, stale, base_revision=base)

    loaded = svc.load(trip_path)
    assert loaded["intent"]["title"] == "new"
    assert loaded["userNotes"] == "并发笔记"
    assert meta_revision(loaded) >= 1


def test_persist_pipeline_owned_keeps_http_intent(trip_path: Path) -> None:
    svc = TripService()
    memory = svc.load(trip_path)
    memory["pipeline"] = {"status": "rendered"}
    memory.setdefault("intent", {})["title"] = "old"
    memory.setdefault("meta", {})["title"] = "old"

    def patch(disk: dict) -> None:
        apply_intent(disk, title="new", user_notes="并发笔记")

    svc.update(trip_path, patch)
    persist_pipeline_owned(svc, trip_path, memory)
    loaded = svc.load(trip_path)
    assert loaded["intent"]["title"] == "new"
    assert loaded["userNotes"] == "并发笔记"
    assert loaded["pipeline"]["status"] == "rendered"
    assert loaded["meta"]["title"] == "new"
