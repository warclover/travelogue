"""NR-P3-03 · Phase 3 trip remains editable/renderable with clustering off."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from travelogue.config import AppConfig, ClusteringConfig, VisionConfig
from travelogue.curation.clustering import run_clustering_layer
from travelogue.paths import FIXTURES_DIR, TEMPLATE_VISUAL_JOURNAL
from travelogue.render.dual_layout_regression import prepare_trip_web_screens
from travelogue.render.engine import LONGSHOT_INDEX_NAME, render_trip
from travelogue.services.validate import validate_trip


def test_phase3_trip_renders_with_clustering_disabled(tmp_path: Path) -> None:
    demo = TEMPLATE_VISUAL_JOURNAL / "assets"
    if not demo.is_dir():
        pytest.skip("demo assets not present")

    trip_dir = tmp_path / "trip"
    trip_dir.mkdir()
    shutil.copytree(demo, trip_dir / "assets")
    (trip_dir / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (trip_dir / "assets" / "demo" / "video.mp4").write_bytes(b"")

    trip = prepare_trip_web_screens(
        json.loads((FIXTURES_DIR / "trip.render_golden.json").read_text(encoding="utf-8"))
    )
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="true"),
        vision=VisionConfig(enabled="true"),
    )
    run_clustering_layer(trip, trip_dir=trip_dir, cfg=cfg)
    assert (trip.get("curation") or {}).get("clustering")

    cfg_off = AppConfig(
        clustering=ClusteringConfig(enabled="false"),
        vision=VisionConfig(enabled="false"),
    )
    run_clustering_layer(trip, trip_dir=trip_dir, cfg=cfg_off)

    (trip_dir / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    schema_errs = [e for e in validate_trip(trip, level="schema") if not e.startswith("WARN:")]
    assert not schema_errs, schema_errs

    out = render_trip(trip_dir / "trip.json", validate=False, layout_engine="screens")
    assert (out / "index.html").is_file()


def test_phase3_trip_export_longshot_with_clustering_off(tmp_path: Path) -> None:
    pytest.importorskip("playwright")
    demo = TEMPLATE_VISUAL_JOURNAL / "assets"
    if not demo.is_dir():
        pytest.skip("demo assets not present")

    trip_dir = tmp_path / "trip"
    trip_dir.mkdir()
    shutil.copytree(demo, trip_dir / "assets")
    (trip_dir / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (trip_dir / "assets" / "demo" / "video.mp4").write_bytes(b"")

    trip = prepare_trip_web_screens(
        json.loads((FIXTURES_DIR / "trip.render_golden.json").read_text(encoding="utf-8"))
    )
    cfg = AppConfig(clustering=ClusteringConfig(enabled="true"), vision=VisionConfig(enabled="true"))
    run_clustering_layer(trip, trip_dir=trip_dir, cfg=cfg)
    (trip_dir / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")

    cfg_off = AppConfig(clustering=ClusteringConfig(enabled="false"), vision=VisionConfig(enabled="false"))
    run_clustering_layer(trip, trip_dir=trip_dir, cfg=cfg_off)
    (trip_dir / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")

    render_trip(trip_dir / "trip.json", validate=False, layout_engine="screens")
    assert (trip_dir / LONGSHOT_INDEX_NAME).is_file()
    from travelogue.export.longshot import export_trip_longshot

    result = export_trip_longshot(trip_dir, scale=1)
    assert result.outputs
    assert all(item.path.is_file() for item in result.outputs)
