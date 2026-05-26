"""Agent 1 · Curator — day-based chapters, cover, then layout."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from travelogue.curation.bucket_planning import (
    bucket_day_span,
    cap_book_buckets,
    group_assets_by_day,
    group_assets_by_segments,
    merge_small_buckets,
    merge_small_buckets_with_segments,
    normalize_bucket_counts,
)
from travelogue.curation.curate_patterns import pattern_hint_for_bucket
from travelogue.curation.curate_scoring import (
    cover_candidates as _cover_candidates,
    cover_score as _cover_score,
    median_sharpness,
    pick_chapter_hero,
    pick_cover_asset_id as _pick_cover_asset_id,
)
from travelogue.curation.chapter_titles import chapter_titles, title_for_bucket_span
from travelogue.curation.layout_planner import (
    aspect_kind_for_asset,
    build_chapters_from_buckets,
    summarize_orientations,
)
from travelogue.curation.time_segments import TimeSegment, parse_asset_date
from travelogue.services.layout import LAYOUT_PLAN_VERSION, format_layout_summary
from travelogue.services.pipeline_state import set_layout_status

# Backward-compatible private aliases for tests and internal callers.
_cap_book_buckets = cap_book_buckets
_chapter_titles = chapter_titles
_group_assets_by_day = group_assets_by_day
_group_assets_by_segments = group_assets_by_segments
_merge_small_buckets = merge_small_buckets
_merge_small_buckets_with_segments = merge_small_buckets_with_segments
_normalize_bucket_counts = normalize_bucket_counts
_title_for_bucket_span = title_for_bucket_span
_bucket_day_span = bucket_day_span
_parse_asset_date = parse_asset_date


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class CurateError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass
class CurateResult:
    chapter_count: int
    cover_asset_id: str
    layout_summary: str
    day_groups: int
    warnings: list[str]


def _date_span_warning(
    assets: list[dict],
    segments: list | None = None,
    *,
    max_span_days: int = 365,
) -> str | None:
    """Warn when multiple time segments or a very wide date span is detected."""
    if segments and len(segments) >= 2:
        labels = []
        for s in segments:
            if isinstance(s, TimeSegment):
                labels.append(s.label)
            else:
                labels.append(str(s.get("label", s.get("id", ""))))
        preview = "、".join(labels[:4])
        if len(segments) > 4:
            preview += f" 等{len(segments)}段"
        return (
            f"检测到 {len(segments)} 个时间段（{preview}），已合成一本并按段编排；"
            "可在 G1 合并段，或拆成多本游记"
        )

    dates = [d for a in assets if (d := parse_asset_date(a))]
    if len(dates) < 2:
        return None
    lo, hi = min(dates), max(dates)
    span = (hi - lo).days
    if span > max_span_days:
        return (
            f"素材拍摄日跨度 {span} 天（{lo.isoformat()} – {hi.isoformat()}），"
            "已合成一本并按日期编排；可在 G1 合并时间段或拆成多本"
        )
    return None


def layout_eligible_assets(trip: dict) -> list[dict]:
    """Assets usable for cover, chapters, and screens (excludes low-res curation drops)."""
    excluded = set((trip.get("curation") or {}).get("excludedLowResAssetIds") or [])
    return [
        a
        for a in trip.get("assets") or []
        if a["id"] not in excluded and a.get("type", "image") != "video"
    ]


def apply_low_resolution_exclusion(
    trip: dict,
    *,
    trip_dir: Path | None = None,
) -> str | None:
    """Mark明显偏低分辨率 assets; returns warning message if any dropped."""
    from travelogue.curation.asset_quality import (
        apply_layout_eligibility_marks,
        backfill_native_dimensions,
    )

    if trip_dir is not None:
        backfill_native_dimensions(trip, Path(trip_dir))

    return apply_layout_eligibility_marks(trip)


def resolve_cover_asset_id(
    trip: dict,
    *,
    export_layout: str,
) -> str:
    """Pick cover for render/curate profile (mobile | web | auto→mobile)."""
    assets = layout_eligible_assets(trip)
    if not assets:
        return ""
    profile = export_layout
    if profile == "auto":
        profile = "mobile"
    by_layout = (trip.get("curation") or {}).get("coverByLayout") or {}
    if isinstance(by_layout, dict) and profile in by_layout:
        cid = by_layout[profile]
        if cid and any(a.get("id") == cid for a in assets):
            return cid
    return _pick_cover_asset_id(assets, export_layout=profile)


def sync_trip_covers(
    trip: dict,
    *,
    export_layout: str | None = None,
    assets: list[dict] | None = None,
) -> str:
    """Write coverAssetId (+ coverByLayout when exportLayout=auto). Returns primary cover id."""
    assets = assets if assets is not None else layout_eligible_assets(trip)
    layout = export_layout or trip.get("exportLayout") or "auto"
    curation = trip.setdefault("curation", {})

    if layout == "auto":
        mobile_id = _pick_cover_asset_id(assets, export_layout="mobile")
        web_id = _pick_cover_asset_id(assets, export_layout="web")
        curation["coverByLayout"] = {"mobile": mobile_id, "web": web_id}
        trip["coverAssetId"] = mobile_id
        trip["coverCandidates"] = _cover_candidates(assets, mobile_id, export_layout="mobile")
        curation["coverCandidatesByLayout"] = {
            "mobile": _cover_candidates(assets, mobile_id, export_layout="mobile"),
            "web": _cover_candidates(assets, web_id, export_layout="web"),
        }
        return mobile_id

    cover_id = _pick_cover_asset_id(assets, export_layout=layout)
    trip["coverAssetId"] = cover_id
    trip["coverCandidates"] = _cover_candidates(assets, cover_id, export_layout=layout)
    curation.pop("coverByLayout", None)
    curation.pop("coverCandidatesByLayout", None)
    return cover_id


from travelogue.curation.chapter_items import (
    MAX_CHAPTER_ITEMS,
    collect_screen_asset_ids,
    item_asset_ids,
    items_from_asset_ids,
)


def _filter_item_excluded(item: dict, excluded: set[str]) -> dict | None:
    itype = item.get("type")
    if itype == "media-card":
        aid = item.get("assetId")
        if not aid or aid in excluded:
            return None
        return item
    if itype in ("media-row", "media-scroll"):
        aids = [a for a in item.get("assetIds") or [] if a not in excluded]
        if not aids:
            return None
        out = dict(item)
        out["assetIds"] = aids
        return out
    return item


def _sanitize_chapters_after_exclusion(chapters: list[dict], excluded: set[str]) -> None:
    """Drop excluded assets from items[] and keep within schema maxItems."""
    for ch in chapters:
        items = []
        for it in ch.get("items", []):
            kept = _filter_item_excluded(it, excluded)
            if kept is not None:
                items.append(kept)
        if len(items) > MAX_CHAPTER_ITEMS:
            aids = [
                aid
                for aid in collect_screen_asset_ids(ch)
                if aid not in excluded
            ]
            if not aids:
                flat: list[str] = []
                for it in items:
                    flat.extend(aid for aid in item_asset_ids(it) if aid not in flat)
                aids = flat
            if aids:
                items = items_from_asset_ids(aids)
            else:
                items = items[:MAX_CHAPTER_ITEMS]
        ch["items"] = items


def run_curate(
    trip: dict,
    *,
    export_layout: str | None = None,
    layout_engine: str | None = None,
    apply_layout: bool = True,
    trip_dir: Path | None = None,
) -> CurateResult:
    if len(trip.get("assets") or []) < 4:
        raise CurateError("E_CURATE_TOO_FEW", "need at least 4 assets to curate")

    res_warn = apply_low_resolution_exclusion(trip, trip_dir=trip_dir)
    layout_assets = layout_eligible_assets(trip)
    if len(layout_assets) < 4:
        raise CurateError(
            "E_CURATE_TOO_FEW",
            "need at least 4 layout-eligible assets after resolution filter",
        )

    from travelogue.curation.screen_planner import (
        LAYOUT_ENGINE_LEGACY,
        LAYOUT_ENGINE_SCREENS,
        LAYOUT_ENGINE_VERSION_SCREENS,
    )

    from travelogue.config import default_web_layout_engine, get_config

    app_cfg = get_config()
    cur_cfg = app_cfg.curate
    layout = export_layout or trip.get("exportLayout") or "auto"
    engine = (
        layout_engine
        or trip.get("layoutEngine")
        or default_web_layout_engine(layout)
    )
    if engine not in (LAYOUT_ENGINE_LEGACY, LAYOUT_ENGINE_SCREENS):
        engine = LAYOUT_ENGINE_LEGACY
    cover_id = sync_trip_covers(trip, export_layout=layout, assets=layout_assets)
    curation = trip.get("curation") or {}
    by_layout = curation.get("coverByLayout") or {}
    skip_screen_ids: set[str] = set()
    if layout in ("auto", "web") and isinstance(by_layout, dict):
        web_cover = by_layout.get("web") or ""
        if web_cover:
            skip_screen_ids.add(web_cover)

    meta = trip.get("meta", {})
    buckets, bucket_segment_ids, bucket_segment_ids_all, segments = group_assets_by_segments(
        layout_assets,
        cover_id,
        meta,
        segment_gap_days=cur_cfg.segment_gap_days,
        city_gap_days=cur_cfg.city_gap_days,
        min_bucket_size=cur_cfg.min_bucket_size,
    )
    segment_labels = {s.id: s.label for s in segments}
    curation_segments = [s.to_dict() for s in segments]

    aspects = {a["id"]: aspect_kind_for_asset(a) for a in layout_assets}
    non_empty_buckets = [b for b in buckets if b]
    arc_profile = "dynamic"
    use_arc = cur_cfg.arc_mode in ("v2_adaptive", "v2_five_beat")
    if use_arc:
        from travelogue.curation.arc_patterns import (
            arc_pattern_hint_for_bucket,
            arc_profile_to_dict,
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
    chapter_heroes: dict[str, str] = {}
    for i, bucket in enumerate(non_empty_buckets):
        hero = pick_chapter_hero(
            bucket,
            assets_by_id,
            exclude=skip_screen_ids,
            median_sharp=med_sharp,
        )
        if hero:
            chapter_heroes[f"ch-{i + 1:02d}"] = hero

    titles = chapter_titles(
        buckets,
        layout_assets,
        meta,
        bucket_segment_ids=bucket_segment_ids,
        bucket_segment_ids_all=bucket_segment_ids_all,
        segment_labels=segment_labels,
    )
    summary = summarize_orientations(layout_assets, export_layout=layout)  # type: ignore[arg-type]
    summary_dict = summary.to_dict()
    chapters = build_chapters_from_buckets(
        buckets,
        aspects,
        export_layout=layout,  # type: ignore[arg-type]
        titles=titles,
        layout_engine=engine,
        assets=layout_assets,
        orientation_summary=summary_dict,
        skip_screen_asset_ids=skip_screen_ids,
        trip_photo_total=len(layout_assets),
        pattern_hints=pattern_hints,
    )
    for ch, bucket, seg_id, seg_ids, hint in zip(
        chapters,
        non_empty_buckets,
        bucket_segment_ids,
        bucket_segment_ids_all,
        pattern_hints,
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
    excluded_ids = set(curation.get("excludedLowResAssetIds") or [])
    if excluded_ids:
        _sanitize_chapters_after_exclusion(chapters, excluded_ids)

    from travelogue.curation.degradation import assess_degradation
    from travelogue.curation.layout_metrics import compute_layout_metrics
    from travelogue.curation.layout_scoring import ScoringWeights
    from travelogue.curation.layout_search import maybe_replan_chapters

    layout_cfg = app_cfg.layout
    pipe_status = (trip.get("pipeline") or {}).get("status") or ""
    structure_locked = pipe_status in (
        "structure_locked",
        "copy_draft",
        "copy_locked",
        "rendered",
        "exported",
    )
    degradation = assess_degradation(
        layout_assets,
        aspects,
        min_layout_eligible=layout_cfg.scoring.min_layout_eligible,
        min_aspect_kinds=layout_cfg.scoring.min_aspect_kinds,
        structure_locked=structure_locked,
        force_relayout=False,
    )
    scoring_weights = ScoringWeights.from_dict(layout_cfg.scoring.weights)
    chapters, replan_meta = maybe_replan_chapters(
        chapters,
        buckets=non_empty_buckets,
        aspects=aspects,
        assets=layout_assets,
        scoring_enabled=layout_cfg.scoring.enabled,
        weights=scoring_weights,
        beam_width=layout_cfg.scoring.beam_width,
        degradation=degradation,
        arc_mode=cur_cfg.arc_mode,
        arc_profile=arc_profile,
        chapter_heroes=chapter_heroes,
        orientation_summary=summary_dict,
        skip_screen_asset_ids=skip_screen_ids,
        mixed_proximity_seconds=layout_cfg.mixed_proximity_seconds,
        trip_photo_total=len(layout_assets),
        search_timeout_ms=layout_cfg.scoring.search_timeout_ms,
        max_candidates_per_bucket=layout_cfg.scoring.max_candidates_per_bucket,
        max_evaluations_per_trip=layout_cfg.scoring.max_evaluations_per_trip,
        allow_burst_split=layout_cfg.scoring.allow_burst_split,
        subject_run_tolerance=layout_cfg.scoring.subject_run_tolerance,
    )
    layout_metrics = compute_layout_metrics(chapters)
    degradation_reason = degradation.reason if degradation.force_legacy and layout_cfg.scoring.enabled else None
    decision_logs = replan_meta.get("decisionLogs") or None

    trip["chapters"] = chapters
    trip["exportLayout"] = layout
    trip["layoutEngine"] = engine
    if engine == LAYOUT_ENGINE_SCREENS:
        trip["layoutEngineVersion"] = LAYOUT_ENGINE_VERSION_SCREENS
    curation = trip.setdefault("curation", {})
    if degradation_reason:
        curation["degradationReason"] = degradation_reason
    if decision_logs:
        curation["layoutDecisionLog"] = decision_logs
    if replan_meta.get("searchBudget"):
        curation["layoutSearchBudget"] = replan_meta["searchBudget"]
    if use_arc:
        from travelogue.curation.arc_patterns import arc_profile_to_dict

        curation["arcProfile"] = arc_profile_to_dict(arc_profile)
    curation["layoutMetrics"] = layout_metrics
    curation["curatePlanVersion"] = "1.1"
    curation["orientationSummary"] = summary_dict
    curation["layoutPlanVersion"] = LAYOUT_PLAN_VERSION
    curation["chapterPlan"] = [
        {
            "chapterIndex": ch.get("index"),
            "chapterId": ch.get("id"),
            "assetCount": len(non_empty_buckets[i]) if i < len(non_empty_buckets) else 0,
            "daySpan": (ch.get("curation") or {}).get("daySpan"),
            "segmentId": (ch.get("curation") or {}).get("segmentId"),
            "patternHint": pattern_hints[i] if i < len(pattern_hints) else None,
            "patternId": ch.get("patternId"),
            "heroAssetId": chapter_heroes.get(ch.get("id", "")),
        }
        for i, ch in enumerate(chapters)
    ]
    if chapter_heroes:
        curation["chapterHeroAssetIds"] = dict(chapter_heroes)

    from travelogue.curation.chapter_items import summarize_screen_patterns

    pattern_summary = summarize_screen_patterns(chapters)
    if pattern_summary:
        curation["layoutPlanSummary"] = pattern_summary
    if curation_segments:
        curation["segments"] = curation_segments
        if len(curation_segments) == 1:
            curation["primarySegmentId"] = curation_segments[0]["id"]
        else:
            best = max(curation_segments, key=lambda s: len(s.get("assetIds") or []))
            curation["primarySegmentId"] = best["id"]
    from travelogue.curation.media_classify import summarize_media_classes

    mc = summarize_media_classes(trip.get("assets") or [])
    if mc:
        curation["mediaClassSummary"] = mc
    warnings: list[str] = []
    span_warn = _date_span_warning(layout_assets, segments)
    if span_warn:
        warnings.append(span_warn)
    if res_warn:
        warnings.append(res_warn)

    cross_seg = sum(
        1 for ch in chapters if len((ch.get("curation") or {}).get("segmentIds") or []) > 1
    )
    if cross_seg:
        warnings.append(f"{cross_seg} 章跨时间段合并，章标题已标注多段信息")

    undated_seg = any(s.label.startswith("未标注") for s in segments)
    if undated_seg:
        warnings.append("含未标注日期照片，已单独成段或置于末段")

    if warnings:
        curation["warnings"] = warnings

    layout_summary = format_layout_summary(summary_dict, chapters)
    pipe = trip.setdefault("pipeline", {})
    now = _utc_now_iso()
    if apply_layout:
        set_layout_status(trip, "layout_draft")
        pipe.setdefault("runs", []).append(
            {
                "runId": f"layout-{trip.get('tripId', 'trip')}",
                "agent": "layout",
                "startedAt": now,
                "finishedAt": now,
                "model": None,
            }
        )
    else:
        set_layout_status(trip, "pending")

    pipe["status"] = "structure_draft"
    pipe["pendingAssets"] = []
    trip["updatedAt"] = now
    pipe.setdefault("runs", []).append(
        {
            "runId": f"curate-{trip.get('tripId', 'trip')}",
            "agent": "curator",
            "startedAt": now,
            "finishedAt": now,
            "model": None,
        }
    )

    return CurateResult(
        chapter_count=len(trip.get("chapters", [])),
        cover_asset_id=cover_id,
        layout_summary=layout_summary,
        day_groups=len(buckets),
        warnings=warnings,
    )
