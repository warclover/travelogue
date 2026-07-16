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


def test_merge_pipeline_persist_propagates_render_bundle_stamp() -> None:
    """Post-render metadata persist must hand stamp to disk so update can watermark."""
    from travelogue.media.ingest_persist import merge_pipeline_persist
    from travelogue.services.trip import STAMP_RENDERED_REVISION, mark_render_bundle_current

    disk = {
        "assets": [{"id": "a1"}],
        "pipeline": {"status": "rendered", "timings": {}},
        "meta": {"revision": 4, "renderedRevision": 4, "title": "keep"},
    }
    memory = {
        "assets": [{"id": "a1"}],
        "pipeline": {"status": "rendered", "timings": {"totalMs": 12.0}},
        "meta": {"revision": 4, "renderedRevision": 4, "title": "stale memory"},
    }
    mark_render_bundle_current(memory)
    merge_pipeline_persist(disk, memory_trip=memory)
    assert disk["meta"][STAMP_RENDERED_REVISION] is True
    assert disk["pipeline"]["timings"]["totalMs"] == 12.0
    assert disk["meta"]["renderedRevision"] == 4
    assert disk["meta"]["title"] == "stale memory"


def test_pipeline_persist_mutator_keeps_render_bundle_fresh(tmp_path) -> None:
    """Studio _persist_trip_state after mark_render_bundle_current must not stale."""
    from pathlib import Path

    from travelogue.layout_templates.css_stale import trip_render_bundle_stale
    from travelogue.media.ingest_persist import make_pipeline_persist_mutator
    from travelogue.services.trip import (
        TripService,
        mark_render_bundle_current,
        meta_rendered_revision,
        meta_revision,
    )

    trips_dir = tmp_path / "trips" / "demo"
    trips_dir.mkdir(parents=True)
    trip_json = trips_dir / "trip.json"
    (trips_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    svc = TripService(root=tmp_path)
    seed = {
        "tripId": "demo",
        "meta": {"revision": 0, "title": "demo"},
        "pipeline": {"status": "rendered", "timings": {}},
        "assets": [],
    }
    svc.save(seed, trip_json)

    def stamp(t: dict) -> None:
        mark_render_bundle_current(t)

    svc.update(trip_json, stamp)
    memory = svc.load(trip_json)
    assert meta_rendered_revision(memory) == meta_revision(memory)
    assert trip_render_bundle_stale(trips_dir, memory) is False

    memory.setdefault("pipeline", {})["timings"] = {"totalMs": 99.0}
    mark_render_bundle_current(memory)
    svc.update(trip_json, make_pipeline_persist_mutator(memory))
    after = svc.load(trip_json)
    assert after["pipeline"]["timings"]["totalMs"] == 99.0
    assert meta_rendered_revision(after) == meta_revision(after)
    assert trip_render_bundle_stale(Path(trips_dir), after) is False


def test_intent_folders_merge_mutator_pushes_featured_detected() -> None:
    """Stable-QH D-QH-02: folders merge survives disk-intent-wins pipeline persist."""
    from travelogue.media.ingest_persist import (
        make_intent_folders_merge_mutator,
        merge_pipeline_persist,
    )

    disk = {
        "intent": {"version": "1", "title": "HTTP wins", "places": ["京都"], "folders": {}},
        "meta": {"title": "HTTP wins"},
        "pipeline": {"status": "ingest_ready"},
    }
    memory = {
        "intent": {
            "version": "1",
            "title": "stale",
            "places": [],
            "folders": {"featuredDetected": True},
        },
        "pipeline": {"status": "structure_locked"},
        "chapters": [{"id": "ch-01"}],
    }
    mutator = make_intent_folders_merge_mutator(memory)
    mutator(disk)
    assert disk["intent"]["title"] == "HTTP wins"
    assert disk["intent"]["folders"]["featuredDetected"] is True
    merge_pipeline_persist(disk, memory_trip=memory)
    assert disk["intent"]["title"] == "HTTP wins"
    assert disk["intent"]["folders"]["featuredDetected"] is True
    assert disk["chapters"][0]["id"] == "ch-01"


def test_intent_flush_mutator_persists_travel_plan_and_hints() -> None:
    """F5: plan cities must survive disk flush after ingest_travel_plan."""
    from travelogue.media.ingest_persist import make_intent_flush_mutator

    disk: dict = {"intent": {"version": "1", "title": "关西之旅"}}
    memory = {
        "intent": {
            "version": "1",
            "title": "关西之旅",
            "travelPlan": {"cities": ["大阪", "京都"], "format": "text"},
        },
        "curation": {"intentHints": {"planCities": ["大阪", "京都"]}},
    }
    make_intent_flush_mutator(memory)(disk)
    assert disk["intent"]["travelPlan"]["cities"] == ["大阪", "京都"]
    assert disk["curation"]["intentHints"]["planCities"] == ["大阪", "京都"]
