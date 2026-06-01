"""Phase 7 NR-P7 equivalence gate tests (M27-C-03)."""

from __future__ import annotations

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_script_module(name: str, rel_path: str):
    path = ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


eq_mod = _load_script_module("phase7_equivalence_check_testmod", "scripts/phase7_equivalence_check.py")
perf_mod = _load_script_module("phase7_pipeline_perf_testmod", "scripts/phase7_pipeline_perf.py")


def _passing_nr_record() -> dict:
    return {
        "baseline": {
            "studio_e2e_250_ms": 400_000,
            "studio_e2e_250_p95_ms": 520_000,
            "ingest_time_250_ms": 120_000,
            "clip_embed_time_250_ms": 180_000,
            "clip_embed_time_250_p95_ms": 240_000,
            "pipeline_time_1k_sec": 600,
            "peak_memory_1k_mb": 2048,
        },
        "candidate": {
            "studio_e2e_250_ms": 250_000,
            "studio_e2e_250_p95_ms": 350_000,
            "ingest_time_250_ms": 80_000,
            "clip_embed_time_250_ms": 90_000,
            "clip_embed_time_250_p95_ms": 140_000,
            "clip_embed_time_incr_append_10pct_ms": 50_000,
            "clip_embed_time_incr_delete_10pct_ms": 45_000,
            "clip_embed_time_incr_replace_10pct_ms": 55_000,
            "auto_batch_win_rate": 0.98,
            "cache_rebuild_success_rate": 1.0,
            "rollback_recovery_success": 1.0,
            "pipeline_time_1k_sec": 580,
            "peak_memory_1k_mb": 2100,
        },
        "nr_p7": {
            "curate_hash_rate_fixed": 1.0,
            "cluster_hash_rate_fixed": 1.0,
            "curate_hash_rate_real": 0.97,
            "cluster_hash_rate_real": 0.96,
            "subject_class_agreement": 1.0,
        },
        "qualityGuard": {
            "cluster_noise_ratio_p6": 0.12,
            "cluster_noise_ratio_p7": 0.11,
            "event_boundary_f1_p6": 0.72,
            "event_boundary_f1_p7": 0.74,
            "layout_repeat_streak_p6": 4,
            "layout_repeat_streak_p7": 3,
        },
        "ac_p7": {},
    }


def test_nr_dual_threshold_passes() -> None:
    record = _passing_nr_record()
    summary = eq_mod._compute_nr_and_ac(record)
    ac = summary["ac_p7"]
    assert ac["AC-P7-04"] is True
    assert ac["AC-P7-06"] is True
    assert ac["AC-P7-09"] is True
    assert ac["AC-P7-11"] is True
    assert summary["nr_p7"]["passed"] is True


def test_nr_fixed_threshold_fails_below_100() -> None:
    record = _passing_nr_record()
    record["nr_p7"]["curate_hash_rate_fixed"] = 0.99
    summary = eq_mod._compute_nr_and_ac(record)
    assert summary["ac_p7"]["AC-P7-04"] is False
    assert summary["ac_p7"]["AC-P7-06"] is False


def test_nr_real_threshold_fails_below_95() -> None:
    record = _passing_nr_record()
    record["nr_p7"]["curate_hash_rate_real"] = 0.94
    summary = eq_mod._compute_nr_and_ac(record)
    assert summary["ac_p7"]["AC-P7-04"] is False


def test_perf_ac_computation_passes() -> None:
    record = _passing_nr_record()
    eq_mod._compute_nr_and_ac(record)
    summary = perf_mod._compute_ac(record)
    ac = summary["ac_p7"]
    assert ac["AC-P7-01"] is True
    assert ac["AC-P7-02"] is True
    assert ac["AC-P7-03"] is True
    assert ac["AC-P7-05"] is True
    assert ac["AC-P7-10"] is True
    assert ac["AC-P7-12"] is True


def test_incremental_cache_respects_scoring_context() -> None:
    """Incremental cache keys include intent/arc context (separate entries per eval)."""
    from travelogue.curation.arc_patterns import ARC_PEAK
    from travelogue.curation.layout_scoring import (
        IncrementalScoreState,
        PHASE6_WEIGHTS,
        score_screen_plan,
    )
    from tests._golden.helpers import build_mixed_aspects_trip, plan_legacy_screens

    buckets, aspects, assets = build_mixed_aspects_trip()
    plan = plan_legacy_screens(buckets, aspects, assets)
    assets_by_id = {a["id"]: a for a in assets}
    weights = PHASE6_WEIGHTS
    state = IncrementalScoreState()
    base = score_screen_plan(
        plan,
        aspects=aspects,
        assets_by_id=assets_by_id,
        weights=weights,
        arc_segment=ARC_PEAK,
        intent_arc_boost=0.0,
        incremental=True,
        incremental_state=state,
    )
    boosted_cached = score_screen_plan(
        plan,
        aspects=aspects,
        assets_by_id=assets_by_id,
        weights=weights,
        arc_segment=ARC_PEAK,
        intent_arc_boost=0.25,
        incremental=True,
        incremental_state=state,
    )
    boosted_full = score_screen_plan(
        plan,
        aspects=aspects,
        assets_by_id=assets_by_id,
        weights=weights,
        arc_segment=ARC_PEAK,
        intent_arc_boost=0.25,
        incremental=False,
    )
    assert len(state.prefix_parts) == 2
    assert abs(boosted_cached.total - boosted_full.total) < 1e-6
    assert boosted_cached.total > base.total


