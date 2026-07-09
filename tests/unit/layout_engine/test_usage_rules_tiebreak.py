"""P1 tie-break · UT-01～04 (AC-URO-06)."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

import pytest

from travelogue.config import get_config
from travelogue.config.layout import UsageRulesConfig
from travelogue.layout_contract.usage_rules_registry import (
    RULE_UT_01,
    RULE_UT_02,
    RULE_UT_03,
    RULE_UT_04,
)
from travelogue.layout_engine.mosaic.candidates import ScreenCandidate
from travelogue.layout_engine.mosaic.constants import (
    PATTERN_LANDSCAPE_3,
    PATTERN_LANDSCAPE_6,
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_PORTRAIT_1_LANDSCAPE_2,
    PATTERN_PORTRAIT_3,
)
from travelogue.layout_engine.usage_rules.context import WindowContext
from travelogue.layout_engine.usage_rules.tiebreak import (
    TIEBREAK_MAX_SCORE_DELTA,
    UT01_BONUS,
    UT02_BONUS,
    UT03_BONUS,
    UT04_BONUS,
    apply_usage_tiebreaks,
    evaluate_ut01,
    evaluate_ut02,
    evaluate_ut03,
    evaluate_ut04,
)


def _row(pattern_id: str, score: float) -> tuple[ScreenCandidate, float, list[str], dict]:
    return (
        ScreenCandidate(
            pattern_id=pattern_id,
            ordered_asset_ids=["a0"],
            screen={"patternId": pattern_id, "slots": []},
            hard_valid=True,
        ),
        score,
        [],
        {},
    )


def _ctx_six() -> WindowContext:
    return WindowContext(
        window_asset_ids=tuple(f"a{i}" for i in range(6)),
        aspects={f"a{i}": "landscape" for i in range(6)},
        assets_map={
            f"a{i}": {
                "id": f"a{i}",
                "width": 3000,
                "height": 1687,
                "quality": {"sharpness": 0.8},
            }
            for i in range(6)
        },
        layout_state=None,
        median_sharp=0.5,
    )


def test_ut01_disabled_when_tiebreak_off(monkeypatch):
    cfg = UsageRulesConfig(enabled=True, tiebreak_enabled=False)
    base = get_config()
    monkeypatch.setattr(
        "travelogue.layout_engine.usage_rules.tiebreak.get_config",
        lambda: replace(base, layout=replace(base.layout, usage_rules=cfg)),
    )
    scored = [_row(PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4, 0.6), _row(PATTERN_LANDSCAPE_6, 0.58)]
    hits: list[dict] = []
    out = apply_usage_tiebreaks(
        scored,
        ctx=_ctx_six(),
        rejected=[],
        usage_hits=hits,
    )
    assert out[1][1] == pytest.approx(0.58)
    assert not hits


def test_ut01_edge_zone_prefers_landscape_six(monkeypatch):
    cfg = UsageRulesConfig(
        enabled=True,
        tiebreak_enabled=True,
        hero_gap_threshold=0.15,
        hero_gap_prefer_threshold=0.22,
    )
    ctx = _ctx_six()
    scored = [_row(PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4, 0.52), _row(PATTERN_LANDSCAPE_6, 0.50)]
    with patch(
        "travelogue.layout_engine.usage_rules.tiebreak.main_eligible_hero_score_gap",
        return_value=(0.18, (0.9, 0.72)),
    ):
        hit = evaluate_ut01(ctx, scored, [], cfg=cfg)
    assert hit is not None
    assert hit[0] == PATTERN_LANDSCAPE_6
    assert hit[1] == UT01_BONUS
    detail = hit[3]
    assert detail is not None
    assert "mode=edge" in detail
    assert abs(0.52 - 0.50) < TIEBREAK_MAX_SCORE_DELTA


def test_ut01_edge_skipped_when_scores_too_far(monkeypatch):
    cfg = UsageRulesConfig(enabled=True, tiebreak_enabled=True)
    ctx = _ctx_six()
    scored = [_row(PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4, 0.70), _row(PATTERN_LANDSCAPE_6, 0.50)]
    with patch(
        "travelogue.layout_engine.usage_rules.tiebreak.main_eligible_hero_score_gap",
        return_value=(0.18, (0.9, 0.72)),
    ):
        hit = evaluate_ut01(ctx, scored, [], cfg=cfg)
    assert hit is None


def test_ut01_ur01_zone_prefers_landscape_when_hero_rejected():
    cfg = UsageRulesConfig(
        enabled=True,
        tiebreak_enabled=True,
        hero_gap_threshold=0.15,
        hero_gap_prefer_threshold=0.22,
    )
    ctx = _ctx_six()
    scored = [_row(PATTERN_LANDSCAPE_6, 0.55)]
    rejected = [
        {
            "templateId": PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
            "reason": "usage_rule:UR-01",
            "detail": "main_eligible_gap=0.09",
        }
    ]
    with patch(
        "travelogue.layout_engine.usage_rules.tiebreak.main_eligible_hero_score_gap",
        return_value=(0.09, (0.82, 0.80)),
    ):
        hit = evaluate_ut01(ctx, scored, rejected, cfg=cfg)
    assert hit is not None
    assert hit[1] == UT01_BONUS
    detail = hit[3]
    assert detail is not None
    assert "mode=ur01_zone" in detail


def test_apply_usage_tiebreaks_logs_prefer_hit(monkeypatch):
    cfg = UsageRulesConfig(enabled=True, tiebreak_enabled=True)
    base = get_config()
    monkeypatch.setattr(
        "travelogue.layout_engine.usage_rules.tiebreak.get_config",
        lambda: replace(base, layout=replace(base.layout, usage_rules=cfg)),
    )
    scored = [_row(PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4, 0.51), _row(PATTERN_LANDSCAPE_6, 0.50)]
    hits: list[dict] = []
    with patch(
        "travelogue.layout_engine.usage_rules.tiebreak.evaluate_ut01",
        return_value=(
            PATTERN_LANDSCAPE_6,
            UT01_BONUS,
            RULE_UT_01,
            "mode=edge;gap=0.180;score_delta=0.010",
        ),
    ), patch(
        "travelogue.layout_engine.usage_rules.tiebreak.evaluate_ut02",
        return_value=None,
    ), patch(
        "travelogue.layout_engine.usage_rules.tiebreak.evaluate_ut03",
        return_value=None,
    ), patch(
        "travelogue.layout_engine.usage_rules.tiebreak.evaluate_ut04",
        return_value=[],
    ):
        out = apply_usage_tiebreaks(
            scored,
            ctx=_ctx_six(),
            rejected=[],
            usage_hits=hits,
        )
    assert out[1][1] == pytest.approx(0.50 + UT01_BONUS)
    assert RULE_UT_01 in out[1][2]
    assert len(hits) == 1
    assert hits[0]["ruleId"] == RULE_UT_01
    assert hits[0]["action"] == "prefer"
    assert hits[0]["templateId"] == PATTERN_LANDSCAPE_6


def _ctx_three_1p2l() -> WindowContext:
    return WindowContext(
        window_asset_ids=("p0", "l1", "l2"),
        aspects={"p0": "portrait", "l1": "landscape", "l2": "landscape"},
        assets_map={
            "p0": {
                "id": "p0",
                "width": 2000,
                "height": 3000,
                "quality": {"sharpness": 0.95},
            },
            "l1": {
                "id": "l1",
                "width": 3000,
                "height": 1687,
                "quality": {"sharpness": 0.70},
            },
            "l2": {
                "id": "l2",
                "width": 3000,
                "height": 1687,
                "quality": {"sharpness": 0.65},
            },
        },
        layout_state=None,
        median_sharp=0.5,
    )


def _ctx_three_portraits() -> WindowContext:
    return WindowContext(
        window_asset_ids=("p0", "p1", "p2"),
        aspects={"p0": "portrait", "p1": "portrait", "p2": "portrait"},
        assets_map={
            f"p{i}": {
                "id": f"p{i}",
                "width": 2000,
                "height": 3000,
                "quality": {"sharpness": 0.8 - i * 0.05},
            }
            for i in range(3)
        },
        layout_state=None,
        median_sharp=0.5,
    )


def test_ut02_prefers_1p2l_over_mosaic_when_close():
    ctx = _ctx_three_1p2l()
    scored = [
        _row(PATTERN_PORTRAIT_3, 0.52),
        _row(PATTERN_PORTRAIT_1_LANDSCAPE_2, 0.50),
    ]
    hit = evaluate_ut02(ctx, scored)
    assert hit is not None
    assert hit[0] == PATTERN_PORTRAIT_1_LANDSCAPE_2
    assert hit[1] == UT02_BONUS
    assert hit[2] == RULE_UT_02


def test_ut02_skipped_when_not_1p2l():
    ctx = _ctx_three_portraits()
    scored = [
        _row(PATTERN_PORTRAIT_3, 0.50),
        _row(PATTERN_PORTRAIT_1_LANDSCAPE_2, 0.52),
    ]
    assert evaluate_ut02(ctx, scored) is None


def test_ut03_prefers_editorial_path_for_three_portraits():
    ctx = _ctx_three_portraits()
    scored = [_row(PATTERN_PORTRAIT_3, 0.50), _row(PATTERN_LANDSCAPE_3, 0.52)]
    with patch(
        "travelogue.layout_engine.editorial.portrait_row.is_editorial_portrait_row_enabled",
        return_value=True,
    ), patch(
        "travelogue.layout_engine.editorial.portrait_row.editorial_portrait_row_config",
    ) as mock_cfg, patch(
        "travelogue.layout_engine.editorial.portrait_row.editorial_scope_matches",
        return_value=True,
    ):
        mock_cfg.return_value.replace_patterns = (PATTERN_PORTRAIT_3,)
        result = evaluate_ut03(ctx, scored)
    assert result is not None
    hit, log_id = result
    assert hit[0] == PATTERN_PORTRAIT_3
    assert hit[1] == UT03_BONUS
    assert hit[2] == RULE_UT_03
    assert log_id == "screen-portrait-3-editorial"


def test_ut03_skipped_when_editorial_disabled():
    ctx = _ctx_three_portraits()
    scored = [_row(PATTERN_PORTRAIT_3, 0.50), _row(PATTERN_LANDSCAPE_3, 0.52)]
    with patch(
        "travelogue.layout_engine.editorial.portrait_row.is_editorial_portrait_row_enabled",
        return_value=False,
    ):
        assert evaluate_ut03(ctx, scored) is None


def test_ut04_prefers_template_sibling_when_ur01_zone():
    cfg = UsageRulesConfig(
        enabled=True,
        tiebreak_enabled=True,
        hero_gap_threshold=0.15,
    )
    ctx = _ctx_six()
    scored = [
        _row(PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4, 0.52),
        _row(PATTERN_LANDSCAPE_6, 0.51),
    ]
    with patch(
        "travelogue.layout_engine.usage_rules.tiebreak.main_eligible_hero_score_gap",
        return_value=(0.10, (0.9, 0.80)),
    ):
        hits = evaluate_ut04(ctx, scored, [], cfg=cfg)
    assert len(hits) == 1
    assert hits[0][0] == PATTERN_LANDSCAPE_6
    assert hits[0][1] == UT04_BONUS
    assert hits[0][2] == RULE_UT_04


def test_ut04_from_rejected_hero_boosts_siblings_without_score_delta():
    cfg = UsageRulesConfig(enabled=True, tiebreak_enabled=True)
    ctx = _ctx_six()
    scored = [_row(PATTERN_LANDSCAPE_6, 0.54)]
    rejected = [
        {
            "templateId": PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
            "reason": "usage_rule:UR-01",
            "detail": "main_eligible_gap=0.08",
        }
    ]
    hits = evaluate_ut04(ctx, scored, rejected, cfg=cfg)
    assert len(hits) == 1
    assert hits[0][0] == PATTERN_LANDSCAPE_6


def test_tiebreak_off_baseline_unchanged(monkeypatch):
    """AC-URO-06 · tiebreak_enabled=false leaves scores untouched."""
    cfg = UsageRulesConfig(enabled=True, tiebreak_enabled=False)
    base = get_config()
    monkeypatch.setattr(
        "travelogue.layout_engine.usage_rules.tiebreak.get_config",
        lambda: replace(base, layout=replace(base.layout, usage_rules=cfg)),
    )
    before = [_row(PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4, 0.51), _row(PATTERN_LANDSCAPE_6, 0.50)]
    hits: list[dict] = []
    after = apply_usage_tiebreaks(
        before,
        ctx=_ctx_six(),
        rejected=[],
        usage_hits=hits,
    )
    assert [r[1] for r in before] == [r[1] for r in after]
    assert not hits
