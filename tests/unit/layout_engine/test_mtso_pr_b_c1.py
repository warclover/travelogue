"""MTSO PR-B / PR-C1 · six-hero opportunity + mixed_portrait hard reject."""

from __future__ import annotations

from dataclasses import replace

import pytest

from travelogue.config import get_config
from travelogue.config.mosaic import SelectionOptimizationConfig
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)
from travelogue.layout_engine.mosaic.hero_six import (
    qualify_hero_six,
)
from travelogue.layout_engine.mosaic.hook import (
    begin_mosaic_capture,
    drain_mosaic_capture,
    try_mosaic_window,
)
from travelogue.layout_engine.mosaic.lifecycle import (
    SIX_HERO_FAMILY_CANONICAL,
    six_hero_family_id,
)
from travelogue.layout_engine.planner.screen_planner_stages import build_chapter_plan_context
from travelogue.layout_templates.registry import reset_engine_cache_for_tests


@pytest.fixture(autouse=True)
def _reset_engine() -> None:
    reset_engine_cache_for_tests()
    yield
    reset_engine_cache_for_tests()


def _asset(aid: str, *, w: int, h: int, sharp: float, kind: str) -> dict:
    return {
        "id": aid,
        "width": w,
        "height": h,
        "takenAt": "2024-06-01T12:00:00Z",
        "aspectKind": kind,
        "quality": {"sharpness": sharp},
    }


def _six_landscape_admit_window() -> tuple[list[str], dict, dict]:
    """One ladder-eligible main + five off-ladder lands ⇒ gap=inf (SUP-02)."""
    ids = [f"l{i}" for i in range(6)]
    aspects = {aid: "landscape" for aid in ids}
    assets_map = {
        "l0": _asset("l0", w=3000, h=1687, sharp=0.9, kind="landscape"),
        **{
            f"l{i}": _asset(f"l{i}", w=1900, h=1000, sharp=0.5, kind="landscape")
            for i in range(1, 6)
        },
    }
    return ids, aspects, assets_map


def _mtso_cfg(monkeypatch, *, so_enabled: bool = True, **mosaic_kw):
    base = get_config()
    mosaic = replace(
        base.mosaic,
        enabled=True,
        enabled_window_sizes=(4, 5, 6),
        min_candidate_score=0.0,
        prefer_five_slot_single_portrait=True,
        skip_dense_window_multi_portrait=True,
        density_budget=replace(
            base.mosaic.density_budget,
            enabled=True,
            window_order=(5, 4, 6),
        ),
        selection_optimization=SelectionOptimizationConfig(
            enabled=so_enabled,
            hero_six_opportunity_enabled=True,
            mixed_hero_routing_enabled=True,
        ),
        **mosaic_kw,
    )
    app = replace(base, mosaic=mosaic)
    monkeypatch.setattr("travelogue.config.get_config", lambda: app)
    return mosaic


def test_qualify_hero_six_all_landscape_admits(monkeypatch) -> None:
    cfg = _mtso_cfg(monkeypatch)
    ids, aspects, assets_map = _six_landscape_admit_window()
    st = ScreenLayoutPlannerState.from_trip_total(40)
    q = qualify_hero_six(
        ids,
        aspects,
        assets_map,
        cfg=cfg,
        layout_state=st,
        seg_cap=6,
        median_sharp=0.5,
    )
    assert q.structural
    assert q.admit


def test_qualify_hero_six_two_portraits_not_structural(monkeypatch) -> None:
    cfg = _mtso_cfg(monkeypatch)
    ids = [f"l{i}" for i in range(4)] + ["p0", "p1"]
    aspects = {**{f"l{i}": "landscape" for i in range(4)}, "p0": "portrait", "p1": "portrait"}
    assets_map = {
        **{
            f"l{i}": _asset(f"l{i}", w=3000, h=1687, sharp=0.8, kind="landscape")
            for i in range(4)
        },
        "p0": _asset("p0", w=1200, h=1800, sharp=0.8, kind="portrait"),
        "p1": _asset("p1", w=1200, h=1800, sharp=0.8, kind="portrait"),
    }
    st = ScreenLayoutPlannerState.from_trip_total(40)
    q = qualify_hero_six(
        ids,
        aspects,
        assets_map,
        cfg=cfg,
        layout_state=st,
        seg_cap=6,
        median_sharp=0.5,
    )
    assert not q.structural
    assert not q.admit
    assert q.reason == "six_hero_portrait_overflow"


