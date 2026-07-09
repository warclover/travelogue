"""Tests for domain pipeline view (M-C4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.domain.pipeline_view import (
    PipelineError,
    append_pipeline_run,
    assert_stage_allowed,
    clear_pending_assets,
    lock_copy,
    lock_structure,
    revert_copy_lock_for_edit,
    set_layout_status,
    set_pipeline_status,
    set_pipeline_timings,
    trip_status,
    unlock_structure_for_replan,
)
from travelogue.services.trip import TripService, meta_revision


def test_trip_status_default() -> None:
    assert trip_status({}) == "draft_ingest"


def test_lock_structure_and_unlock_replan() -> None:
    trip = {"pipeline": {"status": "structure_draft", "locks": {"structure": False}}}
    lock_structure(trip)
    assert trip["pipeline"]["status"] == "structure_locked"
    assert trip["pipeline"]["locks"]["structure"] is True
    unlock_structure_for_replan(trip)
    assert trip["pipeline"]["status"] == "structure_draft"
    assert trip["pipeline"]["locks"]["structure"] is False


def test_revert_copy_lock_for_edit() -> None:
    trip = {"pipeline": {"status": "copy_locked", "locks": {"copy": True}}}
    revert_copy_lock_for_edit(trip)
    assert trip["pipeline"]["status"] == "copy_draft"
    assert trip["pipeline"]["locks"]["copy"] is False


def test_append_run_and_timings() -> None:
    trip: dict = {}
    append_pipeline_run(trip, {"runId": "r1", "agent": "layout"})
    set_pipeline_timings(trip, {"ingest": 1.2})
    assert trip["pipeline"]["runs"][0]["runId"] == "r1"
    assert trip["pipeline"]["timings"]["ingest"] == 1.2


def test_set_layout_status() -> None:
    trip: dict = {}
    set_layout_status(trip, "layout_draft")
    assert trip["pipeline"]["layoutStatus"] == "layout_draft"


def test_set_pipeline_status() -> None:
    trip: dict = {}
    set_pipeline_status(trip, "copy_draft")
    assert trip["pipeline"]["status"] == "copy_draft"


def test_lock_copy() -> None:
    trip = {"pipeline": {"status": "copy_draft", "locks": {"copy": False}}}
    lock_copy(trip)
    assert trip["pipeline"]["status"] == "copy_locked"
    assert trip["pipeline"]["locks"]["copy"] is True


def test_pipeline_mutations_preserve_meta_revision() -> None:
    trip = {
        "meta": {"revision": 5},
        "pipeline": {"status": "structure_draft", "locks": {"structure": False, "copy": False}},
    }
    lock_structure(trip)
    assert trip["meta"]["revision"] == 5
    assert trip["pipeline"]["status"] == "structure_locked"
    set_pipeline_timings(trip, {"ingestMs": 12.5})
    assert trip["meta"]["revision"] == 5
    assert trip["pipeline"]["timings"]["ingestMs"] == 12.5


def test_clear_pending_assets() -> None:
    trip = {"pipeline": {"pendingAssets": ["a1", "a2"]}}
    clear_pending_assets(trip)
    assert trip["pipeline"]["pendingAssets"] == []


def test_update_bumps_revision_with_pipeline_view_mutator(tmp_path: Path) -> None:
    """TripService.update owns revision; pipeline_view mutators compose inside update."""
    path = tmp_path / "trip.json"
    trip = {
        "version": "0.2",
        "tripId": "pipeline-rev",
        "assets": [],
        "chapters": [],
        "pipeline": {"status": "copy_draft", "locks": {"copy": False}},
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-01T00:00:00Z",
    }
    svc = TripService()
    svc.save(trip, path)
    assert meta_revision(svc.load(path)) == 0

    def lock_in_update(body: dict) -> None:
        lock_copy(body)

    svc.update(path, lock_in_update)
    loaded = svc.load(path)
    assert loaded["pipeline"]["status"] == "copy_locked"
    assert meta_revision(loaded) == 1


def test_assert_stage_allowed_curate_after_ingest() -> None:
    trip = {"pipeline": {"status": "ingest_ready"}}
    assert_stage_allowed(trip, "curate")


def test_assert_stage_allowed_blocks_early_curate() -> None:
    trip = {"pipeline": {"status": "draft_ingest"}}
    with pytest.raises(PipelineError):
        assert_stage_allowed(trip, "curate")
