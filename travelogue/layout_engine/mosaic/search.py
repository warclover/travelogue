"""Segment beam search (M5' · Phase 15 MCS import surface)."""

from __future__ import annotations

import copy
import logging
from dataclasses import replace

from travelogue.config import AppConfig
from travelogue.layout_contract.decision_log import LayoutDecisionLog
from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_contract.rhythm import (
    PORTRAIT_PAIR_PATTERN,
    PORTRAIT_SINGLE_PATTERNS,
    RhythmRules,
)
from travelogue.layout_contract.scoring import (
    IncrementalScoreState,
    ScoringWeights,
)
from travelogue.layout_contract.search_budget import SearchBudget
from travelogue.layout_engine.planner.beam_scoring import score_screen_plan

_log = logging.getLogger(__name__)


def _late_chapter_beam_adjustment(
    plan: list[dict],
    rhythm: RhythmRules,
    chapter_index: int,
) -> float:
    """Bonus/penalty for late-chapter beam picks favouring portrait-2 over singles."""
    late = rhythm.late_chapter_pairing
    if not late.is_late_chapter(chapter_index):
        return 0.0
    delta = 0.0
    for sc in plan:
        pid = str(sc.get("patternId") or "")
        if pid in PORTRAIT_SINGLE_PATTERNS:
            delta -= late.beam_portrait_single_penalty
        elif pid == PORTRAIT_PAIR_PATTERN:
            delta += late.beam_portrait_pair_bonus
    return delta


def _arc_scoring_active(arc_mode: str) -> bool:
    return arc_mode in ("v2_adaptive", "v2_five_beat")


def _shallow_copy_chapters(chapters: list[dict]) -> list[dict]:
    out: list[dict] = []
    for ch in chapters:
        nc = dict(ch)
        if "screens" in ch:
            nc["screens"] = list(ch.get("screens") or [])
        if "items" in ch:
            nc["items"] = [dict(it) if isinstance(it, dict) else it for it in (ch.get("items") or [])]
        if "curation" in ch and isinstance(ch.get("curation"), dict):
            nc["curation"] = dict(ch["curation"])
        out.append(nc)
    return out


def _screens_signature(chapters: list[dict]) -> list[list[str]]:
    sig: list[list[str]] = []
    for ch in chapters:
        sig.append([s.get("patternId", "") for s in (ch.get("screens") or [])])
    return sig


def _collect_asset_ids_from_chapter(ch: dict) -> list[str]:
    from travelogue.layout_contract.chapter_items import collect_screen_asset_ids, item_asset_ids

    aids = collect_screen_asset_ids(ch)
    if aids:
        return aids
    out: list[str] = []
    for it in ch.get("items") or []:
        for aid in item_asset_ids(it):
            if aid not in out:
                out.append(aid)
    return out


def _apply_winning_plan_to_state(
    layout_state: ScreenLayoutPlannerState | None,
    screens: list[dict],
) -> None:
    if layout_state is None:
        return
    for sc in screens:
        layout_state.note_screen(sc.get("patternId", ""))