def test_ac04_admit_reorders_to_six_first(monkeypatch) -> None:
    """AC-MTSO-04 · admit ⇒ effective order 6,5,4 and size=6 attempted."""
    _mtso_cfg(monkeypatch)
    ids, aspects, assets_map = _six_landscape_admit_window()
    ctx = build_chapter_plan_context(
        ids,
        aspects,
        assets=assets_map,
        trip_photo_total=40,
        include_chapter_hero=False,
        layout_state=ScreenLayoutPlannerState.from_trip_total(40),
    )
    begin_mosaic_capture()
    adv = try_mosaic_window(ctx, 0)
    _formatted, raw = drain_mosaic_capture()
    assert raw, "expected mosaic funnel logs"
    six_logs = [e for e in raw if int(e.get("windowSize") or 0) == 6]
    assert six_logs, "AC-04 requires at least one size=6 attempt"
    first = six_logs[0]
    assert first.get("admitSixHero") is True
    assert first.get("structurallyQualifiedSix") is True
    assert list(first.get("effectiveWindowOrder") or [])[:3] == [6, 5, 4]
    assert first.get("reorderReason") == "structurally_qualified_six"
    assert adv in (4, 5, 6)


def test_ac05_non_structural_no_six_protect_reorder(monkeypatch) -> None:
    """AC-MTSO-05 · non-structural: no structurally_qualified_six reorder."""
    _mtso_cfg(monkeypatch)
    # remaining>6 so exact-tail does not force size=6 first; two portraits disqualify six.
    ids = [f"l{i}" for i in range(6)] + ["p0", "p1"]
    aspects = {
        **{f"l{i}": "landscape" for i in range(6)},
        "p0": "portrait",
        "p1": "portrait",
    }
    assets_map = {
        **{
            f"l{i}": _asset(f"l{i}", w=3000, h=1687, sharp=0.8, kind="landscape")
            for i in range(6)
        },
        "p0": _asset("p0", w=1200, h=1800, sharp=0.85, kind="portrait"),
        "p1": _asset("p1", w=1200, h=1800, sharp=0.8, kind="portrait"),
    }
    # Put portraits in the first six so structural six fails at cursor 0.
    order_ids = ["p0", "p1", "l0", "l1", "l2", "l3", "l4", "l5"]
    ctx = build_chapter_plan_context(
        order_ids,
        aspects,
        assets=assets_map,
        trip_photo_total=40,
        include_chapter_hero=False,
        layout_state=ScreenLayoutPlannerState.from_trip_total(40),
    )
    begin_mosaic_capture()
    try_mosaic_window(ctx, 0)
    _formatted, raw = drain_mosaic_capture()
    assert raw
    for entry in raw:
        assert entry.get("structurallyQualifiedSix") is False
        assert entry.get("admitSixHero") is False
        assert entry.get("reorderReason") != "structurally_qualified_six"
        order = list(entry.get("effectiveWindowOrder") or [])
        if 5 in order and 6 in order:
            assert order.index(5) < order.index(6)


def test_armed_does_not_block_unrelated_cursor_landscape4(monkeypatch) -> None:
    """SUP-03 isolation · armed six opportunity is cursor-bound only."""
    _mtso_cfg(monkeypatch)
    st = ScreenLayoutPlannerState.from_trip_total(40)
    st.arm_hero_six_opportunity(0)
    assert st.hero_six_opportunity == "armed"
    assert st.hero_six_armed_cursor == 0
    # Unrelated cursor may still emit landscape-4 (no chapter-wide ban).
    assert st.can_emit_pattern("screen-landscape-4")
    st.release_hero_six_opportunity()
    assert st.hero_six_opportunity == "released"


def test_ac13_family_quota_shared(monkeypatch) -> None:
    _mtso_cfg(monkeypatch)
    st = ScreenLayoutPlannerState.from_trip_total(40)
    st.large_mosaic_max_per_template_trip = 1
    st.note_screen(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5)
    assert six_hero_family_id(PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4) == SIX_HERO_FAMILY_CANONICAL
    assert not st.can_use_large_mosaic(PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4)


