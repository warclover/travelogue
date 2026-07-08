"""AC-URO-09 · legacy path must not emit usage-rejected patterns."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

from travelogue.config import get_config
from travelogue.config.layout import UsageRulesConfig
from travelogue.curation.mosaic.legacy import append_legacy_window
from travelogue.curation.screen_planner_stages import ChapterPlanContext


def _minimal_ctx(**overrides) -> ChapterPlanContext:
    base = ChapterPlanContext(
        chapter_id="ch-01",
        aspects={},
        assets_map={},
        mix_gap=12.0,
        med_sharp=0.5,
        trip_total=40,
        burst_seconds=12.0,
        burst_groups={},
        layout_state=None,
        enable_mosaic=True,
        enable_portrait_grid8=False,
        enable_food_grid=False,
        mundane_grid_buckets=(),
        use_portrait_grid8=False,
        max_per_screen=9,
        portrait_heavy=False,
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def test_legacy_blocked_when_usage_reject(monkeypatch):
    screen = {"patternId": "screen-mosaic-5-main-portrait-3land", "slots": []}
    ctx = _minimal_ctx()

    base_cfg = get_config()
    layout = replace(base_cfg.layout, usage_rules=UsageRulesConfig(enabled=True))
    monkeypatch.setattr(
        "travelogue.curation.usage_rules.evaluator.get_config",
        lambda: replace(base_cfg, layout=layout),
    )

    with patch(
        "travelogue.curation.mosaic.legacy.build_legacy_screen",
        return_value=screen,
    ), patch(
        "travelogue.curation.usage_rules.evaluator.evaluate_reject",
        return_value=(True, "UR-04", "portrait_hero_is_max"),
    ), patch(
        "travelogue.curation.mosaic.slot_geometry.screen_slots_geometry_ok",
        return_value=True,
    ), patch(
        "travelogue.curation.mosaic.lte_adapter.mosaic_pattern_disabled",
        return_value=False,
    ), patch(
        "travelogue.curation.mosaic.lte_adapter.read_templates_from_lte",
        return_value=False,
    ), patch(
        "travelogue.curation.screen_planner_stages.append_screen",
    ) as append_mock:
        ok = append_legacy_window(ctx, ["a", "b", "c", "d", "e"], 5)

    assert ok is False
    append_mock.assert_not_called()
