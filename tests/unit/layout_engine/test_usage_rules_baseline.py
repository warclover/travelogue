"""AC-URO-01 · usage_rules.enabled=false must not change MCS candidates."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import MosaicConfig, get_config
from travelogue.config.layout import UsageRulesConfig
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_contract.usage_context import build_window_context
from travelogue.layout_engine.mosaic.candidates import generate_window_candidates_with_rejections
from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5


def _asset(aid: str, *, w: int, h: int, sharp: float = 0.8) -> dict:
    return {
        "id": aid,
        "width": w,
        "height": h,
        "takenAt": "2024-06-01T12:00:00Z",
        "quality": {"sharpness": sharp},
    }


def _six_landscape_window():
    aspects = {f"a{i}": "landscape" for i in range(6)}
    assets_map = {
        f"a{i}": _asset(f"a{i}", w=3000, h=1687, sharp=0.75 + i * 0.03)
        for i in range(6)
    }
    ids = [f"a{i}" for i in range(6)]
    return ids, aspects, assets_map


def test_usage_rules_off_matches_no_ctx(monkeypatch):
    ids, aspects, assets_map = _six_landscape_window()
    cfg = MosaicConfig()
    st = ScreenLayoutPlannerState.from_trip_total(40)
    st.last_was_dense_collage = True

    without_ctx = generate_window_candidates_with_rejections(
        ids, aspects, assets_map, cfg=cfg
    )
    base = get_config()
    layout = replace(
        base.layout,
        usage_rules=UsageRulesConfig(enabled=True, hero_gap_threshold=0.15),
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.usage_rules.evaluator.get_config",
        lambda: replace(base, layout=layout),
    )
    ctx = build_window_context(
        ids,
        aspects,
        assets_map,
        layout_state=st,
        median_sharp=0.5,
    )
    with_ctx_on = generate_window_candidates_with_rejections(
        ids,
        aspects,
        assets_map,
        cfg=cfg,
        window_ctx=ctx,
    )
    layout_disabled = replace(
        base.layout,
        usage_rules=UsageRulesConfig(enabled=False),
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.usage_rules.evaluator.get_config",
        lambda: replace(base, layout=layout_disabled),
    )
    with_rules_disabled = generate_window_candidates_with_rejections(
        ids,
        aspects,
        assets_map,
        cfg=cfg,
        window_ctx=ctx,
    )

    def _hard(result):
        hard = [
            (c.pattern_id, tuple(c.ordered_asset_ids))
            for c in result.candidates
            if c.hard_valid
        ]
        hard.sort()
        return hard

    # enabled=false must match no-ctx hard set (AC-URO-01).
    assert _hard(without_ctx) == _hard(with_rules_disabled)
    # LTN C3 · size=6 仅剩 hero SKUs；UR 拒尽后 empty-fallback restore，
    # hard 集可与无 ctx 相同，但必须留下 restore 痕迹。
    assert with_ctx_on.usage_rule_hits
    assert any(h.get("action") == "restore" for h in with_ctx_on.usage_rule_hits)


def test_usage_rules_on_restores_main_hero_when_only_heroes(monkeypatch):
    """LTN C3 · 平铺 6 剪枝后，size=6 仅 hero 候选；UR-01 拒尽 → restore。"""
    ids, aspects, assets_map = _six_landscape_window()
    cfg = MosaicConfig()
    base = get_config()
    layout = replace(
        base.layout,
        usage_rules=UsageRulesConfig(enabled=True, hero_gap_threshold=0.15),
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.usage_rules.evaluator.get_config",
        lambda: replace(base, layout=layout),
    )
    ctx = build_window_context(ids, aspects, assets_map, median_sharp=0.5)
    result = generate_window_candidates_with_rejections(
        ids, aspects, assets_map, cfg=cfg, window_ctx=ctx
    )
    hard_ids = {c.pattern_id for c in result.candidates if c.hard_valid}
    assert PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5 in hard_ids
    restores = [h for h in result.usage_rule_hits if h.get("action") == "restore"]
    assert any(
        h.get("templateId") == PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5 for h in restores
    )
