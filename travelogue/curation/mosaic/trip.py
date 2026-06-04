"""Trip-level MCS orchestration (compose_trip · Phase 15)."""

from __future__ import annotations

from typing import Any

from travelogue.config import AppConfig
from travelogue.curation.degradation import DegradationAssessment
from travelogue.curation.layout_planner import AspectKind
from travelogue.curation.layout_scoring import ScoringWeights


def compose_trip(
    chapters: list[dict],
    *,
    buckets: list[list[str]],
    aspects: dict[str, AspectKind],
    assets: list[dict] | None,
    app_cfg: AppConfig,
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
    incremental_scoring: bool = False,
) -> tuple[list[dict], dict[str, Any]]:
    """
    Replan chapters via beam when mosaic is enabled.

    Window-level MCS already ran during ``build_chapters_from_buckets``; this pass
    applies segment beam with mosaic ``deterministic_strict`` when configured.
    """
    from travelogue.curation.layout_search import maybe_replan_chapters

    mosaic = app_cfg.mosaic
    det = mosaic.deterministic_strict if mosaic.enabled else app_cfg.clustering.deterministic_strict
    chapters, meta = maybe_replan_chapters(
        chapters,
        buckets=buckets,
        aspects=aspects,
        assets=assets,
        scoring_enabled=scoring_enabled,
        weights=weights,
        beam_width=beam_width,
        degradation=degradation,
        arc_mode=arc_mode,
        arc_profile=arc_profile,
        chapter_heroes=chapter_heroes,
        orientation_summary=orientation_summary,
        skip_screen_asset_ids=skip_screen_asset_ids,
        mixed_proximity_seconds=mixed_proximity_seconds,
        trip_photo_total=trip_photo_total,
        search_timeout_ms=search_timeout_ms,
        max_candidates_per_bucket=max_candidates_per_bucket,
        max_evaluations_per_trip=max_evaluations_per_trip,
        max_evaluations_per_segment=max_evaluations_per_segment,
        allow_burst_split=allow_burst_split,
        subject_run_tolerance=subject_run_tolerance,
        enable_food_grid=enable_food_grid,
        mundane_grid_buckets=mundane_grid_buckets,
        intent_peak_chapters=intent_peak_chapters,
        enable_gravity_balance=enable_gravity_balance,
        max_consecutive_same_pattern=max_consecutive_same_pattern,
        skip_duplicate_signatures=skip_duplicate_signatures,
        deterministic_strict=det,
        incremental_scoring=incremental_scoring,
    )
    meta["mosaicEnabled"] = mosaic.enabled
    meta["mosaicScorerVersion"] = mosaic.scorer_version
    return chapters, meta
