"""M-B2 · StudioProfile + clustering stage in run_trip."""

from __future__ import annotations

import json
from pathlib import Path

from tests.test_ingest import _album
from travelogue.config import AppConfig, ClusteringConfig, VisionConfig
from travelogue.orchestrator.run import run_trip
from travelogue.orchestrator.studio_hooks import StudioHooks
from travelogue.orchestrator.studio_profile import StudioProfile
from travelogue.services.trip_factory import create_trip


def test_studio_profile_defaults() -> None:
    cli = StudioProfile.cli_default()
    studio = StudioProfile.studio_default()
    assert cli.run_clustering is False
    assert studio.run_clustering is True
    assert studio.export_layout == "auto"
    assert studio.ingest.resume_ingest is True


def test_run_trip_clustering_stage_when_enabled(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("cluster-stage", trips, title="聚类阶段")
    album = _album(tmp_path, 6)
    profile = StudioProfile.cli_default()
    profile.run_clustering = True
    profile.export_layout = "auto"
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="false"),
        vision=VisionConfig(enabled="false"),
    )
    result = run_trip(
        trip_json,
        from_stage="ingest",
        until="structure",
        album_dir=album,
        validate=False,
        dedupe=False,
        cfg=cfg,
        studio_profile=profile,
    )
    assert "ingest" in result.stages
    assert "clustering" in result.stages
    assert "curate" in result.stages
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    timings = (trip.get("pipeline") or {}).get("timings") or {}
    assert "clusterMs" in timings


def test_run_trip_skips_clustering_by_default(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("no-cluster", trips, title="默认无聚类")
    album = _album(tmp_path, 6)
    result = run_trip(
        trip_json,
        from_stage="ingest",
        until="structure",
        album_dir=album,
        validate=False,
        dedupe=False,
    )
    assert "clustering" not in result.stages


def test_studio_hooks_timing_callback(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("hooks-timing", trips, title="计时回调")
    album = _album(tmp_path, 6)
    seen: list[dict[str, float]] = []

    hooks = StudioHooks(
        on_timing=lambda timings: seen.append(dict(timings)),
    )
    run_trip(
        trip_json,
        from_stage="ingest",
        until="structure",
        album_dir=album,
        validate=False,
        dedupe=False,
        studio_hooks=hooks,
    )
    assert seen, "expected at least one timing flush"
    assert "totalMs" in seen[-1]
