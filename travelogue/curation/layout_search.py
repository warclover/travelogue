"""Beam search wrapper around legacy screen planner (V2 PRD §7 · P7 signature skip)."""

from __future__ import annotations

import copy
import logging
from typing import Any

_log = logging.getLogger(__name__)

from travelogue.curation.degradation import DegradationAssessment
from travelogue.curation.decision_log import LayoutDecisionLog
from travelogue.curation.layout_candidates import generate_day_bucket_candidates
from travelogue.curation.layout_planner import AspectKind
from travelogue.curation.layout_scoring import ScoringWeights, score_screen_plan
from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState
from travelogue.curation.search_budget import SearchBudget


def _arc_scoring_active(arc_mode: str) -> bool:
    return arc_mode in ("v2_adaptive", "v2_five_beat")


def _shallow_copy_chapters(chapters: list[dict]) -> list[dict]:
    """P7-D3 · local copy instead of full deepcopy where safe."""
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
    from travelogue.curation.chapter_items import collect_screen_asset_ids, item_asset_ids

    aids = collect_screen_asset_ids(ch)
    if aids:
        return aids
    out: list[str] = []
    for it in ch.get("items") or []:
        for aid in item_asset_ids(it):
            if aid not in out:
                out.append(aid)
    return out


def _preferred_hero_for_bucket(
    bucket: list[str],
    asset_to_ch: dict[str, str],
    hero_by_ch: dict[str, str],
    assets_by_id: dict[str, dict],
    *,
    median_sharp: float | None = None,
) -> str | None:
    from travelogue.curation.screen_planner import _preferred_hero_for_bucket as _pick

    return _pick(
        bucket, asset_to_ch, hero_by_ch, assets_by_id, median_sharp=median_sharp
    )


def _apply_winning_plan_to_state(
    layout_state: ScreenLayoutPlannerState | None,
    screens: list[dict],
) -> None:
    if layout_state is None:
        return
    for sc in screens:
        layout_state.note_screen(sc.get("patternId", ""))


def _replan_day_buckets_beam(
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
    intent_peak_chapters: set[int] | None = None,
    enable_gravity_balance: bool = True,
    max_consecutive_same_pattern: int = 2,
    skip_duplicate_signatures: bool = True,
    deterministic_strict: bool = False,
) -> tuple[list[dict], list[dict], SearchBudget]:
    from travelogue.curation.intent_hints import INTENT_PEAK_ARC_BOOST, arc_segment_for_chapter_with_intent

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

    layout_state = ScreenLayoutPlannerState.from_trip_total(trip_photo_total)
    seq_per_ch: dict[str, int] = {}
    total_ch = len(out)
    decision_logs: list[dict] = []
    skip = skip_screen_asset_ids or set()
    from travelogue.curation.curate_scoring import median_sharpness

    med_sharp = median_sharpness(list(assets_by_id.values())) if assets_by_id else 0.0
    from travelogue.curation.layout_constraints import plan_violates_consecutive_pattern

    for bucket_idx, bucket in enumerate(day_buckets):
        if not budget.can_evaluate():
            break
        filtered = [a for a in bucket if a not in gallery_asset_ids and a not in skip]
        if not filtered:
            continue
        preferred_hero = _preferred_hero_for_bucket(
            filtered, asset_to_ch, hero_by_ch, assets_by_id, median_sharp=med_sharp
        )
        candidates = generate_day_bucket_candidates(
            filtered,
            aspects,
            assets_by_id=assets_by_id,
            orientation_summary=orientation_summary,
            skip_screen_asset_ids=skip,
            mixed_proximity_seconds=mixed_proximity_seconds,
            trip_photo_total=trip_photo_total,
            preferred_hero_id=preferred_hero,
            layout_state=layout_state,
            beam_width=beam_width,
            budget=budget,
        )
        if max_consecutive_same_pattern > 0:
            filtered = [
                plan
                for plan in candidates
                if not plan_violates_consecutive_pattern(
                    plan,
                    max_streak=max_consecutive_same_pattern,
                )
            ]
            if not filtered and candidates:
                _log.warning(
                    "layout_search: no plan satisfies consecutive pattern "
                    "(max_streak=%d); using unfiltered candidates",
                    max_consecutive_same_pattern,
                )
            candidates = filtered or candidates
        legacy_plan = candidates[0][1] if candidates else []
        legacy_sig = _screens_signature([{"screens": legacy_plan}])
        if budget.can_evaluate():
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
            )
        else:
            from travelogue.curation.layout_scoring import ScoreBreakdown

            legacy_score = ScoreBreakdown(total=0.0)
        best_plan = legacy_plan
        best_score = legacy_score
        best_variant = "legacy"
        eval_candidates = list(candidates)
        if deterministic_strict:
            eval_candidates.sort(key=lambda item: str(_screens_signature([{"screens": item[1]}])))
        for variant_name, plan in eval_candidates:
            plan_sig = _screens_signature([{"screens": plan}])
            if skip_duplicate_signatures and plan_sig == legacy_sig:
                continue
            if not budget.can_evaluate():
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
                arc_seg = arc_segment_for_chapter_with_intent(
                    ch_index,
                    total_ch,
                    profile=arc_profile,
                    peak_chapters=intent_peak_chapters,
                )
                if intent_peak_chapters and ch_index in intent_peak_chapters:
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
            )
            if bd.total > best_score.total + 1e-6:
                best_plan = plan
                best_score = bd
                best_variant = variant_name

        log = LayoutDecisionLog(chapter_id=f"day-bucket-{bucket_idx + 1}")
        log.add(
            "beam_pick",
            {
                "variant": best_variant,
                "candidateCount": len(candidates),
                "score": best_score.to_dict(),
                "legacyScore": legacy_score.to_dict(),
                "changed": _screens_signature([{"screens": best_plan}]) != legacy_sig,
                "arcProfile": arc_profile,
            },
        )
        decision_logs.append(log.to_dict())

        _apply_winning_plan_to_state(layout_state, best_plan)
        for sc in best_plan:
            slots = sc.get("slots") or []
            if not slots:
                continue
            ch_id = asset_to_ch.get(slots[0].get("assetId", ""))
            if not ch_id or ch_id not in ch_by_id:
                continue
            seq_per_ch[ch_id] = seq_per_ch.get(ch_id, 0) + 1
            screen = dict(sc)
            screen["screenId"] = f"{ch_id}-sc-{seq_per_ch[ch_id]:02d}"
            ch_by_id[ch_id]["screens"].append(screen)

    return out, decision_logs, budget