def test_incremental_scoring_matches_full_plan_score() -> None:
    """P7-D2 · incremental path must match full scoring within 1e-6."""
    from travelogue.curation.layout_scoring import (
        IncrementalScoreState,
        ScoringWeights,
        score_screen_plan,
    )
    from tests._golden.helpers import build_mixed_aspects_trip, plan_legacy_screens

    buckets, aspects, assets = build_mixed_aspects_trip()
    plan = plan_legacy_screens(buckets, aspects, assets)
    assets_by_id = {a["id"]: a for a in assets}
    weights = ScoringWeights(aspect_match=1.0)
    full = score_screen_plan(
        plan,
        aspects=aspects,
        assets_by_id=assets_by_id,
        weights=weights,
        incremental=False,
    )
    inc = score_screen_plan(
        plan,
        aspects=aspects,
        assets_by_id=assets_by_id,
        weights=weights,
        incremental=True,
        incremental_state=IncrementalScoreState(),
    )
    assert abs(full.total - inc.total) < 1e-6


def test_skip_duplicate_signatures_preserves_golden_layout() -> None:
    """P7-D1 · signature skip must not change beam output on aspect-only weights."""
    from travelogue.curation.degradation import DegradationAssessment
    from travelogue.curation.layout_scoring import ScoringWeights
    from travelogue.curation.layout_search import maybe_replan_chapters
    from tests._golden.helpers import build_mixed_aspects_trip, layout_snapshot, plan_legacy_screens

    buckets, aspects, assets = build_mixed_aspects_trip()
    legacy = plan_legacy_screens(buckets, aspects, assets)
    weights = ScoringWeights(aspect_match=1.0)
    replanned_on, _ = maybe_replan_chapters(
        deepcopy(legacy),
        buckets=buckets,
        aspects=aspects,
        assets=assets,
        scoring_enabled=True,
        weights=weights,
        beam_width=3,
        degradation=DegradationAssessment(force_legacy=False),
        skip_duplicate_signatures=True,
    )
    replanned_off, _ = maybe_replan_chapters(
        deepcopy(legacy),
        buckets=buckets,
        aspects=aspects,
        assets=assets,
        scoring_enabled=True,
        weights=weights,
        beam_width=3,
        degradation=DegradationAssessment(force_legacy=False),
        skip_duplicate_signatures=False,
    )
    assert layout_snapshot(replanned_on) == layout_snapshot(legacy)
    assert layout_snapshot(replanned_off) == layout_snapshot(legacy)


def test_ac_p7_08_rollback_patch_matches_p6_flags() -> None:
    rollback_mod = _load_script_module(
        "phase7_verify_rollback_testmod",
        "scripts/phase7_verify_rollback.py",
    )
    patch = rollback_mod.rollback_patch()
    assert patch["vision"]["batch_size"] == 0
    assert patch["vision"]["prefer_web_derivative"] is False
    assert patch["pipeline"]["parallel_embed"] is False
    assert patch["ingest"]["webp_method"] == 6
    assert patch["layout_scoring"]["incremental"] is False


def test_ac_p7_07_embed_stats_telemetry_shape() -> None:
    from travelogue.vision.clip_encoder import EmbedStats

    stats = EmbedStats(
        elapsed_ms=12.5,
        batch_size=8,
        batches=3,
        prefetch_enabled=True,
        web_derivative_hits=2,
        cache_hit_ratio=0.5,
        recommended_batch_size=8,
    )
    payload = stats.to_dict()
    for key in (
        "elapsedMs",
        "batchSize",
        "batches",
        "prefetchEnabled",
        "webDerivativeHits",
        "cacheHitRatio",
        "recommendedBatchSize",
    ):
        assert key in payload


def test_gate_runner_from_record_passes(tmp_path: Path) -> None:
    gate_mod = _load_script_module("phase7_gate_run_testmod", "scripts/phase7_gate_run.py")
    record = _passing_nr_record()
    perf_summary = perf_mod._compute_ac(record)
    eq_summary = eq_mod._compute_nr_and_ac(record)
    record["ac_p7"] = {**perf_summary["ac_p7"], **eq_summary["ac_p7"]}
    record["ac_p7"]["AC-P7-07"] = True
    record["ac_p7"]["AC-P7-08"] = True
    rec_path = tmp_path / "phase7-perf-eval.json"
    rec_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    summary, code = gate_mod._from_record_summary(rec_path, strict=True)
    assert code == 0
    assert summary["overallPassed"] is True
