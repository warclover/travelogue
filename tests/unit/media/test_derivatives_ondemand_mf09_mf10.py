"""PRD-PIPELINE-PERF-V1 · MF-09 on-demand materialize + MF-10 fail-closed."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from travelogue.config import AppConfig, IngestConfig, PipelineConfig
from travelogue.media.derivatives import (
    asset_ids_needing_materialize,
    ensure_derivatives_before_export,
    ensure_derivatives_for_trip,
    materialize_on_demand,
    selected_asset_ids,
)
from travelogue.media.ingest import IngestError, ingest_into_trip
from travelogue.services.trip_factory import create_trip


def _cfg() -> AppConfig:
    return AppConfig(
        pipeline=PipelineConfig(deferred_derivatives=True, parallel_ingest=False),
        ingest=IngestConfig(
            webp_widths=(800, 1600, 2400),
            webp_ingest_widths=(800, 1600),
            detect_faces=False,
            generate_crops=False,
            webp_method=0,
        ),
    )


def _ingest_n(tmp_path: Path, n: int) -> tuple[dict, Path, AppConfig]:
    trips = tmp_path / "trips"
    album = tmp_path / "album"
    album.mkdir()
    for i in range(n):
        Image.new("RGB", (1800, 1200), (10 * i, 40, 80)).save(
            album / f"p{i}.jpg", quality=90
        )
    trip_json = create_trip(f"od-{n}", trips, title="od")
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    cfg = _cfg()
    ingest_into_trip(
        trip,
        trip_json.parent,
        from_dir=album,
        app_cfg=cfg,
        min_assets=n,
        dedupe=False,
    )
    return trip, trip_json.parent, cfg


def test_selected_includes_closing_asset() -> None:
    trip = {
        "coverAssetId": "a",
        "curation": {"closingAssetId": "z"},
        "chapters": [],
    }
    assert selected_asset_ids(trip) == {"a", "z"}


def test_mf09_sync_materialize_single(tmp_path: Path) -> None:
    trip, trip_dir, cfg = _ingest_n(tmp_path, 1)
    aid = trip["assets"][0]["id"]
    trip["coverAssetId"] = aid
    trip["chapters"] = [{"items": [{"assetId": aid}]}]
    planned = cfg.ingest.webp_widths
    assert asset_ids_needing_materialize(trip, planned_widths=planned) == [aid]
    result = materialize_on_demand(
        trip, trip_dir, asset_ids={aid}, app_cfg=cfg, sync_max_assets=3
    )
    assert result.mode == "sync"
    assert result.preparing_count == 0
    assert result.sync_result is not None
    assert result.sync_result.errors == []
    assert asset_ids_needing_materialize(trip, planned_widths=planned) == []
    assert (trip_dir / "assets" / f"{aid}-w2400.webp").is_file()


def test_mf09_async_when_over_threshold(tmp_path: Path) -> None:
    trip, trip_dir, cfg = _ingest_n(tmp_path, 4)
    ids = [a["id"] for a in trip["assets"]]
    trip["coverAssetId"] = ids[0]
    trip["chapters"] = [
        {"items": [{"assetId": i} for i in ids], "screens": []}
    ]
    result = materialize_on_demand(
        trip, trip_dir, app_cfg=cfg, sync_max_assets=3, persist=True
    )
    assert result.mode == "async"
    assert result.preparing_count == 4
    assert int((trip.get("pipeline") or {}).get("derivativesPreparing") or 0) == 4
    # Join background work
    import time

    planned = cfg.ingest.webp_widths
    for _ in range(80):
        if int((trip.get("pipeline") or {}).get("derivativesPreparing") or 0) == 0:
            break
        time.sleep(0.05)
    assert int((trip.get("pipeline") or {}).get("derivativesPreparing") or 0) == 0
    assert asset_ids_needing_materialize(trip, planned_widths=planned) == []


def test_mf10_export_recreates_deleted_hd(tmp_path: Path) -> None:
    """MF-10 · 删档后导出：同步物化补齐，不产出缺图。"""
    trip, trip_dir, cfg = _ingest_n(tmp_path, 1)
    aid = trip["assets"][0]["id"]
    trip["coverAssetId"] = aid
    trip["chapters"] = [{"items": [{"assetId": aid}]}]
    ensure_derivatives_for_trip(trip, trip_dir, app_cfg=cfg)
    hd = trip_dir / "assets" / f"{aid}-w2400.webp"
    assert hd.is_file()
    hd.unlink()
    # Drop srcset entry so missing_planned sees gap
    asset = trip["assets"][0]
    asset["srcset"] = [e for e in asset["srcset"] if int(e["width"]) < 2400]
    result = ensure_derivatives_before_export(trip, trip_dir, app_cfg=cfg)
    assert not result.errors
    assert hd.is_file()
    assert (trip.get("pipeline") or {}).get("derivativesStatus") == "ready"


def test_mf10_partial_kill_then_ensure(tmp_path: Path) -> None:
    """MF-10 · 物化中途缺档：再次 ensure 幂等补齐。"""
    trip, trip_dir, cfg = _ingest_n(tmp_path, 1)
    aid = trip["assets"][0]["id"]
    trip["coverAssetId"] = aid
    trip["chapters"] = [{"items": [{"assetId": aid}]}]
    # Simulate mid-kill: only write one of the missing tiers via ensure then delete
    ensure_derivatives_for_trip(trip, trip_dir, app_cfg=cfg)
    path_2400 = trip_dir / "assets" / f"{aid}-w2400.webp"
    path_2400.unlink()
    asset = next(a for a in trip["assets"] if a["id"] == aid)
    asset["srcset"] = [e for e in asset["srcset"] if int(e["width"]) != 2400]
    again = ensure_derivatives_for_trip(
        trip, trip_dir, app_cfg=cfg, asset_ids={aid}, mark_unselected_skipped=False
    )
    assert again.errors == []
    assert path_2400.is_file()


def test_mf10_export_handler_raises_when_materialize_errors(tmp_path: Path) -> None:
    """MF-10 · export helper fail-closed when materialize cannot recover."""
    import pytest

    from travelogue.web.studio_handlers.export_handlers import (
        _ensure_derivatives_for_export,
    )

    trip, trip_dir, cfg = _ingest_n(tmp_path, 1)
    aid = trip["assets"][0]["id"]
    trip["coverAssetId"] = aid
    trip["chapters"] = [{"items": [{"assetId": aid}]}]
    asset = trip["assets"][0]
    src = trip_dir / str(asset.get("sourceFile") or "")
    if src.is_file():
        src.unlink()
    asset["srcset"] = [e for e in asset.get("srcset") or [] if int(e["width"]) < 2400]
    asset.pop("sourceRef", None)
    # Leave only preview tiers on disk; wipe HD if any
    for w in (2400, 3200):
        p = trip_dir / "assets" / f"{aid}-w{w}.webp"
        if p.is_file():
            p.unlink()
    (trip_dir / "trip.json").write_text(
        json.dumps(trip, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    # Force deferred path through broken source
    with pytest.raises(IngestError) as excinfo:
        _ensure_derivatives_for_export(trip_dir)
    assert excinfo.value.code == "E_DERIVATIVE_MATERIALIZE"
    _ = cfg  # config used by ingest helper path
