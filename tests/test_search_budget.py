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


def test_budget_times_out():
    b = SearchBudget(search_timeout_ms=1, max_evaluations_per_trip=100)
    time.sleep(0.002)
    assert not b.can_evaluate()
    assert b.timed_out
