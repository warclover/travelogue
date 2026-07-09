"""UR-01 / UR-02 unit tests."""

from __future__ import annotations

from dataclasses import replace

import pytest

from travelogue.config import get_config
from travelogue.config.layout import UsageRulesConfig
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_contract.usage_rules_registry import RULE_UR_01, RULE_UR_09
from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
from travelogue.layout_engine.usage_rules.context import WindowContext, main_eligible_hero_score_gap
from travelogue.layout_engine.usage_rules.evaluator import (
    evaluate_reject,
    evaluate_ur01,
    evaluate_ur02,
    evaluate_ur09,
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
    *,
    layout_state: ScreenLayoutPlannerState | None = None,
) -> WindowContext:
    aspects = {}
    for a in assets:
        from travelogue.curation.layout_planner import aspect_kind_for_asset

        aspects[a["id"]] = aspect_kind_for_asset(a)
    assets_map = {a["id"]: a for a in assets}
    return WindowContext(
        window_asset_ids=tuple(a["id"] for a in assets),
        aspects=aspects,
        assets_map=assets_map,
        layout_state=layout_state,
        median_sharp=0.5,
    )


def test_ur01_rejects_flat_hero_window():
    assets = [
        _asset(f"a{i}", w=3000, h=1687, sharp=0.80 + i * 0.01)
        for i in range(6)
    ]
    ctx = _ctx(assets)
    gap, _ = main_eligible_hero_score_gap(ctx, PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5)
    assert gap < 0.15
    cfg = UsageRulesConfig(enabled=True, hero_gap_threshold=0.15)
    reject, detail = evaluate_ur01(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5, ctx, cfg)
    assert reject
    assert "main_eligible_gap" in detail


def test_ur01_allows_clear_hero():
    assets = [_asset("hero", w=3000, h=1687, sharp=0.99)]
    assets.extend(_asset(f"p{i}", w=1200, h=1800, sharp=0.95) for i in range(5))
    ctx = _ctx(assets)
    gap, scores = main_eligible_hero_score_gap(ctx, PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5)
    assert len(scores) == 1
    assert gap == pytest.approx(float("inf"))
    cfg = UsageRulesConfig(enabled=True)
    reject, _ = evaluate_ur01(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5, ctx, cfg)
    assert not reject


def test_ur02_rejects_after_dense_screen():
    assets = [_asset(f"a{i}", w=3000, h=1687) for i in range(6)]
    st = ScreenLayoutPlannerState.from_trip_total(40)
    st.last_was_dense_collage = True
    ctx = _ctx(assets, layout_state=st)
    cfg = UsageRulesConfig(enabled=True)
    reject, detail = evaluate_ur02(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5, ctx, cfg)
    assert reject
    assert detail == "prev_dense_no_breath"


def test_evaluate_reject_disabled_rules():
    assets = [
        _asset(f"a{i}", w=3000, h=1687, sharp=0.80 + i * 0.01)
        for i in range(6)
    ]
    ctx = _ctx(assets)
    cfg = UsageRulesConfig(enabled=True, disabled_rules=(RULE_UR_01,))
    reject, rule_id, _ = evaluate_reject(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5, ctx, cfg=cfg)
    assert not reject or rule_id != RULE_UR_01


def test_evaluate_reject_respects_global_enabled_flag(monkeypatch):
    base = get_config()
    layout = replace(base.layout, usage_rules=UsageRulesConfig(enabled=False))
    monkeypatch.setattr(
        "travelogue.layout_engine.usage_rules.evaluator.get_config",
        lambda: replace(base, layout=layout),
    )
    assets = [_asset(f"a{i}", w=3000, h=1687, sharp=0.80 + i * 0.01) for i in range(6)]
    ctx = _ctx(assets)
    reject, rule_id, _ = evaluate_reject(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5, ctx)
    assert not reject
    assert rule_id is None


def test_ur09_rejects_hero_when_two_portraits():
    assets = [_asset("hero", w=3000, h=1687, sharp=0.99)]
    assets.extend(_asset(f"l{i}", w=3000, h=1687, sharp=0.70) for i in range(3))
    assets.extend(
        [
            _asset("p1", w=1200, h=1800),
            _asset("p2", w=1200, h=1800),
        ]
    )
    ctx = _ctx(assets)
    cfg = UsageRulesConfig(enabled=True)
    reject, detail = evaluate_ur09(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5, ctx, cfg)
    assert reject
    assert detail == "window_portraits=2"
    reject_all, rule_id, _ = evaluate_reject(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5, ctx, cfg=cfg)
    assert reject_all
    assert rule_id == RULE_UR_09


def test_ur09_allows_hero_with_one_portrait():
    assets = [_asset(f"l{i}", w=3000, h=1687) for i in range(5)]
    assets.append(_asset("p1", w=1200, h=1800))
    ctx = _ctx(assets)
    cfg = UsageRulesConfig(enabled=True)
    reject, _ = evaluate_ur09(PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5, ctx, cfg)
    assert not reject
