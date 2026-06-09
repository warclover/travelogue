"""P17 controlled parity · AC-P17-01 (audit B runbook)."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.phase3_ig2_report import _cfg_for_mode, _prepare_trip, load_fixture_trip
from tests._golden.helpers import layout_snapshot
from tests.p17_golden_fixtures import P17_CONTROLLED_PARITY_FIXTURES
from travelogue.curation.clustering import run_clustering_layer
from travelogue.curation.curate import run_curate


def _cfg_with_lse(*, enabled: bool):
    base = _cfg_for_mode("p3_full")
    se = replace(base.layout.strategy_engine, enabled=enabled)
    layout = replace(base.layout, strategy_engine=se)
    return replace(base, layout=layout)


def _curate_snapshot(trip: dict, work_dir: Path, cfg) -> dict:
    body = _prepare_trip(trip)
    run_clustering_layer(body, trip_dir=work_dir / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=work_dir, cfg=cfg)
    return layout_snapshot(body.get("chapters") or [])


@pytest.mark.controlled_parity
@pytest.mark.parametrize("fixture_id", P17_CONTROLLED_PARITY_FIXTURES)
def test_p17_lse_disabled_matches_baseline_snapshot(
    tmp_path: Path, fixture_id: str
) -> None:
    trip = load_fixture_trip(fixture_id)
    baseline = _curate_snapshot(trip, tmp_path / "baseline", _cfg_for_mode("p3_full"))
    explicit_off = _curate_snapshot(trip, tmp_path / "lse_off", _cfg_with_lse(enabled=False))
    assert baseline == explicit_off


@pytest.mark.controlled_parity
@pytest.mark.parametrize("fixture_id", P17_CONTROLLED_PARITY_FIXTURES)
def test_p17_lse_enabled_pure_convergence(tmp_path: Path, fixture_id: str) -> None:
    """W1: enabled=true default pack must match P16 screens (no CAP)."""
    trip = load_fixture_trip(fixture_id)
    baseline = _curate_snapshot(trip, tmp_path / "base", _cfg_for_mode("p3_full"))
    lse_on = _curate_snapshot(trip, tmp_path / "lse_on", _cfg_with_lse(enabled=True))
    assert baseline == lse_on


@pytest.mark.controlled_parity
def test_p17_lse_writes_sidecar_and_strategy_summary(tmp_path: Path) -> None:
    trip = load_fixture_trip("golden-mixed-scenes")
    cfg = _cfg_with_lse(enabled=True)
    body = _prepare_trip(trip)
    run_clustering_layer(body, trip_dir=tmp_path / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=tmp_path, cfg=cfg)

    curation = body.get("curation") or {}
    layout_strategy = curation.get("layoutStrategy") or {}
    assert layout_strategy.get("enabled") is True
    assert layout_strategy.get("strategyId") == "lse-default-2026-06"
    assert str(layout_strategy.get("weightsHash", "")).startswith("sha256:")

    sidecar = tmp_path / "runs" / "layout-decisions.jsonl"
    assert sidecar.is_file()
    lines = [ln for ln in sidecar.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) >= 1
    first = json.loads(lines[0])
    assert first.get("schemaVersion") == 1
    assert first.get("meta", {}).get("source") == "mosaic_window"


@pytest.mark.controlled_parity
def test_p17_ac05_mosaic_window_records_in_sidecar(tmp_path: Path) -> None:
    """AC-P17-05 · mosaic-enabled curate emits window-level sidecar events."""
    trip = load_fixture_trip("golden-mixed-scenes")
    cfg = _cfg_with_lse(enabled=True)
    body = _prepare_trip(trip)
    run_clustering_layer(body, trip_dir=tmp_path / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=tmp_path, cfg=cfg)

    chapters = body.get("chapters") or []
    assert chapters

    sidecar = tmp_path / "runs" / "layout-decisions.jsonl"
    events = [
        json.loads(ln)
        for ln in sidecar.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    mosaic_events = [
        e for e in events if (e.get("meta") or {}).get("source") == "mosaic_window"
    ]
    assert len(mosaic_events) >= 1
    for ev in mosaic_events:
        assert int((ev.get("window") or {}).get("size") or 0) >= 1
        assert (ev.get("picked") or {}).get("patternId")


@pytest.mark.controlled_parity
def test_p17_lse_disabled_no_strategy_trace(tmp_path: Path) -> None:
    trip = load_fixture_trip("golden-mixed-scenes")
    base = _cfg_with_lse(enabled=False)
    scoring = replace(base.layout.scoring, enabled=False)
    cfg = replace(base, layout=replace(base.layout, scoring=scoring))
    body = _prepare_trip(trip)
    run_clustering_layer(body, trip_dir=tmp_path / "cluster", cfg=cfg)
    run_curate(body, apply_layout=True, trip_dir=tmp_path, cfg=cfg)

    layout_strategy = (body.get("curation") or {}).get("layoutStrategy") or {}
    assert layout_strategy.get("enabled") is False
    assert "strategyId" not in layout_strategy
    assert not (tmp_path / "runs" / "layout-decisions.jsonl").is_file()
