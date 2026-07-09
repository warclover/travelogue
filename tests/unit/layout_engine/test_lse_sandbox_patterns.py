"""LSE sandbox, rollback, disable_patterns (W2)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import travelogue.curation.screen_planner  # noqa: F401
from scripts.phase3_ig2_report import _cfg_for_mode, _prepare_trip, load_fixture_trip
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.curate import run_curate
from travelogue.layout_engine.mosaic.lte_adapter import mosaic_registry
from travelogue.layout_engine.mosaic.runtime import (
    reset_mosaic_disabled_patterns,
    set_mosaic_disabled_patterns,
)
from travelogue.layout_engine.runtime_store import merge_approved_patch, rollback_lse_runtime
from travelogue.layout_engine.sandbox import sandbox_replay_trip


def test_disable_patterns_excludes_from_registry() -> None:
    pid = "screen-portrait-3"
    set_mosaic_disabled_patterns((pid,))
    try:
        reg = mosaic_registry()
        assert pid not in reg
    finally:
        reset_mosaic_disabled_patterns()


def test_rollback_restores_runtime_snapshot(tmp_path: Path, monkeypatch) -> None:
    store = tmp_path / "lse_runtime.json"
    monkeypatch.setattr(
        "travelogue.layout_engine.runtime_store.resolve_store_path",
        lambda _path=None: store,
    )
    merge_approved_patch(
        {"layout_strategy_overrides_disable_stages": ["mosaic"]},
        store_path=store,
        change_id="cfg-1",
    )
    rt = rollback_lse_runtime(steps=1, store_path=store)
    assert rt["overrides"]["disable_stages"] == []


def test_sandbox_lse_off_vs_on_zero_diff(tmp_path: Path) -> None:
    trip = load_fixture_trip("golden-mixed-scenes")
    base = _cfg_for_mode("p3_full")
    from travelogue.layout_engine.sandbox import cfg_lse_sandbox_pair

    baseline_cfg, candidate_cfg = cfg_lse_sandbox_pair(base)
    report = sandbox_replay_trip(
        trip,
        baseline_cfg=baseline_cfg,
        candidate_cfg=candidate_cfg,
        work_dir=tmp_path / "sandbox",
    )
    assert report["diff"]["unchanged"] is True
    assert report["diffRate"] == 0.0


def test_enrich_changed_screen_previews_injects_callback(tmp_path: Path) -> None:
    from travelogue.layout_engine.sandbox import enrich_changed_screen_previews

    trip = {
        "assets": [
            {
                "id": "a1",
                "displayFile": "assets/a1.webp",
                "width": 800,
                "height": 600,
            }
        ]
    }
    asset_path = tmp_path / "assets" / "a1.webp"
    asset_path.parent.mkdir(parents=True)
    asset_path.write_bytes(b"x")
    diff = {
        "changedScreens": [
            {
                "index": 0,
                "baseline": {"slotAssetIds": ["a1"]},
                "candidate": None,
            }
        ]
    }
    rows = enrich_changed_screen_previews(
        trip,
        tmp_path,
        diff,
        preview_url_for=lambda rel: f"/trip/{rel}",
    )
    assert rows[0]["baselinePreview"] == "/trip/assets/a1.webp"
    assert "candidatePreview" not in rows[0]


def test_curate_respects_runtime_disable_patterns(tmp_path: Path, monkeypatch) -> None:
    store = tmp_path / "lse_runtime.json"
    monkeypatch.setattr(
        "travelogue.layout_engine.runtime_store.resolve_store_path",
        lambda _path=None: store,
    )
    merge_approved_patch(
        {
            "layout_strategy_overrides_disable_patterns": [
                "screen-mosaic-5-main-hero-plus-4"
            ]
        },
        store_path=store,
        change_id="cfg-p",
    )
    trip = load_fixture_trip("golden-mixed-scenes")
    base = _cfg_for_mode("p3_full")
    se = replace(
        base.layout.strategy_engine,
        enabled=True,
        runtime_store=str(store),
    )
    cfg = replace(base, layout=replace(base.layout, strategy_engine=se))
    body = _prepare_trip(trip)
    run_clustering_layer(body, trip_dir=tmp_path / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=tmp_path, cfg=cfg)
    patterns = {
        str(s.get("patternId"))
        for ch in body.get("chapters") or []
        for s in ch.get("screens") or []
        if s.get("patternId")
    }
    assert "screen-mosaic-5-main-hero-plus-4" not in patterns
