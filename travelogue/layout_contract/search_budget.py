"""Beam search budget / guardrails (layout kernel)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class SearchBudget:
    search_timeout_ms: int = 2000
    max_candidates_per_bucket: int = 12
    max_evaluations_per_trip: int = 500
    max_evaluations_per_segment: int = 0
    allow_burst_split: bool = False
    wall_clock_limits_output: bool = False
    generations: int = 0
    evaluations: int = 0
    segment_evaluations: int = 0
    started_at: float = field(default_factory=time.monotonic)
    timed_out: bool = False
    wall_clock_exceeded: bool = False
    exhausted: bool = False

    def elapsed_ms(self) -> float:
        return (time.monotonic() - self.started_at) * 1000.0

    def _check_timeout(self) -> bool:
        if self.elapsed_ms() >= self.search_timeout_ms:
            self.wall_clock_exceeded = True
            if self.wall_clock_limits_output:
                self.timed_out = True
                return True
        return False

    def can_generate(self) -> bool:
        if self.timed_out:
            return False
        return not self._check_timeout()

    def note_generation(self, count: int = 1) -> None:
        self.generations += count
        self._check_timeout()

    def begin_segment(self) -> None:
        self.segment_evaluations = 0

    def trip_evaluations_remaining(self) -> bool:
        if self.timed_out or self.exhausted:
            return False
        if self._check_timeout():
            return False
        return self.evaluations < self.max_evaluations_per_trip

    def segment_evaluations_remaining(self) -> bool:
        if not self.trip_evaluations_remaining():
            return False
        if self.max_evaluations_per_segment <= 0:
            return True
        return self.segment_evaluations < self.max_evaluations_per_segment

    def can_evaluate(self) -> bool:
        return self.segment_evaluations_remaining()

    def note_evaluation(self, count: int = 1) -> None:
        self.evaluations += count
        self.segment_evaluations += count
        if self.evaluations >= self.max_evaluations_per_trip:
            self.exhausted = True
        self._check_timeout()

    def to_dict(self) -> dict:
        return {
            "generations": self.generations,
            "evaluations": self.evaluations,
            "segmentEvaluations": self.segment_evaluations,
            "maxEvaluationsPerSegment": self.max_evaluations_per_segment,
            "elapsedMs": round(self.elapsed_ms(), 2),
            "timedOut": self.timed_out,
            "wallClockExceeded": self.wall_clock_exceeded,
            "exhausted": self.exhausted,
            "allowBurstSplit": self.allow_burst_split,
        }
