"""Admission hook registry (layer-0 · render registers golden step)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

GoldenRenderStepFn = Callable[[str, Any], dict[str, Any]]

_golden_render_step: GoldenRenderStepFn | None = None


def register_golden_render_step(fn: GoldenRenderStepFn | None) -> None:
    global _golden_render_step
    _golden_render_step = fn


def run_golden_render_step(template_id: str, fixture_trip: dict) -> dict[str, Any]:
    if _golden_render_step is None:
        return {"name": "golden_render", "pass": True, "skipped": True}
    return _golden_render_step(template_id, fixture_trip)
