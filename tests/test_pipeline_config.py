"""Pipeline-level AppConfig pinning via app_config_scope."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.integration

from travelogue.config import (
    app_config_scope,
    config_override,
    get_config,
    reset_config_cache,
)
from travelogue.orchestrator.run import run_trip


@pytest.fixture(autouse=True)
def _reset_config_cache():
    reset_config_cache()
    yield
    reset_config_cache()


def test_app_config_scope_pins_get_config():
    base = get_config()
    pinned = replace(base, curate=replace(base.curate, segment_gap_days=99))
    global_other = replace(base, curate=replace(base.curate, segment_gap_days=1))

    with config_override(global_other):
        with app_config_scope(pinned):
            assert get_config().curate.segment_gap_days == 99
        assert get_config().curate.segment_gap_days == 1


def test_run_trip_curate_stage_uses_pinned_cfg(tmp_path):
    import json

    from tests.test_ingest import _album
    from travelogue.media.ingest import ingest_into_trip
    from travelogue.services.trip_factory import create_trip

    trips = tmp_path / "trips"
    trip_json = create_trip("pipeline-cfg", trips)
    trip_dir = trips / "pipeline-cfg"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    ingest_into_trip(trip, trip_dir, from_dir=_album(tmp_path, 8), dedupe=False)
    for i, asset in enumerate(trip["assets"]):
        asset["takenAt"] = f"2025-04-0{(i % 3) + 2}T12:00:00Z"
    trip_json.write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")

    captured: list[int] = []

    def _capture_curate(trip_obj, **kwargs):
        captured.append(get_config().curate.segment_gap_days)
        from travelogue.curation.curate import run_curate as real_run_curate

        return real_run_curate(trip_obj, **kwargs)

    pinned = replace(get_config(), curate=replace(get_config().curate, segment_gap_days=42))
    global_cfg = replace(get_config(), curate=replace(get_config().curate, segment_gap_days=7))

    with config_override(global_cfg):
        with patch("travelogue.orchestrator.run.run_curate", side_effect=_capture_curate):
            run_trip(
                trip_json,
                from_stage="curate",
                until="structure",
                cfg=pinned,
            )

    assert captured == [42]
