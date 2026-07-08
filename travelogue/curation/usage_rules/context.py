"""WindowContext shim → layout_contract + layout_engine helpers."""

from __future__ import annotations

import importlib

from travelogue.layout_contract.usage_context import (
    DEFAULT_FEATURED_WEIGHT,
    WindowContext,
    build_window_context,
)

_ctx = importlib.import_module("travelogue.layout_engine.usage_rules.context")
main_eligible_hero_score_gap = _ctx.main_eligible_hero_score_gap
portrait_is_window_hero_max = _ctx.portrait_is_window_hero_max
window_std_portrait_count = _ctx.window_std_portrait_count

__all__ = [
    "DEFAULT_FEATURED_WEIGHT",
    "WindowContext",
    "build_window_context",
    "main_eligible_hero_score_gap",
    "portrait_is_window_hero_max",
    "window_std_portrait_count",
]