def replan_day_buckets_beam(
    chapters: list[dict],
    day_buckets: list[list[str]],
    aspects: dict[str, AspectKind],
    *,
    assets_by_id: dict[str, dict],
    orientation_summary: dict | None,
    skip_screen_asset_ids: set[str] | None,
    mixed_proximity_seconds: float,
    trip_photo_total: int,
    weights: ScoringWeights,
    beam_width: int,
    chapter_heroes: dict[str, str] | None,
    arc_mode: str,
    arc_profile: str,
    budget: SearchBudget,
    subject_run_tolerance: int,
    enable_food_grid: bool = True,
    mundane_grid_buckets: tuple[str, ...] = ("food",),
    intent_peak_chapters: set[int] | None = None,
    enable_gravity_balance: bool = True,
    max_consecutive_same_pattern: int = 2,
    skip_duplicate_signatures: bool = True,
    deterministic_strict: bool = False,
    incremental_scoring: bool = False,
    cfg: AppConfig | None = None,
    burst_seconds: float = 3.0,
    moment_secondary_ids: set[str] | frozenset[str] | None = None,
    moment_secondary_boost: float = 0.0,
) -> tuple[list[dict], list[dict], SearchBudget]:
    from travelogue.layout_engine.intent_hints import (
        INTENT_PEAK_ARC_BOOST,
        arc_segment_for_chapter_with_intent,
    )
    from travelogue.layout_engine.planner.screen_planner import DEFAULT_FEATURED_WEIGHT

    out = _shallow_copy_chapters(chapters)
    asset_to_ch: dict[str, str] = {}
    for ch in out:
        for aid in _collect_asset_ids_from_chapter(ch):
            asset_to_ch[aid] = ch.get("id", "ch")

    hero_by_ch = chapter_heroes or {
        ch["id"]: str((ch.get("curation") or {}).get("heroAssetId") or "")
        for ch in out
        if ch.get("id")
    }
    ch_by_id = {ch["id"]: ch for ch in out}
    gallery_asset_ids: set[str] = set()
    orig_by_id = {ch.get("id"): ch for ch in chapters}
    for ch in out:
        if ch.get("patternId") == "gallery":
            orig = orig_by_id.get(ch.get("id"), ch)
            ch["screens"] = copy.deepcopy(orig.get("screens") or [])
            gallery_asset_ids.update(_collect_asset_ids_from_chapter(ch))
        else:
            ch["screens"] = []

    from travelogue.layout_contract.rhythm import RhythmRules
    from travelogue.layout_engine.adapter import layout_state_for_trip, lse_enabled

    if cfg is not None and lse_enabled(cfg):
        layout_state = layout_state_for_trip(trip_photo_total, cfg=cfg)
    else:
        layout_state = ScreenLayoutPlannerState.from_trip_total(
            trip_photo_total,
            rhythm=RhythmRules.from_config(cfg),
        )
    seq_per_ch: dict[str, int] = {}
    total_ch = len(out)
    decision_logs: list[dict] = []
    skip = skip_screen_asset_ids or set()
    carry: list[str] = []
    carry_age: dict[str, int] = {}
    hero_ids = {h for h in hero_by_ch.values() if h}
    noted_patterns: list[str] = []
    from travelogue.layout_contract.scoring import median_sharpness
    from travelogue.layout_engine.planner.screen_planner_attach import (
        _carry_inject_ids,
        _consolidate_adjacent_portrait_singles,
        _flush_portrait_carry_tail,
        _late_chapter_planning_kwargs,
        assign_bucket_screens_with_portrait_carry,
    )

    med_sharp = median_sharpness(list(assets_by_id.values())) if assets_by_id else 0.0
    incr_state = IncrementalScoreState() if incremental_scoring else None
    from travelogue.layout_contract.constraints import plan_violates_consecutive_pattern

    for bucket_idx, bucket in enumerate(day_buckets):
        budget.begin_segment()
        legacy_only = False
        fallback_reason: str | None = None
        if not budget.trip_evaluations_remaining():
            legacy_only = True
            fallback_reason = "BUDGET_EXHAUSTED"
        elif not budget.segment_evaluations_remaining():
            legacy_only = True
            fallback_reason = "BUDGET_EXHAUSTED_SEGMENT"
        filtered = [a for a in bucket if a not in gallery_asset_ids and a not in skip]
        if not filtered:
            continue
        plan_ids = _carry_inject_ids(
            filtered,
            carry,
            aspects,
            late_chapter=layout_state.rhythm.late_chapter_pairing.is_late_chapter(
                bucket_idx + 1
            ),
        )
        layout_state.begin_chapter_bucket(chapter_index=bucket_idx + 1)
        late_kwargs = _late_chapter_planning_kwargs(
            layout_state.rhythm, bucket_idx + 1
        )
        from travelogue.layout_engine.planner.screen_planner_attach import (
            _preferred_hero_for_bucket,
        )

        preferred_hero = _preferred_hero_for_bucket(
            plan_ids, asset_to_ch, hero_by_ch, assets_by_id, median_sharp=med_sharp
        )
        from travelogue.layout_engine.planner.layout_search import generate_day_bucket_candidates

        candidates = generate_day_bucket_candidates(
            plan_ids,
            aspects,
            assets_by_id=assets_by_id,
            orientation_summary=orientation_summary,
            skip_screen_asset_ids=skip,
            mixed_proximity_seconds=mixed_proximity_seconds,
            trip_photo_total=trip_photo_total,
            preferred_hero_id=preferred_hero,
            layout_state=layout_state,
            enable_food_grid=enable_food_grid,
            mundane_grid_buckets=mundane_grid_buckets,
            beam_width=beam_width,
            budget=budget,
            **late_kwargs,
        )
        consecutive_filter_bypassed = False
        filtered_candidate_count: int | None = None
        if max_consecutive_same_pattern > 0:
            filtered_plans = [
                plan
                for plan in candidates
                if not plan_violates_consecutive_pattern(
                    plan[1],
                    max_streak=max_consecutive_same_pattern,
                )
            ]
            filtered_candidate_count = len(filtered_plans)
            if not filtered_plans and candidates:
                _log.warning(
                    "mosaic.search: no plan satisfies consecutive pattern "
                    "(max_streak=%d); using unfiltered candidates",
                    max_consecutive_same_pattern,
                )
                consecutive_filter_bypassed = True
                fallback_reason = fallback_reason or "CONSECUTIVE_PATTERN_UNSATISFIABLE"
            candidates = filtered_plans or candidates
        legacy_plan = candidates[0][1] if candidates else []
        legacy_sig = _screens_signature([{"screens": legacy_plan}])
        from travelogue.layout_contract.scoring import ScoreBreakdown

        legacy_score = ScoreBreakdown(total=0.0)
        if legacy_plan and budget.can_evaluate():
            budget.note_evaluation()
            legacy_score = score_screen_plan(
                legacy_plan,
                aspects=aspects,
                assets_by_id=assets_by_id,
                weights=weights,
                arc_profile=arc_profile,
                subject_run_tolerance=subject_run_tolerance,
                featured_beam=True,
                enable_gravity_balance=enable_gravity_balance,
                incremental=incremental_scoring,
                incremental_state=incr_state,
                moment_secondary_ids=moment_secondary_ids,
                moment_secondary_boost=moment_secondary_boost,
            )
            legacy_adjusted = legacy_score.total + _late_chapter_beam_adjustment(
                legacy_plan, layout_state.rhythm, bucket_idx + 1
            )
            legacy_score = replace(legacy_score, total=legacy_adjusted)
        best_plan = legacy_plan
        best_score = legacy_score
        best_variant = "legacy"
        if not legacy_only:
            eval_candidates = list(candidates)
            if deterministic_strict:
                eval_candidates.sort(
                    key=lambda item: str(_screens_signature([{"screens": item[1]}]))
                )
            for variant_name, plan in eval_candidates:
                plan_sig = _screens_signature([{"screens": plan}])
                if skip_duplicate_signatures and plan_sig == legacy_sig:
                    continue
                if not budget.can_evaluate():
                    best_plan = legacy_plan
                    best_score = legacy_score
                    best_variant = "legacy"
                    fallback_reason = fallback_reason or "BUDGET_EXHAUSTED"
                    break
                budget.note_evaluation()
                ch_id = asset_to_ch.get(
                    (plan[0].get("slots") or [{}])[0].get("assetId", "")
                )
                ch_index = next(
                    (i + 1 for i, c in enumerate(out) if c.get("id") == ch_id),
                    bucket_idx + 1,
                )
                arc_seg = None
                arc_boost = 0.0
                if _arc_scoring_active(arc_mode):
                    from travelogue.layout_contract.arc import ARC_PEAK

                    arc_seg = arc_segment_for_chapter_with_intent(
                        ch_index,
                        total_ch,
                        profile=arc_profile,
                        peak_chapters=intent_peak_chapters,
                    )
                    if intent_peak_chapters and ch_index in intent_peak_chapters:
                        arc_seg = ARC_PEAK
                        arc_boost = INTENT_PEAK_ARC_BOOST
                hero_ids = {hero_by_ch[ch_id]} if ch_id and hero_by_ch.get(ch_id) else set()
                bd = score_screen_plan(
                    plan,
                    aspects=aspects,
                    assets_by_id=assets_by_id,
                    weights=weights,
                    arc_segment=arc_seg,
                    arc_profile=arc_profile,
                    hero_asset_ids=hero_ids or None,
                    subject_run_tolerance=subject_run_tolerance,
                    featured_beam=True,
                    intent_arc_boost=arc_boost,
                    enable_gravity_balance=enable_gravity_balance,
                    incremental=incremental_scoring,
                    incremental_state=incr_state,
                    moment_secondary_ids=moment_secondary_ids,
                    moment_secondary_boost=moment_secondary_boost,
                )
                adjusted_total = bd.total + _late_chapter_beam_adjustment(
                    plan, layout_state.rhythm, bucket_idx + 1
                )
                if adjusted_total > best_score.total + 1e-6:
                    best_plan = plan
                    from travelogue.layout_contract.scoring import combine_utility

                    best_score = replace(
                        bd,
                        total=adjusted_total,
                        utility=combine_utility(adjusted_total, {}).utility,
                    )
                    best_variant = variant_name

        prefix_enabled = bool(
            cfg is not None
            and getattr(getattr(cfg, "layout", None), "scoring", None) is not None
            and bool(cfg.layout.scoring.prefix_beam_enabled)
        )
        if prefix_enabled and not legacy_only and plan_ids:
            from travelogue.layout_engine.mosaic.prefix_beam import prefix_beam_plan_bucket

            pb_plan, pb_fallback = prefix_beam_plan_bucket(
                plan_ids,
                aspects,
                assets_by_id=assets_by_id,
                orientation_summary=orientation_summary,
                skip_screen_asset_ids=skip,
                mixed_proximity_seconds=mixed_proximity_seconds,
                trip_photo_total=trip_photo_total,
                preferred_hero_id=preferred_hero,
                layout_state=replace(layout_state),
                enable_food_grid=enable_food_grid,
                mundane_grid_buckets=mundane_grid_buckets,
                beam_width=beam_width,
                budget=budget,
                weights=weights,
                subject_run_tolerance=subject_run_tolerance,
                enable_gravity_balance=enable_gravity_balance,
                late_kwargs=late_kwargs,
                moment_secondary_ids=moment_secondary_ids,
                moment_secondary_boost=moment_secondary_boost,
                incremental_state=incr_state,
            )
            if pb_fallback:
                fallback_reason = fallback_reason or pb_fallback
            elif pb_plan and budget.can_evaluate():
                budget.note_evaluation()
                pb_bd = score_screen_plan(
                    pb_plan,
                    aspects=aspects,
                    assets_by_id=assets_by_id,
                    weights=weights,
                    arc_profile=arc_profile,
                    subject_run_tolerance=subject_run_tolerance,
                    featured_beam=True,
                    enable_gravity_balance=enable_gravity_balance,
                    incremental=incremental_scoring,
                    incremental_state=incr_state,
                    moment_secondary_ids=moment_secondary_ids,
                    moment_secondary_boost=moment_secondary_boost,
                )
                pb_adj = pb_bd.total + _late_chapter_beam_adjustment(
                    pb_plan, layout_state.rhythm, bucket_idx + 1
                )
                if pb_adj > best_score.total + 1e-6:
                    best_plan = pb_plan
                    from travelogue.layout_contract.scoring import combine_utility

                    best_score = replace(
                        pb_bd,
                        total=pb_adj,
                        utility=combine_utility(pb_adj, {}).utility,
                    )
                    best_variant = "prefix_beam"

        if late_kwargs and best_plan:
            best_plan = _consolidate_adjacent_portrait_singles(best_plan, aspects)

        log = LayoutDecisionLog(chapter_id=f"day-bucket-{bucket_idx + 1}")
        log.add(
            "beam_pick",
            {
                "variant": best_variant,
                "candidateCount": len(candidates),
                "score": best_score.to_dict(),
                "utility": round(
                    float(getattr(best_score, "utility", 0.0) or best_score.total),
                    6,
                ),
                "legacyScore": legacy_score.to_dict(),
                "changed": _screens_signature([{"screens": best_plan}]) != legacy_sig,
                "arcProfile": arc_profile,
                "fallbackUsed": bool(fallback_reason),
                "fallbackReason": fallback_reason,
                "plannerPath": (
                    "legacy"
                    if legacy_only or (fallback_reason and best_variant != "prefix_beam")
                    else ("prefix_beam" if best_variant == "prefix_beam" else "beam")
                ),
                "consecutivePatternFilterBypassed": consecutive_filter_bypassed,
                "filteredCandidateCount": filtered_candidate_count,
                "maxConsecutiveStreak": (
                    max_consecutive_same_pattern if consecutive_filter_bypassed else None
                ),
            },
        )
        decision_logs.append(log.to_dict())

        carry, carry_age, layout_state = assign_bucket_screens_with_portrait_carry(
            best_plan,
            bucket_idx=bucket_idx,
            total_buckets=len(day_buckets),
            carry_age=carry_age,
            layout_state=layout_state,
            noted_patterns=noted_patterns,
            asset_to_ch=asset_to_ch,
            ch_by_id=ch_by_id,
            seq_per_ch=seq_per_ch,
            assets_by_id=assets_by_id,
            hero_ids=hero_ids,
        )

    _flush_portrait_carry_tail(
        carry,
        aspects,
        assets_by_id=assets_by_id,
        asset_to_ch=asset_to_ch,
        ch_by_id=ch_by_id,
        seq_per_ch=seq_per_ch,
        layout_state=layout_state,
        skip=skip,
        burst_seconds=burst_seconds,
        mixed_proximity_seconds=mixed_proximity_seconds,
        orientation_summary=orientation_summary,
        trip_photo_total=trip_photo_total,
        median_sharp=med_sharp,
        featured_weight=DEFAULT_FEATURED_WEIGHT,
        enable_food_grid=enable_food_grid,
        mundane_grid_buckets=mundane_grid_buckets,
        cfg=cfg,
    )

    return out, decision_logs, budget


# Backward-compatible alias for layout_search and tests
_replan_day_buckets_beam = replan_day_buckets_beam

__all__ = ["replan_day_buckets_beam", "_replan_day_buckets_beam"]
