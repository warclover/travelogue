"""Beam search budget / guardrails (Phase 3a · P7-D4 gen/eval split)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class SearchBudget:
    search_timeout_ms: int = 2000
    max_candidates_per_bucket: int = 12
    max_evaluations_per_trip: int = 500
    allow_burst_split: bool = False
    generations: int = 0
    evaluations: int = 0
    started_at: float = field(default_factory=time.monotonic)
    timed_out: bool = False
    exhausted: bool = False

    def elapsed_ms(self) -> float:
        return (time.monotonic() - self.started_at) * 1000.0

    def _check_timeout(self) -> bool:
        if self.elapsed_ms() >= self.search_timeout_ms:
            self.timed_out = True
            return True
        return False

    def can_generate(self) -> bool:
        """Candidate generation is timeout-gated only (P7-D4)."""
        if self.timed_out:
            return False
        return not self._check_timeout()

    def note_generation(self, count: int = 1) -> None:
        self.generations += count
        self._check_timeout()

    def can_evaluate(self) -> bool:
        if self.timed_out or self.exhausted:
            return False
        if self._check_timeout():
            return False
        if self.evaluations >= self.max_evaluations_per_trip:
            self.exhausted = True
            return False
        return True

    def note_evaluation(self, count: int = 1) -> None:
        self.evaluations += count
        if self.evaluations >= self.max_evaluations_per_trip:
            self.exhausted = True
        self._check_timeout()

    def to_dict(self) -> dict:
        return {
            "generations": self.generations,
            "evaluations": self.evaluations,
            "elapsedMs": round(self.elapsed_ms(), 2),
            "timedOut": self.timed_out,
            "exhausted": self.exhausted,
            "allowBurstSplit": self.allow_burst_split,
        }
