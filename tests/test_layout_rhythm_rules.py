"""排版规则优化 v0.5 · R-06 / R-08 / V-08 节奏规则单测。"""

from __future__ import annotations

from travelogue.curation.layout_constraints import (
    audit_rhythm_violations,
    check_full_bleed_portrait_consecutive,
    check_portrait_orientation_streak,
    check_portrait_pair_streak,
    max_consecutive_pattern_streak,
)
from travelogue.curation.screen_layout_state import (
    MAX_PORTRAIT_PAIR_STREAK,
    ScreenLayoutPlannerState,
)
from travelogue.curation.screen_planner import _tile_portrait_run


def _screen(pid: str) -> dict:
    return {"patternId": pid, "slots": [{"assetId": "a"}]}


def _chapters(pids: list[str]) -> list[dict]:
    return [{"id": "ch-01", "screens": [_screen(p) for p in pids]}]


# --- _tile_portrait_run (R-06 + R-02 + pair-first) ---


def test_tile_run_small_cases():
    assert _tile_portrait_run(0) == []
    assert _tile_portrait_run(1) == [1]
    assert _tile_portrait_run(2) == [2]
    assert _tile_portrait_run(3) == [3]
    assert _tile_portrait_run(4) == [2, 2]
    assert _tile_portrait_run(5) == [2, 3]


def test_tile_run_breaks_pair_streak():
    # 6 cannot be 3 consecutive pairs → break with a triple.
    assert _tile_portrait_run(6) == [2, 3, 1]
    assert _tile_portrait_run(7) == [2, 2, 3]
    assert _tile_portrait_run(8) == [2, 2, 3, 1]


def test_tile_run_no_more_than_two_consecutive_pairs():
    for n in range(0, 40):
        groups = _tile_portrait_run(n)
        assert sum(groups) == n, (n, groups)
        # no 3 consecutive pairs (size==2)
        streak = 0
        for g in groups:
            streak = streak + 1 if g == 2 else 0
            assert streak <= MAX_PORTRAIT_PAIR_STREAK, (n, groups)
        # no consecutive triples
        prev = None
        for g in groups:
            assert not (g == 3 and prev == 3), (n, groups)
            prev = g


def test_tile_run_respects_seed_streak():
    # already 2 consecutive pairs → must start with a non-pair.
    groups = _tile_portrait_run(4, seed_pair_streak=2)
    assert groups[0] != 2, groups


# --- ScreenLayoutPlannerState R-06 ---


def test_state_blocks_third_consecutive_pair():
    st = ScreenLayoutPlannerState(nine_min=0, nine_max=1)
    assert st.can_emit_pattern("screen-portrait-2")
    st.note_screen("screen-portrait-2")
    assert st.can_emit_pattern("screen-portrait-2")
    st.note_screen("screen-portrait-2")
    assert not st.can_emit_pattern("screen-portrait-2")  # 3rd blocked
    st.note_screen("screen-portrait-3")  # break streak
    assert st.can_emit_pattern("screen-portrait-2")


def test_state_pair_streak_helper():
    st = ScreenLayoutPlannerState(nine_min=0, nine_max=1)
    assert st.current_portrait_pair_streak() == 0
    st.note_screen("screen-portrait-2")
    st.note_screen("screen-portrait-2")
    assert st.current_portrait_pair_streak() == 2
    st.note_screen("screen-landscape-1")
    assert st.current_portrait_pair_streak() == 0


# --- post-check validators ---


def test_check_portrait_pair_streak():
    assert not check_portrait_pair_streak(_chapters(["screen-portrait-2"] * 2))
    bad = check_portrait_pair_streak(_chapters(["screen-portrait-2"] * 3))
    assert bad and bad[0].code == "portrait_pair_streak"


def test_check_full_bleed_portrait_consecutive():
    ok = _chapters(["screen-portrait-1", "screen-landscape-1", "screen-tall-1"])
    assert not check_full_bleed_portrait_consecutive(ok)
    bad = check_full_bleed_portrait_consecutive(
        _chapters(["screen-portrait-1", "screen-tall-1"])
    )
    assert bad and bad[0].code == "full_bleed_portrait_consecutive"


def test_check_portrait_orientation_streak():
    pids = ["screen-portrait-2"] * 4  # 8 portraits across 4 screens, within 6 streak
    assert not check_portrait_orientation_streak(_chapters(pids))
    pids7 = ["screen-portrait-1"] * 7
    bad = check_portrait_orientation_streak(_chapters(pids7))
    assert bad and bad[0].code == "portrait_orientation_streak"


def test_audit_rhythm_violations_aggregate():
    chapters = _chapters(["screen-portrait-2"] * 3)
    codes = {v.code for v in audit_rhythm_violations(chapters)}
    assert "portrait_pair_streak" in codes


def test_max_consecutive_pattern_streak_ignores_breaks():
    pids = ["screen-portrait-2", "screen-portrait-3", "screen-portrait-2"]
    assert max_consecutive_pattern_streak([_screen(p) for p in pids]) == 1