def test_size6_fail_releases_opportunity(monkeypatch) -> None:
    """SUP-05 · size6 attempt fails → opportunity released."""
    from travelogue.layout_engine.mosaic import hook as hook_mod

    cfg = _mtso_cfg(monkeypatch)
    ids, aspects, assets_map = _six_landscape_admit_window()
    st = ScreenLayoutPlannerState.from_trip_total(40)
    q = qualify_hero_six(
        ids, aspects, assets_map, cfg=cfg, layout_state=st, seg_cap=6, median_sharp=0.5
    )
    assert q.admit
    ctx = build_chapter_plan_context(
        ids,
        aspects,
        assets=assets_map,
        trip_photo_total=40,
        include_chapter_hero=False,
        layout_state=st,
    )
    real_mcs = hook_mod.try_mosaic_window_mcs

    def _fail_six(ctx, start, size, cfg, *, funnel=None):
        if size == 6:
            return False
        return real_mcs(ctx, start, size, cfg, funnel=funnel)

    monkeypatch.setattr(hook_mod, "try_mosaic_window_mcs", _fail_six)
    begin_mosaic_capture()
    try_mosaic_window(ctx, 0)
    # After failed size6 with admit, must not stay armed.
    assert st.hero_six_opportunity != "armed"


def test_prc1_mixed_portrait_hard_reject_no_undo(monkeypatch) -> None:
    """AC-MTSO-07 / SUP-06 · strong portrait ⇒ hard reject, never usage-undo."""
    cfg = _mtso_cfg(monkeypatch)
    ids = ["p0"] + [f"l{i}" for i in range(4)]
    aspects = {"p0": "portrait", **{f"l{i}": "landscape" for i in range(4)}}
    assets_map = {
        "p0": _asset("p0", w=1200, h=1800, sharp=0.99, kind="portrait"),
        **{
            f"l{i}": _asset(f"l{i}", w=3000, h=1687, sharp=0.40, kind="landscape")
            for i in range(4)
        },
    }
    result = generate_window_candidates_with_rejections(
        ids,
        aspects,
        assets_map,
        cfg=cfg,
        median_sharp=0.5,
    )
    hard = [
        r
        for r in result.rejected
        if r.get("templateId") == PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND
        and r.get("reason") == "usage_rule:mixed_portrait_is_hero"
    ]
    assert hard, result.rejected
    assert PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND not in {
        c.pattern_id for c in result.candidates if c.hard_valid
    }
    assert not any(
        h.get("action") == "restore" and h.get("templateId") == PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND
        for h in result.usage_rule_hits
    )


def test_prc1_off_parent_switch_no_hard_reject(monkeypatch) -> None:
    cfg = _mtso_cfg(monkeypatch, so_enabled=False)
    ids = ["p0"] + [f"l{i}" for i in range(4)]
    aspects = {"p0": "portrait", **{f"l{i}": "landscape" for i in range(4)}}
    assets_map = {
        "p0": _asset("p0", w=1200, h=1800, sharp=0.99, kind="portrait"),
        **{
            f"l{i}": _asset(f"l{i}", w=3000, h=1687, sharp=0.40, kind="landscape")
            for i in range(4)
        },
    }
    result = generate_window_candidates_with_rejections(
        ids,
        aspects,
        assets_map,
        cfg=cfg,
        median_sharp=0.5,
    )
    assert not any(
        r.get("reason") == "usage_rule:mixed_portrait_is_hero" for r in result.rejected
    )


def test_d10_order_hero_six_reason_no_main(monkeypatch) -> None:
    _mtso_cfg(monkeypatch)
    from travelogue.layout_engine.mosaic.builders import _order_hero_six_detailed

    ids = [f"l{i}" for i in range(6)]
    aspects = {aid: "landscape" for aid in ids}
    # All off-ladder → no eligible main
    assets_map = {
        aid: _asset(aid, w=1900, h=1000, sharp=0.8, kind="landscape") for aid in ids
    }
    ordered, reason = _order_hero_six_detailed(
        ids, aspects, assets_map, median_sharp=0.5
    )
    assert ordered is None
    assert reason == "six_hero_no_main"


def test_sup07_canonical_tiebreak_on_emit() -> None:
    from travelogue.layout_engine.mosaic.candidates import ScreenCandidate
    from travelogue.layout_engine.mosaic.compose import _prefer_six_hero_canonical
    from travelogue.layout_engine.mosaic.lifecycle import SIX_HERO_FAMILY_CANONICAL

    hist = ScreenCandidate(
        pattern_id=PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
        ordered_asset_ids=["a"] * 6,
        screen={"patternId": PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4},
    )
    can = ScreenCandidate(
        pattern_id=SIX_HERO_FAMILY_CANONICAL,
        ordered_asset_ids=["a"] * 6,
        screen={"patternId": SIX_HERO_FAMILY_CANONICAL},
    )
    scored = [(hist, 0.9, [], {}), (can, 0.9, [], {})]
    out = _prefer_six_hero_canonical(scored)
    assert out[0][0].pattern_id == SIX_HERO_FAMILY_CANONICAL


