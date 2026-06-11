"""P19 R-105 · LTE template rollout cohort by tripId."""

from __future__ import annotations

import pytest

from travelogue.config.rollout import rollout_bucket
from travelogue.curation.mosaic.hook import begin_mosaic_capture
from travelogue.curation.mosaic.trip_context import mosaic_trip_id
from travelogue.curation.mosaic.lte_adapter import lte_rollout_eligible
from travelogue.curation.mosaic.legacy_specs import reset_legacy_specs_cache_for_tests
from travelogue.layout_templates.registry import reset_engine_cache_for_tests


@pytest.fixture(autouse=True)
def _fresh() -> None:
    from travelogue.curation.mosaic.trip_context import set_mosaic_trip_id

    reset_engine_cache_for_tests()
    reset_legacy_specs_cache_for_tests()
    set_mosaic_trip_id(None)


@pytest.mark.unit
def test_lte_rollout_percent_zero_disabled() -> None:
    assert lte_rollout_eligible("screen-whitespace-hero", trip_id="demo-2025") is False


@pytest.mark.unit
def test_lte_rollout_full_percent_always_eligible() -> None:
    assert lte_rollout_eligible("screen-justified-row", trip_id="demo-2025") is True


@pytest.mark.unit
def test_lte_rollout_partial_uses_trip_cohort() -> None:
    tid = "demo-d66fe642a9"
    pct = 15.0
    bucket = rollout_bucket(tid, cohort_salt="lte-template:screen-spread-folio", traffic_percent=pct)
    in_cohort = bucket < int(round(pct))
    assert lte_rollout_eligible("screen-spread-folio", trip_id=tid) is in_cohort


@pytest.mark.unit
def test_mosaic_capture_sets_trip_id_context() -> None:
    begin_mosaic_capture("demo-d66fe642a9")
    assert mosaic_trip_id() == "demo-d66fe642a9"
