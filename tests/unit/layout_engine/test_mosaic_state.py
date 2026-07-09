"""MCS rhythm state helpers (mosaic/state.py)."""

from __future__ import annotations

from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_engine.mosaic.state import note_screens_batch


def test_note_screens_batch_noop_when_state_none() -> None:
    note_screens_batch(None, [{"patternId": "screen-portrait-3"}])


def test_note_screens_batch_records_nine_grid() -> None:
    state = ScreenLayoutPlannerState.from_trip_total(100)
    note_screens_batch(
        state,
        [
            {"patternId": "screen-portrait-9"},
            {"patternId": "screen-portrait-3"},
        ],
    )
    assert state.nine_used == 1
    assert state.last_kind == "triple"
