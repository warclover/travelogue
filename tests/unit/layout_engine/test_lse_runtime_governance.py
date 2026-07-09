"""LSE runtime store + config_governance patches (W2)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import travelogue.layout_engine.planner.screen_planner  # noqa: F401
from scripts.phase3_ig2_report import _cfg_for_mode, _prepare_trip, load_fixture_trip
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.curate import run_curate
from travelogue.layout_engine.adapter import mosaic_config_from_pack
from travelogue.layout_engine.governance import normalize_lse_patch
from travelogue.layout_engine.registry import get_strategy_pack
from travelogue.layout_engine.runtime_store import (
    effective_disable_stages,
    load_lse_runtime,
    merge_approved_patch,
)
from travelogue.templating.config_governance import (
    approve_router_change,
    propose_layout_strategy_change,
    propose_router_change,
)


def test_merge_disable_stages_patch(tmp_path: Path, monkeypatch) -> None:
    store = tmp_path / "lse_runtime.json"
    monkeypatch.setattr(
        "travelogue.layout_engine.runtime_store.resolve_store_path",
        lambda _path=None: store,
    )
    merge_approved_patch(
        {"layout_strategy_overrides_disable_stages": ["mosaic", "hero"]},
        store_path=store,
        change_id="cfg-1",
    )
    rt = load_lse_runtime(store)
    assert rt["overrides"]["disable_stages"] == ["mosaic", "hero"]


def test_config_governance_approves_lse_patch(tmp_path: Path, monkeypatch) -> None:
    store = tmp_path / "lse_runtime.json"
    state = tmp_path / "template_admin_state.json"
    cfg = _cfg_for_mode("p3_full")
    se = replace(cfg.layout.strategy_engine, runtime_store=str(store))
    cfg = replace(cfg, layout=replace(cfg.layout, strategy_engine=se))
    monkeypatch.setattr(
        "travelogue.layout_engine.runtime_store.resolve_store_path",
        lambda _path=None: store,
    )
    monkeypatch.setattr("travelogue.templating.admin_store._STATE_PATH", state)
    monkeypatch.setattr("travelogue.domain.template_admin_state._ADMIN_STATE_PATH", state)
    monkeypatch.setattr("travelogue.domain.template_admin_state._RUNTIME_CACHE", None)
    monkeypatch.setattr("travelogue.config.get_config", lambda **_: cfg)

    req = propose_router_change(
        {"layout_strategy_overrides_disable_stages": ["mosaic"]},
        operator="op1",
        reason="test",
    )
    approve_router_change(req["id"], approver="ap1")
    approve_router_change(req["id"], approver="ap2")
    rt = load_lse_runtime(store)
    assert rt["overrides"]["disable_stages"] == ["mosaic"]


def test_weights_patch_rejects_unnormalized(tmp_path: Path, monkeypatch) -> None:
    store = tmp_path / "lse_runtime.json"
    monkeypatch.setattr(
        "travelogue.layout_engine.runtime_store.resolve_store_path",
        lambda _path=None: store,
    )
    try:
        merge_approved_patch(
            {"layout_strategy_weights": {"aspect_match": 0.1, "sharpness": 0.1}},
            store_path=store,
        )
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "NORMALIZED" in str(exc.args[0])


def _mosaic_log_count(body: dict) -> int:
    return len((body.get("curation") or {}).get("mosaicDecisionLog") or [])


def test_ac_p17_08_disable_mosaic_stage(tmp_path: Path) -> None:
    """L3 overrides.disable_stages=[mosaic] → mosaic window exposure = 0."""
    trip = load_fixture_trip("golden-mixed-scenes")
    base = _cfg_for_mode("p3_full")
    se = replace(
        base.layout.strategy_engine,
        enabled=True,
        overrides=replace(base.layout.strategy_engine.overrides, disable_stages=("mosaic",)),
    )
    cfg_off = replace(base, layout=replace(base.layout, strategy_engine=se))
    se_on = replace(se, overrides=replace(se.overrides, disable_stages=()))
    cfg_on = replace(base, layout=replace(base.layout, strategy_engine=se_on))

    body_off = _prepare_trip(trip)
    run_clustering_layer(body_off, trip_dir=tmp_path / "off" / "cluster", cfg=cfg_off)
    run_curate(body_off, apply_layout=True, trip_dir=tmp_path / "off", cfg=cfg_off)

    body_on = _prepare_trip(trip)
    run_clustering_layer(body_on, trip_dir=tmp_path / "on" / "cluster", cfg=cfg_on)
    run_curate(body_on, apply_layout=True, trip_dir=tmp_path / "on", cfg=cfg_on)

    assert _mosaic_log_count(body_off) == 0
    assert _mosaic_log_count(body_on) >= 1


def test_effective_disable_stages_merges_runtime(tmp_path: Path, monkeypatch) -> None:
    store = tmp_path / "lse_runtime.json"
    monkeypatch.setattr(
        "travelogue.layout_engine.runtime_store.resolve_store_path",
        lambda _path=None: store,
    )
    merge_approved_patch(
        {"layout_strategy_overrides_disable_stages": ["portrait"]},
        store_path=store,
    )
    cfg = _cfg_for_mode("p3_full")
    se = replace(
        cfg.layout.strategy_engine,
        enabled=True,
        runtime_store=str(store),
        overrides=replace(cfg.layout.strategy_engine.overrides, disable_stages=("mosaic",)),
    )
    cfg2 = replace(cfg, layout=replace(cfg.layout, strategy_engine=se))
    merged = effective_disable_stages(cfg2)
    assert merged == ("mosaic", "portrait")


def test_propose_layout_strategy_change_validates(tmp_path: Path, monkeypatch) -> None:
    state = tmp_path / "template_admin_state.json"
    monkeypatch.setattr("travelogue.templating.admin_store._STATE_PATH", state)
    monkeypatch.setattr("travelogue.domain.template_admin_state._ADMIN_STATE_PATH", state)
    monkeypatch.setattr("travelogue.domain.template_admin_state._RUNTIME_CACHE", None)
    try:
        propose_layout_strategy_change(
            {"layout_strategy_weights": {"aspect_match": 0.05}},
            operator="op",
        )
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "NORMALIZED" in str(exc.args[0])


def test_normalize_lse_patch_api_shape() -> None:
    patch = normalize_lse_patch(
        {
            "patch": {
                "disableStages": ["mosaic"],
                "weights": {
                    "aspect_match": 0.20,
                    "sharpness": 0.15,
                    "temporal_coherence": 0.15,
                    "hero_separation": 0.10,
                    "subject_run": 0.10,
                    "layout_rhythm": 0.10,
                    "diversity": 0.10,
                    "category_coherence": 0.10,
                },
            }
        }
    )
    assert patch["layout_strategy_overrides_disable_stages"] == ["mosaic"]
    assert "layout_strategy_weights" in patch


def test_mosaic_config_applies_runtime_weight_overlay(tmp_path: Path, monkeypatch) -> None:
    store = tmp_path / "lse_runtime.json"
    monkeypatch.setattr(
        "travelogue.layout_engine.runtime_store.resolve_store_path",
        lambda _path=None: store,
    )
    weights = {
        "aspect_match": 0.20,
        "sharpness": 0.20,
        "temporal_coherence": 0.15,
        "hero_separation": 0.10,
        "subject_run": 0.10,
        "layout_rhythm": 0.10,
        "diversity": 0.05,
        "category_coherence": 0.10,
    }
    merge_approved_patch({"layout_strategy_weights": weights}, store_path=store)
    cfg = _cfg_for_mode("p3_full")
    se = replace(cfg.layout.strategy_engine, enabled=True, runtime_store=str(store))
    cfg = replace(cfg, layout=replace(cfg.layout, strategy_engine=se))
    pack = get_strategy_pack("lse-default-2026-06")
    mosaic = mosaic_config_from_pack(cfg, pack=pack)
    assert mosaic.weights["sharpness"] == 0.20
