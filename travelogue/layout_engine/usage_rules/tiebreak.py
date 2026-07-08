"""P1 usage tie-break rules (UT-01～04 · PRD §4.2)."""

from __future__ import annotations

from typing import Any

from travelogue.config import get_config
from travelogue.config.layout import UsageRulesConfig
from travelogue.layout_engine.mosaic.candidates import ScreenCandidate
from travelogue.layout_contract.usage_context import WindowContext
from travelogue.curation.usage_rules.context import (
    main_eligible_hero_score_gap,
    portrait_is_window_hero_max,
    window_std_portrait_count,
)
from travelogue.layout_contract.usage_rules_registry import (
    HERO_LED_PATTERNS,
    RULE_UT_01,
    RULE_UT_02,
    RULE_UT_03,
    RULE_UT_04,
)

PATTERN_LANDSCAPE_6 = "screen-landscape-6"
PATTERN_LANDSCAPE_3 = "screen-landscape-3"
PATTERN_PORTRAIT_3 = "screen-portrait-3"
PATTERN_PORTRAIT_3_EDITORIAL = "screen-portrait-3-editorial"
PATTERN_PORTRAIT_1_LANDSCAPE_2 = "screen-portrait-1-landscape-2"
MOSAIC_3_ALTERNATIVES = frozenset({PATTERN_PORTRAIT_3, PATTERN_LANDSCAPE_3})
MOSAIC_5_PREFIX = "screen-mosaic-5-"

UT01_BONUS = 0.05
UT02_BONUS = 0.05
UT03_BONUS = 0.05
UT04_BONUS = 0.03
TIEBREAK_MAX_SCORE_DELTA = 0.03

ScoredRow = tuple[ScreenCandidate, float, list[str], dict[str, float]]
TiebreakHit = tuple[str, float, str, str | None]  # pattern_id, bonus, rule_id, detail


def _usage_cfg() -> UsageRulesConfig:
    return get_config().layout.usage_rules


def _row_by_pattern(scored: list[ScoredRow], pattern_id: str) -> ScoredRow | None:
    for row in scored:
        if row[0].pattern_id == pattern_id:
            return row
    return None


def _within_tiebreak_delta(a: float, b: float) -> bool:
    return abs(a - b) < TIEBREAK_MAX_SCORE_DELTA


def _window_is_1p2l(ctx: WindowContext) -> bool:
    if len(ctx.window_asset_ids) != 3:
        return False
    from travelogue.layout_engine.planner.screen_planner import _is_std_portrait_id

    portraits = sum(
        1 for aid in ctx.window_asset_ids if _is_std_portrait_id(aid, ctx.aspects)
    )
    landscapes = sum(
        1 for aid in ctx.window_asset_ids if ctx.aspects.get(aid) == "landscape"
    )
    return portraits == 1 and landscapes == 2


def _ut01_detail(*, gap: float, score_delta: float | None, mode: str) -> str:
    parts = [f"mode={mode}", f"gap={gap:.3f}"]
    if score_delta is not None:
        parts.append(f"score_delta={score_delta:.3f}")
    return ";".join(parts)


def evaluate_ut01(
    ctx: WindowContext,
    scored: list[ScoredRow],
    rejected: list[dict[str, Any]],
    *,
    cfg: UsageRulesConfig | None = None,
) -> TiebreakHit | None:
    """Return prefer hit for landscape-6 when UT-01 applies."""
    cfg = cfg or _usage_cfg()
    if len(ctx.window_asset_ids) != 6:
        return None

    landscape_row = _row_by_pattern(scored, PATTERN_LANDSCAPE_6)
    if landscape_row is None:
        return None

    landscape_score = landscape_row[1]
    hero_rows = [row for row in scored if row[0].pattern_id in HERO_LED_PATTERNS]
    hero_row = max(hero_rows, key=lambda r: r[1]) if hero_rows else None

    if hero_row is not None:
        hero_pattern = hero_row[0].pattern_id
        hero_score: float | None = hero_row[1]
    else:
        rejected_heroes = [
            str(r.get("templateId") or "")
            for r in rejected
            if str(r.get("reason") or "") == "usage_rule:UR-01"
            and str(r.get("templateId") or "") in HERO_LED_PATTERNS
        ]
        if not rejected_heroes:
            return None
        hero_pattern = rejected_heroes[0]
        hero_score = None

    gap, _ = main_eligible_hero_score_gap(ctx, hero_pattern)
    if gap >= cfg.hero_gap_prefer_threshold:
        return None

    if gap < cfg.hero_gap_threshold:
        return (
            PATTERN_LANDSCAPE_6,
            UT01_BONUS,
            RULE_UT_01,
            _ut01_detail(gap=gap, score_delta=None, mode="ur01_zone"),
        )

    if hero_score is None:
        return None
    score_delta = abs(hero_score - landscape_score)
    if score_delta >= TIEBREAK_MAX_SCORE_DELTA:
        return None
    return (
        PATTERN_LANDSCAPE_6,
        UT01_BONUS,
        RULE_UT_01,
        _ut01_detail(gap=gap, score_delta=score_delta, mode="edge"),
    )


