"""Usage rules engine (URO · PRD-USAGE-RULES-LAYOUT-OPTIMIZATION)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from travelogue.curation.usage_rules.context import WindowContext, build_window_context
from travelogue.curation.usage_rules.registry import HERO_LED_DENSE_PATTERNS, HERO_LED_PATTERNS

if TYPE_CHECKING:
    from travelogue.curation.usage_rules.evaluator import evaluate_reject

__all__ = [
    "HERO_LED_DENSE_PATTERNS",
    "HERO_LED_PATTERNS",
    "WindowContext",
    "build_window_context",
    "evaluate_reject",
]


def __getattr__(name: str):
    if name == "evaluate_reject":
        from travelogue.curation.usage_rules.evaluator import evaluate_reject

        return evaluate_reject
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
