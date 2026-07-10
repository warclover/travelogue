"""M-D1 · unified studio pipeline orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.studio_test_helpers import make_test_album
from travelogue.config import AppConfig, ClusteringConfig, PipelineConfig, VisionConfig
from travelogue.config.misc import pipeline_from_dict
from travelogue.orchestrator.run import run_trip
from travelogue.web.studio_pipeline import run_studio_pipeline


def test_pipeline_from_dict_warns_on_removed_legacy_orchestration() -> None:
    with pytest.warns(UserWarning, match="pipeline.orchestration=legacy was removed"):
        cfg = pipeline_from_dict({"orchestration": "legacy"})
    assert cfg.parallel_embed is True


def test_unified_studio_pipeline_imports_album(tmp_path: Path) -> None:
    album = make_test_album(tmp_path, 6)
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="false"),
        vision=VisionConfig(enabled="false"),
        pipeline=PipelineConfig(parallel_embed=False),
    )
    result = run_studio_pipeline(
        album,
        trips_dir=tmp_path / "trips",
        dedupe=False,
        app_config=cfg,
    )
    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    assert trip.get("tripId")
    assert result.photo_count >= 1


def test_post_curate_uses_single_run_trip_until_rendered(tmp_path: Path) -> None:
    """Non-G1 post-curate should call run_trip once: lock_structure → rendered."""
    album = make_test_album(tmp_path, 6)
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="false"),
        vision=VisionConfig(enabled="false"),
        pipeline=PipelineConfig(parallel_embed=False),
    )
    calls: list[tuple[str, str]] = []
    real_run_trip = run_trip

    def _spy(trip_json, *args, **kwargs):
        calls.append((kwargs.get("from_stage") or "", kwargs.get("until") or ""))
        return real_run_trip(trip_json, *args, **kwargs)

    with patch("travelogue.web.studio_pipeline.run_trip", side_effect=_spy):
        result = run_studio_pipeline(
            album,
            trips_dir=tmp_path / "trips",
            dedupe=False,
            app_config=cfg,
        )

    assert ("lock_structure", "rendered") in calls
    assert ("lock_structure", "copy") not in calls
    assert ("render", "rendered") not in calls
    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    timings = (trip.get("pipeline") or {}).get("timings") or {}
    assert "totalMs" in timings or "renderMs" in timings
    # Post-render timings flush must not false-flag renderBundleStale.
    from travelogue.layout_templates.css_stale import trip_render_bundle_stale
    from travelogue.services.trip import meta_rendered_revision, meta_revision

    assert meta_rendered_revision(trip) == meta_revision(trip)
    assert trip_render_bundle_stale(result.trip_json.parent, trip) is False


def test_stop_after_structure_skips_post_curate(tmp_path: Path) -> None:
    album = make_test_album(tmp_path, 6)
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="false"),
        vision=VisionConfig(enabled="false"),
        pipeline=PipelineConfig(parallel_embed=False),
    )
    calls: list[tuple[str, str]] = []
    real_run_trip = run_trip

    def _spy(trip_json, *args, **kwargs):
        calls.append((kwargs.get("from_stage") or "", kwargs.get("until") or ""))
        return real_run_trip(trip_json, *args, **kwargs)

    with patch("travelogue.web.studio_pipeline.run_trip", side_effect=_spy):
        run_studio_pipeline(
            album,
            trips_dir=tmp_path / "trips",
            dedupe=False,
            app_config=cfg,
            stop_after="structure",
        )

    assert ("lock_structure", "rendered") not in calls
    assert any(until == "structure" for _, until in calls)
