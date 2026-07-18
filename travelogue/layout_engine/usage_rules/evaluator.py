"""Deterministic usage rule evaluation (P0-a/b · UR-01～UR-06, UR-09)."""

from __future__ import annotations

from typing import Any

from travelogue.config import get_config
from travelogue.config.layout import UsageRulesConfig
from travelogue.layout_contract.usage_context import WindowContext
from travelogue.layout_contract.usage_rules_registry import (
    HERO_32_PATTERN,
    HERO_32_WIDE_AR_THRESHOLD,
    HERO_LED_DENSE_PATTERNS,
    HERO_LED_PATTERNS,
    MAIN_PORTRAIT_3LAND_PATTERN,
    NINE_GRID_DENSE_PATTERNS,
    RULE_UR_01,
    RULE_UR_02,
    RULE_UR_03,
    RULE_UR_04,
    RULE_UR_05,
    RULE_UR_06,
    RULE_UR_09,
)
from travelogue.layout_engine.usage_rules.context import (
    main_eligible_hero_score_gap,
    portrait_is_window_hero_max,
    window_std_portrait_count,
)


def _usage_rules_config() -> UsageRulesConfig:
    return get_config().layout.usage_rules


def _rule_disabled(rule_id: str, cfg: UsageRulesConfig) -> bool:
    return rule_id in set(cfg.disabled_rules)


def evaluate_ur01(pattern_id: str, ctx: WindowContext, cfg: UsageRulesConfig) -> tuple[bool, str]:
    if pattern_id not in HERO_LED_PATTERNS:
        return False, ""
    gap, _ = main_eligible_hero_score_gap(ctx, pattern_id)
    if gap >= cfg.hero_gap_threshold:
        return False, ""
    return True, f"main_eligible_gap={gap:.3f}"


def evaluate_ur02(pattern_id: str, ctx: WindowContext, cfg: UsageRulesConfig) -> tuple[bool, str]:
    if pattern_id not in HERO_LED_DENSE_PATTERNS:
        return False, ""
    return _evaluate_dense_breath(pattern_id, ctx)


def evaluate_ur03(
    pattern_id: str,
    ctx: WindowContext,
    cfg: UsageRulesConfig,
    *,
    screen: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    if pattern_id != HERO_32_PATTERN or screen is None:
        return False, ""
    main_aid: str | None = None
    for slot in screen.get("slots") or []:
        if slot.get("role") == "main":
            main_aid = str(slot.get("assetId") or "") or None
            break
    if not main_aid:
        slots = screen.get("slots") or []
        if slots:
            main_aid = str(slots[0].get("assetId") or "") or None
    if not main_aid:
        return False, ""
    from travelogue.layout_contract.asset_geometry import asset_native_ar

    ar = asset_native_ar(ctx.assets_map.get(main_aid) or {})
    if ar is not None and ar > HERO_32_WIDE_AR_THRESHOLD:
        return True, f"main_display_ar={ar:.2f}"
    return False, ""


def evaluate_ur04(pattern_id: str, ctx: WindowContext, cfg: UsageRulesConfig) -> tuple[bool, str]:
    if pattern_id != MAIN_PORTRAIT_3LAND_PATTERN:
        return False, ""
    if portrait_is_window_hero_max(ctx):
        return True, "portrait_hero_is_max"
    return False, ""


def evaluate_ur05(pattern_id: str, ctx: WindowContext, cfg: UsageRulesConfig) -> tuple[bool, str]:
    if pattern_id not in NINE_GRID_DENSE_PATTERNS:
        return False, ""
    return _evaluate_dense_breath(pattern_id, ctx)


def evaluate_ur06(pattern_id: str, ctx: WindowContext, cfg: UsageRulesConfig) -> tuple[bool, str]:
    from travelogue.layout_engine.editorial.four_mix import is_editorial_composite_pattern

    if not is_editorial_composite_pattern(pattern_id):
        return False, ""
    st = ctx.layout_state
    if st is None:
        return False, ""
    if not st.can_emit_editorial_composite():
        return True, "editorial_chapter_quota"
    return False, ""


def evaluate_ur09(pattern_id: str, ctx: WindowContext, cfg: UsageRulesConfig) -> tuple[bool, str]:
    if pattern_id not in HERO_LED_PATTERNS:
        return False, ""
    n = window_std_portrait_count(ctx)
    if n >= 2:
        return True, f"window_portraits={n}"
    return False, ""


def _evaluate_dense_breath(pattern_id: str, ctx: WindowContext) -> tuple[bool, str]:
    st = ctx.layout_state
    if st is None:
        return False, ""
    if not st.can_use_dense_collage(pattern_id):
        if st.last_was_dense_collage:
            return True, "prev_dense_no_breath"
        return True, "dense_quota_or_budget"
    return False, ""


def evaluate_reject(
    pattern_id: str,
    ctx: WindowContext | None,
    *,
    cfg: UsageRulesConfig | None = None,
    screen: dict[str, Any] | None = None,
) -> tuple[bool, str | None, str | None]:
    """
    Return (should_reject, rule_id, detail).

    When usage rules are disabled or ctx is None, never reject.
    """
    cfg = cfg or _usage_rules_config()
    if not cfg.enabled or ctx is None:
        return False, None, None

    checks: list[tuple[str, tuple[bool, str]]] = []
    if not _rule_disabled(RULE_UR_09, cfg):
        checks.append((RULE_UR_09, evaluate_ur09(pattern_id, ctx, cfg)))
    if not _rule_disabled(RULE_UR_01, cfg):
        checks.append((RULE_UR_01, evaluate_ur01(pattern_id, ctx, cfg)))
    if not _rule_disabled(RULE_UR_02, cfg):
        checks.append((RULE_UR_02, evaluate_ur02(pattern_id, ctx, cfg)))
    if not _rule_disabled(RULE_UR_03, cfg):
        checks.append((RULE_UR_03, evaluate_ur03(pattern_id, ctx, cfg, screen=screen)))
    if not _rule_disabled(RULE_UR_04, cfg):
        checks.append((RULE_UR_04, evaluate_ur04(pattern_id, ctx, cfg)))
    if not _rule_disabled(RULE_UR_05, cfg):
        checks.append((RULE_UR_05, evaluate_ur05(pattern_id, ctx, cfg)))
    if not _rule_disabled(RULE_UR_06, cfg):
        checks.append((RULE_UR_06, evaluate_ur06(pattern_id, ctx, cfg)))

    for rule_id, (reject, detail) in checks:
        if reject:
            return True, rule_id, detail or None
    return False, None, None
