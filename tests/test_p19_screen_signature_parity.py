"""P19 S2 · LTE runtime grid_specs must not change mosaic screen signatures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from tests._golden.helpers import (
    build_mosaic_eligible_trip,
    build_portrait_heavy_trip,
    plan_mosaic_screens,
)
from travelogue.curation.mosaic import _legacy_generated as legacy_gen
from travelogue.curation.mosaic.grid_specs import (
    AUTO_FLOW_GRIDS,
    EXPLICIT_GRID_SPECS,
    STACK_PATTERNS,
)
from travelogue.curation.mosaic.legacy_specs import reset_legacy_specs_cache_for_tests
from travelogue.layout_templates.registry import LayoutTemplateEngine, reset_engine_cache_for_tests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
_GOLDEN_PATH = Path(__file__).resolve().parent / "_golden" / "p19_screen_signatures.json"


def _pattern_sequence(chapters: list[dict]) -> list[str]:
    seq: list[str] = []
    for ch in chapters:
        for s in ch.get("screens") or []:
            pid = s.get("patternId")
            if pid:
                seq.append(str(pid))
    return seq


@pytest.fixture(autouse=True)
def _fresh_lte() -> None:
    reset_engine_cache_for_tests()
    reset_legacy_specs_cache_for_tests()


@pytest.mark.unit
def test_grid_specs_runtime_matches_legacy_snapshot() -> None:
    assert EXPLICIT_GRID_SPECS == legacy_gen.EXPLICIT_GRID_SPECS
    assert AUTO_FLOW_GRIDS == legacy_gen.AUTO_FLOW_GRIDS
    assert STACK_PATTERNS == legacy_gen.STACK_PATTERNS


@pytest.mark.unit
def test_grid_specs_runtime_matches_lte_export() -> None:
    engine = LayoutTemplateEngine.load(rebuild_cache=True)
    exported = engine.export_legacy_registry()
    assert EXPLICIT_GRID_SPECS == exported["explicit_grid_specs"]
    assert AUTO_FLOW_GRIDS == exported["auto_flow_grids"]
    assert STACK_PATTERNS == exported["stack_patterns"]


@pytest.mark.unit
def test_p19_synthetic_pattern_sequences_match_golden() -> None:
    if not _GOLDEN_PATH.is_file():
        pytest.skip(f"missing golden file: {_GOLDEN_PATH}")
    golden = json.loads(_GOLDEN_PATH.read_text(encoding="utf-8"))
    builders = {
        "mosaic_eligible": build_mosaic_eligible_trip,
        "portrait_heavy": build_portrait_heavy_trip,
    }
    for key, builder in builders.items():
        expected = golden.get(key)
        if not expected:
            continue
        buckets, aspects, assets = builder()
        chapters = plan_mosaic_screens(buckets, aspects, assets)
        seq = _pattern_sequence(chapters)
        assert seq == expected["patternSequence"], key


@pytest.mark.unit
def test_p19_mosaic_signatures_stable_after_cache_refresh() -> None:
    for builder in (build_mosaic_eligible_trip, build_portrait_heavy_trip):
        buckets, aspects, assets = builder()
        chapters_a = plan_mosaic_screens(buckets, aspects, assets)
        seq_a = _pattern_sequence(chapters_a)
        reset_engine_cache_for_tests()
        reset_legacy_specs_cache_for_tests()
        chapters_b = plan_mosaic_screens(buckets, aspects, assets)
        assert _pattern_sequence(chapters_b) == seq_a


@pytest.mark.integration
def test_p19_golden_trips_curate_pattern_sequence_self_consistent() -> None:
    """LTE runtime path: two curate passes per trip must yield identical pattern sequences."""
    from travelogue.eval.golden_trips import resolve_existing_golden_trips

    rows = [r for r in resolve_existing_golden_trips(root=ROOT) if r["exists"]]
    if not rows:
        pytest.skip("no golden trips under trips/")

    from book_quality_baseline import _curate_trip, _p16_cfg
    from travelogue.config import get_config

    cfg = _p16_cfg(get_config(reload=True))

    for row in rows:
        tid = row["tripId"]
        trip_path = Path(row["tripDir"]) / "trip.json"
        trip = json.loads(trip_path.read_text(encoding="utf-8"))
        work_a = ROOT / ".cache" / "book-quality" / "signature-parity" / tid / "a"
        work_b = ROOT / ".cache" / "book-quality" / "signature-parity" / tid / "b"
        body_a = _curate_trip(trip, work_dir=work_a, cfg=cfg)
        reset_engine_cache_for_tests()
        reset_legacy_specs_cache_for_tests()
        body_b = _curate_trip(trip, work_dir=work_b, cfg=cfg)
        seq_a = _pattern_sequence(body_a.get("chapters") or [])
        seq_b = _pattern_sequence(body_b.get("chapters") or [])
        assert seq_a == seq_b, tid