def evaluate_ut02(
    ctx: WindowContext,
    scored: list[ScoredRow],
) -> TiebreakHit | None:
    """1P+2L · portrait hero max → prefer portrait-1-landscape-2 over mosaic-3."""
    if len(ctx.window_asset_ids) != 3:
        return None
    if not _window_is_1p2l(ctx) or not portrait_is_window_hero_max(ctx):
        return None

    target = _row_by_pattern(scored, PATTERN_PORTRAIT_1_LANDSCAPE_2)
    if target is None:
        return None

    mosaic_scores = [
        row[1] for row in scored if row[0].pattern_id in MOSAIC_3_ALTERNATIVES
    ]
    if not mosaic_scores:
        return None
    best_mosaic = max(mosaic_scores)
    score_delta = abs(target[1] - best_mosaic)
    if score_delta >= TIEBREAK_MAX_SCORE_DELTA:
        return None
    return (
        PATTERN_PORTRAIT_1_LANDSCAPE_2,
        UT02_BONUS,
        RULE_UT_02,
        f"score_delta={score_delta:.3f}",
    )


def evaluate_ut03(
    ctx: WindowContext,
    scored: list[ScoredRow],
) -> tuple[TiebreakHit, str] | None:
    """3-portrait run · web editorial → boost portrait-3 (emit as editorial)."""
    if len(ctx.window_asset_ids) != 3 or window_std_portrait_count(ctx) != 3:
        return None

    from travelogue.layout_engine.editorial.portrait_row import (
        editorial_portrait_row_config,
        editorial_scope_matches,
        is_editorial_portrait_row_enabled,
    )

    if not is_editorial_portrait_row_enabled(None):
        return None
    epr = editorial_portrait_row_config()
    if PATTERN_PORTRAIT_3 not in epr.replace_patterns:
        return None
    if not editorial_scope_matches(
        epr.scope,
        list(ctx.window_asset_ids),
        ctx.assets_map,
    ):
        return None

    target = _row_by_pattern(scored, PATTERN_PORTRAIT_3)
    if target is None:
        return None

    other_scores = [row[1] for row in scored if row[0].pattern_id != PATTERN_PORTRAIT_3]
    if not other_scores:
        return None
    best_other = max(other_scores)
    score_delta = abs(target[1] - best_other)
    if score_delta >= TIEBREAK_MAX_SCORE_DELTA:
        return None

    hit: TiebreakHit = (
        PATTERN_PORTRAIT_3,
        UT03_BONUS,
        RULE_UT_03,
        f"web_editorial;score_delta={score_delta:.3f}",
    )
    return hit, PATTERN_PORTRAIT_3_EDITORIAL


def _template_needs_hero_strong(pattern_id: str) -> bool:
    try:
        from travelogue.layout_templates.registry import get_layout_template

        tpl = get_layout_template(pattern_id)
        if tpl and tpl.raw:
            sig = (tpl.raw.get("usage") or {}).get("signals") or {}
            level = str(sig.get("needsHero") or "").lower()
            if level:
                return level == "strong"
    except Exception:
        pass
    return pattern_id in HERO_LED_PATTERNS


def _ut04_sibling_targets(
    hero_pattern_id: str,
    scored_ids: frozenset[str],
) -> frozenset[str]:
    targets: set[str] = set()
    try:
        from travelogue.layout_templates.registry import get_layout_template

        tpl = get_layout_template(hero_pattern_id)
        if tpl and tpl.raw:
            siblings = (tpl.raw.get("usage") or {}).get("siblings") or []
            for sib in siblings:
                if not isinstance(sib, dict):
                    continue
                sid = str(sib.get("id") or "")
                if sid and sid in scored_ids and sid not in HERO_LED_PATTERNS:
                    targets.add(sid)
    except Exception:
        pass

    if not targets:
        for pid in scored_ids:
            if pid.startswith(MOSAIC_5_PREFIX) and pid not in HERO_LED_PATTERNS:
                targets.add(pid)
            elif pid == PATTERN_LANDSCAPE_6:
                targets.add(pid)
    return frozenset(targets)


