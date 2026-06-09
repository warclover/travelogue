"""P17 W3a cut-engine gates · AC-P17-23/27/31."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

import travelogue.curation.screen_planner  # noqa: F401
from scripts.phase3_ig2_report import _cfg_for_mode, _prepare_trip, load_fixture_trip
from tests._golden.helpers import layout_snapshot
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.curate import run_curate
from travelogue.curation.layout_density import resolve_import_layout_density
from travelogue.layout_engine.render_contract import (
    RENDER_ISOLATED_CURATION_KEYS,
    curation_for_render_contract,
    trip_render_fingerprint_payload,
)
from travelogue.services.trip import apply_intent


def _quick_share_cfg(base=None):
    cfg = base or _cfg_for_mode("p3_full")
    scoring = replace(cfg.layout.scoring, enabled=False)
    return replace(cfg, layout=replace(cfg.layout, scoring=scoring))


def _curate_quick_share(trip: dict, work_dir: Path, cfg) -> dict:
    body = _prepare_trip(trip)
    apply_intent(body, layout_density=resolve_import_layout_density(None, import_mode="quick_share"))
    assert "layoutDensity" not in body.get("intent", {})
    run_clustering_layer(body, trip_dir=work_dir / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=work_dir, cfg=cfg)
    return layout_snapshot(body.get("chapters") or [])


@pytest.mark.w3a_gate
def test_ac_p17_27_quick_share_lse_on_off_zero_diff(tmp_path: Path) -> None:
    """quick_share 路径 LSE on/off screens 逻辑等价（AC-P17-27）。"""
    trip = load_fixture_trip("golden-mixed-scenes")
    base = _quick_share_cfg()
    off = replace(base.layout.strategy_engine, enabled=False)
    on = replace(base.layout.strategy_engine, enabled=True)
    snap_off = _curate_quick_share(
        trip, tmp_path / "qs-off", replace(base, layout=replace(base.layout, strategy_engine=off))
    )
    snap_on = _curate_quick_share(
        trip, tmp_path / "qs-on", replace(base, layout=replace(base.layout, strategy_engine=on))
    )
    assert snap_off == snap_on


@pytest.mark.w3a_gate
def test_ac_p17_27_quick_share_fixture_parity_direct(tmp_path: Path) -> None:
    trip = load_fixture_trip("golden-portrait-family")
    base = _quick_share_cfg()
    off = replace(base.layout.strategy_engine, enabled=False)
    on = replace(base.layout.strategy_engine, enabled=True)
    snap_off = _curate_quick_share(trip, tmp_path / "off", replace(base, layout=replace(base.layout, strategy_engine=off)))
    snap_on = _curate_quick_share(trip, tmp_path / "on", replace(base, layout=replace(base.layout, strategy_engine=on)))
    assert snap_off == snap_on


@pytest.mark.w3a_gate
def test_ac_p17_31_render_contract_strips_lse_observability() -> None:
    raw = {
        "layoutStrategy": {"enabled": True, "weightsHash": "sha256:abc"},
        "mosaicDecisionLog": [{"winnerPatternId": "x"}],
        "displayedAssetIds": ["a1"],
    }
    stripped = curation_for_render_contract(raw)
    assert "layoutStrategy" not in stripped
    assert "mosaicDecisionLog" not in stripped
    assert stripped["displayedAssetIds"] == ["a1"]
    assert "layoutStrategy" in RENDER_ISOLATED_CURATION_KEYS


@pytest.mark.w3a_gate
def test_ac_p17_31_trip_render_fingerprint_omits_lse_fields() -> None:
    trip = {
        "assets": [{"id": "a1"}],
        "chapters": [{"screens": []}],
        "curation": {
            "layoutStrategy": {"enabled": True},
            "displayedAssetIds": ["a1"],
        },
    }
    fp = trip_render_fingerprint_payload(trip)
    assert "layoutStrategy" not in fp.get("curation", {})


@pytest.mark.w3a_gate
def test_ac_p17_23_quick_share_no_layout_density_intent() -> None:
    """零步：quick_share 不写入 layoutDensity intent（AC-P17-23 配套）。"""
    trip: dict = {"meta": {}}
    density = resolve_import_layout_density("hero_first", import_mode="quick_share")
    apply_intent(trip, layout_density=density)
    assert "layoutDensity" not in trip.get("intent", {})
