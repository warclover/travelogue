"""Tests for domain pipeline view (M-C4)."""

from __future__ import annotations

import pytest

from travelogue.domain.pipeline_view import PipelineError, assert_stage_allowed, trip_status
from travelogue.services.pipeline_state import trip_status as svc_trip_status


def test_trip_status_default() -> None:
    assert trip_status({}) == "draft_ingest"
    assert svc_trip_status({}) == "draft_ingest"


def test_assert_stage_allowed_curate_after_ingest() -> None:
    trip = {"pipeline": {"status": "ingest_ready"}}
    assert_stage_allowed(trip, "curate")


def test_assert_stage_allowed_blocks_early_curate() -> None:
    trip = {"pipeline": {"status": "draft_ingest"}}
    with pytest.raises(PipelineError):
        assert_stage_allowed(trip, "curate")
