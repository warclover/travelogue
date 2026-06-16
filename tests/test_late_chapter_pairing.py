"""Late-chapter portrait pairing: front chapters unchanged, back chapters consolidate."""

from __future__ import annotations

from travelogue.curation.screen_layout_state import (
    LateChapterPairingPolicy,
    RhythmRules,
    ScreenLayoutPlannerState,
)
from travelogue.curation.screen_planner import attach_screens_to_chapters
from travelogue.curation.screen_planner_attach import (
    _carry_inject_ids,
    _consolidate_adjacent_portrait_singles,
    _portrait_carry_hop_limit,
)
from travelogue.curation.screen_planner_stages import (
    build_chapter_plan_context,
    stage_flush_pending_for_other_family,
)


def _chapter(ch_id: str, asset_ids: list[str]) -> dict:
    return {
        "id": ch_id,
        "items": [{"type": "media-card", "assetId": aid} for aid in asset_ids],
    }


def _patterns(out: list[dict]) -> list[str]:
    pats: list[str] = []
    for ch in out:
        for sc in ch.get("screens") or []:
            pats.append(str(sc.get("patternId") or ""))
    return pats


def _patterns_by_chapter(out: list[dict]) -> dict[str, list[str]]:
    return {
        ch["id"]: [str(sc.get("patternId") or "") for sc in ch.get("screens") or []]
        for ch in out
    }


def test_begin_chapter_bucket_resets_streaks_only_in_late_zone() -> None:
    rhythm = RhythmRules(
        late_chapter_pairing=LateChapterPairingPolicy(from_chapter_index=3)
    )
    st = ScreenLayoutPlannerState.from_trip_total(60, rhythm=rhythm)
    st.note_screen("screen-portrait-2")
    st.note_screen("screen-portrait-2")
    assert st.portrait_orientation_streak == 2
    assert st.current_portrait_pair_streak() == 2

    st.begin_chapter_bucket(chapter_index=2)
    assert st.portrait_orientation_streak == 2
    assert st.current_portrait_pair_streak() == 2

    st.begin_chapter_bucket(chapter_index=3)
    assert st.portrait_orientation_streak == 0
    assert st.current_portrait_pair_streak() == 0


def test_no_outward_carry_in_late_chapters() -> None:
    rhythm = RhythmRules(
        late_chapter_pairing=LateChapterPairingPolicy(
            from_chapter_index=2, no_outward_portrait_carry=True
        )
    )
    assert _portrait_carry_hop_limit(0, 4, rhythm) == 3
    assert _portrait_carry_hop_limit(1, 4, rhythm) == 0


def test_consolidate_adjacent_portrait_singles() -> None:
    aspects = {"a": "portrait", "b": "portrait"}
    screens = [
        {"patternId": "screen-portrait-1", "slots": [{"assetId": "a"}]},
        {"patternId": "screen-portrait-1", "slots": [{"assetId": "b"}]},
    ]
    merged = _consolidate_adjacent_portrait_singles(screens, aspects)
    assert len(merged) == 1
    assert merged[0]["patternId"] == "screen-portrait-2"


def test_late_chapter_flush_lookahead_defers_single_pending() -> None:
    from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState

    aspects = {"p1": "portrait", "l1": "landscape", "p2": "portrait"}
    ctx = build_chapter_plan_context(
        ["p1", "l1", "p2"],
        aspects,
        layout_state=ScreenLayoutPlannerState.from_trip_total(60),
        late_chapter_active=True,
        flush_lookahead_portraits=3,
    )
    ctx.pending_portraits = ["p1"]
    ctx.i = 1
    advance = stage_flush_pending_for_other_family(ctx, "landscape")
    assert advance is None
    assert ctx.pending_portraits == ["p1"]


def test_early_chapters_still_defer_carry_outward() -> None:
    chapters = [
        _chapter("ch-a", ["pa"]),
        _chapter("ch-b", ["pb"]),
        _chapter("ch-c", ["pc", "pd"]),
    ]
    aspects = {aid: "portrait" for aid in ("pa", "pb", "pc", "pd")}

    out = attach_screens_to_chapters(
        chapters,
        aspects,
        plan_scope="day",
        day_buckets=[["pa"], ["pb"], ["pc", "pd"]],
    )

    by_ch = _patterns_by_chapter(out)
    assert "screen-portrait-1" not in by_ch.get("ch-a", [])
    assert "screen-portrait-2" in _patterns(out)


def test_late_chapter_no_outward_carry_reduces_tail_singles() -> None:
    """Ch3+ must digest carry locally; ch1-2 may still defer forward."""
    from travelogue.config import AppConfig
    from travelogue.config.layout import (
        LayoutConfig,
        LayoutLateChapterPairingConfig,
        LayoutRhythmConfig,
    )

    cfg = AppConfig()
    cfg.layout = LayoutConfig(
        rhythm=LayoutRhythmConfig(
            late_chapter_pairing=LayoutLateChapterPairingConfig(
                from_chapter_index=3,
                no_outward_portrait_carry=True,
            )
        )
    )

    chapters = [
        _chapter("ch-a", ["p0"]),
        _chapter("ch-b", ["p1"]),
        _chapter("ch-c", ["p2", "p3"]),
        _chapter("ch-d", ["p4", "p5"]),
    ]
    aspects = {f"p{i}": "portrait" for i in range(6)}

    out = attach_screens_to_chapters(
        chapters,
        aspects,
        plan_scope="day",
        day_buckets=[["p0"], ["p1"], ["p2", "p3"], ["p4", "p5"]],
        cfg=cfg,
    )

    patterns = _patterns(out)
    assert patterns.count("screen-portrait-2") >= 2
    assert patterns.count("screen-portrait-1") <= 2


def test_carry_inject_uses_longest_run_in_late_chapter() -> None:
    aspects = {
        "l1": "landscape",
        "p1": "portrait",
        "p2": "portrait",
        "c1": "portrait",
    }
    plan = ["l1", "p1", "p2", "l1"]
    injected = _carry_inject_ids(plan, ["c1"], aspects, late_chapter=True)
    assert injected.index("c1") == 3
    assert injected[1:3] == ["p1", "p2"]