def test_ac07_landscape_strong_allows_main_portrait(monkeypatch) -> None:
    """AC-MTSO-07 · weak portrait + strong lands ⇒ main-portrait may remain."""
    cfg = _mtso_cfg(monkeypatch)
    ids = ["p0"] + [f"l{i}" for i in range(4)]
    aspects = {"p0": "portrait", **{f"l{i}": "landscape" for i in range(4)}}
    assets_map = {
        "p0": _asset("p0", w=1200, h=1800, sharp=0.30, kind="portrait"),
        **{
            f"l{i}": _asset(f"l{i}", w=3000, h=1687, sharp=0.90, kind="landscape")
            for i in range(4)
        },
    }
    result = generate_window_candidates_with_rejections(
        ids,
        aspects,
        assets_map,
        cfg=cfg,
        median_sharp=0.5,
    )
    assert not any(
        r.get("reason") == "usage_rule:mixed_portrait_is_hero" for r in result.rejected
    )
    assert any(
        c.pattern_id == PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND and c.hard_valid
        for c in result.candidates
    )


def test_portrait_rescue_emits_portrait_1(monkeypatch) -> None:
    """S-MTSO-02 · after MCS fail, strong portrait cursor → screen-portrait-1."""
    from travelogue.layout_engine.mosaic import hook as hook_mod

    _mtso_cfg(monkeypatch)
    ids = ["p0"] + [f"l{i}" for i in range(4)]
    aspects = {"p0": "portrait", **{f"l{i}": "landscape" for i in range(4)}}
    assets_map = {
        "p0": _asset("p0", w=1200, h=1800, sharp=0.99, kind="portrait"),
        **{
            f"l{i}": _asset(f"l{i}", w=3000, h=1687, sharp=0.35, kind="landscape")
            for i in range(4)
        },
    }
    ctx = build_chapter_plan_context(
        ids,
        aspects,
        assets=assets_map,
        trip_photo_total=40,
        include_chapter_hero=False,
        layout_state=ScreenLayoutPlannerState.from_trip_total(40),
    )
    monkeypatch.setattr(
        hook_mod,
        "try_mosaic_window_mcs",
        lambda *a, **k: False,
    )
    begin_mosaic_capture()
    adv = try_mosaic_window(ctx, 0)
    assert adv == 1
    assert ctx.screens[0]["patternId"] == "screen-portrait-1"


def test_ac06_dense_and_large_invariants(monkeypatch) -> None:
    """AC-MTSO-06 · synthetic chapter: no adjacent dense; large chapter cap held."""
    from travelogue.layout_contract.planner_state import is_dense_collage_pattern
    from travelogue.layout_engine.planner.screen_planner_stages import (
        run_planning_loop,
    )

    _mtso_cfg(monkeypatch)
    # Two admit-friendly six packs + filler landscapes
    ids: list[str] = []
    aspects: dict[str, str] = {}
    assets_map: dict[str, dict] = {}
    for pack in range(2):
        for i in range(6):
            aid = f"p{pack}l{i}"
            ids.append(aid)
            aspects[aid] = "landscape"
            if i == 0:
                assets_map[aid] = _asset(aid, w=3000, h=1687, sharp=0.95, kind="landscape")
            else:
                assets_map[aid] = _asset(aid, w=1900, h=1000, sharp=0.4, kind="landscape")
    for i in range(4):
        aid = f"tail{i}"
        ids.append(aid)
        aspects[aid] = "landscape"
        assets_map[aid] = _asset(aid, w=3000, h=1687, sharp=0.7, kind="landscape")

    st = ScreenLayoutPlannerState.from_trip_total(80)
    ctx = build_chapter_plan_context(
        ids,
        aspects,
        assets=assets_map,
        trip_photo_total=80,
        include_chapter_hero=False,
        layout_state=st,
    )
    run_planning_loop(ctx)
    patterns = [str(s.get("patternId") or "") for s in ctx.screens]
    dense_flags = [
        is_dense_collage_pattern(pid, min_slots=st.dense_collage_min_slots)
        for pid in patterns
        if pid
    ]
    for a, b in zip(dense_flags, dense_flags[1:]):
        assert not (a and b), f"adjacent dense: {patterns}"
    assert st.large_mosaic_chapter_used <= st.large_mosaic_max_per_chapter


