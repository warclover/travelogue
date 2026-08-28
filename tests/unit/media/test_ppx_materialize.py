"""PRD-PIPELINE-PERF-EXECUTION-V1 · AC-PPX-07/11 parallel materialize."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.config import AppConfig, IngestConfig, PipelineConfig
from travelogue.media.derivatives import (
    apply_materialize_worker_results,
    collect_materialize_jobs,
    ensure_derivatives_for_trip,
    materialize_widths_worker,
    missing_planned_widths,
    run_materialize_jobs,
)
from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip


def _parallel_cfg() -> AppConfig:
    return AppConfig(
        pipeline=PipelineConfig(
            parallel_ingest=True,
            parallel_ingest_min_photos=2,
            parallel_ingest_workers=2,
            deferred_derivatives=True,
        ),
        ingest=IngestConfig(
            webp_widths=(800, 1600, 2400),
            webp_ingest_widths=(800, 1600),
            detect_faces=False,
            generate_crops=False,
            webp_method=0,
        ),
    )


def _album(tmp_path: Path, n: int, *, size: tuple[int, int] = (640, 480)) -> Path:
    from PIL import Image

    album = tmp_path / "album"
    album.mkdir()
    for i in range(n):
        Image.new("RGB", size, (20 * i, 40, 80)).save(album / f"p{i}.jpg", quality=90)
    return album


def test_materialize_worker_does_not_mutate_trip(tmp_path: Path) -> None:
    """AC-PPX-07 · worker never edits the trip; main process merges srcset."""
    album = _album(tmp_path, 2, size=(2000, 1400))
    trips = tmp_path / "trips"
    trip_json = create_trip("ppx-mat", trips, title="ppx")
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    cfg = _parallel_cfg()
    ingest_into_trip(
        trip,
        trip_json.parent,
        from_dir=album,
        app_cfg=cfg,
        min_assets=2,
        dedupe=False,
    )
    a0, a1 = trip["assets"][0], trip["assets"][1]
    trip["coverAssetId"] = a0["id"]
    trip["chapters"] = [{"items": [{"assetId": a0["id"]}, {"assetId": a1["id"]}]}]
    jobs, _seed = collect_materialize_jobs(trip, trip_json.parent, app_cfg=cfg)
    assert jobs
    snapshot = json.dumps(trip, sort_keys=True, ensure_ascii=False)
    payloads = []
    tmp_root = trip_json.parent / ".materialize-partial"
    tmp_root.mkdir(exist_ok=True)
    for job in jobs:
        payload = dict(job)
        payload["tmp_dir"] = str(tmp_root / str(job["asset_id"]))
        payloads.append(payload)
    outcomes = [materialize_widths_worker(p) for p in payloads]
    assert json.dumps(trip, sort_keys=True, ensure_ascii=False) == snapshot
    for out in outcomes:
        assert "trip" not in out
        assert out.get("ok") is True
    planned = tuple(int(w) for w in cfg.ingest.webp_widths)
    apply_materialize_worker_results(trip, trip_json.parent, outcomes, planned_widths=planned)
    for asset in (a0, a1):
        assert missing_planned_widths(asset, planned_widths=planned) == []
        assert asset["derivedPlan"]["status"] == "ready"
        widths = [int(e["width"]) for e in asset["srcset"]]
        assert widths == [800, 1600, 2400]


def test_sync_materialize_is_noop_when_already_ready(tmp_path: Path) -> None:
    """AC-PPX-11 · orchestrator sync path writes 0 widths when HD is complete."""
    album = _album(tmp_path, 2, size=(2000, 1400))
    trips = tmp_path / "trips"
    trip_json = create_trip("ppx-noop", trips, title="ppx")
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    cfg = _parallel_cfg()
    ingest_into_trip(
        trip,
        trip_json.parent,
        from_dir=album,
        app_cfg=cfg,
        min_assets=2,
        dedupe=False,
    )
    trip["coverAssetId"] = trip["assets"][0]["id"]
    trip["chapters"] = [{"items": [{"assetId": a["id"]} for a in trip["assets"]]}]
    first = ensure_derivatives_for_trip(trip, trip_json.parent, app_cfg=cfg)
    assert first.widths_written > 0
    again = ensure_derivatives_for_trip(trip, trip_json.parent, app_cfg=cfg)
    assert again.widths_written == 0
    assert again.errors == []


def test_run_materialize_jobs_leaves_no_tmp_when_empty(tmp_path: Path) -> None:
    assert run_materialize_jobs([], trip_dir=tmp_path, workers=2) == []
    assert not (tmp_path / ".materialize-partial").exists()
