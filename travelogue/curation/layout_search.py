"""Beam search wrapper around legacy screen planner (V2 PRD §7 · P7 signature skip)."""

from __future__ import annotations

from typing import Any

from travelogue.curation.degradation import DegradationAssessment
from travelogue.curation.layout_candidates import generate_day_bucket_candidates
from travelogue.curation.layout_planner import AspectKind
from travelogue.curation.layout_scoring import ScoringWeights
from travelogue.curation.mosaic.search import replan_day_buckets_beam as _replan_day_buckets_beam
from travelogue.curation.search_budget import SearchBudget

# Re-export beam entry for ADR / tests
from travelogue.curation.mosaic.search import replan_day_buckets_beam  # noqa: F401


def _screens_signature(chapters: list[dict]) -> list[list[str]]:
    sig: list[list[str]] = []
    for ch in chapters:
        sig.append([s.get("patternId", "") for s in (ch.get("screens") or [])])
    return sig


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
    max_evaluations_per_segment: int = 0,
    allow_burst_split: bool = False,
    subject_run_tolerance: int = 1,
    enable_food_grid: bool = True,
    mundane_grid_buckets: tuple[str, ...] = ("food",),
    intent_peak_chapters: set[int] | None = None,
    enable_gravity_balance: bool = True,
    max_consecutive_same_pattern: int = 2,
    skip_duplicate_signatures: bool = True,
    deterministic_strict: bool = False,
    incremental_scoring: bool = False,
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
        max_evaluations_per_segment=max_evaluations_per_segment,
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
        enable_food_grid=enable_food_grid,
        mundane_grid_buckets=mundane_grid_buckets,
        intent_peak_chapters=intent_peak_chapters,
        enable_gravity_balance=enable_gravity_balance,
        max_consecutive_same_pattern=max_consecutive_same_pattern,
        skip_duplicate_signatures=skip_duplicate_signatures,
        deterministic_strict=deterministic_strict,
        incremental_scoring=incremental_scoring,
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