def maybe_replan_chapters(
    chapters: list[dict],
    *,
    buckets: list[list[str]],
    aspects: dict[str, AspectKind],
    assets: list[dict] | None,
    scoring_enabled: bool,
    weights: ScoringWeights,
    beam_width: int,
    degradation: DegradationAssessment,
    arc_mode: str = "legacy",
    arc_profile: str = "dynamic",
    chapter_heroes: dict[str, str] | None = None,
    orientation_summary: dict | None = None,
    skip_screen_asset_ids: set[str] | None = None,
    mixed_proximity_seconds: float = 12.0,
    trip_photo_total: int | None = None,
    search_timeout_ms: int = 2000,
    max_candidates_per_bucket: int = 12,
    max_evaluations_per_trip: int = 500,
    allow_burst_split: bool = False,
    subject_run_tolerance: int = 1,
    intent_peak_chapters: set[int] | None = None,
    enable_gravity_balance: bool = True,
    max_consecutive_same_pattern: int = 2,
    skip_duplicate_signatures: bool = True,
    deterministic_strict: bool = False,
) -> tuple[list[dict], dict[str, Any]]:
    """Return chapters unchanged when scoring off, degraded, or aspect-only."""
    meta: dict[str, Any] = {"replanApplied": False, "decisionLogs": []}
    if not scoring_enabled or degradation.force_legacy:
        meta["skipReason"] = degradation.reason or "scoring_disabled"
        return chapters, meta

    if weights.is_aspect_only():
        meta["skipReason"] = "aspect_only_preserve_legacy"
        meta["equivalentToLegacy"] = True
        return chapters, meta

    assets_by_id = {a["id"]: a for a in (assets or []) if a.get("id")}
    if trip_photo_total is None:
        trip_photo_total = len(assets_by_id) or sum(len(b) for b in buckets)

    budget = SearchBudget(
        search_timeout_ms=search_timeout_ms,
        max_candidates_per_bucket=max_candidates_per_bucket,
        max_evaluations_per_trip=max_evaluations_per_trip,
        allow_burst_split=allow_burst_split,
    )
    out, logs, budget = _replan_day_buckets_beam(
        chapters,
        buckets,
        aspects,
        assets_by_id=assets_by_id,
        orientation_summary=orientation_summary,
        skip_screen_asset_ids=skip_screen_asset_ids,
        mixed_proximity_seconds=mixed_proximity_seconds,
        trip_photo_total=trip_photo_total,
        weights=weights,
        beam_width=beam_width,
        chapter_heroes=chapter_heroes,
        arc_mode=arc_mode,
        arc_profile=arc_profile,
        budget=budget,
        subject_run_tolerance=subject_run_tolerance,
        intent_peak_chapters=intent_peak_chapters,
        enable_gravity_balance=enable_gravity_balance,
        max_consecutive_same_pattern=max_consecutive_same_pattern,
        skip_duplicate_signatures=skip_duplicate_signatures,
        deterministic_strict=deterministic_strict,
    )
    meta["decisionLogs"] = logs
    meta["searchBudget"] = budget.to_dict()
    if budget.timed_out:
        meta["skipReason"] = "search_timeout"
    elif budget.exhausted:
        meta["skipReason"] = "search_eval_exhausted"

    if _screens_signature(out) != _screens_signature(chapters):
        meta["replanApplied"] = True
    else:
        meta["replanApplied"] = False
    return out, meta
