"""Pipeline Throughput · ingest merge mutator."""

from __future__ import annotations

from travelogue.media.ingest_persist import merge_ingest_partial


def test_merge_ingest_partial_preserves_intent_and_copy() -> None:
    disk = {
        "assets": [{"id": "asset-001"}],
        "intent": {"title": "HTTP patched", "places": ["京都"]},
        "chapters": [{"id": "ch-1", "title": "keep"}],
        "pipeline": {"locks": {"structure": True, "copy": False}, "status": "old"},
        "meta": {"revision": 5, "title": "disk"},
    }
    memory = {
        "assets": [{"id": "asset-001"}, {"id": "asset-002"}],
        "intent": {"title": "stale memory", "places": []},
        "chapters": [],
        "coverAssetId": "asset-001",
        "pipeline": {
            "status": "ingest_ready",
            "ingestStats": {"added": 2},
            "locks": {"structure": False, "copy": False},
        },
        "meta": {"dateStart": "2024-01-01", "revision": 99},
    }
    merge_ingest_partial(disk, memory_trip=memory)
    assert len(disk["assets"]) == 2
    assert disk["coverAssetId"] == "asset-001"
    assert disk["intent"]["title"] == "HTTP patched"
    assert disk["chapters"][0]["id"] == "ch-1"
    assert disk["pipeline"]["status"] == "ingest_ready"
    assert disk["pipeline"]["ingestStats"]["added"] == 2
    # existing structure lock must not be cleared by ingest memory
    assert disk["pipeline"]["locks"]["structure"] is True
    assert disk["meta"]["revision"] == 5
    assert disk["meta"]["dateStart"] == "2024-01-01"
    # mid-ingest must not clobber HTTP-mirrored title
    assert disk["meta"]["title"] == "disk"


def test_merge_pipeline_persist_preserves_http_intent() -> None:
    from travelogue.media.ingest_persist import merge_pipeline_persist

    disk = {
        "assets": [{"id": "a1"}],
        "intent": {"title": "HTTP wins", "places": ["大阪"]},
        "userNotes": "用户补丁",
        "chapters": [],
        "pipeline": {"status": "ingest_ready"},
        "meta": {"title": "old"},
    }
    memory = {
        "assets": [{"id": "a1"}, {"id": "a2"}],
        "intent": {"title": "stale", "places": []},
        "userNotes": "过期",
        "chapters": [{"id": "ch-01"}],
        "pipeline": {"status": "structure_locked", "locks": {"structure": True}},
        "meta": {"title": "pipeline", "dateStart": "2025-01-01"},
        "coverAssetId": "a1",
    }
    merge_pipeline_persist(disk, memory_trip=memory)
    assert disk["intent"]["title"] == "HTTP wins"
    assert disk["userNotes"] == "用户补丁"
    assert len(disk["assets"]) == 2
    assert disk["chapters"][0]["id"] == "ch-01"
    assert disk["pipeline"]["status"] == "structure_locked"
    assert disk["meta"]["dateStart"] == "2025-01-01"
    assert disk["meta"]["title"] == "HTTP wins"
    assert disk["meta"]["places"] == ["大阪"]
