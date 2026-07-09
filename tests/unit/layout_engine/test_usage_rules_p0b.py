"""P0-b usage rules · UR-03～UR-06 + empty-candidate fallback."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import MosaicConfig, get_config
from travelogue.config.layout import UsageRulesConfig
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_contract.usage_context import WindowContext, build_window_context
from travelogue.layout_contract.usage_rules_registry import (
    RULE_UR_05,
    RULE_UR_09,
    USAGE_RULE_UNDO_ORDER,
)
from travelogue.layout_engine.mosaic.candidates import generate_window_candidates_with_rejections
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_LANDSCAPE_9,
    PATTERN_MOSAIC_5_HERO_3_2_PLUS_4,
    PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND,
)
from travelogue.layout_engine.mosaic.runtime import (
    reset_mosaic_config_override,
    set_mosaic_config_override,
)
from travelogue.layout_engine.planner.screen_planner import _can_mosaic_5_main_portrait_3land
from travelogue.layout_engine.usage_rules.evaluator import (
    evaluate_reject,
    evaluate_ur03,
    evaluate_ur04,
    evaluate_ur05,
    evaluate_ur06,
)


def _asset(aid: str, *, w: int, h: int, sharp: float = 0.8) -> dict:
    return {
        "id": aid,
        "width": w,
        "height": h,
        "takenAt": "2024-06-01T12:00:00Z",
        "quality": {"sharpness": sharp},
    }


def _ctx(
    assets: list[dict],
    aspects: dict[str, str],
    *,
    layout_state: ScreenLayoutPlannerState | None = None,
) -> WindowContext:
    assets_map = {a["id"]: a for a in assets}
    return WindowContext(
        window_asset_ids=tuple(a["id"] for a in assets),
        aspects=aspects,
        assets_map=assets_map,
        layout_state=layout_state,
        median_sharp=0.5,
    )


def test_ur03_rejects_wide_main_in_hero_32():
    aspects = {f"a{i}": "landscape" for i in range(5)}
    assets = [_asset(f"a{i}", w=2800, h=1000, sharp=0.8) for i in range(5)]
    ctx = _ctx(assets, aspects)
    screen = {
        "patternId": PATTERN_MOSAIC_5_HERO_3_2_PLUS_4,
        "slots": [
            {"assetId": "a0", "slot": 0, "role": "main"},
            {"assetId": "a1", "slot": 1, "role": "landscape"},
        ],
    }
    cfg = UsageRulesConfig(enabled=True)
    reject, detail = evaluate_ur03(PATTERN_MOSAIC_5_HERO_3_2_PLUS_4, ctx, cfg, screen=screen)
    assert reject
    assert "main_display_ar" in detail


def test_ur04_rejects_portrait_hero_max():
    aspects = {
        "p0": "portrait",
        **{f"l{i}": "landscape" for i in range(4)},
    }
    assets = [
        _asset("p0", w=1200, h=1800, sharp=0.99),
        *[_asset(f"l{i}", w=3000, h=1687, sharp=0.40) for i in range(4)],
    ]
    ctx = _ctx(assets, aspects)
    cfg = UsageRulesConfig(enabled=True)
    reject, detail = evaluate_ur04(PATTERN_MOSAIC_5_MAIN_PORTRAIT_3LAND, ctx, cfg)
    assert reject
    assert detail == "portrait_hero_is_max"


def test_ur05_rejects_nine_grid_after_dense():
    aspects = {f"a{i}": "landscape" for i in range(9)}
    assets = [_asset(f"a{i}", w=3000, h=1687) for i in range(9)]
    st = ScreenLayoutPlannerState.from_trip_total(40)
    st.last_was_dense_collage = True
    ctx = _ctx(assets, aspects, layout_state=st)
    cfg = UsageRulesConfig(enabled=True)
    reject, detail = evaluate_ur05(PATTERN_LANDSCAPE_9, ctx, cfg)
    assert reject
    assert detail == "prev_dense_no_breath"


def test_ur06_rejects_second_editorial_in_chapter():
    aspects = {f"a{i}": "landscape" for i in range(4)}
    aspects["p0"] = "portrait"
    aspects["p1"] = "portrait"
    assets = [
        _asset("p0", w=1200, h=1800),
        _asset("p1", w=1200, h=1800),
        _asset("l0", w=3000, h=1687),
        _asset("l1", w=3000, h=1687),
    ]
    st = ScreenLayoutPlannerState.from_trip_total(40)
    st.editorial_composite_chapter_used = 1
    ctx = _ctx(assets, aspects, layout_state=st)
    cfg = UsageRulesConfig(enabled=True)
    reject, detail = evaluate_ur06("screen-editorial-4mix", ctx, cfg)
    assert reject
    assert detail == "editorial_chapter_quota"


def test_can_mosaic_main_portrait_blocked_by_ur04(monkeypatch):
    aspects = {
        "p0": "portrait",
        **{f"l{i}": "landscape" for i in range(4)},
    }
    assets_map = {
        "p0": _asset("p0", w=1200, h=1800, sharp=0.99),
        **{f"l{i}": _asset(f"l{i}", w=3000, h=1687, sharp=0.40) for i in range(4)},
    }
    window = ["p0", "l0", "l1", "l2", "l3"]
    base = get_config()
    layout = replace(base.layout, usage_rules=UsageRulesConfig(enabled=True))
    patched = replace(base, layout=layout)
    monkeypatch.setattr("travelogue.config.get_config", lambda: patched)
    monkeypatch.setattr(
        "travelogue.layout_engine.usage_rules.evaluator.get_config",
        lambda: patched,
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.usage_rules.evaluator.get_config",
        lambda: patched,
    )
    ordered = _can_mosaic_5_main_portrait_3land(
        window,
        aspects,
        assets_map,
        burst_seconds=3600,
        median_sharp=0.5,
    )
    assert ordered is None


def test_usage_empty_fallback_restores_weakest_rule(monkeypatch):
    aspects = {f"a{i}": "landscape" for i in range(9)}
    assets_map = {f"a{i}": _asset(f"a{i}", w=3000, h=1687) for i in range(9)}
    ids = [f"a{i}" for i in range(9)]
    cfg = MosaicConfig()
    st = ScreenLayoutPlannerState.from_trip_total(40)
    st.last_was_dense_collage = True
    ctx = build_window_context(ids, aspects, assets_map, layout_state=st, median_sharp=0.5)
    base = get_config()
    layout = replace(base.layout, usage_rules=UsageRulesConfig(enabled=True))
    monkeypatch.setattr(
        "travelogue.layout_engine.usage_rules.evaluator.get_config",
        lambda: replace(base, layout=layout),
    )
    result = generate_window_candidates_with_rejections(
        ids, aspects, assets_map, cfg=cfg, window_ctx=ctx
    )
    hard = [c for c in result.candidates if c.hard_valid]
    assert hard
    assert any(c.pattern_id == PATTERN_LANDSCAPE_9 for c in hard)
    usage_rejects = [
        r for r in result.rejected if str(r.get("reason", "")).startswith("usage_rule:")
    ]
    assert not any(
        r.get("templateId") == PATTERN_LANDSCAPE_9 and r.get("reason") == f"usage_rule:{RULE_UR_05}"
        for r in usage_rejects
    )
    restores = [h for h in result.usage_rule_hits if h.get("action") == "restore"]
    if restores:
        assert any(h.get("ruleId") == RULE_UR_05 for h in restores)


def test_ur03_sole_candidate_restored_by_empty_fallback(monkeypatch):
    """UR-03 rejects hero-3-2, but §3.6 fallback restores when it is the only option."""
    aspects = {f"a{i}": "landscape" for i in range(5)}
    assets_map = {f"a{i}": _asset(f"a{i}", w=3000, h=1687) for i in range(5)}
    ids = [f"a{i}" for i in range(5)]
    cfg = replace(MosaicConfig(), hero_weighted_geometry_guard=False)
    set_mosaic_config_override(cfg)
    base = get_config()
    layout = replace(base.layout, usage_rules=UsageRulesConfig(enabled=True))
    patched = replace(base, layout=layout)
    try:
        monkeypatch.setattr(
            "travelogue.layout_engine.usage_rules.evaluator.get_config",
            lambda: patched,
        )
        ctx = build_window_context(ids, aspects, assets_map, median_sharp=0.5)
        screen = {
            "patternId": PATTERN_MOSAIC_5_HERO_3_2_PLUS_4,
            "slots": [{"assetId": "a0", "slot": 0, "role": "main"}],
        }
        reject, rule_id, _ = evaluate_reject(
            PATTERN_MOSAIC_5_HERO_3_2_PLUS_4,
            ctx,
            cfg=UsageRulesConfig(enabled=True),
            screen=screen,
        )
        assert reject and rule_id == "UR-03"

        result = generate_window_candidates_with_rejections(
            ids, aspects, assets_map, cfg=cfg, window_ctx=ctx
        )
        hero = next(
            (
                c
                for c in result.candidates
                if c.pattern_id == PATTERN_MOSAIC_5_HERO_3_2_PLUS_4 and c.hard_valid
            ),
            None,
        )
        assert hero is not None
    finally:
        reset_mosaic_config_override()


def test_ur09_is_weakest_undo_rule():
    """§3.6 · UR-09 is evaluated first (strongest) and undone last."""
    assert RULE_UR_09 in USAGE_RULE_UNDO_ORDER
    assert USAGE_RULE_UNDO_ORDER[-1] == RULE_UR_09


def test_ur09_empty_fallback_restores_when_sole_deferral():
    """When UR-09 is the only usage deferral, §3.6 undo must restore candidates."""
    from travelogue.layout_engine.mosaic.candidates import (
        ScreenCandidate,
        _restore_if_usage_emptied_candidates,
    )
    from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4

    cand = ScreenCandidate(
        pattern_id=PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
        ordered_asset_ids=["a0", "a1", "a2", "a3", "a4"],
        screen={"patternId": PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4, "slots": []},
        hard_valid=True,
    )
    out: list[ScreenCandidate] = []
    rejected = [
        {"templateId": cand.pattern_id, "reason": f"usage_rule:{RULE_UR_09}"},
    ]
    deferred = [(cand, RULE_UR_09)]
    hits: list[dict] = []
    _restore_if_usage_emptied_candidates(out, rejected, deferred, hits)
    assert len(out) == 1
    assert out[0].hard_valid
    assert hits == [
        {
            "ruleId": RULE_UR_09,
            "templateId": PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
            "action": "restore",
        }
    ]
    assert not any(
        r.get("reason") == f"usage_rule:{RULE_UR_09}"
        and r.get("templateId") == PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4
        for r in rejected
    )