def test_d03_gap_branch_when_square_is_window_max(monkeypatch) -> None:
    """D-MTSO-03 · Branch B: portrait≻lands by ≥thr even if square is absolute max."""
    from travelogue.layout_engine.mosaic.hero_six import mixed_portrait_is_hero

    cfg = _mtso_cfg(monkeypatch)
    # Keep parent ON; set a known gap threshold.
    cfg = replace(
        cfg,
        selection_optimization=replace(
            cfg.selection_optimization,
            enabled=True,
            hero_gap_threshold=0.15,
        ),
    )
    ids = ["p0", "l0", "l1", "l2", "sq"]
    aspects = {
        "p0": "portrait",
        "l0": "landscape",
        "l1": "landscape",
        "l2": "landscape",
        "sq": "square",
    }
    assets_map = {
        "sq": _asset("sq", w=1600, h=1600, sharp=0.99, kind="square"),
        "p0": _asset("p0", w=1200, h=1800, sharp=0.80, kind="portrait"),
        "l0": _asset("l0", w=3000, h=1687, sharp=0.50, kind="landscape"),
        "l1": _asset("l1", w=3000, h=1687, sharp=0.45, kind="landscape"),
        "l2": _asset("l2", w=3000, h=1687, sharp=0.40, kind="landscape"),
    }
    assert mixed_portrait_is_hero(
        ids, aspects, assets_map, median_sharp=0.5, cfg=cfg
    )
    # Below threshold vs lands → no gap-branch hit (and not window max).
    assets_map["p0"] = _asset("p0", w=1200, h=1800, sharp=0.55, kind="portrait")
    assert not mixed_portrait_is_hero(
        ids, aspects, assets_map, median_sharp=0.5, cfg=cfg
    )


def test_yaml_when_not_to_use_co_tested_with_hard_reject(monkeypatch) -> None:
    """S-MTSO-02 · YAML whenNotToUse must name the hard-reject code; same fixture rejects."""
    from pathlib import Path

    import yaml

    cfg = _mtso_cfg(monkeypatch)
    yaml_path = (
        Path(__file__).resolve().parents[3]
        / "travelogue"
        / "layout_templates"
        / "templates"
        / "screen-mosaic-5-main-portrait-3land.yaml"
    )
    doc = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    when_not = str((doc.get("usage") or {}).get("whenNotToUse") or "")
    assert "mixed_portrait_is_hero" in when_not
    assert "hero_gap_threshold" in when_not

    ids = ["p0"] + [f"l{i}" for i in range(4)]
    aspects = {"p0": "portrait", **{f"l{i}": "landscape" for i in range(4)}}
    assets_map = {
        "p0": _asset("p0", w=1200, h=1800, sharp=0.99, kind="portrait"),
        **{
            f"l{i}": _asset(f"l{i}", w=3000, h=1687, sharp=0.40, kind="landscape")
            for i in range(4)
        },
    }
    result = generate_window_candidates_with_rejections(
        ids, aspects, assets_map, cfg=cfg, median_sharp=0.5
    )
    assert any(
        r.get("reason") == "usage_rule:mixed_portrait_is_hero"
        and r.get("templateId") == PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND
        for r in result.rejected
    )


def test_qualify_reason_on_segment_cap_probe(monkeypatch) -> None:
    _mtso_cfg(monkeypatch)
    ids, aspects, assets_map = _six_landscape_admit_window()
    ctx = build_chapter_plan_context(
        ids,
        aspects,
        assets=assets_map,
        trip_photo_total=40,
        include_chapter_hero=False,
        layout_state=ScreenLayoutPlannerState.from_trip_total(40),
    )
    from travelogue.layout_engine.mosaic.coarse_segments import CoarseSegment

    ctx.coarse_segments = [CoarseSegment(0, 3)]  # seg_cap < 6
    begin_mosaic_capture()
    try_mosaic_window(ctx, 0)
    _formatted, raw = drain_mosaic_capture()
    probes = [
        e
        for e in raw
        if e.get("sixHeroQualifyReason") == "six_hero_blocked:segment_cap"
        or e.get("sixHeroOutcome") == "segment_blocked"
    ]
    assert probes, raw
