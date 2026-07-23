"""M-B2 · StudioProfile + clustering stage in run_trip."""

from __future__ import annotations

import json
from pathlib import Path

from tests.studio_test_helpers import make_test_album as _album
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
    assert "shot_grouping" in result.stages
    assert "curate" in result.stages
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    timings = (trip.get("pipeline") or {}).get("timings") or {}
    assert "clusterMs" in timings
    assert "shotGroupingMs" in timings


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


def test_clustering_stage_matches_manual_preflight(tmp_path: Path) -> None:
    """M-B2 AC: run_trip clustering stage ≡ manual run_clustering_layer + curate."""
    from travelogue.curation.clustering import run_clustering_layer
    from travelogue.media.ingest import ingest_into_trip

    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="false"),
        vision=VisionConfig(enabled="false"),
    )
    album = _album(tmp_path, 8)
    profile = StudioProfile(
        run_clustering=True,
        export_layout="auto",
        ingest=StudioProfile.cli_default().ingest,
    )

    trips_a = tmp_path / "trips-a"
    trip_json_a = create_trip("eq-stage", trips_a, title="stage path")
    run_trip(
        trip_json_a,
        from_stage="ingest",
        until="structure",
        album_dir=album,
        validate=False,
        dedupe=False,
        cfg=cfg,
        studio_profile=profile,
    )
    trip_a = json.loads(trip_json_a.read_text(encoding="utf-8"))

    trips_b = tmp_path / "trips-b"
    trip_json_b = create_trip("eq-manual", trips_b, title="manual path")
    trip_dir_b = trips_b / "eq-manual"
    trip_b = json.loads(trip_json_b.read_text(encoding="utf-8"))
    ingest_into_trip(trip_b, trip_dir_b, from_dir=album, dedupe=False, app_cfg=cfg)
    trip_json_b.write_text(json.dumps(trip_b, ensure_ascii=False, indent=2), encoding="utf-8")
    run_clustering_layer(trip_b, trip_dir=trip_dir_b, cfg=cfg)
    trip_json_b.write_text(json.dumps(trip_b, ensure_ascii=False, indent=2), encoding="utf-8")
    run_trip(
        trip_json_b,
        from_stage="curate",
        until="structure",
        export_layout="auto",
        validate=False,
        dedupe=False,
        cfg=cfg,
        studio_profile=profile,
    )
    trip_b = json.loads(trip_json_b.read_text(encoding="utf-8"))

    cluster_a = (trip_a.get("curation") or {}).get("clustering") or {}
    cluster_b = (trip_b.get("curation") or {}).get("clustering") or {}
    assert cluster_a.get("mode") == cluster_b.get("mode")
    assert len(trip_a.get("chapters") or []) == len(trip_b.get("chapters") or [])
    assert trip_a["pipeline"]["status"] == trip_b["pipeline"]["status"]
