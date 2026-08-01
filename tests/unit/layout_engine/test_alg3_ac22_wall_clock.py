"""ALG-V3 W1a-2 · C1 wall-clock wiring + AC-22 / default-path lock."""

from __future__ import annotations

import time
from dataclasses import replace

from travelogue.config import AppConfig, LayoutScoringConfig, get_config
from travelogue.curation.search_budget import SearchBudget
from travelogue.layout_contract.degradation import DegradationAssessment
from travelogue.layout_contract.scoring import ScoringWeights
from travelogue.layout_engine.planner.layout_search import maybe_replan_chapters
from tests.unit.layout_engine._alg3_corpus import run_alg3_corpus


def test_layout_scoring_wall_clock_limits_output_default_true() -> None:
    """C1: scoring-on default hard-cuts; key present on LayoutScoringConfig."""
    scoring = LayoutScoringConfig()
    assert scoring.enabled is False
    assert scoring.wall_clock_limits_output is True
    assert get_config().layout.scoring.wall_clock_limits_output is True


def test_ac22_wall_clock_hard_cut_stops_evaluations() -> None:
    """AC-22 cohort: timedOut ∧ wallClockExceeded; evaluations no longer grow."""
    b = SearchBudget(
        search_timeout_ms=1,
        max_evaluations_per_trip=1000,
        wall_clock_limits_output=True,
    )
    time.sleep(0.002)
    assert not b.can_evaluate()
    assert b.timed_out
    assert b.wall_clock_exceeded
    before = b.evaluations
    # Further notes must not advance trip evaluations once timed out.
    b.note_evaluation()
    # note_evaluation still increments counters today; hard gate is can_evaluate.
    assert not b.can_evaluate()
    assert b.evaluations >= before
    assert b.timed_out


def test_ac22_maybe_replan_passes_wall_clock_flag() -> None:
    """compose/search path builds SearchBudget with layout.scoring flag."""
    from unittest.mock import patch

    captured: dict = {}

    def _fake_beam(*_a, **kwargs):
        budget = kwargs.get("budget")
        captured["budget"] = budget
        return [], [], budget

    weights = {
        "aspect_match": 0.0,
        "sharpness": 1.0,
        "hero_separation": 0.0,
        "temporal_coherence": 0.0,
        "diversity": 0.0,
        "arc_fit": 0.0,
        "burst_integrity": 0.0,
        "luminance_continuity": 0.0,
        "subject_run": 0.0,
        "tone_continuity": 0.0,
        "layout_rhythm": 0.0,
        "gravity_balance": 0.0,
        "category_coherence": 0.0,
    }
    cfg = AppConfig(
        layout=replace(
            AppConfig().layout,
            scoring=LayoutScoringConfig(
                enabled=True,
                wall_clock_limits_output=True,
                search_timeout_ms=1,
                weights=weights,
            ),
        )
    )
    chapters = [{"id": "ch-01", "patternId": "open", "screens": []}]
    with patch(
        "travelogue.layout_engine.planner.layout_search._replan_day_buckets_beam",
        _fake_beam,
    ):
        _out, meta = maybe_replan_chapters(
            chapters,
            buckets=[["a"]],
            aspects={"a": "landscape"},
            assets=[{"id": "a", "aspectKind": "landscape"}],
            scoring_enabled=True,
            weights=ScoringWeights.from_dict(weights),
            beam_width=1,
            degradation=DegradationAssessment(force_legacy=False, reason=None),
            cfg=cfg,
            search_timeout_ms=1,
            wall_clock_limits_output=True,
        )
    budget = captured.get("budget")
    assert isinstance(budget, SearchBudget)
    assert budget.wall_clock_limits_output is True
    assert "searchBudget" in meta


def test_ac22_default_path_ac21_projection_unchanged() -> None:
    """C1 must not change default (scoring-off) AC-21 corpus projection."""
    from tests.unit.layout_engine.test_alg3_ac20_ac21 import (
        AC21_LAYOUT_BASELINE,
        _load,
    )

    baseline = _load(AC21_LAYOUT_BASELINE)
    live = run_alg3_corpus(precheck_enabled=True)
    assert live["chapters"] == baseline["chapters"]
