"""PRD-PIPELINE-PERF-V1 · R2.1/R2.2 deferred derivatives."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from travelogue.config import AppConfig, IngestConfig, PipelineConfig
from travelogue.media.derivatives import (
    build_derived_plan,
    effective_ingest_widths,
    ensure_derivatives_for_trip,
    missing_planned_widths,
    selected_asset_ids,
)
from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip


def test_effective_ingest_widths_deferred() -> None:
    cfg = IngestConfig(
        webp_widths=(800, 1600, 2400, 3200),
        webp_ingest_widths=(800, 1600),
    )
    assert effective_ingest_widths(cfg, deferred=True) == (800, 1600)
    assert effective_ingest_widths(cfg, deferred=False) == (800, 1600, 2400, 3200)


def test_build_derived_plan_partial() -> None:
    plan = build_derived_plan(
        planned_widths=(800, 1600, 2400, 3200),
        ready_widths=(800, 1600),
    )
    assert plan["status"] == "partial"
    assert plan["readyWidths"] == [800, 1600]


def test_selected_asset_ids_from_chapters() -> None:
    trip = {
        "coverAssetId": "asset-001",
        "curation": {"closingAssetId": "asset-006"},
        "chapters": [
            {
                "items": [{"assetId": "asset-002"}, {"assetIds": ["asset-003", "asset-004"]}],
                "screens": [{"slots": [{"assetId": "asset-005"}]}],
            }
        ],
    }
    assert selected_asset_ids(trip) == {
        "asset-001",
        "asset-002",
        "asset-003",
        "asset-004",
        "asset-005",
        "asset-006",
    }


def test_ingest_writes_preview_srcset_only(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    album = tmp_path / "album"
    album.mkdir()
    Image.new("RGB", (2400, 1600), (40, 80, 120)).save(album / "a.jpg", quality=90)
    trip_json = create_trip("deriv-1", trips, title="d")
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    cfg = AppConfig(
        pipeline=PipelineConfig(deferred_derivatives=True, parallel_ingest=False),
        ingest=IngestConfig(
            webp_widths=(800, 1600, 2400, 3200),
            webp_ingest_widths=(800, 1600),
            detect_faces=False,
            generate_crops=False,
        ),
    )
    ingest_into_trip(trip, trip_json.parent, from_dir=album, app_cfg=cfg, min_assets=1)
    asset = trip["assets"][0]
    widths = [e["width"] for e in asset["srcset"]]
    assert widths == [800, 1600]
    assert asset["derivedPlan"]["plannedWidths"] == [800, 1600, 2400, 3200]
    assert asset["derivedPlan"]["status"] == "partial"
    assets_dir = trip_json.parent / "assets"
    assert (assets_dir / f"{asset['id']}-w1600.webp").is_file()
    assert not (assets_dir / f"{asset['id']}-w2400.webp").is_file()


def test_ensure_materializes_selected_only(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    album = tmp_path / "album"
    album.mkdir()
    for i in range(2):
        Image.new("RGB", (2000, 1400), (10 * i, 20, 30)).save(album / f"p{i}.jpg", quality=90)
    trip_json = create_trip("deriv-2", trips, title="d")
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    cfg = AppConfig(
        pipeline=PipelineConfig(deferred_derivatives=True, parallel_ingest=False),
        ingest=IngestConfig(
            webp_widths=(800, 1600, 2400),
            webp_ingest_widths=(800, 1600),
            detect_faces=False,
            generate_crops=False,
        ),
    )
    ingest_into_trip(
        trip, trip_json.parent, from_dir=album, app_cfg=cfg, min_assets=2, dedupe=False
    )
    a0, a1 = trip["assets"][0], trip["assets"][1]
    trip["coverAssetId"] = a0["id"]
    trip["chapters"] = [{"items": [{"assetId": a0["id"]}]}]
    result = ensure_derivatives_for_trip(trip, trip_json.parent, app_cfg=cfg)
    assert result.materialized_assets == 1
    assert missing_planned_widths(a0, planned_widths=(800, 1600, 2400)) == []
    assert a0["derivedPlan"]["status"] == "ready"
    assert (trip_json.parent / "assets" / f"{a0['id']}-w2400.webp").is_file()
    assert not (trip_json.parent / "assets" / f"{a1['id']}-w2400.webp").is_file()
    assert a1["derivedPlan"]["status"] == "skipped"
