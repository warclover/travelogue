"""LTN C5 · hero_reserve state machine."""

from __future__ import annotations

from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_LANDSCAPE_4,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)


def test_hero_reserve_arm_consume_release_cycle():
    st = ScreenLayoutPlannerState.from_trip_total(40)
    assert st.hero_reserve == "idle"
    st.arm_hero_reserve()
    assert st.hero_reserve == "armed"
    st.consume_hero_reserve()
    assert st.hero_reserve == "consumed"
    st.begin_chapter_bucket(chapter_index=2)
    assert st.hero_reserve == "idle"


def test_hero_reserve_release_when_chapter_ends_armed():
    st = ScreenLayoutPlannerState.from_trip_total(40)
    st.arm_hero_reserve()
    st.begin_chapter_bucket(chapter_index=2)
    assert st.hero_reserve == "released"
    st.arm_hero_reserve()
    assert st.hero_reserve == "armed"


def test_armed_blocks_equal_weight_dense_not_hero():
    st = ScreenLayoutPlannerState.from_trip_total(40)
    st.arm_hero_reserve()
    assert st.blocks_dense_for_hero_reserve(PATTERN_LANDSCAPE_4)
    assert not st.can_emit_pattern(PATTERN_LANDSCAPE_4)
    assert not st.blocks_dense_for_hero_reserve(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5)


def test_note_screen_main_consumes_reserve():
    st = ScreenLayoutPlannerState.from_trip_total(40)
    st.arm_hero_reserve()
    st.note_screen(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5)
    assert st.hero_reserve == "consumed"
