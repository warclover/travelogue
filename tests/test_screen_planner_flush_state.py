"""Chapter-end portrait flush respects layout_state."""

from travelogue.curation.screen_planner import (
    ScreenLayoutPlannerState,
    is_portrait_single_pattern,
    plan_screens_for_chapter,
)


def test_chapter_end_flush_no_consecutive_portrait_single() -> None:
    ids = [f"p{i}" for i in range(5)]
    aspects = {x: "portrait" for x in ids}
    state = ScreenLayoutPlannerState.from_trip_total(40)
    state.last_kind = "portrait_single"
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        chapter_id="ch-end",
        layout_state=state,
    )
    patterns = [sc["patternId"] for sc in screens]
    for i in range(len(patterns) - 1):
        if is_portrait_single_pattern(patterns[i]):
            assert not is_portrait_single_pattern(patterns[i + 1])
