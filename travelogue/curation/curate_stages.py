"""Curate pipeline stages (AAD-10 · extract from run_curate).

First slice: preflight + bucket planning helpers. Further stages land in
follow-up PRs until ``run_curate`` is an ≤80-line shell.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from travelogue.config import AppConfig, CurateConfig
from travelogue.curation.bucket_planning import (
    group_assets_by_segments,
)
from travelogue.curation.curate_limits import (
    COMPACT_ALBUM_PHOTO_CAP,
    MIN_CURATE_ASSETS,
    SMALL_ALBUM_PHOTO_CAP,
)
from travelogue.domain.cover_view import layout_eligible_assets


@dataclass
class CuratePreflight:
    """Resolved layout/cover context before bucket planning."""

    app_cfg: AppConfig
    cur_cfg: CurateConfig
    layout: str
    engine: str
    layout_assets: list[dict]
    cover_id: str
    cover_p6: bool
    skip_screen_ids: set[str]
    res_warn: str | None
    saved_memory_anchors: list[list[str] | None]


@dataclass
class CurateBucketPlan:
    buckets: list[list[str]]
    bucket_segment_ids: list[str]
    bucket_segment_ids_all: list[list[str]]
    segments: list
    segment_labels: dict[str, str]
    curation_segments: list[dict]
    meta_places: list[str]


# Backward-compatible private aliases (tests / curate.py re-exports).
_CuratePreflight = CuratePreflight
_CurateBucketPlan = CurateBucketPlan


def stage_refresh_cull_cohort(
    trip: dict,
    *,
    trip_dir: Path | None,
    cfg: AppConfig | None,
    curate_scope: str,
    refresh_algorithms: bool | None,
) -> dict | None:
    """Refresh cull profile and optional cohort face tags."""
    from travelogue.curation.algorithm_profile import maybe_refresh_cull

    maybe_refresh_cull(
        trip,
        trip_dir=trip_dir,
        app_cfg=cfg,
        refresh_algorithms=(
            False if curate_scope == "tier" and refresh_algorithms is None else refresh_algorithms
        ),
    )
    if trip_dir is None:
        return None
    from travelogue.curation.cohort_faces import apply_cohort_tags

    return apply_cohort_tags(trip, trip_dir=trip_dir, cfg=cfg)


def curate_preflight(
    trip: dict,
    *,
    export_layout: str | None,
    layout_engine: str | None,
    trip_dir: Path | None,
    cfg: AppConfig | None,
    saved_memory_anchors: list[list[str] | None],
    cover_force: bool = False,
) -> CuratePreflight:
    from travelogue.config import default_web_layout_engine, get_config
    from travelogue.curation.curate import (
        CurateError,
        apply_low_resolution_exclusion,
        sync_trip_covers,
    )
    from travelogue.layout_engine.planner.screen_planner import (
        LAYOUT_ENGINE_LEGACY,
        LAYOUT_ENGINE_SCREENS,
    )

    app_cfg = cfg or get_config()
    trip_id = str(trip.get("tripId") or (trip_dir.name if trip_dir else "")).strip()
    cover_p6 = True
    if trip_id:
        from travelogue.curation.phase6_rollout import (
            phase6_in_rollout_cohort,
            resolve_app_config_for_trip,
        )

        cover_p6 = phase6_in_rollout_cohort(trip_id, app_cfg)
        app_cfg = resolve_app_config_for_trip(app_cfg, trip_id)
        from travelogue.layout_engine.rollout import resolve_lse_config_for_trip

        app_cfg = resolve_lse_config_for_trip(app_cfg, trip_id)
    res_warn = apply_low_resolution_exclusion(trip, trip_dir=trip_dir, app_cfg=app_cfg)
    layout_assets = layout_eligible_assets(trip)
    if len(layout_assets) < MIN_CURATE_ASSETS:
        raise CurateError(
            "E_CURATE_TOO_FEW",
            f"need at least {MIN_CURATE_ASSETS} layout-eligible assets after resolution filter",
        )

    cur_cfg = app_cfg.curate
    layout = export_layout or trip.get("exportLayout") or "auto"
    engine = (
        layout_engine
        or trip.get("layoutEngine")
        or default_web_layout_engine(layout, cfg=app_cfg)
    )
    if engine not in (LAYOUT_ENGINE_LEGACY, LAYOUT_ENGINE_SCREENS):
        engine = LAYOUT_ENGINE_LEGACY
    cover_id = sync_trip_covers(
        trip,
        export_layout=layout,
        assets=layout_assets,
        featured_weight=cur_cfg.featured_weight,
        featured_min_for_cover_pool=cur_cfg.featured_min_for_cover_pool,
        enable_phase6_cover_factors=cover_p6,
        cover_scoring=cur_cfg.cover_scoring,
        cover_scoring_v2=cur_cfg.cover_scoring_v2,
        scoring_version=cur_cfg.cover_scoring_version,
        force=cover_force,
    )
    curation = trip.get("curation") or {}
    by_layout = curation.get("coverByLayout") or {}
    skip_screen_ids: set[str] = set()
    if layout in ("auto", "web") and isinstance(by_layout, dict):
        web_cover = by_layout.get("web") or ""
        if web_cover:
            skip_screen_ids.add(web_cover)
    return CuratePreflight(
        app_cfg=app_cfg,
        cur_cfg=cur_cfg,
        layout=layout,
        engine=engine,
        layout_assets=layout_assets,
        cover_id=cover_id,
        cover_p6=cover_p6,
        skip_screen_ids=skip_screen_ids,
        res_warn=res_warn,
        saved_memory_anchors=saved_memory_anchors,
    )


def build_curate_buckets(trip: dict, preflight: CuratePreflight) -> CurateBucketPlan:
    from travelogue.curation.clustering_buckets import (
        build_buckets_from_clustering,
        should_use_clustering_buckets,
    )
    from travelogue.domain.copy_subject import effective_meta_places

    meta = trip.get("meta", {})
    meta_places = effective_meta_places(
        meta,
        intent=trip.get("intent"),
        assets=trip.get("assets") or [],
    )
    cur_cfg = preflight.cur_cfg
    layout_assets = preflight.layout_assets
    cover_id = preflight.cover_id

    if should_use_clustering_buckets(trip, preflight.app_cfg):
        buckets, bucket_segment_ids, bucket_segment_ids_all, segments = build_buckets_from_clustering(
            trip,
            layout_assets,
            cover_id,
            meta,
            cfg=preflight.app_cfg,
            min_bucket_size=cur_cfg.min_bucket_size,
        )
    else:
        buckets, bucket_segment_ids, bucket_segment_ids_all, segments = group_assets_by_segments(
            layout_assets,
            cover_id,
            meta,
            intent=trip.get("intent"),
            segment_gap_days=cur_cfg.segment_gap_days,
            city_gap_days=cur_cfg.city_gap_days,
            min_bucket_size=cur_cfg.min_bucket_size,
            chapter_balance_enabled=cur_cfg.chapter_balance_enabled,
            chapter_balance_ratio=cur_cfg.chapter_balance_ratio,
        )

    if len(layout_assets) <= SMALL_ALBUM_PHOTO_CAP:
        from travelogue.curation.bucket_planning import normalize_bucket_counts

        max_ch = 2 if len(layout_assets) <= COMPACT_ALBUM_PHOTO_CAP else 3
        norm = normalize_bucket_counts(
            buckets,
            bucket_segment_ids,
            max_chapters=max_ch,
            min_bucket_size=min(2, cur_cfg.min_bucket_size),
            chapter_balance_enabled=cur_cfg.chapter_balance_enabled,
            chapter_balance_ratio=cur_cfg.chapter_balance_ratio,
        )
        buckets = norm.buckets
        bucket_segment_ids = norm.primary_segment_ids
        bucket_segment_ids_all = norm.segment_ids_per_bucket

    from travelogue.layout_engine.adapter import lse_enabled, resolve_pack
    from travelogue.layout_engine.capabilities import effective_capabilities
    from travelogue.layout_engine.segment_order import apply_segment_order_to_buckets

    if lse_enabled(preflight.app_cfg):
        pack = resolve_pack(preflight.app_cfg)
        caps = effective_capabilities(preflight.app_cfg, pack)
        seg_raw = (pack.raw.get("segment_order") if pack else {}) or {}
        max_len = int(seg_raw.get("max_segment_len") or 30) if isinstance(seg_raw, dict) else 30
        seg_on = bool(caps.segment_order_optimizer)
        if isinstance(seg_raw, dict):
            seg_on = seg_on or bool(seg_raw.get("enabled", False))
        apply_segment_order_to_buckets(
            buckets,
            layout_assets,
            enabled=seg_on,
            max_segment_len=max_len,
        )

    segment_labels = {s.id: s.label for s in segments}
    curation_segments = [s.to_dict() for s in segments]
    return CurateBucketPlan(
        buckets=buckets,
        bucket_segment_ids=bucket_segment_ids,
        bucket_segment_ids_all=bucket_segment_ids_all,
        segments=segments,
        segment_labels=segment_labels,
        curation_segments=curation_segments,
        meta_places=meta_places,
    )


def build_layout_only_bucket_plan(
    trip: dict, preflight: CuratePreflight
) -> CurateBucketPlan | None:
    from travelogue.domain.copy_subject import effective_meta_places
    from travelogue.layout_engine.replan import buckets_from_existing_chapters

    raw = buckets_from_existing_chapters(trip)
    if raw is None:
        return None
    meta = trip.get("meta", {})
    meta_places = effective_meta_places(
        meta,
        intent=trip.get("intent"),
        assets=trip.get("assets") or [],
    )
    return CurateBucketPlan(
        buckets=raw["buckets"],
        bucket_segment_ids=raw["bucket_segment_ids"],
        bucket_segment_ids_all=raw["bucket_segment_ids_all"],
        segments=raw["segments"],
        segment_labels=raw["segment_labels"],
        curation_segments=raw["curation_segments"],
        meta_places=meta_places,
    )


def stage_resolve_buckets(
    trip: dict,
    preflight: CuratePreflight,
    *,
    curate_scope: str,
    trip_dir: Path | None,
) -> tuple[CurateBucketPlan, Any]:
    """Pick layout-only vs full buckets; return plan + replan decision."""
    from travelogue.curation.curate import CurateError
    from travelogue.layout_engine.replan import (
        mark_layout_replan,
        should_layout_only_replan,
    )

    replan_decision = should_layout_only_replan(
        trip, trip_dir=trip_dir, cfg=preflight.app_cfg
    )
    if curate_scope == "tier":
        bucket_plan = build_layout_only_bucket_plan(trip, preflight)
        if bucket_plan is None:
            raise CurateError(
                "E_CURATE_NO_STRUCTURE",
                "tier scope requires existing chapter structure",
            )
        mark_layout_replan(trip, reason="tier_rerank")
    elif replan_decision.layout_only:
        bucket_plan = build_layout_only_bucket_plan(trip, preflight)
        if bucket_plan is None:
            bucket_plan = build_curate_buckets(trip, preflight)
        else:
            mark_layout_replan(trip, reason=replan_decision.reason or "density_change")
    else:
        bucket_plan = build_curate_buckets(trip, preflight)
    return bucket_plan, replan_decision


# Private aliases matching former curate.py names.
_curate_preflight = curate_preflight
_build_curate_buckets = build_curate_buckets
_build_layout_only_bucket_plan = build_layout_only_bucket_plan
