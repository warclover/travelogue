"""Agent 1 · Curator — day-based chapters, cover, then layout."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from travelogue.config import AppConfig, CurateConfig
from travelogue.config.moment import effective_secondary_boost
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
from travelogue.curation.curate_limits import (
    COMPACT_ALBUM_PHOTO_CAP,
    MIN_CURATE_ASSETS,
    SEGMENT_LABEL_PREVIEW_LIMIT,
    SMALL_ALBUM_PHOTO_CAP,
)
from travelogue.curation.curate_patterns import pattern_hint_for_bucket
from travelogue.curation.curate_scoring import (
    build_cover_explain,
    build_cover_layout_review,
    cover_asset_pool,
    median_sharpness,
    pick_chapter_hero,
)
from travelogue.curation.curate_scoring import (
    cover_candidates as _cover_candidates,
)
from travelogue.curation.curate_scoring import (
    pick_cover_asset_id as _pick_cover_asset_id,
)
from travelogue.curation.layout_planner import (
    aspect_kind_for_asset,
    build_chapters_from_buckets,
    summarize_orientations,
)
from travelogue.curation.time_segments import TimeSegment, parse_asset_date
from travelogue.errors import CodeError
from travelogue.layout_contract import LAYOUT_PLAN_VERSION, format_layout_summary
from travelogue.services.pipeline_state import set_layout_status
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


class CurateError(CodeError):
    pass


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
        preview = "、".join(labels[:SEGMENT_LABEL_PREVIEW_LIMIT])
        if len(segments) > SEGMENT_LABEL_PREVIEW_LIMIT:
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


def layout_eligible_assets(trip: dict) -> list[dict]:
    """Assets usable for cover, chapters, and screens."""
    return [
        a
        for a in trip.get("assets") or []
        if a.get("type", "image") != "video" and a.get("layoutEligible", True) is not False
    ]


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


def resolve_cover_render_profile(
    export_layout: str,
    *,
    index_name: str = "index.html",
    layout_engine: str | None = None,
) -> str:
    """Map render surface to cover profile (mobile portrait vs web landscape)."""
    if export_layout in ("mobile", "web"):
        return export_layout
    if index_name in ("index-mobile.html",):
        return "mobile"
    from travelogue.curation.screen_planner import LAYOUT_ENGINE_SCREENS

    if layout_engine == LAYOUT_ENGINE_SCREENS or index_name in (
        "index.html",
        "index-present.html",
    ):
        return "web"
    return "mobile"


def resolve_cover_asset_id(
    trip: dict,
    *,
    export_layout: str,
    index_name: str | None = None,
    layout_engine: str | None = None,
) -> str:
    """Pick cover for render/curate profile (mobile | web | auto→surface)."""
    assets = layout_eligible_assets(trip)
    if not assets:
        return ""
    profile = resolve_cover_render_profile(
        export_layout,
        index_name=index_name or "index.html",
        layout_engine=layout_engine or trip.get("layoutEngine"),
    )
    by_layout = (trip.get("curation") or {}).get("coverByLayout") or {}
    if isinstance(by_layout, dict) and profile in by_layout:
        cid = by_layout[profile]
        if cid and any(a.get("id") == cid for a in assets):
            return cid
    return _pick_cover_asset_id(assets, export_layout=profile)


def _cover_scoring_runtime(
    cover_scoring=None,
    cover_scoring_v2=None,
    scoring_version: str | None = None,
):
    from travelogue.config import get_config

    cur = get_config().curate
    cs = cover_scoring if cover_scoring is not None else cur.cover_scoring
    cs_v2 = cover_scoring_v2 if cover_scoring_v2 is not None else cur.cover_scoring_v2
    ver = scoring_version or cur.cover_scoring_version
    return cs, cs_v2, ver


def _cover_explain_for(
    assets: list[dict],
    cover_id: str,
    export_layout: str,
    *,
    cover_scoring=None,
    cover_scoring_v2=None,
    scoring_version: str | None = None,
    enable_phase6_cover_factors: bool = True,
) -> list[dict]:
    from travelogue.curation.cover_scoring_params import resolve_person_demote
    from travelogue.curation.cover_scoring_v2 import resolve_person_demote_v2

    asset = next((a for a in assets if a.get("id") == cover_id), None)
    if not asset:
        return []
    params, params_v2, ver = _cover_scoring_runtime(
        cover_scoring, cover_scoring_v2, scoring_version
    )
    pool = cover_asset_pool(assets, export_layout=export_layout)
    featured = [a for a in pool if a.get("userTier") == "featured"]
    search = featured if featured else pool
    person_demote = (
        resolve_person_demote_v2(params_v2, search)
        if ver == "v2"
        else resolve_person_demote(params, search)
    )
    return build_cover_explain(
        asset,
        export_layout,
        median_sharp=median_sharpness(search),
        cover_scoring=params,
        cover_scoring_v2=params_v2,
        scoring_version=ver,
        pool=search,
        person_demote_mult=person_demote,
        enable_phase6_cover_factors=enable_phase6_cover_factors,
    )


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
) -> str:
    """Write coverAssetId (+ coverByLayout when exportLayout=auto). Returns primary cover id."""
    assets = assets if assets is not None else layout_eligible_assets(trip)
    layout = export_layout or trip.get("exportLayout") or "auto"
    curation = trip.setdefault("curation", {})
    cs, cs_v2, ver = _cover_scoring_runtime(cover_scoring, cover_scoring_v2, scoring_version)
    p6 = bool(enable_phase6_cover_factors and cs.enable_phase6_factors)
    scoring_kwargs = {
        "cover_scoring": cs,
        "cover_scoring_v2": cs_v2,
        "scoring_version": ver,
    }

    def _write_blind_review(cover_id: str, profile: str) -> None:
        curation.setdefault("coverBlindReview", {})[profile] = build_cover_layout_review(
            assets,
            cover_id,
            export_layout=profile,
            featured_weight=featured_weight,
            enable_phase6_cover_factors=p6,
            **scoring_kwargs,
        )

    if layout == "auto":
        mobile_id = _pick_cover_asset_id(
            assets,
            export_layout="mobile",
            featured_weight=featured_weight,
            enable_phase6_cover_factors=p6,
            **scoring_kwargs,
        )
        web_id = _pick_cover_asset_id(
            assets,
            export_layout="web",
            featured_weight=featured_weight,
            enable_phase6_cover_factors=p6,
            **scoring_kwargs,
        )
        curation["coverByLayout"] = {"mobile": mobile_id, "web": web_id}
        trip["coverAssetId"] = mobile_id
        trip["coverCandidates"] = _cover_candidates(
            assets,
            mobile_id,
            export_layout="mobile",
            featured_weight=featured_weight,
            featured_min=featured_min_for_cover_pool,
            enable_phase6_cover_factors=p6,
            **scoring_kwargs,
        )
        curation["coverCandidatesByLayout"] = {
            "mobile": _cover_candidates(
                assets,
                mobile_id,
                export_layout="mobile",
                featured_weight=featured_weight,
                featured_min=featured_min_for_cover_pool,
                enable_phase6_cover_factors=p6,
                **scoring_kwargs,
            ),
            "web": _cover_candidates(
                assets,
                web_id,
                export_layout="web",
                featured_weight=featured_weight,
                featured_min=featured_min_for_cover_pool,
                enable_phase6_cover_factors=p6,
                **scoring_kwargs,
            ),
        }
        mobile_explain = _cover_explain_for(
            assets,
            mobile_id,
            "mobile",
            enable_phase6_cover_factors=p6,
            **scoring_kwargs,
        )
        web_explain = _cover_explain_for(
            assets,
            web_id,
            "web",
            enable_phase6_cover_factors=p6,
            **scoring_kwargs,
        )
        if mobile_explain:
            curation["coverExplain"] = mobile_explain
        else:
            curation.pop("coverExplain", None)
        if mobile_explain or web_explain:
            curation["coverExplainByLayout"] = {
                "mobile": mobile_explain,
                "web": web_explain,
            }
        else:
            curation.pop("coverExplainByLayout", None)
        _write_blind_review(mobile_id, "mobile")
        _write_blind_review(web_id, "web")
        return mobile_id

    cover_id = _pick_cover_asset_id(
        assets,
        export_layout=layout,
        featured_weight=featured_weight,
        enable_phase6_cover_factors=p6,
        **scoring_kwargs,
    )
    trip["coverAssetId"] = cover_id
    trip["coverCandidates"] = _cover_candidates(
        assets,
        cover_id,
        export_layout=layout,
        featured_weight=featured_weight,
        featured_min=featured_min_for_cover_pool,
        enable_phase6_cover_factors=p6,
        **scoring_kwargs,
    )
    curation.pop("coverByLayout", None)
    curation.pop("coverCandidatesByLayout", None)
    curation.pop("coverExplainByLayout", None)
    explain = _cover_explain_for(
        assets,
        cover_id,
        layout,
        enable_phase6_cover_factors=p6,
        **scoring_kwargs,
    )
    if explain:
        curation["coverExplain"] = explain
    else:
        curation.pop("coverExplain", None)
    _write_blind_review(cover_id, layout)
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


def _curate_preflight(
    trip: dict,
    *,
    export_layout: str | None,
    layout_engine: str | None,
    trip_dir: Path | None,
    cfg: AppConfig | None,
    saved_memory_anchors: list[list[str] | None],
) -> _CuratePreflight:
    from travelogue.config import default_web_layout_engine, get_config
    from travelogue.curation.screen_planner import LAYOUT_ENGINE_LEGACY, LAYOUT_ENGINE_SCREENS

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
    from travelogue.services.copy_subject import effective_meta_places

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
    from travelogue.layout_engine.replan import buckets_from_existing_chapters
    from travelogue.services.copy_subject import effective_meta_places

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


def run_curate(
    trip: dict,
    *,
    export_layout: str | None = None,
    layout_engine: str | None = None,
    apply_layout: bool = True,
    trip_dir: Path | None = None,
    cfg: AppConfig | None = None,
    refresh_algorithms: bool | None = None,
) -> CurateResult:
    if len(trip.get("assets") or []) < MIN_CURATE_ASSETS:
        raise CurateError(
            "E_CURATE_TOO_FEW",
            f"need at least {MIN_CURATE_ASSETS} assets to curate",
        )

    from travelogue.templating.curation_adapter import apply_curation_adapter_hints

    apply_curation_adapter_hints(trip, cfg=cfg)

    from travelogue.curation.intent_hints import (
        apply_editorial_intent_hints,
        peak_chapter_hints_for_trip,
        prior_chapter_memory_anchors,
    )

    apply_editorial_intent_hints(trip)
    saved_memory_anchors = prior_chapter_memory_anchors(trip)

    from travelogue.curation.algorithm_profile import maybe_refresh_cull

    maybe_refresh_cull(
        trip,
        trip_dir=trip_dir,
        app_cfg=cfg,
        refresh_algorithms=refresh_algorithms,
    )

    cohort_summary = None
    if trip_dir is not None:
        from travelogue.curation.cohort_faces import apply_cohort_tags

        cohort_summary = apply_cohort_tags(trip, trip_dir=trip_dir, cfg=cfg)

    preflight = _curate_preflight(
        trip,
        export_layout=export_layout,
        layout_engine=layout_engine,
        trip_dir=trip_dir,
        cfg=cfg,
        saved_memory_anchors=saved_memory_anchors,
    )
    app_cfg = preflight.app_cfg
    cur_cfg = preflight.cur_cfg
    layout = preflight.layout
    engine = preflight.engine
    layout_assets = preflight.layout_assets
    cover_id = preflight.cover_id
    skip_screen_ids = preflight.skip_screen_ids
    res_warn = preflight.res_warn
    saved_memory_anchors = preflight.saved_memory_anchors

    if trip_dir is not None and app_cfg.aesthetic.enabled:
        from travelogue.curation.aesthetic_score import apply_aesthetic_alignment

        apply_aesthetic_alignment(
            trip.get("assets") or [],
            trip_dir=trip_dir,
            cfg=app_cfg,
            trip=trip,
        )

    from travelogue.curation.screen_planner import (
        LAYOUT_ENGINE_SCREENS,
        LAYOUT_ENGINE_VERSION_SCREENS,
    )
    from travelogue.layout_engine.replan import (
        mark_layout_replan,
        record_applied_layout_density,
        should_layout_only_replan,
    )

    replan_decision = should_layout_only_replan(trip, trip_dir=trip_dir, cfg=app_cfg)
    if replan_decision.layout_only:
        bucket_plan = _build_layout_only_bucket_plan(trip, preflight)
        if bucket_plan is None:
            bucket_plan = _build_curate_buckets(trip, preflight)
        else:
            mark_layout_replan(trip, reason=replan_decision.reason or "density_change")
    else:
        bucket_plan = _build_curate_buckets(trip, preflight)
    buckets = bucket_plan.buckets
    bucket_segment_ids = bucket_plan.bucket_segment_ids
    bucket_segment_ids_all = bucket_plan.bucket_segment_ids_all
    segments = bucket_plan.segments
    segment_labels = bucket_plan.segment_labels
    curation_segments = bucket_plan.curation_segments
    meta_places = bucket_plan.meta_places
    meta = trip.get("meta", {})
    curation = trip.get("curation") or {}
    if cohort_summary:
        curation["cohort"] = cohort_summary
        trip["curation"] = curation

    from travelogue.curation.album_profile import write_album_profile

    write_album_profile(trip)

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

    from travelogue.curation.moment_scoring import (
        preferred_secondary_hero_for_bucket,
        sync_trip_moments_finalize,
        sync_trip_moments_preflight,
    )

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
        buckets,
        layout_assets,
        meta,
        intent=trip.get("intent"),
        bucket_segment_ids=bucket_segment_ids,
        bucket_segment_ids_all=bucket_segment_ids_all,
        segment_labels=segment_labels,
        plan_cities=(
            ((curation.get("intentHints") or {}).get("planCities"))
            or ((trip.get("intent") or {}).get("travelPlan") or {}).get("cities")
            or []
        ),
    )
    summary = summarize_orientations(layout_assets, export_layout=layout)  # type: ignore[arg-type]
    summary_dict = summary.to_dict()
    from travelogue.curation.mosaic.runtime import (
        cohort_mosaic_override,
        reset_mosaic_config_override,
        set_mosaic_config_override,
    )

    mosaic_override_active = None
    if app_cfg.layout.strategy_engine.enabled:
        from dataclasses import replace as _dc_replace

        from travelogue.layout_engine.adapter import mosaic_config_from_pack

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
    from travelogue.curation.mosaic.runtime import (
        reset_mosaic_disabled_patterns,
        set_mosaic_disabled_patterns,
    )

    pattern_blacklist_active = False
    if app_cfg.layout.strategy_engine.enabled:
        from travelogue.layout_engine.pattern_policy import effective_pattern_blacklist

        set_mosaic_disabled_patterns(effective_pattern_blacklist(app_cfg))
        pattern_blacklist_active = True
    if mosaic_override_active is not None:
        set_mosaic_config_override(mosaic_override_active)
    if app_cfg.mosaic.enabled:
        from travelogue.curation.mosaic.hook import begin_mosaic_capture

        begin_mosaic_capture()
    try:
        from travelogue.curation.layout_density import layout_density_params

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
            enable_food_grid=cur_cfg.enable_food_grid,
            mundane_grid_buckets=cur_cfg.mundane_grid_buckets,
            layout_density=layout_density_params(trip, app_cfg=app_cfg).density,
            cfg=app_cfg,
        )
    finally:
        if mosaic_override_active is not None:
            reset_mosaic_config_override()
        if pattern_blacklist_active:
            reset_mosaic_disabled_patterns()
    if app_cfg.mosaic.enabled:
        from travelogue.curation.mosaic.hook import drain_mosaic_dropped, drain_mosaic_logs

        mosaic_logs = drain_mosaic_logs()
        dropped = drain_mosaic_dropped()
        curation = trip.setdefault("curation", {})
        if mosaic_logs:
            curation["mosaicDecisionLog"] = mosaic_logs
        if dropped:
            curation["mosaicDroppedAssetIds"] = list(dict.fromkeys(dropped))
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
        _sanitize_chapters_after_exclusion(chapters, excluded_ids)

    from travelogue.curation.degradation import assess_degradation
    from travelogue.curation.layout_metrics import compute_layout_metrics
    from travelogue.curation.layout_scoring import ScoringWeights, resolve_scoring_weights

    layout_cfg = app_cfg.layout
    pipe_status = (trip.get("pipeline") or {}).get("status") or ""
    from travelogue.domain.pipeline import PIPELINE_LOCKED_STATUSES

    structure_locked = pipe_status in PIPELINE_LOCKED_STATUSES
    degradation = assess_degradation(
        layout_assets,
        aspects,
        min_layout_eligible=layout_cfg.scoring.min_layout_eligible,
        min_aspect_kinds=layout_cfg.scoring.min_aspect_kinds,
        structure_locked=structure_locked,
        force_relayout=False,
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
    intent_peak = peak_chapter_hints_for_trip(trip, len(non_empty_buckets))
    # 统一 beam 入口（架构收敛 A3）：mosaic 开/关均走 compose_trip，
    # deterministic_strict 与 meta 标注由 compose_trip 内部按 mosaic.enabled 选择。
    from travelogue.curation.mosaic.trip import compose_trip

    chapters, replan_meta = compose_trip(
        chapters,
        buckets=non_empty_buckets,
        aspects=aspects,
        assets=layout_assets,
        app_cfg=app_cfg,
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
        enable_food_grid=cur_cfg.enable_food_grid,
        mundane_grid_buckets=cur_cfg.mundane_grid_buckets,
        intent_peak_chapters=intent_peak,
        enable_gravity_balance=cur_cfg.enable_gravity_balance,
        max_consecutive_same_pattern=cur_cfg.max_consecutive_same_pattern,
        skip_duplicate_signatures=layout_cfg.scoring.skip_duplicate_signatures,
        incremental_scoring=layout_cfg.scoring.incremental,
        max_evaluations_per_segment=layout_cfg.scoring.max_evaluations_per_segment,
        moment_secondary_ids=set(secondary_hints),
        moment_secondary_boost=effective_secondary_boost(cur_cfg.moment),
    )
    if engine == LAYOUT_ENGINE_SCREENS:
        from travelogue.curation.chapter_items import (
            collect_displayed_asset_ids,
            compact_chapter_items_for_screens,
        )

        compact_chapter_items_for_screens(chapters)
    mosaic_logs_for_metrics = (trip.get("curation") or {}).get("mosaicDecisionLog")
    layout_metrics = compute_layout_metrics(
        chapters,
        layout_assets,
        subject_run_tolerance=layout_cfg.scoring.subject_run_tolerance,
        mosaic_logs=mosaic_logs_for_metrics,
    )
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

        hero_extra = [h for h in (chapter_heroes or {}).values() if h]
        curation["displayedAssetIds"] = collect_displayed_asset_ids(
            chapters, extra_asset_ids=hero_extra
        )
        from travelogue.curation.mosaic.coverage import compute_coverage_metrics

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
        from travelogue.layout_engine.adapter import resolve_pack
        from travelogue.layout_engine.capabilities import effective_capabilities
        from travelogue.layout_engine.editorial_hints import (
            build_editorial_hints,
            editorial_hints_from_pack,
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
        from travelogue.curation.mosaic.telemetry import (
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
        plan_entry: dict = {
            "chapterIndex": ch.get("index"),
            "chapterId": ch.get("id"),
            "assetCount": len(non_empty_buckets[i]) if i < len(non_empty_buckets) else 0,
            "daySpan": (ch.get("curation") or {}).get("daySpan"),
            "segmentId": (ch.get("curation") or {}).get("segmentId"),
            "patternHint": pattern_hints[i] if i < len(pattern_hints) else None,
            "patternId": ch.get("patternId"),
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

    # Main pipeline status (structure_draft); layoutStatus above is the Agent 1.5 sub-state.
    pipe["status"] = "structure_draft"
    # Re-curate from structure_draft clears the post-lock pending ingest queue.
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

    from travelogue.curation.arc_screen_tags import stamp_screen_arc_segments
    from travelogue.curation.breath_pauses import insert_breath_screens_in_chapters
    from travelogue.curation.chapter_explain import attach_chapter_explain

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

    n_breath = insert_breath_screens_in_chapters(
        chapters,
        arc_driven=cur_cfg.enable_arc_breath,
    )
    if n_breath:
        warnings.append(f"卷轴呼吸屏 · 插入 {n_breath} 屏（叙事弧驱动）")

    # AC-RHY-07 · 节奏 post-check（灰度先 log，OQ-09=B）：R-06 / R-08 / V-09 观测。
    if apply_layout and engine == LAYOUT_ENGINE_SCREENS:
        from travelogue.curation.layout_constraints import run_rhythm_postcheck

        rhythm_mode = app_cfg.layout.rhythm.post_check_mode
        rhythm_summary, rhythm_viol = run_rhythm_postcheck(
            chapters,
            mode=rhythm_mode,
            trip_id=trip.get("tripId"),
            max_pair_streak=app_cfg.layout.rhythm.max_portrait_pair_streak,
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
    if apply_layout:
        record_applied_layout_density(trip, cfg=app_cfg)

    return CurateResult(
        chapter_count=len(trip.get("chapters", [])),
        cover_asset_id=cover_id,
        layout_summary=layout_summary,
        day_groups=len(buckets),
        warnings=warnings,
    )
