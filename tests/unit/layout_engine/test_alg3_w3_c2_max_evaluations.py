"""ALG-V3 W3-C2 · finite max_evaluations_per_segment (scoring still default-off)."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import get_config
from travelogue.config.layout import LayoutScoringConfig, layout_scoring_from_dict
from travelogue.curation.search_budget import SearchBudget
from travelogue.layout_contract.degradation import DegradationAssessment
from travelogue.layout_contract.scoring import ScoringWeights
from travelogue.layout_engine.planner.layout_search import maybe_replan_chapters


def test_c2_default_segment_cap_is_64_scoring_still_off() -> None:
    scoring = LayoutScoringConfig()
    assert scoring.enabled is False
    assert scoring.max_evaluations_per_segment == 64
    assert get_config().layout.scoring.max_evaluations_per_segment == 64


def test_c2_loader_default_and_camel() -> None:
    empty = layout_scoring_from_dict({})
    assert empty.max_evaluations_per_segment == 64
    camel = layout_scoring_from_dict({"maxEvaluationsPerSegment": 32})
    assert camel.max_evaluations_per_segment == 32
    # Explicit 0 still means unlimited (legacy / operator override).
    unlimited = layout_scoring_from_dict({"max_evaluations_per_segment": 0})
    assert unlimited.max_evaluations_per_segment == 0


def test_c2_segment_budget_exhausts_at_default_cap() -> None:
    b = SearchBudget(
        max_evaluations_per_trip=500,
        max_evaluations_per_segment=64,
        search_timeout_ms=60_000,
    )
    b.begin_segment()
    for _ in range(64):
        assert b.can_evaluate()
        b.note_evaluation()
    assert not b.can_evaluate()
    b.begin_segment()
    assert b.can_evaluate()


def test_c2_default_path_replan_still_skipped() -> None:
    """Scoring remains off → maybe_replan early-returns (production path lock)."""
    chapters = [{"id": "ch1", "screens": [{"patternId": "solo", "slots": ["a"]}]}]
    out, meta = maybe_replan_chapters(
        chapters,
        buckets=[["a"]],
        aspects={"a": "landscape"},
        assets=[{"id": "a", "aspectKind": "landscape"}],
        scoring_enabled=False,
        weights=ScoringWeights(),
        beam_width=3,
        degradation=DegradationAssessment(force_legacy=False, reason=None),
        max_evaluations_per_segment=64,
    )
    assert out == chapters
    assert meta.get("replanApplied") is False
    assert str(meta.get("skipReason") or "").lower().find("scoring") >= 0 or meta.get(
        "skipReason"
    ) == "scoring_disabled"



def test_c2_scoring_off_ignores_segment_cap_in_appconfig() -> None:
    """Changing segment cap must not flip default enabled."""
    base = get_config()
    cfg = replace(
        base,
        layout=replace(
            base.layout,
            scoring=replace(base.layout.scoring, max_evaluations_per_segment=8),
        ),
    )
    assert cfg.layout.scoring.enabled is False
    assert cfg.layout.scoring.max_evaluations_per_segment == 8
