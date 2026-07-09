"""Cross-chapter carry-forward for lone portraits (web/screens, day scope).

A lone portrait left at the end of a chapter bucket is deferred forward (through
remaining chapter buckets when ``portrait_carry_max_hops=0``) so it can pair
with a later portrait, minimising the number of single-portrait screens.
"""

from __future__ import annotations

from travelogue.layout_engine.planner.screen_planner import (
    _collect_asset_ids_from_chapter,
    attach_screens_to_chapters,
)


def _chapter(ch_id: str, asset_ids: list[str], **curation: object) -> dict:
    ch: dict = {
        "id": ch_id,
        "items": [{"type": "media-card", "assetId": aid} for aid in asset_ids],
    }
    if curation:
        ch["curation"] = dict(curation)
    return ch


def _all_screens(out: list[dict]) -> list[dict]:
    screens: list[dict] = []
    for ch in out:
        screens.extend(ch.get("screens") or [])
    return screens


def _patterns(out: list[dict]) -> list[str]:
    return [str(sc.get("patternId") or "") for sc in _all_screens(out)]


def _covered_assets(out: list[dict]) -> set[str]:
    ids: set[str] = set()
    for sc in _all_screens(out):
        for slot in sc.get("slots") or []:
            if slot.get("assetId"):
                ids.add(slot["assetId"])
    return ids


def test_two_lone_portraits_pair_across_day_buckets() -> None:
    chapters = [_chapter("ch-a", ["pa"]), _chapter("ch-b", ["pb"])]
    aspects = {"pa": "portrait", "pb": "portrait"}

    out = attach_screens_to_chapters(
        chapters,
        aspects,
        plan_scope="day",
        day_buckets=[["pa"], ["pb"]],
    )

    patterns = _patterns(out)
    assert "screen-portrait-1" not in patterns
    assert "screen-portrait-2" in patterns
    assert _covered_assets(out) == {"pa", "pb"}


def test_odd_lone_portraits_reduce_to_single_tail() -> None:
    chapters = [
        _chapter("ch-a", ["pa"]),
        _chapter("ch-b", ["pb"]),
        _chapter("ch-c", ["pc"]),
    ]
    aspects = {"pa": "portrait", "pb": "portrait", "pc": "portrait"}

    out = attach_screens_to_chapters(
        chapters,
        aspects,
        plan_scope="day",
        day_buckets=[["pa"], ["pb"], ["pc"]],
    )

    patterns = _patterns(out)
    # Three lone portraits collapse to one pair + at most one trailing single.
    assert patterns.count("screen-portrait-2") >= 1
    assert patterns.count("screen-portrait-1") <= 1
    assert _covered_assets(out) == {"pa", "pb", "pc"}


def test_single_lone_portrait_still_rendered() -> None:
    chapters = [_chapter("ch-a", ["pa"])]
    aspects = {"pa": "portrait"}

    out = attach_screens_to_chapters(
        chapters,
        aspects,
        plan_scope="day",
        day_buckets=[["pa"]],
    )

    # Nothing to pair with: the carried portrait must still be emitted, not lost.
    assert _patterns(out) == ["screen-portrait-1"]
    assert _covered_assets(out) == {"pa"}
    assert set(_collect_asset_ids_from_chapter(out[0])) == {"pa"}


def test_flush_pairs_one_person_with_one_scenery_portrait() -> None:
    """V-08 收紧：1 人物 + 1 风景竖版边界 flush 合并双列，不出两张连续竖单。"""
    from travelogue.layout_engine.planner.screen_planner import _flush_portrait_pending

    aspects = {"pp": "portrait", "ps": "portrait"}
    assets = {
        "pp": {"id": "pp", "tags": ["person"]},
        "ps": {"id": "ps"},
    }
    pending = ["pp", "ps"]
    screens = _flush_portrait_pending(
        pending, aspects, assets_map=assets, force=True
    )
    assert [sc["patternId"] for sc in screens] == ["screen-portrait-2"]
    assert {s["assetId"] for s in screens[0]["slots"]} == {"pp", "ps"}
    assert pending == []


