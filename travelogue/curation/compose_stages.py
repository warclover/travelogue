"""Compose stages around S-01: align, peel, score, materialize. No edition branch."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AlignedBuckets:
    raw_buckets: list[list[str]]
    non_empty_buckets: list[list[str]]
    bucket_segment_ids: list[str]
    bucket_segment_ids_all: list[list[str]]
    aspects: dict
    segment_labels: dict[str, str]
    curation_segments: list[dict]
    meta_places: list[str]


@dataclass
class PeeledBuckets:
    raw_buckets: list[list[str]]
    non_empty_buckets: list[list[str]]
    bucket_segment_ids: list[str]
    bucket_segment_ids_all: list[list[str]]
    aspects: dict
    segment_labels: dict[str, str]
    curation_segments: list[dict]
    meta_places: list[str]
    appendix_outlier_ids: list[str]


@dataclass
class ComposeReady:
    chapters: list[dict]
    non_empty_buckets: list[list[str]]
    bucket_segment_ids: list[str]
    aspects: dict
    pattern_hints: list
    arc_profile: str
    use_arc: bool
    chapter_heroes: dict[str, str]
    secondary_hints: list
    trip_memory_anchors: list[str]
    summary_dict: dict
    appendix_outlier_ids: list[str]
    scoring_weights: Any
    intent_peak: Any
    degradation: Any
    layout_cfg: Any
    curation_segments: list[dict]


def align_non_empty_buckets(bucket_plan, preflight) -> AlignedBuckets:
    from travelogue.curation.layout_planner import aspect_kind_for_asset
    from travelogue.layout_engine.adapter import reset_build_screen_calls

    reset_build_screen_calls()
    aspects = {a["id"]: aspect_kind_for_asset(a) for a in preflight.layout_assets}
    buckets = bucket_plan.buckets
    bucket_segment_ids = bucket_plan.bucket_segment_ids
    bucket_segment_ids_all = bucket_plan.bucket_segment_ids_all
    if len(bucket_segment_ids) == len(buckets) and len(bucket_segment_ids_all) == len(
        buckets
    ):
        aligned = [
            (b, sid, sids)
            for b, sid, sids in zip(
                buckets, bucket_segment_ids, bucket_segment_ids_all, strict=True
            )
            if b
        ]
        non_empty_buckets = [row[0] for row in aligned]
        bucket_segment_ids = [row[1] for row in aligned]
        bucket_segment_ids_all = [row[2] for row in aligned]
    else:
        non_empty_buckets = [b for b in buckets if b]
    return AlignedBuckets(
        raw_buckets=buckets,
        non_empty_buckets=non_empty_buckets,
        bucket_segment_ids=bucket_segment_ids,
        bucket_segment_ids_all=bucket_segment_ids_all,
        aspects=aspects,
        segment_labels=bucket_plan.segment_labels,
        curation_segments=bucket_plan.curation_segments,
        meta_places=bucket_plan.meta_places,
    )


def peel_time_outliers(aligned: AlignedBuckets, preflight) -> PeeledBuckets:
    # BE-SFI-08 · ≥2 outliers → peel into appendix; 单张仅降权留在原桶（不消失）
    assets_by_id_early = {a["id"]: a for a in preflight.layout_assets}
    appendix_outlier_ids: list[str] = []
    for bucket in aligned.non_empty_buckets:
        for aid in bucket:
            if (assets_by_id_early.get(aid) or {}).get("timeOutlier"):
                appendix_outlier_ids.append(str(aid))
    _seen_out: set[str] = set()
    _unique_out: list[str] = []
    for aid in appendix_outlier_ids:
        if aid not in _seen_out:
            _seen_out.add(aid)
            _unique_out.append(aid)
    appendix_outlier_ids = _unique_out

    non_empty_buckets = aligned.non_empty_buckets
    bucket_segment_ids = aligned.bucket_segment_ids
    bucket_segment_ids_all = aligned.bucket_segment_ids_all
    if len(appendix_outlier_ids) >= 2:
        peeled_rows: list[tuple[list[str], str, list[str]]] = []
        has_seg_meta = len(bucket_segment_ids) == len(non_empty_buckets) and len(
            bucket_segment_ids_all
        ) == len(non_empty_buckets)
        outlier_set = set(appendix_outlier_ids)
        for i, bucket in enumerate(non_empty_buckets):
            kept = [aid for aid in bucket if str(aid) not in outlier_set]
            if not kept:
                continue
            sid = bucket_segment_ids[i] if has_seg_meta else ""
            sids = bucket_segment_ids_all[i] if has_seg_meta else []
            peeled_rows.append((kept, sid, sids))
        non_empty_buckets = [row[0] for row in peeled_rows]
        if has_seg_meta:
            bucket_segment_ids = [row[1] for row in peeled_rows]
            bucket_segment_ids_all = [row[2] for row in peeled_rows]
    else:
        appendix_outlier_ids = []

    return PeeledBuckets(
        raw_buckets=aligned.raw_buckets,
        non_empty_buckets=non_empty_buckets,
        bucket_segment_ids=bucket_segment_ids,
        bucket_segment_ids_all=bucket_segment_ids_all,
        aspects=aligned.aspects,
        segment_labels=aligned.segment_labels,
        curation_segments=aligned.curation_segments,
        meta_places=aligned.meta_places,
        appendix_outlier_ids=appendix_outlier_ids,
    )


def prepare_compose_draft(trip: dict, preflight, peeled: PeeledBuckets, *, cohort_summary: dict | None):
    from travelogue.curation.chapter_titles import chapter_titles
    from travelogue.curation.curate_patterns import pattern_hint_for_bucket
    from travelogue.curation.curate_scoring import median_sharpness, pick_chapter_hero
    from travelogue.curation.layout_planner import (
        build_chapters_from_buckets,
        summarize_orientations,
    )
    from travelogue.curation.moment_scoring import (
        preferred_secondary_hero_for_bucket,
        sync_trip_moments_preflight,
    )

    app_cfg = preflight.app_cfg
    cur_cfg = preflight.cur_cfg
    layout = preflight.layout
    engine = preflight.engine
    layout_assets = preflight.layout_assets
    skip_screen_ids = preflight.skip_screen_ids
    saved_memory_anchors = preflight.saved_memory_anchors
    non_empty_buckets = peeled.non_empty_buckets
    bucket_segment_ids = peeled.bucket_segment_ids
    bucket_segment_ids_all = peeled.bucket_segment_ids_all
    aspects = peeled.aspects
    meta_places = peeled.meta_places
    meta = trip.get("meta", {})
    curation = trip.get("curation") or {}

    arc_profile = "dynamic"
    use_arc = cur_cfg.arc_mode in ("v2_adaptive", "v2_five_beat")
    if use_arc:
        from travelogue.curation.arc_patterns import (
            arc_pattern_hint_for_bucket,
            infer_arc_profile,
        )

        if cur_cfg.arc_mode == "v2_adaptive":
            arc_profile = infer_arc_profile(
                layout_assets,
                non_empty_buckets,
                flat_threshold=cur_cfg.arc_flat_variance_threshold,
            )
        pattern_hints = []
        total_buckets = len(non_empty_buckets)
        for i, b in enumerate(non_empty_buckets):
            arc_hint = arc_pattern_hint_for_bucket(
                i + 1, total_buckets, profile=arc_profile
            )
            pattern_hints.append(
                arc_hint
                if arc_hint
                else pattern_hint_for_bucket(i + 1, total_buckets, b, aspects)
            )
    else:
        pattern_hints = [
            pattern_hint_for_bucket(i + 1, len(non_empty_buckets), b, aspects)
            for i, b in enumerate(non_empty_buckets)
        ]
    assets_by_id = {a["id"]: a for a in layout_assets}
    med_sharp = median_sharpness(layout_assets)

    trip_memory_anchors: list[str] = []
    for group in saved_memory_anchors:
        if group:
            trip_memory_anchors.extend(str(a) for a in group if a)
    sync_trip_moments_preflight(
        trip,
        layout_assets,
        cfg=cur_cfg.moment,
        arc_profile=arc_profile,
        featured_weight=cur_cfg.featured_weight,
        aesthetic_enabled=app_cfg.aesthetic.enabled,
        meta_places=meta_places or None,
        memory_anchors=trip_memory_anchors or None,
    )
    secondary_hints = list((trip.get("curation") or {}).get("momentSecondaryHintIds") or [])

    chapter_heroes: dict[str, str] = {}
    used_secondary_heroes: set[str] = set()
    for i, bucket in enumerate(non_empty_buckets):
        anchors = saved_memory_anchors[i] if i < len(saved_memory_anchors) else None
        preferred: str | None = None
        if use_arc:
            from travelogue.curation.arc_patterns import arc_segment_for_chapter

            if arc_segment_for_chapter(i + 1, len(non_empty_buckets), profile=arc_profile) == "peak":
                available_hints = [h for h in secondary_hints if h not in used_secondary_heroes]
                preferred = preferred_secondary_hero_for_bucket(bucket, available_hints)
        hero = pick_chapter_hero(
            bucket,
            assets_by_id,
            exclude=skip_screen_ids,
            preferred_id=preferred,
            median_sharp=med_sharp,
            featured_weight=cur_cfg.featured_weight,
            memory_anchors=anchors or None,
            meta_places=meta_places or None,
        )
        if hero and preferred and hero == preferred:
            used_secondary_heroes.add(hero)
        if hero:
            chapter_heroes[f"ch-{i + 1:02d}"] = hero

    titles = chapter_titles(
        non_empty_buckets,
        layout_assets,
        meta,
        intent=trip.get("intent"),
        bucket_segment_ids=bucket_segment_ids,
        bucket_segment_ids_all=bucket_segment_ids_all,
        segment_labels=peeled.segment_labels,
        plan_cities=(
            ((curation.get("intentHints") or {}).get("planCities"))
            or ((trip.get("intent") or {}).get("travelPlan") or {}).get("cities")
            or []
        ),
    )
    summary = summarize_orientations(layout_assets, export_layout=layout)  # type: ignore[arg-type]
    summary_dict = summary.to_dict()
    from travelogue.layout_engine.adapter import (
        cohort_mosaic_override,
        mosaic_config_from_pack,
        reset_mosaic_config_override,
        set_mosaic_config_override,
    )

    mosaic_override_active = None
    if app_cfg.layout.strategy_engine.enabled:
        from dataclasses import replace as _dc_replace

        mosaic_override_active = mosaic_config_from_pack(app_cfg)
        cohort_ov = cohort_mosaic_override(app_cfg) if cohort_summary else None
        if cohort_ov is not None:
            mw = dict(mosaic_override_active.weights)
            cw = float(cohort_ov.weights.get("cohort_coherence") or 0.0)
            if cw > 0:
                mw["cohort_coherence"] = cw
            mosaic_override_active = _dc_replace(mosaic_override_active, weights=mw)
    elif cohort_summary:
        mosaic_override_active = cohort_mosaic_override(app_cfg)
    # LTN C7 · curated/archive/quick_share track overlay (shared MCS path).
    from travelogue.layout_contract.mosaic_track import resolve_and_apply_mosaic_track

    track_base = mosaic_override_active if mosaic_override_active is not None else app_cfg.mosaic
    intent_mode = str((trip.get("intent") or {}).get("mode") or "")
    mosaic_override_active, _track_params = resolve_and_apply_mosaic_track(
        track_base,
        kept_count=len(layout_assets),
        intent_mode=intent_mode,
    )
    from travelogue.layout_engine.adapter import (
        effective_pattern_blacklist,
        reset_mosaic_disabled_patterns,
        set_mosaic_disabled_patterns,
    )

    pattern_blacklist_active = False
    if app_cfg.layout.strategy_engine.enabled:
        set_mosaic_disabled_patterns(effective_pattern_blacklist(app_cfg))
        pattern_blacklist_active = True
    if mosaic_override_active is not None:
        set_mosaic_config_override(mosaic_override_active)
    if app_cfg.mosaic.enabled:
        from travelogue.layout_engine.adapter import begin_mosaic_capture

        begin_mosaic_capture()
    try:
        from travelogue.curation.layout_density import layout_density_params

        chapters = build_chapters_from_buckets(
            peeled.raw_buckets,
            aspects,
            export_layout=layout,  # type: ignore[arg-type]
            titles=titles,
            layout_engine=engine,
            assets=layout_assets,
            orientation_summary=summary_dict,
            skip_screen_asset_ids=skip_screen_ids,
            trip_photo_total=len(layout_assets),
            pattern_hints=pattern_hints,
            enable_food_grid=cur_cfg.enable_food_grid,
            mundane_grid_buckets=cur_cfg.mundane_grid_buckets,
            layout_density=layout_density_params(trip, app_cfg=app_cfg).density,
            cfg=app_cfg,
            trip=trip,
        )
    finally:
        if mosaic_override_active is not None:
            reset_mosaic_config_override()
        if pattern_blacklist_active:
            reset_mosaic_disabled_patterns()
    from travelogue.curation.bucket_planning import bucket_day_span

    for ch_idx, (ch, bucket, seg_id, seg_ids, hint) in enumerate(
        zip(
            chapters,
            non_empty_buckets,
            bucket_segment_ids,
            bucket_segment_ids_all,
            pattern_hints,
            strict=True,
        )
    ):
        ch_cur = ch.setdefault("curation", {})
        span = bucket_day_span(bucket, assets_by_id)
        if span:
            ch_cur["daySpan"] = span
        if seg_id:
            ch_cur["segmentId"] = seg_id
        if len(seg_ids) > 1:
            ch_cur["segmentIds"] = seg_ids
        ch_cur["patternHint"] = hint
        hero_id = chapter_heroes.get(ch.get("id", ""))
        if hero_id:
            ch_cur["heroAssetId"] = hero_id
        anchor_idx = ch_idx
        if anchor_idx < len(saved_memory_anchors) and saved_memory_anchors[anchor_idx]:
            ch_cur["memoryAnchors"] = list(saved_memory_anchors[anchor_idx])
    excluded_ids = set(curation.get("excludedLowResAssetIds") or [])
    if excluded_ids:
        from travelogue.curation.curate import _sanitize_chapters_after_exclusion

        _sanitize_chapters_after_exclusion(chapters, excluded_ids)

    return {
        "chapters": chapters,
        "non_empty_buckets": non_empty_buckets,
        "bucket_segment_ids": bucket_segment_ids,
        "aspects": aspects,
        "pattern_hints": pattern_hints,
        "arc_profile": arc_profile,
        "use_arc": use_arc,
        "chapter_heroes": chapter_heroes,
        "secondary_hints": secondary_hints,
        "trip_memory_anchors": trip_memory_anchors,
        "summary_dict": summary_dict,
        "appendix_outlier_ids": peeled.appendix_outlier_ids,
        "curation_segments": peeled.curation_segments,
    }


def resolve_compose_scoring(
    trip: dict,
    preflight,
    draft: dict,
    *,
    curate_scope: str,
    cohort_summary: dict | None,
) -> ComposeReady:
    from travelogue.curation.degradation import assess_degradation
    from travelogue.curation.intent_hints import peak_chapter_hints_for_trip
    from travelogue.curation.layout_scoring import ScoringWeights, resolve_scoring_weights
    from travelogue.domain.pipeline import PIPELINE_LOCKED_STATUSES

    app_cfg = preflight.app_cfg
    cur_cfg = preflight.cur_cfg
    layout_assets = preflight.layout_assets
    aspects = draft["aspects"]
    layout_cfg = app_cfg.layout
    pipe_status = (trip.get("pipeline") or {}).get("status") or ""
    structure_locked = pipe_status in PIPELINE_LOCKED_STATUSES
    degradation = assess_degradation(
        layout_assets,
        aspects,
        min_layout_eligible=layout_cfg.scoring.min_layout_eligible,
        min_aspect_kinds=layout_cfg.scoring.min_aspect_kinds,
        structure_locked=structure_locked,
        force_relayout=curate_scope == "tier",
    )
    has_color_metrics = any(a.get("dominantTone") for a in layout_assets)
    scoring_weights = resolve_scoring_weights(
        ScoringWeights.from_dict(layout_cfg.scoring.weights),
        scoring_enabled=layout_cfg.scoring.enabled,
        has_color_metrics=has_color_metrics,
        enable_gravity_balance=cur_cfg.enable_gravity_balance,
    )
    if cohort_summary and app_cfg.cohort.enabled:
        from travelogue.curation.cohort_faces import merge_cohort_weight

        scoring_weights = merge_cohort_weight(scoring_weights, app_cfg.cohort)
    intent_peak = peak_chapter_hints_for_trip(trip, len(draft["non_empty_buckets"]))
    return ComposeReady(
        chapters=draft["chapters"],
        non_empty_buckets=draft["non_empty_buckets"],
        bucket_segment_ids=draft["bucket_segment_ids"],
        aspects=aspects,
        pattern_hints=draft["pattern_hints"],
        arc_profile=draft["arc_profile"],
        use_arc=draft["use_arc"],
        chapter_heroes=draft["chapter_heroes"],
        secondary_hints=draft["secondary_hints"],
        trip_memory_anchors=draft["trip_memory_anchors"],
        summary_dict=draft["summary_dict"],
        appendix_outlier_ids=draft["appendix_outlier_ids"],
        scoring_weights=scoring_weights,
        intent_peak=intent_peak,
        degradation=degradation,
        layout_cfg=layout_cfg,
        curation_segments=draft["curation_segments"],
    )


def materialize_composed_chapters(
    trip: dict,
    preflight,
    ready: ComposeReady,
    chapters: list[dict],
    replan_meta: dict,
    *,
    trip_dir: Path | None,
):
    """Post-compose persist: mosaic logs, appendix, metrics, chapter plan.

    Stays >200 because S-01 return surface writes many curation keys; not the orchestrator.
    """
    from travelogue.curation.layout_metrics import compute_layout_metrics
    from travelogue.layout_contract import LAYOUT_PLAN_VERSION
    from travelogue.layout_contract.engines import (
        LAYOUT_ENGINE_SCREENS,
        LAYOUT_ENGINE_VERSION_SCREENS,
    )

    app_cfg = preflight.app_cfg
    layout = preflight.layout
    engine = preflight.engine
    layout_assets = preflight.layout_assets
    curation = trip.get("curation") or {}
    layout_cfg = ready.layout_cfg
    non_empty_buckets = ready.non_empty_buckets
    aspects = ready.aspects
    pattern_hints = ready.pattern_hints
    chapter_heroes = ready.chapter_heroes
    summary_dict = ready.summary_dict
    appendix_outlier_ids = ready.appendix_outlier_ids
    use_arc = ready.use_arc
    arc_profile = ready.arc_profile

    if engine == LAYOUT_ENGINE_SCREENS:
        from travelogue.curation.chapter_items import compact_chapter_items_for_screens

        compact_chapter_items_for_screens(chapters)
    mosaic_logs_for_metrics = None
    if app_cfg.mosaic.enabled:
        from travelogue.layout_engine.api import (
            annotate_winner_plan_logs,
            drain_mosaic_capture,
            drain_mosaic_dropped,
        )

        mosaic_logs, mosaic_logs_for_metrics = drain_mosaic_capture()
        mosaic_logs = annotate_winner_plan_logs(mosaic_logs, chapters)
        mosaic_logs_for_metrics = annotate_winner_plan_logs(
            mosaic_logs_for_metrics, chapters
        )
        dropped = drain_mosaic_dropped()
        curation = trip.setdefault("curation", {})
        if mosaic_logs:
            curation["mosaicDecisionLog"] = mosaic_logs
        if dropped:
            curation["mosaicDroppedAssetIds"] = list(dict.fromkeys(dropped))
        try:
            from travelogue.ai.agents.mosaic_judge import run_post_compose_mosaic_judge

            run_post_compose_mosaic_judge(
                trip,
                mosaic_logs_for_metrics,
                cfg=app_cfg,
                async_schedule=True,
            )
        except Exception:
            pass
    if mosaic_logs_for_metrics is None:
        mosaic_logs_for_metrics = (trip.get("curation") or {}).get("mosaicDecisionLog")

    # BE-SFI-08 · ≥2 outliers → 册尾附录章（不计 ADR-007 cap / 不进 compose beam）
    if len(appendix_outlier_ids) >= 2:
        from travelogue.curation.time_outlier import build_appendix_chapter

        appendix_ch = build_appendix_chapter(
            appendix_outlier_ids,
            index=len(chapters) + 1,
            aspects=aspects,
            export_layout=layout,
            layout_engine=engine,
            assets=layout_assets,
            orientation_summary=summary_dict,
            trip_photo_total=len(layout_assets),
            cfg=app_cfg,
        )
        if appendix_ch:
            chapters.append(appendix_ch)

    layout_metrics = compute_layout_metrics(
        chapters,
        layout_assets,
        subject_run_tolerance=layout_cfg.scoring.subject_run_tolerance,
        mosaic_logs=mosaic_logs_for_metrics,
    )
    degradation = ready.degradation
    degradation_reason = degradation.reason if degradation.force_legacy and layout_cfg.scoring.enabled else None
    decision_logs = replan_meta.get("decisionLogs") or None

    from travelogue.domain.share_face_purity import (
        enforce_no_ordinal_face_titles,
        sort_chapters_by_temporal_key,
    )

    chapters, sfp_reordered = sort_chapters_by_temporal_key(chapters, layout_assets)
    trip["chapters"] = chapters
    enforce_no_ordinal_face_titles(trip)
    trip["exportLayout"] = layout
    trip["layoutEngine"] = engine
    if engine == LAYOUT_ENGINE_SCREENS:
        trip["layoutEngineVersion"] = LAYOUT_ENGINE_VERSION_SCREENS
    curation = trip.setdefault("curation", {})
    if sfp_reordered:
        curation["sfpChapterTimeSortApplied"] = True
    if degradation_reason:
        curation["degradationReason"] = degradation_reason
    if decision_logs:
        curation["layoutDecisionLog"] = decision_logs
    if app_cfg.mosaic.enabled and app_cfg.mosaic.log_level == "debug":
        mosaic_debug = curation.get("mosaicDecisionLog") or []
        if mosaic_debug:
            merged = list(curation.get("layoutDecisionLog") or [])
            merged.extend(mosaic_debug)
            curation["layoutDecisionLog"] = merged
    if replan_meta.get("searchBudget"):
        curation["layoutSearchBudget"] = replan_meta["searchBudget"]
    if engine == LAYOUT_ENGINE_SCREENS:
        from travelogue.curation.chapter_items import collect_displayed_asset_ids
        from travelogue.layout_engine.adapter import compute_coverage_metrics

        hero_extra = [h for h in (chapter_heroes or {}).values() if h]
        curation["displayedAssetIds"] = collect_displayed_asset_ids(
            chapters, extra_asset_ids=hero_extra
        )
        planned_ids = {aid for bucket in non_empty_buckets for aid in bucket}
        displayed_for_cov = list(curation.get("displayedAssetIds") or [])
        for ch in chapters:
            hero_id = (ch.get("curation") or {}).get("heroAssetId")
            if hero_id and hero_id not in displayed_for_cov:
                displayed_for_cov.append(hero_id)
        geo_recovered = (
            (trip.get("meta") or {}).get("geoBucketRecovery") or {}
        ).get("recoveredAssetIds")
        layout_metrics.update(
            compute_coverage_metrics(
                displayed_asset_ids=displayed_for_cov,
                layout_eligible_assets=layout_assets,
                dropped_asset_ids=curation.get("mosaicDroppedAssetIds"),
                planned_asset_ids=planned_ids or None,
                geo_recovered_asset_ids=geo_recovered,
            )
        )
    if use_arc:
        from travelogue.curation.arc_patterns import arc_profile_to_dict

        curation["arcProfile"] = arc_profile_to_dict(arc_profile)
    curation["layoutMetrics"] = layout_metrics
    from travelogue.layout_engine.adapter import persist_layout_observability

    persist_layout_observability(
        curation,
        trip_dir=trip_dir,
        cfg=app_cfg,
        mosaic_logs=curation.get("mosaicDecisionLog"),
        beam_logs=decision_logs,
    )
    if app_cfg.layout.strategy_engine.enabled:
        from travelogue.layout_engine.adapter import (
            build_editorial_hints,
            editorial_hints_from_pack,
            effective_capabilities,
            resolve_pack,
        )

        pack = resolve_pack(app_cfg)
        caps = effective_capabilities(app_cfg, pack)
        ed_cfg = editorial_hints_from_pack(pack.raw if pack else None)
        if caps.editorial_hints or ed_cfg.get("enabled"):
            assets_map = {str(a["id"]): a for a in (trip.get("assets") or []) if a.get("id")}
            curation["editorialHints"] = build_editorial_hints(
                chapters,
                assets_map,
                breath_gap_threshold=int(ed_cfg.get("breath_gap_threshold") or 3),
                folio_tone_delta_max=float(ed_cfg.get("folio_tone_delta_max") or 12.0),
            )
    if engine == LAYOUT_ENGINE_SCREENS:
        from travelogue.layout_engine.adapter import (
            record_mosaic_layout_metrics,
            record_per_template_layout_metrics,
        )

        record_mosaic_layout_metrics(
            trip_id=trip.get("tripId"),
            layout_metrics=layout_metrics,
            mosaic_enabled=app_cfg.mosaic.enabled,
        )
        record_per_template_layout_metrics(
            trip_id=trip.get("tripId"),
            chapters=chapters,
            mosaic_logs=mosaic_logs_for_metrics,
        )
    curation["curatePlanVersion"] = "1.1"
    curation["orientationSummary"] = summary_dict
    curation["layoutPlanVersion"] = LAYOUT_PLAN_VERSION
    curation["chapterPlan"] = []
    for i, ch in enumerate(chapters):
        ch_cur_plan = ch.get("curation") or {}
        if ch_cur_plan.get("isAppendix"):
            asset_count = len(ch_cur_plan.get("appendixAssetIds") or appendix_outlier_ids)
        elif i < len(non_empty_buckets):
            asset_count = len(non_empty_buckets[i])
        else:
            asset_count = 0
        plan_entry: dict = {
            "chapterIndex": ch.get("index"),
            "chapterId": ch.get("id"),
            "assetCount": asset_count,
            "daySpan": ch_cur_plan.get("daySpan"),
            "segmentId": ch_cur_plan.get("segmentId"),
            "patternHint": pattern_hints[i] if i < len(pattern_hints) else None,
            "patternId": ch.get("patternId"),
            "isAppendix": bool(ch_cur_plan.get("isAppendix")),
        }
        hero_plan_id = chapter_heroes.get(ch.get("id", ""))
        if hero_plan_id:
            plan_entry["heroAssetId"] = hero_plan_id
        curation["chapterPlan"].append(plan_entry)
    if chapter_heroes:
        curation["chapterHeroAssetIds"] = dict(chapter_heroes)

    from travelogue.curation.chapter_items import summarize_screen_patterns

    pattern_summary = summarize_screen_patterns(chapters)
    if pattern_summary:
        curation["layoutPlanSummary"] = pattern_summary
    curation_segments = ready.curation_segments
    if curation_segments:
        curation["segments"] = curation_segments
        if len(curation_segments) == 1:
            curation["primarySegmentId"] = curation_segments[0]["id"]
        else:
            best = max(curation_segments, key=lambda s: len(s.get("assetIds") or []))
            curation["primarySegmentId"] = best["id"]
    from travelogue.media.media_classify import summarize_media_classes

    mc = summarize_media_classes(trip.get("assets") or [])
    if mc:
        curation["mediaClassSummary"] = mc

    from travelogue.curation.curate import _ChaptersComposeResult

    return _ChaptersComposeResult(
        chapters=chapters,
        replan_meta=replan_meta,
        non_empty_buckets=non_empty_buckets,
        bucket_segment_ids=ready.bucket_segment_ids,
        pattern_hints=pattern_hints,
        arc_profile=arc_profile,
        use_arc=use_arc,
        chapter_heroes=chapter_heroes,
        secondary_hints=ready.secondary_hints,
        trip_memory_anchors=ready.trip_memory_anchors,
        summary_dict=summary_dict,
        layout_metrics=layout_metrics,
        degradation_reason=degradation_reason,
        decision_logs=decision_logs,
    )
