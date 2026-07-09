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
    with_ctx_off = generate_window_candidates_with_rejections(
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

    def _snapshot(result):
        hard = [
            (c.pattern_id, tuple(c.ordered_asset_ids))
            for c in result.candidates
            if c.hard_valid
        ]
        hard.sort()
        return hard, list(result.rejected)

    assert _snapshot(without_ctx) == _snapshot(with_rules_disabled)
    assert _snapshot(without_ctx) != _snapshot(with_ctx_off)


def test_usage_rules_on_rejects_main_hero(monkeypatch):
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
    usage_rejects = [
        r for r in result.rejected if str(r.get("reason", "")).startswith("usage_rule:")
    ]
    assert usage_rejects
    assert any(
        r.get("templateId") == PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5 for r in usage_rejects
    )
