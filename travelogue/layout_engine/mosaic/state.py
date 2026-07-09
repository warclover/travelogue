"""Shared rhythm / quota state for MCS (thin migration from screen_layout_state)."""

from __future__ import annotations

from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState

MosaicPlannerState = ScreenLayoutPlannerState


def note_screens_batch(
    state: ScreenLayoutPlannerState | None,
    screens: list[dict],
) -> None:
    """Record emitted patterns once after a segment merge (P15-2j)."""
    if state is None:
        return
    for sc in screens:
        state.note_screen(sc.get("patternId", ""))
