"""Dogfood integration · LSE flags admin → config.yaml → curate → trip.json."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
import yaml

import travelogue.layout_engine.planner.screen_planner  # noqa: F401
from scripts.phase3_ig2_report import _cfg_for_mode, _prepare_trip, load_fixture_trip
from travelogue.config import load_config
from travelogue.config.layout import LayoutStrategyCapabilitiesConfig, LayoutStrategyEngineConfig
from travelogue.config.loader import patch_config_file
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.curate import run_curate
from travelogue.layout_engine.adapter import mosaic_config_from_pack, strategy_trace_meta
from travelogue.layout_engine.registry import get_strategy_pack

pytestmark = pytest.mark.unit


def _cfg_lse_caps(*, enabled: bool, saliency: bool = False, tone: bool = False) -> object:
    base = _cfg_for_mode("p3_full")
    caps = LayoutStrategyCapabilitiesConfig(
        saliency_scoring=saliency,
        tone_harmony=tone,
    )
    se = LayoutStrategyEngineConfig(
        enabled=enabled,
        default_strategy_id=base.layout.strategy_engine.default_strategy_id,
        policy_path=base.layout.strategy_engine.policy_path,
        runtime_store=base.layout.strategy_engine.runtime_store,
        capabilities=caps,
    )
    return replace(base, layout=replace(base.layout, strategy_engine=se))


def test_dogfood_curate_writes_capability_flags(tmp_path: Path) -> None:
    """Acceptance: engine + caps on → trip.curation.layoutStrategy.capabilityFlags."""
    trip = load_fixture_trip("golden-mixed-scenes")
    cfg = _cfg_lse_caps(enabled=True, saliency=True, tone=True)
    body = _prepare_trip(trip)
    work = tmp_path / "lse-on"
    run_clustering_layer(body, trip_dir=work / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=work, cfg=cfg)

    ls = (body.get("curation") or {}).get("layoutStrategy") or {}
    assert ls.get("enabled") is True
    flags = ls.get("capabilityFlags") or {}
    assert flags.get("saliencyScoring") is True
    assert flags.get("toneHarmony") is True
    assert flags.get("hungarianAssignment") is False


def test_dogfood_curate_engine_off_no_capability_flags(tmp_path: Path) -> None:
    trip = load_fixture_trip("golden-mixed-scenes")
    cfg = _cfg_lse_caps(enabled=False, saliency=True)
    body = _prepare_trip(trip)
    work = tmp_path / "lse-off"
    run_clustering_layer(body, trip_dir=work / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=work, cfg=cfg)

    ls = (body.get("curation") or {}).get("layoutStrategy") or {}
    assert ls.get("enabled") is False
    assert "capabilityFlags" not in ls


def test_dogfood_mosaic_config_picks_up_config_capabilities() -> None:
    cfg = _cfg_lse_caps(enabled=True, saliency=True, tone=True)
    pack = get_strategy_pack(cfg.layout.strategy_engine.default_strategy_id)
    mosaic = mosaic_config_from_pack(cfg, pack)
    assert mosaic.lse_saliency_scoring is True
    assert mosaic.lse_tone_harmony is True
    assert "salient_crop" in mosaic.penalties
    assert float(mosaic.weights.get("tone_continuity") or 0.0) >= 0.07


def test_dogfood_patch_config_matches_strategy_trace(tmp_path: Path) -> None:
    """Simulates Studio PATCH → curate reads same disk config."""
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("layout: {}\n", encoding="utf-8")
    patch_config_file(
        cfg_path,
        {
            "layout": {
                "strategy_engine": {
                    "enabled": True,
                    "capabilities": {
                        "saliency_scoring": True,
                        "beat_profile": "classic_magazine",
                    },
                }
            }
        },
    )
    cfg = load_config(cfg_path)
    trace = strategy_trace_meta(cfg)
    assert trace["enabled"] is True
    assert trace["capabilityFlags"]["saliencyScoring"] is True
    assert trace["capabilityFlags"]["beatProfile"] == "classic_magazine"

    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    assert raw["layout"]["strategy_engine"]["enabled"] is True
