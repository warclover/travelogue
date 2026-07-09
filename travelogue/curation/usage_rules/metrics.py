"""URO diagnostic metrics (PRD §8.2 · G-URO-06)."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping
from typing import Any

from travelogue.config.layout import UsageRulesConfig
from travelogue.curation.layout_planner import AspectKind, aspect_kind_for_asset
from travelogue.curation.longshot_filter import BREATH_PATTERN
from travelogue.curation.usage_rules.context import build_window_context
from travelogue.curation.usage_rules.density import classify_screen_density
from travelogue.curation.usage_rules.evaluator import evaluate_ur01
from travelogue.curation.usage_rules.registry import HERO_LED_PATTERNS

# BQP §2.3 · 8 本 golden dogfood（脚本会跳过本地不存在的 trip）
URO_GOLDEN_TRIP_IDS: tuple[str, ...] = (
    "demo-2025",
    "demo-80301df45c",
    "demo-1506104ebf",
    "demo-5a7c161a12",
    "demo-2019",
    "linzhi",
    "chuanzang-studio",
    "demo-151e7b488c",
    "demo-ef0cef1d1d",
)

# CI / 无 trips 目录时的 fixture 回退
URO_FIXTURE_TRIP_IDS: tuple[str, ...] = (
    "golden-mixed-scenes",
    "golden-portrait-family",
    "golden-landscape-coast",
)


def _content_screens(chapters: list[dict]) -> list[dict]:
    screens: list[dict] = []
    for ch in chapters:
        for screen in ch.get("screens") or []:
            pid = screen.get("patternId")
            if pid and pid != BREATH_PATTERN:
                screens.append(screen)
    return screens


def _screen_asset_ids(screen: dict) -> list[str]:
    return [
        str(slot.get("assetId"))
        for slot in (screen.get("slots") or [])
        if slot.get("assetId")
    ]


def hero_mismatch_screens(
    chapters: list[dict],
    assets_by_id: Mapping[str, dict],
    aspects: Mapping[str, AspectKind],
    *,
    cfg: UsageRulesConfig | None = None,
) -> tuple[int, int]:
    """(mismatch_count, hero_led_screen_count) · post-hoc UR-01 on emitted screens."""
    rule_cfg = cfg or UsageRulesConfig(enabled=True)
    mismatches = 0
    hero_total = 0
    for screen in _content_screens(chapters):
        pid = str(screen.get("patternId") or "")
        if pid not in HERO_LED_PATTERNS:
            continue
        aids = _screen_asset_ids(screen)
        if not aids:
            continue
        hero_total += 1
        ctx = build_window_context(
            aids,
            dict(aspects),
            dict(assets_by_id),
        )
        reject, _ = evaluate_ur01(pid, ctx, rule_cfg)
        if reject:
            mismatches += 1
    return mismatches, hero_total


def hero_mismatch_rate(
    chapters: list[dict],
    assets_by_id: Mapping[str, dict],
    aspects: Mapping[str, AspectKind],
    *,
    cfg: UsageRulesConfig | None = None,
) -> float | None:
    mismatches, total = hero_mismatch_screens(
        chapters, assets_by_id, aspects, cfg=cfg
    )
    if total == 0:
        return None
    return round(mismatches / total, 6)


def dense_streak_violation_count(chapters: list[dict]) -> int:
    """Consecutive dense→dense screen pairs without breath-pause between."""
    screens = _content_screens(chapters)
    violations = 0
    for prev, nxt in zip(screens, screens[1:]):
        p0 = str(prev.get("patternId") or "")
        p1 = str(nxt.get("patternId") or "")
        if classify_screen_density(p0) == "dense" and classify_screen_density(p1) == "dense":
            violations += 1
    return violations


def dense_streak_violation_rate(chapters: list[dict]) -> float | None:
    screens = _content_screens(chapters)
    if len(screens) < 2:
        return None
    return round(dense_streak_violation_count(chapters) / (len(screens) - 1), 6)


def pattern_exposure_entropy(chapters: list[dict]) -> float | None:
    """Normalized Shannon entropy of patternId distribution (0–1)."""
    pids = [str(s.get("patternId")) for s in _content_screens(chapters) if s.get("patternId")]
    if not pids:
        return None
    counts = Counter(pids)
    total = sum(counts.values())
    ent = -sum((c / total) * math.log(c / total) for c in counts.values())
    max_ent = math.log(len(counts)) if len(counts) > 1 else 1.0
    return round(ent / max_ent, 6) if max_ent else 0.0


def usage_rule_log_stats(mosaic_logs: list[dict] | None) -> dict[str, Any]:
    logs = mosaic_logs or []
    reject_count = 0
    hit_count = 0
    rule_counts: Counter[str] = Counter()
    hit_by_rule: Counter[str] = Counter()
    for lg in logs:
        for row in lg.get("usageRuleRejects") or []:
            reject_count += 1
            rid = str(row.get("ruleId") or "")
            if rid:
                rule_counts[rid] += 1
        for row in lg.get("usageRuleHits") or []:
            hit_count += 1
            rid = str(row.get("ruleId") or "")
            if rid:
                hit_by_rule[rid] += 1
    return {
        "rejectCount": reject_count,
        "hitCount": hit_count,
        "rejectByRule": dict(sorted(rule_counts.items())),
        "hitByRule": dict(sorted(hit_by_rule.items())),
    }


def compute_usage_rules_metrics(
    chapters: list[dict],
    assets: list[dict] | None = None,
    *,
    mosaic_logs: list[dict] | None = None,
    usage_rules_enabled: bool | None = None,
    hero_gap_threshold: float = 0.15,
) -> dict[str, Any]:
    """Diagnostic block for layoutMetrics · usageRules."""
    out: dict[str, Any] = {}
    assets_by_id = {a["id"]: a for a in (assets or []) if a.get("id")}
    if not assets_by_id:
        return out

    aspects: dict[str, AspectKind] = {
        aid: aspect_kind_for_asset(asset)
        for aid, asset in assets_by_id.items()
    }
    rule_cfg = UsageRulesConfig(
        enabled=True,
        hero_gap_threshold=hero_gap_threshold,
    )
    mismatch, hero_total = hero_mismatch_screens(
        chapters, assets_by_id, aspects, cfg=rule_cfg
    )
    mismatch_rate = hero_mismatch_rate(
        chapters, assets_by_id, aspects, cfg=rule_cfg
    )
    dense_rate = dense_streak_violation_rate(chapters)
    entropy = pattern_exposure_entropy(chapters)

    if mismatch_rate is not None:
        out["heroMismatchRate"] = mismatch_rate
        out["layout.usage_rules.hero_mismatch_rate"] = mismatch_rate
    out["heroMismatchScreens"] = mismatch
    out["heroLedScreenCount"] = hero_total
    if dense_rate is not None:
        out["denseStreakViolationRate"] = dense_rate
        out["layout.usage_rules.dense_streak_violation_rate"] = dense_rate
    out["denseStreakViolations"] = dense_streak_violation_count(chapters)
    if entropy is not None:
        out["patternExposureEntropy"] = entropy
        out["layout.usage_rules.pattern_exposure_entropy"] = entropy

    log_stats = usage_rule_log_stats(mosaic_logs)
    usage_block: dict[str, Any] = {
        "enabled": usage_rules_enabled,
        "rejectCount": log_stats["rejectCount"],
        "hitCount": log_stats["hitCount"],
        "heroMismatchScreens": mismatch,
        "denseStreakViolations": out["denseStreakViolations"],
    }
    if log_stats["rejectByRule"]:
        usage_block["rejectByRule"] = log_stats["rejectByRule"]
    out["usageRules"] = usage_block
    if log_stats["rejectCount"] and _mosaic_window_count(mosaic_logs):
        out["usageRuleRejectRate"] = round(
            log_stats["rejectCount"] / _mosaic_window_count(mosaic_logs),
            6,
        )
    return out


def _mosaic_window_count(mosaic_logs: list[dict] | None) -> int:
    return len(mosaic_logs or [])


def compare_usage_rules_metrics(
    baseline: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    """Relative delta for off→on report rows."""

    def _delta(key: str) -> float | None:
        b = baseline.get(key)
        c = candidate.get(key)
        if b is None or c is None:
            return None
        try:
            return round(float(c) - float(b), 6)
        except (TypeError, ValueError):
            return None

    return {
        "heroMismatchRateDelta": _delta("heroMismatchRate"),
        "denseStreakViolationRateDelta": _delta("denseStreakViolationRate"),
        "patternExposureEntropyDelta": _delta("patternExposureEntropy"),
        "screenCountDelta": _delta("screenCount"),
    }
