"""AC-AAD-12 / AC-AAD-20 · curate layout signature A/B (prefix_beam default off).

Compares ``layout_snapshot`` across two ``run_curate`` runs. Self-reflexive
determinism + flag-off path; strips decisionLog / timestamps by using
``layout_snapshot`` only (patternId + slotAssetIds).
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from tests._golden.helpers import build_mixed_aspects_trip, layout_snapshot
from travelogue.config import get_config
from travelogue.curation.curate import run_curate

pytestmark = pytest.mark.unit


def _mini_trip(assets: list[dict]) -> dict:
    return {
        "tripId": "aad-sig-ab",
        "assets": assets,
        "exportLayout": "web",
        "layoutEngine": "screens",
        "pipeline": {"status": "ingested"},
        "meta": {},
        "curation": {},
    }


def _cfg(*, prefix_beam: bool = False, mosaic: bool = False):
    cfg = get_config()
    return replace(
        cfg,
        aesthetic=replace(cfg.aesthetic, enabled=False),
        mosaic=replace(cfg.mosaic, enabled=mosaic),
        layout=replace(
            cfg.layout,
            scoring=replace(
                cfg.layout.scoring,
                enabled=True,
                prefix_beam_enabled=prefix_beam,
                beam_width=2,
                search_timeout_ms=5000,
                max_evaluations_per_trip=200,
            ),
        ),
    )


def test_ac_aad_12_curate_layout_signature_stable(tmp_path: Path) -> None:
    """Two identical curate runs (flag off) produce the same layout snapshot."""
    _buckets, _aspects, assets = build_mixed_aspects_trip()
    cfg = _cfg(prefix_beam=False, mosaic=False)
    snaps = []
    for i in range(2):
        trip = _mini_trip(deepcopy(assets))
        work = tmp_path / f"run-{i}"
        work.mkdir()
        run_curate(trip, apply_layout=True, trip_dir=work, cfg=cfg, export_layout="web")
        snaps.append(layout_snapshot(trip.get("chapters") or []))
    assert snaps[0] == snaps[1]
    assert snaps[0]["chapters"], "expected at least one chapter"


def test_ac_aad_20_prefix_beam_off_planner_path_not_prefix(tmp_path: Path) -> None:
    """Default-off PrefixBeam must not select plannerPath=prefix_beam."""
    _buckets, _aspects, assets = build_mixed_aspects_trip()
    cfg = _cfg(prefix_beam=False, mosaic=False)
    trip = _mini_trip(deepcopy(assets))
    run_curate(trip, apply_layout=True, trip_dir=tmp_path / "off", cfg=cfg, export_layout="web")
    logs = (trip.get("curation") or {}).get("layoutDecisionLog") or []
    for entry in logs:
        for ev in entry.get("events") or []:
            if (ev.get("plannerPath") or "") == "prefix_beam":
                pytest.fail(f"unexpected prefix_beam path with flag off: {ev}")
