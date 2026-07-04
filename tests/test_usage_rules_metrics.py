"""URO metrics · hero_mismatch / dense_streak (P0-c)."""

from __future__ import annotations

from travelogue.config.layout import UsageRulesConfig
from travelogue.curation.mosaic.constants import (
    PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4,
    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
)
from travelogue.curation.usage_rules.metrics import (
    compute_usage_rules_metrics,
    dense_streak_violation_count,
    dense_streak_violation_rate,
    hero_mismatch_rate,
    hero_mismatch_screens,
    pattern_exposure_entropy,
    usage_rule_log_stats,
)


def _asset(aid: str, *, w: int, h: int, sharp: float = 0.8) -> dict:
    return {
        "id": aid,
        "width": w,
        "height": h,
        "takenAt": "2024-06-01T12:00:00Z",
        "quality": {"sharpness": sharp},
    }


def _hero_screen(pattern_id: str, main_id: str, tail_ids: list[str]) -> dict:
    slots = [{"assetId": main_id, "slot": 0, "role": "main"}]
    for i, tid in enumerate(tail_ids, start=1):
        slots.append({"assetId": tid, "slot": i, "role": "tile"})
    return {"patternId": pattern_id, "slots": slots}


def test_hero_mismatch_detects_flat_hero_window():
    assets = [_asset(f"a{i}", w=3000, h=1687, sharp=0.80 + i * 0.01) for i in range(6)]
    aspects = {a["id"]: "landscape" for a in assets}
    assets_map = {a["id"]: a for a in assets}
    chapters = [
        {
            "id": "ch1",
            "screens": [
                _hero_screen(
                    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
                    "a0",
                    [f"a{i}" for i in range(1, 6)],
                )
            ],
        }
    ]
    mismatches, total = hero_mismatch_screens(chapters, assets_map, aspects)
    assert total == 1
    assert mismatches == 1
    rate = hero_mismatch_rate(chapters, assets_map, aspects)
    assert rate == 1.0


def test_hero_mismatch_clear_hero_is_zero():
    assets = [_asset("hero", w=3000, h=1687, sharp=0.99)]
    assets.extend(_asset(f"t{i}", w=1200, h=1800, sharp=0.40) for i in range(5))
    aspects = {"hero": "landscape", **{f"t{i}": "portrait" for i in range(5)}}
    assets_map = {a["id"]: a for a in assets}
    chapters = [
        {
            "id": "ch1",
            "screens": [
                _hero_screen(
                    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
                    "hero",
                    [f"t{i}" for i in range(5)],
                )
            ],
        }
    ]
    rate = hero_mismatch_rate(chapters, assets_map, aspects)
    assert rate == 0.0


def test_dense_streak_violation_rate():
    chapters = [
        {
            "id": "ch1",
            "screens": [
                {"patternId": PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5, "slots": []},
                {"patternId": PATTERN_MOSAIC_5_MAIN_HERO_PLUS_4, "slots": []},
                {"patternId": "screen-landscape-1", "slots": []},
            ],
        }
    ]
    assert dense_streak_violation_count(chapters) == 1
    rate = dense_streak_violation_rate(chapters)
    assert rate == 0.5


def test_usage_rule_log_stats():
    logs = [
        {
            "usageRuleRejects": [
                {"ruleId": "UR-01", "templateId": PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5},
                {"ruleId": "UR-02", "templateId": PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5},
            ],
            "usageRuleHits": [],
        }
    ]
    stats = usage_rule_log_stats(logs)
    assert stats["rejectCount"] == 2
    assert stats["rejectByRule"]["UR-01"] == 1


def test_compute_usage_rules_metrics_block():
    assets = [_asset(f"a{i}", w=3000, h=1687, sharp=0.80 + i * 0.01) for i in range(6)]
    chapters = [
        {
            "id": "ch1",
            "screens": [
                _hero_screen(
                    PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5,
                    "a0",
                    [f"a{i}" for i in range(1, 6)],
                )
            ],
        }
    ]
    metrics = compute_usage_rules_metrics(
        chapters,
        assets,
        mosaic_logs=[{"usageRuleRejects": [{"ruleId": "UR-01", "templateId": "x"}]}],
        usage_rules_enabled=True,
    )
    assert metrics["heroMismatchRate"] == 1.0
    assert metrics["usageRules"]["enabled"] is True
    assert metrics["usageRules"]["rejectCount"] == 1
    assert pattern_exposure_entropy(chapters) == 0.0
