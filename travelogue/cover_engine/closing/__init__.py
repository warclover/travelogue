"""Closing package."""

from __future__ import annotations

from travelogue.cover_engine.closing.gate import (
    build_closing_candidates,
    moment_exclude_ids,
    trip_has_screens,
)
from travelogue.cover_engine.closing.scorer import pick_best_closing_scored, score_closing_candidate

__all__ = [
    "build_closing_candidates",
    "moment_exclude_ids",
    "pick_best_closing_scored",
    "score_closing_candidate",
    "trip_has_screens",
]
