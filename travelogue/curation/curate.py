"""Agent 1 · Curator — S-01 sole compose fork; no is_portfolio in mosaic / editorial_series."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from travelogue.config import AppConfig, CurateConfig
from travelogue.curation.bucket_planning import (
    bucket_day_span,
    cap_book_buckets,
    group_assets_by_day,
    group_assets_by_segments,
    merge_small_buckets,
    merge_small_buckets_with_segments,
    normalize_bucket_counts,
)
from travelogue.curation.chapter_titles import chapter_titles, title_for_bucket_span
from travelogue.curation.cover_sync import _cover_explain_for
from travelogue.curation.curate_limits import (
    COMPACT_ALBUM_PHOTO_CAP,
    MIN_CURATE_ASSETS,
    SEGMENT_LABEL_PREVIEW_LIMIT,
    SMALL_ALBUM_PHOTO_CAP,
)
from travelogue.curation.curate_scoring import (
    pick_cover_asset_id as _pick_cover_asset_id,
)
from travelogue.curation.time_segments import TimeSegment, parse_asset_date
from travelogue.domain.cover_view import (
    layout_eligible_assets,
    resolve_cover_render_profile,
)
from travelogue.domain.cover_view import (
    resolve_cover_asset_id as _resolve_cover_asset_id_from_trip,
)
from travelogue.domain.pipeline_view import (
    append_pipeline_run,
    clear_pending_assets,
    set_layout_status,
    set_pipeline_status,
)
from travelogue.errors import CodeError
from travelogue.layout_contract import format_layout_summary
from travelogue.util.datetime_ import utc_now_iso as _utc_now_iso

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

_log = logging.getLogger(__name__)


class CurateError(CodeError):
    pass


@dataclass
class CurateResult:
    chapter_count: int
    cover_asset_id: str
    layout_summary: str
    day_groups: int
    warnings: list[str]


from travelogue.curation.curate_stages import stage_refresh_cull_cohort  # noqa: E402


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
        preview = "、".join(labels[:SEGMENT_LABEL_PREVIEW_LIMIT])
        if len(segments) > SEGMENT_LABEL_PREVIEW_LIMIT:
            preview += f" 等{len(segments)}段"
        return (
            f"检测到 {len(segments)} 个时间段（{preview}），已合成一本并按段编排；"
            "可在 G1 合并段，或拆成多本画册"
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


READING_LARGE_SCREEN_THRESHOLD = 36
READING_LARGE_ASSET_THRESHOLD = 100


def reading_experience_warnings(
    trip: dict,
    chapters: list[dict],
    layout_assets: list[dict],
) -> list[str]:
    """Warn on heavy reading-mode combos (PRD-EXPERIENCE §9 · P3-4)."""
    reading = (trip.get("export") or {}).get("reading") or {}
    scroll = reading.get("scroll") or {}
    breath = str(scroll.get("breath") or "")
    folio = str(scroll.get("folio") or "")
    profile = str(reading.get("profile") or "")

    if profile == "magazine":
        breath = breath or "flow"
        folio = folio or "full"
    elif profile == "default_hybrid":
        folio = folio or "lite"

    if breath != "cinematic" or folio != "full":
        return []

    out: list[str] = []
    screen_count = sum(len(ch.get("screens") or []) for ch in chapters)
    photo_count = len(layout_assets)

    out.append(
        "reading · cinematic + folio full 同开 · 建议改用 default_hybrid 或 folio=lite"
    )
    if screen_count >= READING_LARGE_SCREEN_THRESHOLD:
        out.append(
            f"reading · cinematic + folio full + {screen_count} 屏 · 大 trip 建议降级 default_hybrid"
        )
    if photo_count >= READING_LARGE_ASSET_THRESHOLD:
        out.append(
            f"reading · cinematic + folio full + {photo_count} 张图 · 性能风险 WARN"
        )
    return out


def apply_low_resolution_exclusion(
    trip: dict,
    *,
    trip_dir: Path | None = None,
    app_cfg: AppConfig | None = None,
) -> str | None:
    """Mark明显偏低分辨率 assets; returns warning message if any dropped."""
    from travelogue.curation.asset_quality import (
        apply_layout_eligibility_marks,
        backfill_native_dimensions,
    )

    if trip_dir is not None:
        backfill_native_dimensions(trip, Path(trip_dir))

    return apply_layout_eligibility_marks(trip, app_cfg=app_cfg)


def resolve_cover_asset_id(
    trip: dict,
    *,
    export_layout: str,
    index_name: str | None = None,
    layout_engine: str | None = None,
) -> str:
    """Pick cover for render/curate profile (mobile | web | auto→surface)."""
    cid = _resolve_cover_asset_id_from_trip(
        trip,
        export_layout=export_layout,
        index_name=index_name,
        layout_engine=layout_engine,
    )
    if cid:
        return cid
    assets = layout_eligible_assets(trip)
    if not assets:
        return ""
    profile = resolve_cover_render_profile(
        export_layout,
        index_name=index_name or "index.html",
        layout_engine=layout_engine or trip.get("layoutEngine"),
    )
    return _pick_cover_asset_id(assets, export_layout=profile)


def _attach_cover_explain(
    curation: dict,
    assets: list[dict],
    cover_id: str,
    export_layout: str,
) -> None:
    explain = _cover_explain_for(assets, cover_id, export_layout)
    if explain:
        curation["coverExplain"] = explain
    else:
        curation.pop("coverExplain", None)


def sync_trip_covers(
    trip: dict,
    *,
    export_layout: str | None = None,
    assets: list[dict] | None = None,
    featured_weight: float = 1.35,
    featured_min_for_cover_pool: int = 2,
    enable_phase6_cover_factors: bool = True,
    cover_scoring=None,
    cover_scoring_v2=None,
    scoring_version: str | None = None,
    force: bool = False,
    joint_enabled: bool | None = None,
) -> str:
    """Write coverAssetId (+ coverByLayout when exportLayout=auto). Returns primary cover id.

    B1 · delegates to cover_engine.api.resolve_opening (D-CSV6-53 / Bookends).
    """
    from travelogue.cover_engine.api import resolve_opening

    decision = resolve_opening(
        trip,
        layout=export_layout,
        assets=assets,
        featured_weight=featured_weight,
        featured_min_for_cover_pool=featured_min_for_cover_pool,
        enable_phase6_cover_factors=enable_phase6_cover_factors,
        cover_scoring=cover_scoring,
        cover_scoring_v2=cover_scoring_v2,
        scoring_version=scoring_version,
        force=force,
        joint_enabled=joint_enabled,
    )
    return decision.cover_asset_id


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


@dataclass
class _CuratePreflight:
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
class _CurateBucketPlan:
    buckets: list[list[str]]
    bucket_segment_ids: list[str]
    bucket_segment_ids_all: list[list[str]]
    segments: list
    segment_labels: dict[str, str]
    curation_segments: list[dict]
    meta_places: list[str]



@dataclass
class _ChaptersComposeResult:
    chapters: list[dict]
    replan_meta: dict
    non_empty_buckets: list[list[str]]
    bucket_segment_ids: list[str]
    pattern_hints: list
    arc_profile: str
    use_arc: bool
    chapter_heroes: dict[str, str]
    secondary_hints: list
    trip_memory_anchors: list[str]
    summary_dict: dict
    layout_metrics: dict
    degradation_reason: str | None
    decision_logs: list | None

def _curate_preflight(
    trip: dict,
    *,
    export_layout: str | None,
    layout_engine: str | None,
    trip_dir: Path | None,
    cfg: AppConfig | None,
    saved_memory_anchors: list[list[str] | None],
    cover_force: bool = False,
) -> _CuratePreflight:
    from travelogue.config import default_web_layout_engine, get_config
    from travelogue.layout_contract.engines import (
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
        from travelogue.layout_engine.adapter import resolve_lse_config_for_trip

        app_cfg = resolve_lse_config_for_trip(app_cfg, trip_id)
    # LVP M1 · trip.studio.layoutVibe overlays mosaic MTSO/MEGC/MSA (⊥ LSE flags)
    from travelogue.config.layout_vibe import apply_layout_vibe_to_config

    app_cfg = apply_layout_vibe_to_config(trip, app_cfg)
    from travelogue.curation.curate_preprocess import run_curation_preprocess
    res_warn = run_curation_preprocess(trip, trip_dir=trip_dir, app_cfg=app_cfg)
    # BE-SFI-08 · 时间离群打标（多段豁免在 detect 内）
    from travelogue.curation.time_outlier import apply_time_outlier_marks
    from travelogue.curation.time_segments import cluster_time_segments

    _eligible = [a for a in (trip.get("assets") or []) if a.get("layoutEligible", True)]
    _segs = cluster_time_segments(
        _eligible,
        gap_days=int(app_cfg.curate.segment_gap_days or 14),
    )
    _seg_sizes = [len(getattr(s, "asset_ids", None) or []) for s in _segs]
    _outlier_ids = apply_time_outlier_marks(
        trip,
        segments_count=len(_segs),
        segment_sizes=_seg_sizes,
    )
    if _outlier_ids:
        try:
            from travelogue.curation.time_segments import parse_asset_date
            from travelogue.domain.studio_events import append_studio_homepage_event

            dated = [
                parse_asset_date(a)
                for a in _eligible
                if parse_asset_date(a) is not None
            ]
            span_days = (
                (max(dated) - min(dated)).days if len(dated) >= 2 else 0
            )
            conf_dist: dict[str, int] = {}
            oid_set = set(_outlier_ids)
            for a in trip.get("assets") or []:
                if not isinstance(a, dict) or a.get("id") not in oid_set:
                    continue
                key = str(a.get("dateConfidence") or "unknown")
                conf_dist[key] = conf_dist.get(key, 0) + 1
            append_studio_homepage_event(
                "outlier_isolated",
                {
                    "trip_id": str(trip.get("tripId") or ""),
                    "n_outliers": len(_outlier_ids),
                    "span_days": span_days,
                    "dateConfidence": conf_dist,
                },
            )
        except Exception:  # noqa: BLE001 — telemetry must not break curate
            pass
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
    return _CuratePreflight(
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


def _build_curate_buckets(trip: dict, preflight: _CuratePreflight) -> _CurateBucketPlan:
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

    weak_merges = 0
    if should_use_clustering_buckets(trip, preflight.app_cfg):
        buckets, bucket_segment_ids, bucket_segment_ids_all, segments = build_buckets_from_clustering(
            trip,
            layout_assets,
            cover_id,
            meta,
            cfg=preflight.app_cfg,
            min_bucket_size=cur_cfg.min_bucket_size,
        )
        weak_merges = int((trip.get("curation") or {}).get("sfpWeakDayMergeCount") or 0)
        # clustering 回退到 group_assets_by_segments 时计数写在 meta 侧写
        weak_merges += int(meta.pop("_sfpWeakDayMergeCount", 0) or 0)
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
        weak_merges = int(meta.pop("_sfpWeakDayMergeCount", 0) or 0)

    if len(layout_assets) <= SMALL_ALBUM_PHOTO_CAP:
        from travelogue.curation.bucket_planning import normalize_bucket_counts

        max_ch = 2 if len(layout_assets) <= COMPACT_ALBUM_PHOTO_CAP else 3
        by_id = {a["id"]: a for a in layout_assets if a.get("id")}
        norm = normalize_bucket_counts(
            buckets,
            bucket_segment_ids,
            max_chapters=max_ch,
            min_bucket_size=min(2, cur_cfg.min_bucket_size),
            chapter_balance_enabled=cur_cfg.chapter_balance_enabled,
            chapter_balance_ratio=cur_cfg.chapter_balance_ratio,
            assets_by_id=by_id,
        )
        buckets = norm.buckets
        bucket_segment_ids = norm.primary_segment_ids
        bucket_segment_ids_all = norm.segment_ids_per_bucket
        weak_merges += int(norm.weak_same_day_merges or 0)

    if weak_merges:
        trip.setdefault("curation", {})["sfpWeakDayMergeCount"] = weak_merges

    from travelogue.layout_engine.adapter import (
        apply_segment_order_to_buckets,
        effective_capabilities,
        lse_enabled,
        resolve_pack,
    )

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
    return _CurateBucketPlan(
        buckets=buckets,
        bucket_segment_ids=bucket_segment_ids,
        bucket_segment_ids_all=bucket_segment_ids_all,
        segments=segments,
        segment_labels=segment_labels,
        curation_segments=curation_segments,
        meta_places=meta_places,
    )


def _build_layout_only_bucket_plan(trip: dict, preflight: _CuratePreflight) -> _CurateBucketPlan | None:
    from travelogue.domain.copy_subject import effective_meta_places
    from travelogue.layout_engine.adapter import buckets_from_existing_chapters

    raw = buckets_from_existing_chapters(trip)
    if raw is None:
        return None
    meta = trip.get("meta", {})
    meta_places = effective_meta_places(
        meta,
        intent=trip.get("intent"),
        assets=trip.get("assets") or [],
    )
    return _CurateBucketPlan(
        buckets=raw["buckets"],
        bucket_segment_ids=raw["bucket_segment_ids"],
        bucket_segment_ids_all=raw["bucket_segment_ids_all"],
        segments=raw["segments"],
        segment_labels=raw["segment_labels"],
        curation_segments=raw["curation_segments"],
        meta_places=meta_places,
    )





def _stage_aesthetic_align(
    trip: dict,
    *,
    trip_dir: Path | None,
    app_cfg: AppConfig,
) -> None:
    if trip_dir is not None and app_cfg.aesthetic.enabled:
        from travelogue.curation.aesthetic_score import apply_aesthetic_alignment

        apply_aesthetic_alignment(
            trip.get("assets") or [],
            trip_dir=trip_dir,
            cfg=app_cfg,
            trip=trip,
        )

def _stage_resolve_buckets(
    trip: dict,
    preflight: _CuratePreflight,
    *,
    curate_scope: str,
    trip_dir: Path | None,
    cohort_summary: dict | None,
) -> _CurateBucketPlan:
    from travelogue.layout_engine.adapter import (
        mark_layout_replan,
        should_layout_only_replan,
    )

    replan_decision = should_layout_only_replan(trip, trip_dir=trip_dir, cfg=preflight.app_cfg)
    if curate_scope == "tier":
        bucket_plan = _build_layout_only_bucket_plan(trip, preflight)
        if bucket_plan is None:
            raise CurateError(
                "E_CURATE_NO_STRUCTURE",
                "tier scope requires existing chapter structure",
            )
        mark_layout_replan(trip, reason="tier_rerank")
    elif replan_decision.layout_only:
        bucket_plan = _build_layout_only_bucket_plan(trip, preflight)
        if bucket_plan is None:
            bucket_plan = _build_curate_buckets(trip, preflight)
        else:
            mark_layout_replan(trip, reason=replan_decision.reason or "density_change")
    else:
        bucket_plan = _build_curate_buckets(trip, preflight)
    trip.get("meta", {})
    curation = trip.get("curation") or {}
    if cohort_summary:
        curation["cohort"] = cohort_summary
        trip["curation"] = curation

    from travelogue.curation.album_profile import write_album_profile

    write_album_profile(trip)
    return bucket_plan

def _stage_build_chapters_compose(
    trip: dict,
    preflight: _CuratePreflight,
    bucket_plan: _CurateBucketPlan,
    *,
    curate_scope: str,
    cohort_summary: dict | None,
    trip_dir: Path | None,
) -> _ChaptersComposeResult:
    from travelogue.config.edition import (
        PortfolioUnavailableError,
        is_portfolio_pipeline_enabled,
        is_portfolio_trip,
    )
    from travelogue.config.moment import effective_secondary_boost
    from travelogue.curation.compose_stages import (
        align_non_empty_buckets,
        materialize_composed_chapters,
        peel_time_outliers,
        prepare_compose_draft,
        resolve_compose_scoring,
    )

    aligned = align_non_empty_buckets(bucket_plan, preflight)
    peeled = peel_time_outliers(aligned, preflight)
    draft = prepare_compose_draft(
        trip, preflight, peeled, cohort_summary=cohort_summary
    )
    ready = resolve_compose_scoring(
        trip,
        preflight,
        draft,
        curate_scope=curate_scope,
        cohort_summary=cohort_summary,
    )
    # S-01 · 统一 beam 入口（架构收敛 A3）：mosaic 开/关均走 compose_trip，
    # deterministic_strict 与 meta 标注由 compose_trip 内部按 mosaic.enabled 选择。
    # PFM：作品集在 compose_trip 之前分叉；失败硬报，禁止静默掉回 journal。
    if is_portfolio_trip(trip):
        if not is_portfolio_pipeline_enabled(preflight.app_cfg):
            raise CurateError('E_PORTFOLIO_UNAVAILABLE', '此功能已关闭')
        from travelogue.layout_engine.editorial_series import compose_portfolio_trip

        try:
            chapters, replan_meta = compose_portfolio_trip(
                ready.chapters,
                buckets=ready.non_empty_buckets,
                aspects=ready.aspects,
                assets=preflight.layout_assets,
                app_cfg=preflight.app_cfg,
                trip=trip,
            )
        except PortfolioUnavailableError as exc:
            raise CurateError(exc.code, exc.message) from exc
    else:
        from travelogue.layout_engine.api import compose_trip

        chapters, replan_meta = compose_trip(
            ready.chapters,
            buckets=ready.non_empty_buckets,
            aspects=ready.aspects,
            assets=preflight.layout_assets,
            app_cfg=preflight.app_cfg,
            scoring_enabled=ready.layout_cfg.scoring.enabled,
            weights=ready.scoring_weights,
            beam_width=ready.layout_cfg.scoring.beam_width,
            degradation=ready.degradation,
            arc_mode=preflight.cur_cfg.arc_mode,
            arc_profile=ready.arc_profile,
            chapter_heroes=ready.chapter_heroes,
            orientation_summary=ready.summary_dict,
            skip_screen_asset_ids=preflight.skip_screen_ids,
            mixed_proximity_seconds=ready.layout_cfg.mixed_proximity_seconds,
            trip_photo_total=len(preflight.layout_assets),
            search_timeout_ms=ready.layout_cfg.scoring.search_timeout_ms,
            max_candidates_per_bucket=ready.layout_cfg.scoring.max_candidates_per_bucket,
            max_evaluations_per_trip=ready.layout_cfg.scoring.max_evaluations_per_trip,
            allow_burst_split=ready.layout_cfg.scoring.allow_burst_split,
            wall_clock_limits_output=ready.layout_cfg.scoring.wall_clock_limits_output,
            subject_run_tolerance=ready.layout_cfg.scoring.subject_run_tolerance,
            enable_food_grid=preflight.cur_cfg.enable_food_grid,
            mundane_grid_buckets=preflight.cur_cfg.mundane_grid_buckets,
            intent_peak_chapters=ready.intent_peak,
            enable_gravity_balance=preflight.cur_cfg.enable_gravity_balance,
            max_consecutive_same_pattern=preflight.cur_cfg.max_consecutive_same_pattern,
            skip_duplicate_signatures=ready.layout_cfg.scoring.skip_duplicate_signatures,
            incremental_scoring=ready.layout_cfg.scoring.incremental,
            max_evaluations_per_segment=ready.layout_cfg.scoring.max_evaluations_per_segment,
            moment_secondary_ids=set(ready.secondary_hints),
            moment_secondary_boost=effective_secondary_boost(preflight.cur_cfg.moment),
        )
    return materialize_composed_chapters(
        trip,
        preflight,
        ready,
        chapters,
        replan_meta,
        trip_dir=trip_dir,
    )


def _stage_finalize(
    trip: dict,
    preflight: _CuratePreflight,
    bucket_plan: _CurateBucketPlan,
    compose: _ChaptersComposeResult,
    *,
    curate_scope: str,
    trip_dir: Path | None,
    apply_layout: bool,
    cohort_summary: dict | None,
) -> CurateResult:
    app_cfg = preflight.app_cfg
    cur_cfg = preflight.cur_cfg
    layout = preflight.layout
    engine = preflight.engine
    layout_assets = preflight.layout_assets
    cover_id = preflight.cover_id
    res_warn = preflight.res_warn

    buckets = bucket_plan.buckets
    segments = bucket_plan.segments
    meta_places = bucket_plan.meta_places

    chapters = compose.chapters
    replan_meta = compose.replan_meta
    arc_profile = compose.arc_profile
    chapter_heroes = compose.chapter_heroes
    trip_memory_anchors = compose.trip_memory_anchors
    summary_dict = compose.summary_dict

    curation = trip.setdefault("curation", {})

    warnings: list[str] = []
    replan_skip = replan_meta.get("skipReason")
    if replan_skip == "search_timeout":
        budget = replan_meta.get("searchBudget") or {}
        ms = budget.get("elapsedMs")
        suffix = f" ({ms}ms)" if ms is not None else ""
        warnings.append(
            f"布局搜索超时{suffix}，已保留当前候选布局"
            " — 可在 config.yaml 调高 layout.scoring.search_timeout_ms"
        )
    elif replan_skip == "search_eval_exhausted":
        budget = replan_meta.get("searchBudget") or {}
        n = budget.get("evaluations")
        suffix = f" ({n} 次评估)" if n is not None else ""
        warnings.append(
            f"布局搜索评估预算用尽{suffix}，已保留当前候选布局"
            " — 可在 config.yaml 调高 layout.scoring.max_evaluations_per_trip"
        )
    span_warn = _date_span_warning(layout_assets, segments)
    if span_warn:
        warnings.append(span_warn)
    if res_warn:
        warnings.append(res_warn)

    from travelogue.curation.curate_scoring import build_user_tier_curation

    cover_for_tier: dict[str, str] | None = None
    if layout == "auto":
        raw = curation.get("coverByLayout")
        cover_for_tier = raw if isinstance(raw, dict) else None
    elif layout == "web" and trip.get("coverAssetId"):
        cover_for_tier = {"web": str(trip["coverAssetId"])}

    tier_fields, tier_warnings = build_user_tier_curation(
        trip,
        layout_assets,
        cover_by_layout=cover_for_tier,
        chapter_heroes=chapter_heroes,
        featured_weight=cur_cfg.featured_weight,
        warn_featured_above=app_cfg.ingest.warn_featured_count_above,
    )
    if tier_fields:
        curation.update(tier_fields)
    warnings.extend(tier_warnings)

    warnings.extend(reading_experience_warnings(trip, chapters, layout_assets))

    cross_seg = sum(
        1 for ch in chapters if len((ch.get("curation") or {}).get("segmentIds") or []) > 1
    )
    if cross_seg:
        warnings.append(f"{cross_seg} 章跨时间段合并，章标题已标注多段信息")

    undated_seg = False
    for s in segments or []:
        label = (
            s.label
            if hasattr(s, "label")
            else str((s.get("label") if isinstance(s, dict) else "") or "")
        )
        if label.startswith("未标注"):
            undated_seg = True
            break
    if undated_seg:
        warnings.append("含未标注日期照片，已单独成段或置于末段")

    if warnings:
        curation["warnings"] = warnings

    layout_summary = format_layout_summary(summary_dict, chapters)
    now = _utc_now_iso()
    trip_id = str(trip.get("tripId") or "trip")
    if apply_layout:
        set_layout_status(trip, "layout_draft")
        append_pipeline_run(
            trip,
            {
                "runId": f"layout-{trip_id}",
                "agent": "layout",
                "startedAt": now,
                "finishedAt": now,
                "model": None,
            },
        )
    else:
        set_layout_status(trip, "pending")

    # Main pipeline status (structure_draft); layoutStatus above is the Agent 1.5 sub-state.
    # scope=tier keeps chapter structure locks / pipeline.status (M3 · OQ-FEED-01).
    if curate_scope != "tier":
        set_pipeline_status(trip, "structure_draft")
        # Re-curate from structure_draft clears the post-lock pending ingest queue.
        clear_pending_assets(trip)
    trip["updatedAt"] = now
    append_pipeline_run(
        trip,
        {
            "runId": f"curate-{trip_id}",
            "agent": "curator",
            "startedAt": now,
            "finishedAt": now,
            "model": None,
            **(
                {"note": "scope=tier"}
                if curate_scope == "tier"
                else {}
            ),
        },
    )

    from travelogue.curation.arc_screen_tags import stamp_screen_arc_segments
    from travelogue.curation.breath_pauses import insert_breath_screens_in_chapters
    from travelogue.curation.chapter_explain import attach_chapter_explain
    from travelogue.curation.moment_scoring import sync_trip_moments_finalize

    stamp_screen_arc_segments(trip, arc_profile=arc_profile)
    sync_trip_moments_finalize(
        trip,
        layout_assets,
        chapters,
        cfg=cur_cfg.moment,
        arc_profile=arc_profile,
        featured_weight=cur_cfg.featured_weight,
        aesthetic_enabled=app_cfg.aesthetic.enabled,
        meta_places=meta_places or None,
        memory_anchors=trip_memory_anchors or None,
        chapter_heroes=chapter_heroes,
    )

    from travelogue.curation.folio_plan import build_folio_plan

    moment_exclude_grid: set[str] = set()
    moment_sig = str(trip.get("momentAssetId") or "").strip()
    if moment_sig:
        moment_exclude_grid.add(moment_sig)
    folio_plan = build_folio_plan(
        trip,
        chapters,
        layout_assets,
        featured_weight=cur_cfg.featured_weight,
        mutate_screens=True,
        exclude_grid_ids=moment_exclude_grid,
    )
    if folio_plan.get("featuredGrid"):
        curation["folioPlan"] = folio_plan
        n_grid = len(folio_plan.get("featuredGridAssetIds") or [])
        warnings.append(f"folio featured-grid · {n_grid} 张精选（已从正文 screens 去重）")
        curation["warnings"] = warnings
    elif folio_plan.get("plateAssetIds"):
        curation["folioPlan"] = {
            k: folio_plan[k]
            for k in ("index", "foreword", "featuredGrid", "featuredGridAssetIds", "plateAssetIds")
        }

    n_breath = 0
    from travelogue.config.edition import is_portfolio_trip

    if not is_portfolio_trip(trip):
        n_breath = insert_breath_screens_in_chapters(
            chapters,
            arc_driven=cur_cfg.enable_arc_breath,
        )
        if n_breath:
            warnings.append(f"卷轴呼吸屏 · 插入 {n_breath} 屏（叙事弧驱动）")

    # AC-RHY-07 · 节奏 post-check（灰度先 log，OQ-09=B）：R-06 / R-08 / V-09 观测。
    from travelogue.layout_contract.engines import LAYOUT_ENGINE_SCREENS

    if apply_layout and engine == LAYOUT_ENGINE_SCREENS:
        from travelogue.curation.layout_constraints import run_rhythm_postcheck

        rhythm_mode = app_cfg.layout.rhythm.post_check_mode
        rhythm_summary, rhythm_viol = run_rhythm_postcheck(
            chapters,
            mode=rhythm_mode,
            trip_id=trip.get("tripId"),
            max_pair_streak=app_cfg.layout.rhythm.max_portrait_pair_streak,
            max_landscape_pair_streak=app_cfg.layout.rhythm.max_landscape_pair_streak,
            max_orientation_streak=app_cfg.layout.rhythm.max_portrait_orientation_streak,
        )
        if rhythm_viol:
            warnings.append(
                f"节奏 post-check（{rhythm_mode}）：{len(rhythm_viol)} 处违规 {rhythm_summary}"
            )

    if trip_dir is not None:
        attach_chapter_explain(trip, trip_dir=trip_dir)

    from travelogue.curation.algorithm_profile import write_curate_profile

    write_curate_profile(
        trip,
        app_cfg=app_cfg,
        export_layout=layout,
        layout_engine=engine,
    )
    from travelogue.curation.algo_v3_summary import attach_algo_v3_summary

    attach_algo_v3_summary(trip, cfg=app_cfg)
    if apply_layout:
        from travelogue.layout_engine.adapter import record_applied_layout_density

        record_applied_layout_density(trip, cfg=app_cfg)
        from travelogue.cover_engine.api import maybe_resolve_closing_after_layout

        maybe_resolve_closing_after_layout(trip, layout=layout)

    return CurateResult(
        chapter_count=len(trip.get("chapters", [])),
        cover_asset_id=cover_id,
        layout_summary=layout_summary,
        day_groups=len(buckets),
        warnings=warnings,
    )


def run_curate(
    trip: dict,
    *,
    export_layout: str | None = None,
    layout_engine: str | None = None,
    apply_layout: bool = True,
    trip_dir: Path | None = None,
    cfg: AppConfig | None = None,
    refresh_algorithms: bool | None = None,
    scope: str = "full",
    cover_force: bool = False,
) -> CurateResult:
    """Run curation. Pins *cfg* via app_config_scope so internal get_config() matches (LTN E6b)."""
    from travelogue.config import get_config
    from travelogue.config.layout_vibe import apply_layout_vibe_to_config
    from travelogue.config.runtime import app_config_scope

    active_cfg = apply_layout_vibe_to_config(trip, cfg or get_config())
    with app_config_scope(active_cfg):
        return _run_curate_inner(
            trip,
            export_layout=export_layout,
            layout_engine=layout_engine,
            apply_layout=apply_layout,
            trip_dir=trip_dir,
            cfg=active_cfg,
            refresh_algorithms=refresh_algorithms,
            scope=scope,
            cover_force=cover_force,
        )


def _run_curate_inner(
    trip: dict,
    *,
    export_layout: str | None = None,
    layout_engine: str | None = None,
    apply_layout: bool = True,
    trip_dir: Path | None = None,
    cfg: AppConfig | None = None,
    refresh_algorithms: bool | None = None,
    scope: str = "full",
    cover_force: bool = False,
) -> CurateResult:
    curate_scope = "tier" if str(scope or "").strip().lower() == "tier" else "full"
    if len(trip.get("assets") or []) < MIN_CURATE_ASSETS:
        raise CurateError(
            "E_CURATE_TOO_FEW",
            f"need at least {MIN_CURATE_ASSETS} assets to curate",
        )

    from travelogue.curation.curation_adapter import apply_curation_adapter_hints

    apply_curation_adapter_hints(trip, cfg=cfg)

    from travelogue.curation.intent_hints import (
        apply_editorial_intent_hints,
        prior_chapter_memory_anchors,
    )

    apply_editorial_intent_hints(trip)
    saved_memory_anchors = prior_chapter_memory_anchors(trip)

    cohort_summary = stage_refresh_cull_cohort(
        trip,
        trip_dir=trip_dir,
        cfg=cfg,
        curate_scope=curate_scope,
        refresh_algorithms=refresh_algorithms,
    )

    preflight = _curate_preflight(
        trip,
        export_layout=export_layout,
        layout_engine=layout_engine,
        trip_dir=trip_dir,
        cfg=cfg,
        saved_memory_anchors=saved_memory_anchors,
        cover_force=bool(cover_force) if curate_scope == "tier" else False,
    )

    _stage_aesthetic_align(trip, trip_dir=trip_dir, app_cfg=preflight.app_cfg)

    bucket_plan = _stage_resolve_buckets(
        trip,
        preflight,
        curate_scope=curate_scope,
        trip_dir=trip_dir,
        cohort_summary=cohort_summary,
    )

    compose = _stage_build_chapters_compose(
        trip,
        preflight,
        bucket_plan,
        curate_scope=curate_scope,
        cohort_summary=cohort_summary,
        trip_dir=trip_dir,
    )

    return _stage_finalize(
        trip,
        preflight,
        bucket_plan,
        compose,
        curate_scope=curate_scope,
        trip_dir=trip_dir,
        apply_layout=apply_layout,
        cohort_summary=cohort_summary,
    )

