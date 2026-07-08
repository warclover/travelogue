"""Search budget guardrails."""

from __future__ import annotations

import time

from travelogue.curation.search_budget import SearchBudget


def test_budget_exhausts_on_max_evaluations():
    b = SearchBudget(max_evaluations_per_trip=2, search_timeout_ms=60_000)
    assert b.can_evaluate()
    b.note_evaluation()
    b.note_evaluation()
    assert not b.can_evaluate()
    assert b.exhausted
    assert b.can_generate()


def test_generation_vs_evaluation_split():
    b = SearchBudget(max_evaluations_per_trip=1, search_timeout_ms=60_000)
    assert b.can_generate()
    b.note_generation(3)
    assert b.generations == 3
    assert b.evaluations == 0
    assert b.can_generate()
    assert b.can_evaluate()
    b.note_evaluation()
    assert not b.can_evaluate()
    assert b.can_generate()


def test_budget_wall_clock_telemetry_only_by_default():
    b = SearchBudget(search_timeout_ms=1, max_evaluations_per_trip=100)
    time.sleep(0.002)
    assert b.can_evaluate()
    assert b.wall_clock_exceeded
    assert not b.timed_out


def test_budget_times_out_when_wall_clock_limits_output():
    b = SearchBudget(
        search_timeout_ms=1,
        max_evaluations_per_trip=100,
        wall_clock_limits_output=True,
    )
    time.sleep(0.002)
    assert not b.can_evaluate()
    assert b.timed_out
    assert b.wall_clock_exceeded


def test_segment_evaluations_reset():
    b = SearchBudget(max_evaluations_per_trip=10, max_evaluations_per_segment=2)
    b.begin_segment()
    b.note_evaluation()
    b.note_evaluation()
    assert not b.can_evaluate()
    b.begin_segment()
    assert b.can_evaluate()