def test_rebuild_layout_state_excludes_deferred_screens() -> None:
    """AC-RHY-05 · 被 carry defer 的竖单不计入节奏 state（重放 kept 屏）。"""
    from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
    from travelogue.layout_engine.planner.screen_planner_attach import _rebuild_layout_state

    base = ScreenLayoutPlannerState.from_trip_total(60)
    # 规划期 note 了 landscape + 被 defer 的 portrait-1（污染 streak）。
    base.note_screen("screen-landscape-1")
    base.note_screen("screen-portrait-1")
    assert base.portrait_orientation_streak == 1
    rebuilt = _rebuild_layout_state(base, ["screen-landscape-1"])
    assert rebuilt.portrait_orientation_streak == 0
    assert rebuilt.last_kind != "portrait_single"
    assert rebuilt.can_emit_pattern("screen-portrait-1")
    assert rebuilt.pattern_counts.get("screen-portrait-1") is None


def test_featured_lone_portrait_is_not_carried() -> None:
    chapters = [_chapter("ch-a", ["pa"]), _chapter("ch-b", ["pb"])]
    aspects = {"pa": "portrait", "pb": "portrait"}
    assets = [
        {"id": "pa", "userTier": "featured"},
        {"id": "pb"},
    ]

    out = attach_screens_to_chapters(
        chapters,
        aspects,
        assets=assets,
        plan_scope="day",
        day_buckets=[["pa"], ["pb"]],
    )

    patterns = _patterns(out)
    # Featured pa stays a deliberate single in ch-a; pb has no partner -> single.
    assert patterns.count("screen-portrait-1") == 2
    pa_screen = next(
        sc for sc in _all_screens(out) if sc["slots"][0]["assetId"] == "pa"
    )
    assert pa_screen["patternId"] == "screen-portrait-1"
    assert _covered_assets(out) == {"pa", "pb"}


def test_lone_portraits_pair_across_many_chapters() -> None:
    """Auto hop limit (0) carries through all remaining chapters before tail single."""
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
                from_chapter_index=999,
            )
        )
    )
    ids = [f"p{i}" for i in range(5)]
    chapters = [_chapter(f"ch-{i}", [pid]) for i, pid in enumerate(ids)]
    aspects = {pid: "portrait" for pid in ids}

    out = attach_screens_to_chapters(
        chapters,
        aspects,
        plan_scope="day",
        day_buckets=[[pid] for pid in ids],
        cfg=cfg,
    )

    patterns = _patterns(out)
    assert patterns.count("screen-portrait-2") == 2
    assert patterns.count("screen-portrait-1") == 1
    assert _covered_assets(out) == set(ids)


def test_chapter_scope_uses_cross_chapter_carry() -> None:
    chapters = [_chapter("ch-a", ["pa"]), _chapter("ch-b", ["pb"])]
    aspects = {"pa": "portrait", "pb": "portrait"}

    out = attach_screens_to_chapters(
        chapters,
        aspects,
        plan_scope="chapter",
    )

    assert "screen-portrait-1" not in _patterns(out)
    assert "screen-portrait-2" in _patterns(out)


def test_replan_beam_carries_lone_portraits_across_buckets() -> None:
    """Beam replan must not bypass cross-chapter portrait carry (scoring.enabled path)."""
    from travelogue.curation.degradation import DegradationAssessment
    from travelogue.curation.layout_scoring import PHASE2_WEIGHTS
    from travelogue.layout_engine.planner.layout_search import maybe_replan_chapters

    chapters = [_chapter("ch-a", ["pa"]), _chapter("ch-b", ["pb"])]
    for ch in chapters:
        ch["screens"] = []
    aspects = {"pa": "portrait", "pb": "portrait"}
    assets = [{"id": "pa"}, {"id": "pb"}]

    replanned, meta = maybe_replan_chapters(
        chapters,
        buckets=[["pa"], ["pb"]],
        aspects=aspects,
        assets=assets,
        scoring_enabled=True,
        weights=PHASE2_WEIGHTS,
        beam_width=3,
        degradation=DegradationAssessment(force_legacy=False),
        trip_photo_total=2,
    )

    assert meta.get("replanApplied") is True
    patterns = _patterns(replanned)
    assert "screen-portrait-1" not in patterns
    assert "screen-portrait-2" in patterns
    assert _covered_assets(replanned) == {"pa", "pb"}
