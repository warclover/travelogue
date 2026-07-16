"""AC-AAD-22/23/25/26 · deterministic strict, cache keys, weights_hash, scoring surface."""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from tests._golden.helpers import build_mixed_aspects_trip, layout_snapshot
from travelogue.config import MosaicConfig, get_config
from travelogue.curation.curate import run_curate
from travelogue.layout_contract.scoring import ScoringWeights, combine_utility
from travelogue.layout_engine.mosaic.scorer import weights_hash
from travelogue.layout_engine.planner.beam_scoring import _incremental_cache_key

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[3]


def _mini_trip(assets: list[dict]) -> dict:
    return {
        "tripId": "aad-ac-boost",
        "assets": assets,
        "exportLayout": "web",
        "layoutEngine": "screens",
        "pipeline": {"status": "ingested"},
        "meta": {},
        "curation": {},
    }


def test_ac_aad_22_deterministic_strict_double_run(tmp_path: Path) -> None:
    """AC-AAD-22: deterministic_strict=true → two runs share layout_snapshot."""
    _buckets, _aspects, assets = build_mixed_aspects_trip()
    cfg = get_config()
    cfg = replace(
        cfg,
        aesthetic=replace(cfg.aesthetic, enabled=False),
        mosaic=replace(cfg.mosaic, enabled=False, deterministic_strict=True),
        clustering=replace(cfg.clustering, deterministic_strict=True),
        layout=replace(
            cfg.layout,
            scoring=replace(
                cfg.layout.scoring,
                enabled=True,
                prefix_beam_enabled=False,
                beam_width=2,
            ),
        ),
    )
    snaps = []
    for i in range(2):
        trip = _mini_trip(deepcopy(assets))
        work = tmp_path / f"d{i}"
        work.mkdir()
        run_curate(trip, apply_layout=True, trip_dir=work, cfg=cfg, export_layout="web")
        snaps.append(layout_snapshot(trip.get("chapters") or []))
    assert snaps[0] == snaps[1]
    assert snaps[0]["chapters"]


def test_ac_aad_23_incremental_cache_key_stable_on_prefix() -> None:
    """AC-AAD-23: screens[:k] key is prefix-stable for IncrementalScoreState."""
    weights = ScoringWeights()
    ctx = dict(
        weights=weights,
        arc_segment=None,
        arc_profile="dynamic",
        hero_asset_ids=None,
        intent_arc_boost=0.0,
        featured_beam=True,
        subject_run_tolerance=1,
        enable_gravity_balance=False,
    )
    s1 = {"patternId": "screen-landscape-1", "slots": [{"assetId": "a", "slot": 0}]}
    s2 = {"patternId": "screen-landscape-1", "slots": [{"assetId": "b", "slot": 0}]}
    key1 = _incremental_cache_key([s1], **ctx)
    key2 = _incremental_cache_key([s1, s2], **ctx)
    key1b = _incremental_cache_key([s1], **ctx)
    assert key1 == key1b
    assert key1 != key2
    # plan key is first element — prefix plan must differ only by length
    assert key1[0] != key2[0]
    assert key1[1:] == key2[1:]


def test_ac_aad_25_weights_hash_changes_with_weights() -> None:
    base = MosaicConfig()
    a = weights_hash(base)
    b = weights_hash(replace(base, weights={**dict(base.weights), "aspect": 0.99}))
    c = weights_hash(base)
    assert a == c
    assert a != b
    assert a.startswith("sha256:")


def test_ac_aad_25_combine_utility_formula() -> None:
    bd = combine_utility(0.8, {"face": 1.0}, {"face": 0.25})
    assert bd.utility == pytest.approx(0.8 * (1 - 0.25), abs=1e-9)


def test_ac_aad_26_no_parallel_utility_kernel() -> None:
    """AC-AAD-26: LayoutUtility kernel lives only in layout_contract.combine_utility."""
    scoring = (ROOT / "travelogue" / "layout_contract" / "scoring.py").read_text(
        encoding="utf-8"
    )
    assert "def combine_utility(" in scoring

    def _calls_combine(path: Path) -> bool:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "combine_utility":
                    return True
                if isinstance(func, ast.Attribute) and func.attr == "combine_utility":
                    return True
        return False

    scorer = ROOT / "travelogue" / "layout_engine" / "mosaic" / "scorer.py"
    beam = ROOT / "travelogue" / "layout_engine" / "planner" / "beam_scoring.py"
    assert _calls_combine(scorer), "mosaic scorer must call combine_utility"
    assert _calls_combine(beam), "beam_scoring must call combine_utility"