def evaluate_ut04(
    ctx: WindowContext,
    scored: list[ScoredRow],
    rejected: list[dict[str, Any]],
    *,
    cfg: UsageRulesConfig | None = None,
) -> list[TiebreakHit]:
    """UR-01 zone on needsHero-strong mosaic-5 hero → prefer non-hero siblings."""
    cfg = cfg or _usage_cfg()
    triggered_hero: str | None = None
    hero_score: float | None = None

    for row in scored:
        pid = row[0].pattern_id
        if pid not in HERO_LED_PATTERNS or MOSAIC_5_PREFIX not in pid:
            continue
        if not _template_needs_hero_strong(pid):
            continue
        gap, _ = main_eligible_hero_score_gap(ctx, pid)
        if gap < cfg.hero_gap_threshold:
            if triggered_hero is None or row[1] > (hero_score or -1.0):
                triggered_hero = pid
                hero_score = row[1]

    if triggered_hero is None:
        for entry in rejected:
            if str(entry.get("reason") or "") != "usage_rule:UR-01":
                continue
            pid = str(entry.get("templateId") or "")
            if pid not in HERO_LED_PATTERNS or MOSAIC_5_PREFIX not in pid:
                continue
            if not _template_needs_hero_strong(pid):
                continue
            triggered_hero = pid
            hero_score = None
            break

    if triggered_hero is None:
        return []

    scored_ids = frozenset(row[0].pattern_id for row in scored)
    targets = _ut04_sibling_targets(triggered_hero, scored_ids)
    if not targets:
        return []

    out: list[TiebreakHit] = []
    for pid in sorted(targets):
        row = _row_by_pattern(scored, pid)
        if row is None:
            continue
        if hero_score is not None and not _within_tiebreak_delta(row[1], hero_score):
            continue
        out.append(
            (
                pid,
                UT04_BONUS,
                RULE_UT_04,
                f"hero={triggered_hero};ur01_zone",
            )
        )
    return out


def apply_usage_tiebreaks(
    scored: list[ScoredRow],
    *,
    ctx: WindowContext,
    rejected: list[dict[str, Any]],
    usage_hits: list[dict[str, Any]],
) -> list[ScoredRow]:
    """Apply enabled UT rules; mutate scores and append prefer hits to ``usage_hits``."""
    cfg = _usage_cfg()
    if not cfg.enabled or not cfg.tiebreak_enabled:
        return scored

    pending: list[tuple[TiebreakHit, str | None]] = []

    ut01 = evaluate_ut01(ctx, scored, rejected, cfg=cfg)
    if ut01 is not None:
        pending.append((ut01, None))

    ut02 = evaluate_ut02(ctx, scored)
    if ut02 is not None:
        pending.append((ut02, None))

    ut03 = evaluate_ut03(ctx, scored)
    if ut03 is not None:
        pending.append(ut03)

    for hit in evaluate_ut04(ctx, scored, rejected, cfg=cfg):
        pending.append((hit, None))

    if not pending:
        return scored

    bonus_by_pattern: dict[str, tuple[float, list[str], list[str]]] = {}
    for (pattern_id, bonus, rule_id, detail), log_template_id in pending:
        tpl_id = log_template_id or pattern_id
        usage_hits.append(
            {
                "ruleId": rule_id,
                "templateId": tpl_id,
                "action": "prefer",
                **({"detail": detail} if detail else {}),
            }
        )
        prev_bonus, rules, details = bonus_by_pattern.get(pattern_id, (0.0, [], []))
        bonus_by_pattern[pattern_id] = (
            prev_bonus + bonus,
            rules + [rule_id],
            details + ([detail] if detail else []),
        )

    out: list[ScoredRow] = []
    for cand, total, reasons, pens in scored:
        entry = bonus_by_pattern.get(cand.pattern_id)
        if entry is None:
            out.append((cand, total, reasons, pens))
            continue
        bonus, rule_ids, _details = entry
        out.append((cand, total + bonus, list(reasons) + rule_ids, pens))
    return out
