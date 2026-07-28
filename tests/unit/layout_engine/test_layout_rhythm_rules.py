"""排版规则优化 v0.5 · R-06 / R-08 / V-08 节奏规则单测。"""

from __future__ import annotations

from travelogue.curation.layout_constraints import (
    RHYTHM_POSTCHECK_CODES,
    audit_rhythm_violations,
    check_full_bleed_portrait_consecutive,
    check_portrait_orientation_streak,
    check_portrait_pair_streak,
    max_consecutive_pattern_streak,
    run_rhythm_postcheck,
)
from travelogue.layout_contract.planner_state import (
    MAX_PORTRAIT_PAIR_STREAK,
    ScreenLayoutPlannerState,
)
from travelogue.layout_engine.planner.screen_planner import _tile_portrait_run


def _screen(pid: str) -> dict:
    return {"patternId": pid, "slots": [{"assetId": "a"}]}


def _chapters(pids: list[str]) -> list[dict]:
    return [{"id": "ch-01", "screens": [_screen(p) for p in pids]}]


# --- _tile_portrait_run (triple-first; pair only as remainder-2 fallback) ---


def test_tile_run_small_cases():
    assert _tile_portrait_run(0) == []
    assert _tile_portrait_run(1) == [1]
    assert _tile_portrait_run(2) == [2]
    assert _tile_portrait_run(3) == [3]
    assert _tile_portrait_run(4) == [3, 1]
    assert _tile_portrait_run(5) == [3, 2]


def test_tile_run_triple_first_matrix():
    assert _tile_portrait_run(6) == [3, 3]
    assert _tile_portrait_run(7) == [3, 3, 1]
    assert _tile_portrait_run(8) == [3, 3, 2]
    assert _tile_portrait_run(9) == [3, 3, 3]


def test_tile_run_pair_only_as_remainder_two():
    for n in range(0, 40):
        groups = _tile_portrait_run(n)
        assert sum(groups) == n, (n, groups)
        # pairs only appear as a single trailing 2 (never consecutive pairs)
        streak = 0
        for g in groups:
            streak = streak + 1 if g == 2 else 0
            assert streak <= 1, (n, groups)
            assert streak <= MAX_PORTRAIT_PAIR_STREAK, (n, groups)
        # when a pair is present it is the sole size-2 group and n % 3 == 2
        if 2 in groups:
            assert groups.count(2) == 1, (n, groups)
            assert n % 3 == 2, (n, groups)


def test_tile_run_seed_streak_ignored_under_triple_first():
    # seed/max retained for call-site compat; tiling ignores them.
    assert _tile_portrait_run(4, seed_pair_streak=2) == [3, 1]
    assert _tile_portrait_run(5, seed_pair_streak=2) == [3, 2]


# --- ScreenLayoutPlannerState R-06 ---


def test_state_allows_consecutive_portrait_triples():
    st = ScreenLayoutPlannerState(nine_min=0, nine_max=1)
    assert st.can_emit_pattern("screen-portrait-3")
    st.note_screen("screen-portrait-3")
    assert st.can_emit_pattern("screen-portrait-3")
    assert st.last_kind == "portrait_triple"


def test_state_blocks_consecutive_landscape_triples():
    st = ScreenLayoutPlannerState(nine_min=0, nine_max=1)
    assert st.can_emit_pattern("screen-landscape-3")
    st.note_screen("screen-landscape-3")
    assert not st.can_emit_pattern("screen-landscape-3")
    assert st.last_kind == "triple"


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


def test_check_landscape_pair_streak():
    from travelogue.curation.layout_constraints import check_landscape_pair_streak

    assert not check_landscape_pair_streak(_chapters(["screen-landscape-2"] * 2))
    mixed = _chapters(
        [
            "screen-landscape-2",
            "screen-landscape-2-overlap-tlbr",
            "screen-landscape-2-asymmetric-left",
        ]
    )
    bad = check_landscape_pair_streak(mixed)
    assert bad and bad[0].code == "landscape_pair_streak"


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


# --- AC-RHY-07 post-check telemetry (灰度 log) ---


def test_run_rhythm_postcheck_clean():
    summary, viol = run_rhythm_postcheck(
        _chapters(["screen-portrait-2", "screen-portrait-3", "screen-portrait-2"])
    )
    assert viol == []
    assert summary == {code: 0 for code in RHYTHM_POSTCHECK_CODES}


def test_run_rhythm_postcheck_counts_and_logs(caplog):
    import logging

    chapters = _chapters(["screen-portrait-2"] * 3)
    with caplog.at_level(logging.WARNING, logger="travelogue.curation.layout_constraints"):
        summary, viol = run_rhythm_postcheck(chapters, mode="log", trip_id="t-01")
    assert summary["portrait_pair_streak"] == 1
    assert len(viol) == 1
    assert any("post-check" in rec.message for rec in caplog.records)


# --- R-08 · 朝向 streak 状态 + 规划期强制换气 ---


def test_state_orientation_streak_and_budget():
    st = ScreenLayoutPlannerState(nine_min=0, nine_max=1)
    assert st.orientation_budget() == 6
    for _ in range(3):
        st.note_screen("screen-portrait-2")
    assert st.portrait_orientation_streak == 3
    assert st.orientation_budget() == 3
    st.note_screen("screen-landscape-1")
    assert st.portrait_orientation_streak == 0
    assert st.orientation_budget() == 6


def test_planner_r08_forces_landscape_break():
    """16 竖 + 2 横：全竖屏连续 ≤6，横版被强制提前换气，且不丢图。"""
    from travelogue.layout_engine.planner.screen_planner import plan_screens_for_chapter

    ids = [f"p{i}" for i in range(16)] + ["l1", "l2"]
    aspects = {aid: ("portrait" if aid.startswith("p") else "landscape") for aid in ids}
    state = ScreenLayoutPlannerState.from_trip_total(40)
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        chapter_id="ch-r08",
        layout_state=state,
        enable_mosaic=False,
        include_chapter_hero=False,
    )
    assert not check_portrait_orientation_streak([{"id": "ch", "screens": screens}])
    total = sum(len(sc.get("slots") or []) for sc in screens)
    assert total == len(ids)


def test_planner_r08_pure_portrait_run_still_covers_all():
    """纯竖版章（无横版可换气）：R-08 无法满足时保证全覆盖不死锁。"""
    from travelogue.layout_engine.planner.screen_planner import plan_screens_for_chapter

    ids = [f"p{i}" for i in range(16)]
    aspects = {aid: "portrait" for aid in ids}
    state = ScreenLayoutPlannerState.from_trip_total(40)
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        chapter_id="ch-r08-pure",
        layout_state=state,
        enable_mosaic=False,
        include_chapter_hero=False,
    )
    total = sum(len(sc.get("slots") or []) for sc in screens)
    assert total == len(ids)


def test_run_rhythm_postcheck_breath_transparent():
    # R-07: breath between pairs must not reset the streak — still a violation.
    pids = [
        "screen-portrait-2",
        "screen-portrait-2",
        "screen-breath-pause",
        "screen-portrait-2",
    ]
    chapters = [
        {
            "id": "ch-01",
            "screens": [
                {"patternId": "screen-portrait-2", "slots": [{"assetId": "a"}]},
                {"patternId": "screen-portrait-2", "slots": [{"assetId": "a"}]},
                {"patternId": "screen-breath-pause", "slots": []},
                {"patternId": "screen-portrait-2", "slots": [{"assetId": "a"}]},
            ],
        }
    ]
    summary, viol = run_rhythm_postcheck(chapters)
    assert summary["portrait_pair_streak"] == 1, (pids, viol)
