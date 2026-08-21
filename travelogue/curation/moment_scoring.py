"""Phase 23 · peak moment pool + signature selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from travelogue.config.moment import MomentConfig
from travelogue.curation.curate_scoring import (
    anchor_match_multiplier,
    featured_weight_multiplier,
    median_sharpness,
)
from travelogue.curation.layout_planner import aspect_kind_for_asset

_EXCLUDED_MEDIA = frozenset({"screenshot", "thumbnail", "reupload"})


def moment_pool_target_size(layout_eligible_count: int, cfg: MomentConfig) -> int:
    if layout_eligible_count <= 0:
        return 0
    raw = round(layout_eligible_count * cfg.pool_ratio)
    return max(cfg.pool_min, min(cfg.pool_max, raw))


def _cover_ids_to_exclude(trip: dict) -> set[str]:
    out: set[str] = set()
    primary = str(trip.get("coverAssetId") or "").strip()
    if primary:
        out.add(primary)
    by_layout = (trip.get("curation") or {}).get("coverByLayout") or {}
    if isinstance(by_layout, dict):
        for value in by_layout.values():
            aid = str(value or "").strip()
            if aid:
                out.add(aid)
    return out


def _eligible_moment_candidates(
    assets: list[dict],
    *,
    exclude: set[str],
    allow_food: bool | None = None,
) -> list[dict]:
    from travelogue.curation.food_policy import is_food_asset, moment_allows_food

    food_ok = moment_allows_food() if allow_food is None else bool(allow_food)
    out: list[dict] = []
    for asset in assets:
        aid = str(asset.get("id") or "").strip()
        if not aid or aid in exclude:
            continue
        if asset.get("type") != "image":
            continue
        if not asset.get("layoutEligible", True):
            continue
        if asset.get("timeOutlier"):
            continue
        if asset.get("mediaClass") in _EXCLUDED_MEDIA:
            continue
        if not food_ok and is_food_asset(asset):
            continue
        out.append(asset)
    return out


def _collect_screen_asset_ids(chapters: list[dict]) -> set[str]:
    ids: set[str] = set()
    for ch in chapters or []:
        for screen in ch.get("screens") or []:
            for slot in screen.get("slots") or []:
                aid = str(slot.get("assetId") or "").strip()
                if aid:
                    ids.add(aid)
    return ids


def _peak_chapter_indices(chapters: list[dict], *, arc_profile: str) -> set[int]:
    from travelogue.curation.arc_patterns import arc_segment_for_chapter

    total = len(chapters or [])
    if total <= 0:
        return set()
    out: set[int] = set()
    for i, ch in enumerate(chapters):
        seg = arc_segment_for_chapter(i + 1, total, profile=arc_profile)  # type: ignore[arg-type]
        if seg == "peak":
            out.add(i)
        hint = str((ch.get("curation") or {}).get("patternHint") or "").strip().lower()
        if hint == "peak":
            out.add(i)
    return out


def _asset_in_peak_chapter(asset_id: str, chapters: list[dict], peak_indices: set[int]) -> bool:
    for idx in peak_indices:
        if idx >= len(chapters):
            continue
        ch = chapters[idx]
        for screen in ch.get("screens") or []:
            for slot in screen.get("slots") or []:
                if str(slot.get("assetId") or "").strip() == asset_id:
                    return True
        bucket_ids = (ch.get("curation") or {}).get("assetIds") or []
        if asset_id in bucket_ids:
            return True
    return False


@dataclass
class _MomentScoreCtx:
    cfg: MomentConfig
    median_sharp: float
    on_screen_ids: set[str]
    peak_indices: set[int]
    chapters: list[dict]
    assets_by_id: dict[str, dict]
    arc_profile: str
    memory_anchors: list[str]
    meta_places: list[str]
    hero_asset_ids: set[str]
    featured_weight: float
    aesthetic_enabled: bool
    include_on_screen: bool


def _asset_in_highlight_window(
    asset_id: str,
    chapters: list[dict],
    assets_by_id: dict[str, dict],
    *,
    arc_profile: str,
) -> bool:
    """P17 highlight_windows hit within a peak chapter (Phase 23 f_arc_peak)."""
    from travelogue.curation.arc_patterns import arc_segment_for_chapter
    hw = __import__('travelogue.layout_engine.highlight_windows', fromlist=['detect_highlight_windows'])
    detect_highlight_windows = hw.detect_highlight_windows

    total = len(chapters or [])
    if total <= 0:
        return False
    for i, ch in enumerate(chapters):
        if arc_segment_for_chapter(i + 1, total, profile=arc_profile) != "peak":
            continue
        order: list[str] = []
        for screen in ch.get("screens") or []:
            for slot in screen.get("slots") or []:
                aid = str(slot.get("assetId") or "").strip()
                if aid:
                    order.append(aid)
        if not order:
            continue
        for window in detect_highlight_windows(order, assets_by_id, max_windows=2):
            if asset_id in window:
                return True
    return False


def peak_moment_score(
    asset: dict,
    ctx: _MomentScoreCtx,
) -> float:
    w = ctx.cfg.scoring
    aid = str(asset.get("id") or "")

    arc_peak = 0.0
    if ctx.peak_indices and ctx.chapters:
        if _asset_in_peak_chapter(aid, ctx.chapters, ctx.peak_indices):
            arc_peak = 1.0
        elif _asset_in_highlight_window(
            aid,
            ctx.chapters,
            ctx.assets_by_id,
            arc_profile=ctx.arc_profile,
        ):
            arc_peak = 1.0

    anchor_mult = anchor_match_multiplier(
        asset, ctx.memory_anchors, meta_places=ctx.meta_places
    )
    anchor = 1.0 if anchor_mult > 1.0 else 0.0

    aesthetic = 0.5
    if ctx.aesthetic_enabled:
        from travelogue.curation.aesthetic_score import purpose_overall

        val = purpose_overall(asset, "moment")
        if val is not None:
            aesthetic = max(0.0, min(1.0, float(val)))

    on_screen = 1.0 if aid in ctx.on_screen_ids else 0.0
    featured = 1.0 if asset.get("userTier") == "featured" else 0.0

    if ctx.include_on_screen:
        total = (
            w.arc_peak * arc_peak
            + w.anchor * anchor
            + w.aesthetic * aesthetic
            + w.on_screen * on_screen
            + w.featured * featured
        )
    else:
        denom = w.arc_peak + w.anchor + w.aesthetic + w.featured
        total = (
            w.arc_peak * arc_peak
            + w.anchor * anchor
            + w.aesthetic * aesthetic
            + w.featured * featured
        ) / denom if denom > 0 else 0.0

    total *= featured_weight_multiplier(asset, weight=ctx.featured_weight)
    if aid in ctx.hero_asset_ids:
        total *= 0.85

    sharp = float((asset.get("quality") or {}).get("sharpness") or 0.0)
    if ctx.median_sharp > 0:
        total += 0.001 * (sharp / ctx.median_sharp)

    # FRP · soft demote double-insurance when food reaches scoring
    # (hard-exclude normally keeps food out of the pool).
    from travelogue.curation.food_policy import food_moment_score_multiplier

    total *= food_moment_score_multiplier(asset)

    return max(0.0, min(1.5, total))


def _build_score_ctx(
    *,
    cfg: MomentConfig,
    layout_assets: list[dict],
    chapters: list[dict] | None,
    trip: dict,
    arc_profile: str,
    include_on_screen: bool,
    featured_weight: float,
    aesthetic_enabled: bool,
    meta_places: list[str] | None,
    memory_anchors: list[str] | None,
    hero_asset_ids: set[str] | None,
) -> _MomentScoreCtx:
    chs = chapters or []
    assets_by_id = {str(a.get("id")): a for a in layout_assets if a.get("id")}
    return _MomentScoreCtx(
        cfg=cfg,
        median_sharp=median_sharpness(layout_assets),
        on_screen_ids=_collect_screen_asset_ids(chs),
        peak_indices=_peak_chapter_indices(chs, arc_profile=arc_profile),
        chapters=chs,
        assets_by_id=assets_by_id,
        arc_profile=arc_profile,
        memory_anchors=list(memory_anchors or []),
        meta_places=list(meta_places or []),
        hero_asset_ids=hero_asset_ids or set(),
        featured_weight=featured_weight,
        aesthetic_enabled=aesthetic_enabled,
        include_on_screen=include_on_screen,
    )


def _rank_assets(
    candidates: list[dict],
    ctx: _MomentScoreCtx,
) -> list[tuple[str, float]]:
    scored: list[tuple[str, float]] = []
    for asset in candidates:
        aid = str(asset.get("id") or "").strip()
        if not aid:
            continue
        scored.append((aid, peak_moment_score(asset, ctx)))
    scored.sort(key=lambda x: (-x[1], x[0]))
    return scored


def build_moment_pool(
    trip: dict,
    layout_assets: list[dict],
    *,
    cfg: MomentConfig,
    chapters: list[dict] | None = None,
    arc_profile: str = "dynamic",
    include_on_screen: bool = True,
    featured_weight: float = 1.35,
    aesthetic_enabled: bool = True,
    meta_places: list[str] | None = None,
    memory_anchors: list[str] | None = None,
    hero_asset_ids: set[str] | None = None,
) -> list[str]:
    from travelogue.curation.food_policy import moment_allows_food

    exclude = _cover_ids_to_exclude(trip)
    allow_food = moment_allows_food()
    candidates = _eligible_moment_candidates(
        layout_assets, exclude=exclude, allow_food=allow_food
    )
    food_fallback = False
    if not candidates and not allow_food:
        candidates = _eligible_moment_candidates(
            layout_assets, exclude=exclude, allow_food=True
        )
        food_fallback = bool(candidates)
    if not candidates:
        return []

    target = moment_pool_target_size(len(layout_assets), cfg)
    if target <= 0:
        return []

    ctx = _build_score_ctx(
        cfg=cfg,
        layout_assets=layout_assets,
        chapters=chapters,
        trip=trip,
        arc_profile=arc_profile,
        include_on_screen=include_on_screen,
        featured_weight=featured_weight,
        aesthetic_enabled=aesthetic_enabled,
        meta_places=meta_places,
        memory_anchors=memory_anchors,
        hero_asset_ids=hero_asset_ids,
    )

    featured = [a for a in candidates if a.get("userTier") == "featured"]
    material = [a for a in candidates if a.get("userTier") != "featured"]
    search = featured if len(featured) >= cfg.pool_min else candidates
    ranked = _rank_assets(search, ctx)
    pool_ids = [aid for aid, _ in ranked[:target]]

    if len(pool_ids) < target and featured and material:
        seen = set(pool_ids)
        extra_ranked = _rank_assets(material, ctx)
        for aid, _ in extra_ranked:
            if aid in seen:
                continue
            pool_ids.append(aid)
            seen.add(aid)
            if len(pool_ids) >= target:
                break
    if food_fallback:
        curation = trip.setdefault("curation", {})
        curation["momentFoodFallback"] = True
        food_policy = curation.get("foodPolicy")
        if not isinstance(food_policy, dict):
            food_policy = {}
        food_policy["moment"] = "fallback"
        curation["foodPolicy"] = food_policy
    else:
        curation = trip.setdefault("curation", {})
        curation.pop("momentFoodFallback", None)
        food_policy = curation.get("foodPolicy")
        if not isinstance(food_policy, dict):
            food_policy = {}
        food_policy["moment"] = "none" if allow_food else "excluded"
        curation["foodPolicy"] = food_policy
    return pool_ids


def _moment_explain(
    asset: dict,
    score: float,
    ctx: _MomentScoreCtx,
) -> list[dict[str, Any]]:
    w = ctx.cfg.scoring
    aid = str(asset.get("id") or "")
    items: list[dict[str, Any]] = []
    if ctx.peak_indices and _asset_in_peak_chapter(aid, ctx.chapters, ctx.peak_indices):
        items.append({"factor": "arc_peak", "weight": w.arc_peak, "detail": "peak chapter"})
    if anchor_match_multiplier(asset, ctx.memory_anchors, meta_places=ctx.meta_places) > 1.0:
        items.append({"factor": "anchor", "weight": w.anchor, "detail": "memory anchor"})
    if aid in ctx.on_screen_ids:
        items.append({"factor": "on_screen", "weight": w.on_screen, "detail": "on layout screen"})
    if asset.get("userTier") == "featured":
        items.append({"factor": "featured", "weight": w.featured, "detail": "featured tier"})
    if aid in ctx.hero_asset_ids:
        items.append({"factor": "hero_dup", "weight": 0.85, "detail": "chapter hero duplicate"})
    items.append({"factor": "score", "weight": 1.0, "detail": f"{score:.3f}"})
    return items[:4]


def _effective_min_score(layout_count: int, cfg: MomentConfig) -> float:
    if (
        cfg.auto_disable_small_trip
        and layout_count <= cfg.small_trip_max_assets
    ):
        return 1.0
    if 16 <= layout_count <= 19:
        return cfg.small_trip_elevated_min_score
    return cfg.min_score


def _should_skip_moment(layout_count: int, cfg: MomentConfig) -> bool:
    return cfg.auto_disable_small_trip and layout_count <= cfg.small_trip_max_assets


def _write_moment_fields(
    trip: dict,
    *,
    pool_ids: list[str],
    signature_id: str,
    cfg: MomentConfig,
    explain: list[dict[str, Any]] | None = None,
    skipped: str | None = None,
    collision: str | None = None,
) -> None:
    curation = trip.setdefault("curation", {})
    if skipped:
        trip.pop("momentAssetId", None)
        for key in (
            "momentPoolIds",
            "momentSecondaryIds",
            "momentPoolSize",
            "momentCandidates",
            "momentExplain",
            "momentPosition",
            "momentCollision",
        ):
            curation.pop(key, None)
        curation["momentSkipped"] = skipped
        return

    curation.pop("momentSkipped", None)
    if not pool_ids or not signature_id:
        trip.pop("momentAssetId", None)
        curation.pop("momentPoolIds", None)
        curation.pop("momentSecondaryIds", None)
        curation.pop("momentPoolSize", None)
        curation.pop("momentCandidates", None)
        curation.pop("momentExplain", None)
        return

    trip["momentAssetId"] = signature_id
    curation["momentPoolIds"] = pool_ids
    curation["momentPoolSize"] = len(pool_ids)
    curation["momentSecondaryIds"] = [aid for aid in pool_ids if aid != signature_id]
    curation["momentCandidates"] = pool_ids[:3]
    curation["momentPosition"] = cfg.position
    if explain:
        curation["momentExplain"] = explain
    if collision:
        curation["momentCollision"] = collision
        # PRD §6.6 · soft warning when moment overlaps locked closing; never steal closing
        warnings = curation.get("bookendsSoftWarnings")
        if not isinstance(warnings, list):
            warnings = []
        code = "moment_closing_overlap"
        if not any(isinstance(w, dict) and w.get("code") == code for w in warnings):
            warnings.append(
                {
                    "code": code,
                    "message": "高光时刻与封底撞车；已保留封底，仅作提示。",
                }
            )
        curation["bookendsSoftWarnings"] = warnings[-5:]
    else:
        curation.pop("momentCollision", None)


def sync_trip_moments_preflight(
    trip: dict,
    layout_assets: list[dict],
    *,
    cfg: MomentConfig,
    arc_profile: str = "dynamic",
    featured_weight: float = 1.35,
    aesthetic_enabled: bool = True,
    meta_places: list[str] | None = None,
    memory_anchors: list[str] | None = None,
) -> list[str]:
    """Pre-layout pool (no on_screen factor) for secondary hero hints."""
    if not cfg.enabled or _should_skip_moment(len(layout_assets), cfg):
        curation = trip.setdefault("curation", {})
        curation.pop("momentSecondaryHintIds", None)
        return []

    pool = build_moment_pool(
        trip,
        layout_assets,
        cfg=cfg,
        chapters=None,
        arc_profile=arc_profile,
        include_on_screen=False,
        featured_weight=featured_weight,
        aesthetic_enabled=aesthetic_enabled,
        meta_places=meta_places,
        memory_anchors=memory_anchors,
    )
    curation = trip.setdefault("curation", {})
    if len(pool) > 1:
        curation["momentSecondaryHintIds"] = pool[1:]
    else:
        curation.pop("momentSecondaryHintIds", None)
    return pool


def sync_trip_moments_finalize(
    trip: dict,
    layout_assets: list[dict],
    chapters: list[dict],
    *,
    cfg: MomentConfig,
    arc_profile: str = "dynamic",
    featured_weight: float = 1.35,
    aesthetic_enabled: bool = True,
    meta_places: list[str] | None = None,
    memory_anchors: list[str] | None = None,
    chapter_heroes: dict[str, str] | None = None,
) -> str | None:
    """Post-layout: full pool + signature moment."""
    curation = trip.setdefault("curation", {})
    curation.pop("momentSecondaryHintIds", None)

    if not cfg.enabled:
        _write_moment_fields(trip, pool_ids=[], signature_id="", cfg=cfg, skipped="disabled")
        return None

    layout_count = len(layout_assets)
    if _should_skip_moment(layout_count, cfg):
        _write_moment_fields(trip, pool_ids=[], signature_id="", cfg=cfg, skipped="small_trip")
        return None

    hero_ids = set((chapter_heroes or {}).values())
    pool = build_moment_pool(
        trip,
        layout_assets,
        cfg=cfg,
        chapters=chapters,
        arc_profile=arc_profile,
        include_on_screen=True,
        featured_weight=featured_weight,
        aesthetic_enabled=aesthetic_enabled,
        meta_places=meta_places,
        memory_anchors=memory_anchors,
        hero_asset_ids=hero_ids,
    )
    if not pool:
        _write_moment_fields(trip, pool_ids=[], signature_id="", cfg=cfg, skipped="no_candidate")
        return None

    assets_by_id = {str(a.get("id")): a for a in layout_assets if a.get("id")}
    ctx = _build_score_ctx(
        cfg=cfg,
        layout_assets=layout_assets,
        chapters=chapters,
        trip=trip,
        arc_profile=arc_profile,
        include_on_screen=True,
        featured_weight=featured_weight,
        aesthetic_enabled=aesthetic_enabled,
        meta_places=meta_places,
        memory_anchors=memory_anchors,
        hero_asset_ids=hero_ids,
    )
    ranked = _rank_assets([assets_by_id[aid] for aid in pool if aid in assets_by_id], ctx)
    if not ranked:
        _write_moment_fields(trip, pool_ids=[], signature_id="", cfg=cfg, skipped="no_candidate")
        return None

    cover_ids = _cover_ids_to_exclude(trip)
    signature_id = ""
    signature_score = 0.0
    for aid, score in ranked:
        if aid in cover_ids:
            continue
        signature_id, signature_score = aid, score
        break
    if not signature_id:
        _write_moment_fields(trip, pool_ids=[], signature_id="", cfg=cfg, skipped="no_candidate")
        return None
    min_score = _effective_min_score(layout_count, cfg)
    if signature_score < min_score:
        _write_moment_fields(trip, pool_ids=[], signature_id="", cfg=cfg, skipped="below_min_score")
        return None

    explain = _moment_explain(assets_by_id.get(signature_id, {}), signature_score, ctx)
    collision: str | None = None
    curation_live = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    if "closingAssetId" in curation_live:
        closing_id = curation_live.get("closingAssetId")
        if closing_id and str(closing_id) == signature_id:
            collision = "closing"
    else:
        # Read-only probe — do not persist closing from moment path (ADR-017)
        from travelogue.domain.closing_view import resolve_closing_asset_id

        assets_map = assets_by_id
        closing_id = resolve_closing_asset_id(
            trip,
            assets_map,
            exclude_ids={signature_id},
        )
        if closing_id == signature_id:
            collision = "closing"

    _write_moment_fields(
        trip,
        pool_ids=pool,
        signature_id=signature_id,
        cfg=cfg,
        explain=explain,
        collision=collision,
    )
    try:
        from travelogue.config.edition import is_portfolio_trip

        if is_portfolio_trip(trip):
            return signature_id
    except Exception:
        pass
    if cfg.pool_solo:
        ensure_pool_assets_solo_screens(
            chapters,
            pool,
            signature_id,
            assets_by_id=assets_by_id,
            arc_profile=arc_profile,
            cfg=cfg,
        )
    else:
        ensure_moment_asset_in_chapters(
            chapters,
            signature_id,
            assets_by_id=assets_by_id,
            arc_profile=arc_profile,
        )
    return signature_id


def _chapter_bucket_ids(chapter: dict) -> set[str]:
    curation = chapter.get("curation") or {}
    out: set[str] = set()
    for aid in curation.get("assetIds") or []:
        val = str(aid or "").strip()
        if val:
            out.add(val)
    return out


def _pick_moment_chapter_index(
    chapters: list[dict],
    signature_id: str,
    *,
    arc_profile: str,
) -> int:
    if not chapters:
        return 0
    peak_indices = _peak_chapter_indices(chapters, arc_profile=arc_profile)
    for idx in sorted(peak_indices):
        if signature_id in _chapter_bucket_ids(chapters[idx]):
            return idx
    for i, ch in enumerate(chapters):
        if signature_id in _chapter_bucket_ids(ch):
            return i
    for i, ch in enumerate(chapters):
        on_screen = _collect_screen_asset_ids([ch])
        if signature_id in on_screen:
            return i
    if peak_indices:
        return min(sorted(peak_indices)[0], len(chapters) - 1)
    return 0


def _solo_pattern_for_asset(asset: dict) -> str:
    kind = aspect_kind_for_asset(asset)
    if kind in ("portrait", "tall", "square"):
        return "screen-portrait-1"
    return "screen-landscape-1"


def _asset_ids_from_slots(slots: list[dict]) -> list[str]:
    out: list[str] = []
    for slot in slots:
        aid = str(slot.get("assetId") or "").strip()
        if aid:
            out.append(aid)
    return out


def _is_fixed_composite_pattern(pattern_id: str) -> bool:
    """Patterns whose slot geometry breaks when a single tile is removed."""
    pid = str(pattern_id or "")
    if pid.startswith("screen-mosaic-"):
        return True
    if "portrait" in pid and "landscape" in pid:
        return True
    return pid in frozenset(
        {
            "screen-portrait-4",
            "screen-portrait-6",
            "screen-portrait-9",
            "screen-portrait-grid-8",
            "screen-landscape-4",
            "screen-landscape-6",
            "screen-landscape-9",
        }
    )


def _homogeneous_stack_pattern(
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
) -> str | None:
    """Map a same-family run to screen-{family}-{n} when n ∈ {1,2,3,4}."""
    if not asset_ids or len(asset_ids) > 4:
        return None
    from travelogue.layout_contract.families import (
        layout_family_for_asset as _layout_family_for_asset,
    )

    aspects = {
        aid: aspect_kind_for_asset(assets_by_id.get(aid, {})) for aid in asset_ids
    }
    families = [
        _layout_family_for_asset(aid, aspects, assets_by_id) for aid in asset_ids
    ]
    if len(set(families)) != 1:
        return None
    fam = families[0]
    if fam in ("panorama", "tall", "square"):
        return _solo_pattern_for_asset(assets_by_id.get(asset_ids[0], {}))
    if fam in ("portrait", "landscape") and len(asset_ids) in (1, 2, 3, 4):
        if len(asset_ids) == 1:
            return _solo_pattern_for_asset(assets_by_id.get(asset_ids[0], {}))
        return f"screen-{fam}-{len(asset_ids)}"
    return None


def _decompose_to_primitive_screens(
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
) -> list[dict]:
    """Rebuild remaining assets as valid primitive screens (pair-first portraits)."""
    from travelogue.layout_contract.families import (
        layout_family_for_asset as _layout_family_for_asset,
    )
    from travelogue.layout_engine.adapter import make_screen as _make_screen
    from travelogue.layout_engine.planner.portrait_2_picker import pick_portrait_2_variant

    if not asset_ids:
        return []
    cfg = None
    try:
        from travelogue.config.loader import load_config

        cfg = load_config()
    except Exception:
        cfg = None
    aspects = {
        aid: aspect_kind_for_asset(assets_by_id.get(aid, {})) for aid in asset_ids
    }
    screens: list[dict] = []
    i = 0
    while i < len(asset_ids):
        fam = _layout_family_for_asset(asset_ids[i], aspects, assets_by_id)
        j = i + 1
        while j < len(asset_ids) and _layout_family_for_asset(
            asset_ids[j], aspects, assets_by_id
        ) == fam:
            j += 1
        run = asset_ids[i:j]
        k = 0
        while k < len(run):
            if fam == "portrait":
                if k + 2 <= len(run):
                    chunk = run[k : k + 2]
                    # P2VF · use picker when dogfood config is loaded.
                    pattern_id = pick_portrait_2_variant(
                        chunk,
                        assets_map=assets_by_id,
                        cfg=cfg,
                    ).pattern_id
                    k += 2
                else:
                    chunk = run[k : k + 1]
                    pattern_id = "screen-portrait-1"
                    k += 1
            elif fam == "landscape":
                rem = len(run) - k
                if rem >= 3:
                    chunk = run[k : k + 3]
                    pattern_id = "screen-landscape-3"
                    k += 3
                elif rem == 2:
                    chunk = run[k : k + 2]
                    pattern_id = "screen-landscape-2"
                    k += 2
                else:
                    chunk = run[k : k + 1]
                    pattern_id = "screen-landscape-1"
                    k += 1
            else:
                chunk = run[k : k + 1]
                pattern_id = _solo_pattern_for_asset(assets_by_id.get(chunk[0], {}))
                k += 1
            screens.append(
                _make_screen(
                    pattern_id,
                    chunk,
                    screen_id="",
                    aspects=aspects,
                    assets_map=assets_by_id,
                )
            )
        i = j
    return screens


def _build_pool_solo_screen(
    asset_id: str,
    *,
    role: str = "moment",
    source_slot: dict | None = None,
    assets_by_id: dict[str, dict] | None = None,
) -> dict:
    asset = (assets_by_id or {}).get(asset_id, {})
    pattern = _solo_pattern_for_asset(asset)
    fit = str((source_slot or {}).get("fit") or "cover")
    slot_role = (source_slot or {}).get("role")
    slot: dict = {"assetId": asset_id, "slot": 0, "fit": fit}
    if slot_role:
        slot["role"] = slot_role
    return {"patternId": pattern, "role": role, "slots": [slot]}


def _is_pool_collage_portrait(asset: dict) -> bool:
    """HPPL · secondary collage candidates (portrait/tall; square stays solo)."""
    return aspect_kind_for_asset(asset) in ("portrait", "tall")


def _tile_pool_portrait_counts(n: int, *, max_per_screen: int = 3) -> list[int]:
    """HPPL · triple-first tiling for secondary pool portraits (3 → 2 → 1)."""
    max_n = max(1, min(3, int(max_per_screen or 3)))
    groups: list[int] = []
    remaining = max(0, int(n))
    while remaining > 0:
        if remaining >= 3 and max_n >= 3:
            groups.append(3)
            remaining -= 3
        elif remaining >= 2 and max_n >= 2:
            groups.append(2)
            remaining -= 2
        else:
            groups.append(1)
            remaining -= 1
    return groups


def _order_portraits_for_collage(
    asset_ids: list[str],
    assets_by_id: dict[str, dict],
) -> list[str]:
    """Prefer chronological takenAt; undated keep relative pool order at end."""
    indexed = list(enumerate(asset_ids))

    def sort_key(item: tuple[int, str]) -> tuple[int, str, int]:
        idx, aid = item
        taken = str((assets_by_id.get(aid) or {}).get("takenAt") or "").strip()
        if taken:
            return (0, taken, idx)
        return (1, "", idx)

    indexed.sort(key=sort_key)
    return [aid for _, aid in indexed]


def _build_pool_collage_screen(
    asset_ids: list[str],
    *,
    role: str = "peak",
    assets_by_id: dict[str, dict] | None = None,
) -> dict:
    ids = [str(a).strip() for a in asset_ids if str(a).strip()]
    n = len(ids)
    if n <= 1:
        aid = ids[0] if ids else ""
        return _build_pool_solo_screen(aid, role=role, assets_by_id=assets_by_id)
    if n > 3:
        ids = ids[:3]
        n = 3
    pattern = f"screen-portrait-{n}"
    slots: list[dict] = [
        {"assetId": aid, "slot": i, "fit": "cover"} for i, aid in enumerate(ids)
    ]
    return {"patternId": pattern, "role": role, "slots": slots}


_HPPL_LAST_STATS: dict[str, int] = {"collage_emit": 0, "collage_fallback": 0}


def get_hppl_last_stats() -> dict[str, int]:
    """Return emit/fallback counters from the last collage ensure pass."""
    return dict(_HPPL_LAST_STATS)


def _is_highlight_role_screen(screen: dict | None) -> bool:
    if not screen:
        return False
    return str(screen.get("role") or "") in ("moment", "peak")


def _pattern_is_portrait_pair(pattern_id: str) -> bool:
    from travelogue.layout_contract.rhythm import PORTRAIT_PAIR_PATTERNS

    return str(pattern_id or "") in PORTRAIT_PAIR_PATTERNS


def _pattern_is_portrait_multi(pattern_id: str) -> bool:
    from travelogue.layout_contract.rhythm import (
        PORTRAIT_PAIR_PATTERNS,
        PORTRAIT_TRIPLE_PATTERNS,
    )

    pid = str(pattern_id or "")
    return pid in PORTRAIT_PAIR_PATTERNS or pid in PORTRAIT_TRIPLE_PATTERNS


def _trailing_portrait_pair_streak(screens: list[dict], end_idx: int) -> int:
    streak = 0
    for i in range(end_idx - 1, -1, -1):
        if _pattern_is_portrait_pair(str(screens[i].get("patternId") or "")):
            streak += 1
        else:
            break
    return streak


def _nudge_away_from_portrait_multi(screens: list[dict], pos: int) -> int:
    """Prefer an insert index whose previous screen is not portrait-2/3."""
    n = len(screens)
    pos = max(0, min(pos, n))
    for _ in range(n + 1):
        prev_multi = pos > 0 and _pattern_is_portrait_multi(
            str(screens[pos - 1].get("patternId") or "")
        )
        if not prev_multi:
            return pos
        pos += 1
        if pos > n:
            return n
    return pos


def _should_degrade_peak_collage(
    screens: list[dict],
    insert_at: int,
    screen: dict,
    *,
    max_pair_streak: int,
) -> bool:
    slots = screen.get("slots") or []
    if len(slots) <= 1:
        return False
    pid = str(screen.get("patternId") or "")
    if insert_at > 0 and _pattern_is_portrait_multi(
        str(screens[insert_at - 1].get("patternId") or "")
    ):
        return True
    if _pattern_is_portrait_pair(pid) and (
        _trailing_portrait_pair_streak(screens, insert_at) >= max_pair_streak
    ):
        return True
    return False


def _degrade_collage_to_solos(
    screen: dict,
    *,
    assets_by_id: dict[str, dict],
) -> list[dict]:
    out: list[dict] = []
    for slot in screen.get("slots") or []:
        aid = str(slot.get("assetId") or "").strip()
        if not aid:
            continue
        out.append(
            _build_pool_solo_screen(
                aid,
                role="peak",
                source_slot=dict(slot),
                assets_by_id=assets_by_id,
            )
        )
    return out


def _resolve_max_portrait_pair_streak() -> int:
    try:
        from travelogue.config.loader import load_config

        return int(load_config().layout.rhythm.max_portrait_pair_streak)
    except Exception:
        from travelogue.layout_contract.rhythm import MAX_PORTRAIT_PAIR_STREAK

        return int(MAX_PORTRAIT_PAIR_STREAK)


def _extract_pool_asset_from_chapters(
    chapters: list[dict],
    asset_id: str,
    *,
    assets_by_id: dict[str, dict],
) -> tuple[int, dict | None]:
    """Remove asset from chapter screens; return (chapter_idx, source_slot)."""
    if not asset_id or not chapters:
        return 0, None
    host = _find_moment_host(chapters, asset_id)
    if host is None:
        return _pick_pool_asset_chapter_index(chapters, asset_id), None

    ch_idx, screen_idx, slot_idx = host
    chapter = chapters[ch_idx]
    screens = list(chapter.get("screens") or [])
    host_screen = dict(screens[screen_idx])
    slots = list(host_screen.get("slots") or [])
    if not slots or slot_idx >= len(slots):
        return ch_idx, None
    source_slot = dict(slots[slot_idx])
    if len(slots) == 1:
        screens.pop(screen_idx)
        chapter["screens"] = screens
        return ch_idx, source_slot

    remaining = [dict(s) for i, s in enumerate(slots) if i != slot_idx]
    normalized = _normalize_screen_after_slot_removal(
        {**host_screen, "slots": remaining},
        assets_by_id=assets_by_id,
    )
    if normalized is None:
        screens.pop(screen_idx)
    elif isinstance(normalized, list):
        screens[screen_idx : screen_idx + 1] = normalized
    else:
        screens[screen_idx] = normalized
    chapter["screens"] = screens
    return ch_idx, source_slot


def _pick_highlight_insert_index(screens: list[dict], prefer: int) -> int:
    """Insert index that avoids adjacent moment/peak screens when possible."""
    n = len(screens)
    if n == 0:
        return 0
    pos = max(0, min(prefer, n))
    for _ in range(n + 1):
        prev_ok = pos == 0 or not _is_highlight_role_screen(screens[pos - 1])
        next_ok = pos >= n or not _is_highlight_role_screen(screens[pos])
        if prev_ok and next_ok:
            return pos
        pos += 1
        if pos > n:
            pos = 0
    return max(1, min(prefer, n))


def _insert_peak_screens(
    chapter: dict,
    new_screens: list[dict],
    *,
    assets_by_id: dict[str, dict],
    max_pair_streak: int = 2,
    stats: dict[str, int] | None = None,
) -> None:
    """Insert peak screens with highlight gaps, R-06 pair-streak and portrait-wall guards."""
    if not new_screens:
        return
    screens = list(chapter.get("screens") or [])
    prefer = _pick_pool_insert_index({"screens": screens}, arc_peak=False)
    counters = stats if stats is not None else {"collage_emit": 0, "collage_fallback": 0}
    queue: list[dict] = list(new_screens)

    while queue:
        screen = queue.pop(0)
        insert_at = _pick_highlight_insert_index(screens, prefer)
        insert_at = _nudge_away_from_portrait_multi(screens, insert_at)

        if len(screen.get("slots") or []) > 1 and _should_degrade_peak_collage(
            screens,
            insert_at,
            screen,
            max_pair_streak=max_pair_streak,
        ):
            alt = _nudge_away_from_portrait_multi(
                screens,
                _pick_highlight_insert_index(screens, len(screens)),
            )
            if not _should_degrade_peak_collage(
                screens,
                alt,
                screen,
                max_pair_streak=max_pair_streak,
            ):
                insert_at = alt
            else:
                counters["collage_fallback"] = int(counters.get("collage_fallback", 0)) + 1
                queue[0:0] = _degrade_collage_to_solos(
                    screen, assets_by_id=assets_by_id
                )
                continue

        if len(screen.get("slots") or []) > 1:
            counters["collage_emit"] = int(counters.get("collage_emit", 0)) + 1
        screens.insert(insert_at, screen)
        prefer = insert_at + 2

    chapter["screens"] = screens


def _ensure_secondary_portrait_collage(
    chapters: list[dict],
    secondary_ids: list[str],
    *,
    assets_by_id: dict[str, dict],
    max_per_screen: int = 3,
    max_pair_streak: int | None = None,
) -> int:
    """Extract secondary pool members and re-emit: portrait 3→2→1, landscape solo."""
    global _HPPL_LAST_STATS
    if not secondary_ids or not chapters:
        _HPPL_LAST_STATS = {"collage_emit": 0, "collage_fallback": 0}
        return 0

    from collections import defaultdict

    pair_max = (
        int(max_pair_streak)
        if max_pair_streak is not None
        else _resolve_max_portrait_pair_streak()
    )
    stats = {"collage_emit": 0, "collage_fallback": 0}

    by_chapter: dict[int, list[str]] = defaultdict(list)
    source_slots: dict[str, dict | None] = {}
    for aid in secondary_ids:
        ch_idx, source_slot = _extract_pool_asset_from_chapters(
            chapters, aid, assets_by_id=assets_by_id
        )
        by_chapter[ch_idx].append(aid)
        source_slots[aid] = source_slot

    changed = 0
    for ch_idx, aids in by_chapter.items():
        chapter = chapters[ch_idx]
        portraits = [
            aid
            for aid in aids
            if _is_pool_collage_portrait(assets_by_id.get(aid, {}))
        ]
        others = [aid for aid in aids if aid not in set(portraits)]
        portraits = _order_portraits_for_collage(portraits, assets_by_id)

        to_insert: list[dict] = []
        for aid in others:
            to_insert.append(
                _build_pool_solo_screen(
                    aid,
                    role="peak",
                    source_slot=source_slots.get(aid),
                    assets_by_id=assets_by_id,
                )
            )
            changed += 1

        cursor = 0
        for size in _tile_pool_portrait_counts(
            len(portraits), max_per_screen=max_per_screen
        ):
            chunk = portraits[cursor : cursor + size]
            cursor += size
            if size <= 1:
                aid = chunk[0]
                to_insert.append(
                    _build_pool_solo_screen(
                        aid,
                        role="peak",
                        source_slot=source_slots.get(aid),
                        assets_by_id=assets_by_id,
                    )
                )
            else:
                to_insert.append(
                    _build_pool_collage_screen(
                        chunk, role="peak", assets_by_id=assets_by_id
                    )
                )
            changed += 1

        # Prefer portrait collages before landscape solos in the insert band.
        collages = [s for s in to_insert if len(s.get("slots") or []) > 1]
        solos = [s for s in to_insert if len(s.get("slots") or []) <= 1]
        _insert_peak_screens(
            chapter,
            collages + solos,
            assets_by_id=assets_by_id,
            max_pair_streak=pair_max,
            stats=stats,
        )
    _HPPL_LAST_STATS = dict(stats)
    return changed


def _build_moment_solo_screen(
    signature_id: str,
    *,
    source_slot: dict | None = None,
    assets_by_id: dict[str, dict] | None = None,
) -> dict:
    return _build_pool_solo_screen(
        signature_id,
        role="moment",
        source_slot=source_slot,
        assets_by_id=assets_by_id,
    )


def _normalize_screen_after_slot_removal(
    screen: dict,
    *,
    assets_by_id: dict[str, dict],
) -> dict | list[dict] | None:
    slots = [dict(s) for s in (screen.get("slots") or [])]
    if not slots:
        return None
    for i, slot in enumerate(slots):
        slot["slot"] = i
    out = dict(screen)
    out.pop("role", None)
    out.pop("layoutGeometry", None)
    original_pattern = str(out.get("patternId") or "")
    asset_ids = _asset_ids_from_slots(slots)
    n = len(slots)

    if _is_fixed_composite_pattern(original_pattern):
        rebuilt = _decompose_to_primitive_screens(asset_ids, assets_by_id)
        return rebuilt if rebuilt else None

    if n == 1:
        aid = asset_ids[0]
        out["patternId"] = _solo_pattern_for_asset(assets_by_id.get(aid, {}))
        out["slots"] = slots
        return out

    stack_pattern = _homogeneous_stack_pattern(asset_ids, assets_by_id)
    if stack_pattern is not None:
        out["patternId"] = stack_pattern
        out["slots"] = slots
        return out

    rebuilt = _decompose_to_primitive_screens(asset_ids, assets_by_id)
    if rebuilt:
        return rebuilt
    out["slots"] = slots
    return out


def _find_moment_host(
    chapters: list[dict],
    signature_id: str,
) -> tuple[int, int, int] | None:
    for ch_idx, ch in enumerate(chapters or []):
        for screen_idx, screen in enumerate(ch.get("screens") or []):
            if str(screen.get("patternId") or "") == "screen-breath-pause":
                continue
            for slot_idx, slot in enumerate(screen.get("slots") or []):
                if str(slot.get("assetId") or "").strip() == signature_id:
                    return ch_idx, screen_idx, slot_idx
    return None


def tag_moment_inline_screen(chapters: list[dict], signature_id: str) -> bool:
    """Mark the first layout-screen that carries the signature moment asset."""
    if not signature_id:
        return False
    for ch in chapters or []:
        for screen in ch.get("screens") or []:
            if str(screen.get("patternId") or "") == "screen-breath-pause":
                continue
            for slot in screen.get("slots") or []:
                if str(slot.get("assetId") or "").strip() == signature_id:
                    screen["role"] = "moment"
                    return True
    return False


def _pick_pool_asset_chapter_index(chapters: list[dict], asset_id: str) -> int:
    if not chapters:
        return 0
    for i, ch in enumerate(chapters):
        if asset_id in _chapter_bucket_ids(ch):
            return i
    for i, ch in enumerate(chapters):
        on_screen = _collect_screen_asset_ids([ch])
        if asset_id in on_screen:
            return i
    return 0


def _pick_pool_insert_index(chapter: dict, *, arc_peak: bool = False) -> int:
    screens = chapter.get("screens") or []
    n = len(screens)
    if n == 0:
        return 0
    if arc_peak:
        return max(1, n // 2)
    return max(1, min(n, int(n * 0.7)))


def _ensure_pool_asset_solo_screen(
    chapters: list[dict],
    asset_id: str,
    *,
    role: str,
    assets_by_id: dict[str, dict] | None = None,
    arc_profile: str = "dynamic",
) -> bool:
    """Ensure one pool asset is a dedicated single-slot layout-screen."""
    if not asset_id or not chapters:
        return False

    assets = assets_by_id or {}
    host = _find_moment_host(chapters, asset_id)
    if host is None:
        if role == "moment":
            ch_idx = _pick_moment_chapter_index(chapters, asset_id, arc_profile=arc_profile)
            insert_at = None
        else:
            ch_idx = _pick_pool_asset_chapter_index(chapters, asset_id)
            insert_at = None
        chapter = chapters[ch_idx]
        screens = list(chapter.get("screens") or [])
        if insert_at is None:
            insert_at = _pick_pool_insert_index(chapter, arc_peak=(role == "moment"))
        screens.insert(
            insert_at,
            _build_pool_solo_screen(asset_id, role=role, assets_by_id=assets),
        )
        chapter["screens"] = screens
        return True

    ch_idx, screen_idx, slot_idx = host
    chapter = chapters[ch_idx]
    screens = list(chapter.get("screens") or [])
    host_screen = dict(screens[screen_idx])
    slots = list(host_screen.get("slots") or [])
    if len(slots) == 1 and str(slots[0].get("assetId") or "").strip() == asset_id:
        if role == "peak" and screen_idx == 0:
            solo = _build_pool_solo_screen(
                asset_id,
                role=role,
                source_slot=slots[0],
                assets_by_id=assets,
            )
            screens.pop(screen_idx)
            insert_pos = _pick_pool_insert_index({"screens": screens}, arc_peak=False)
            screens.insert(insert_pos, solo)
            chapter["screens"] = screens
            return True
        host_screen["role"] = role
        screens[screen_idx] = host_screen
        chapter["screens"] = screens
        return True

    source_slot = dict(slots[slot_idx])
    remaining = [dict(s) for i, s in enumerate(slots) if i != slot_idx]
    normalized = _normalize_screen_after_slot_removal(
        {**host_screen, "slots": remaining},
        assets_by_id=assets,
    )
    solo = _build_pool_solo_screen(
        asset_id,
        role=role,
        source_slot=source_slot,
        assets_by_id=assets,
    )
    if normalized is None:
        insert_pos = max(screen_idx + 1, 1)
        screens.pop(screen_idx)
        screens.insert(insert_pos if insert_pos <= len(screens) else len(screens), solo)
    elif isinstance(normalized, list):
        screens[screen_idx : screen_idx + 1] = normalized
        insert_pos = screen_idx + len(normalized)
        screens.insert(insert_pos, solo)
    else:
        insert_pos = max(screen_idx + 1, 1)
        screens[screen_idx] = normalized
        screens.insert(insert_pos, solo)
    chapter["screens"] = screens
    return True


def ensure_pool_assets_solo_screens(
    chapters: list[dict],
    pool_ids: list[str],
    signature_id: str,
    *,
    assets_by_id: dict[str, dict] | None = None,
    arc_profile: str = "dynamic",
    cfg: MomentConfig | None = None,
) -> int:
    """Ensure pool assets leave ordinary multi-slot hosts.

    Signature is always a dedicated solo ``moment`` screen.
    When ``cfg.pool_portrait_collage`` is enabled (default) and ``pool_solo``
    semantics apply, secondary **portrait/tall** peaks prefer 3→2→1 collage;
    landscape secondaries stay solo. Pass ``pool_portrait_collage=False`` to
    restore P23.1 all-solo behavior.
    """
    if not chapters or not pool_ids:
        return 0

    moment_cfg = cfg or MomentConfig()
    assets = assets_by_id or {}
    sig = str(signature_id or "").strip()
    ordered: list[str] = []
    seen: set[str] = set()
    for aid in pool_ids:
        val = str(aid or "").strip()
        if val and val not in seen:
            seen.add(val)
            ordered.append(val)

    changed = 0
    if sig and sig in seen:
        if _ensure_pool_asset_solo_screen(
            chapters,
            sig,
            role="moment",
            assets_by_id=assets,
            arc_profile=arc_profile,
        ):
            changed += 1

    secondary = [aid for aid in ordered if aid != sig]
    # AC-HPPL-09 · collage only when pool_solo is on (do not entangle secondary_boost path)
    use_collage = bool(moment_cfg.pool_portrait_collage) and bool(moment_cfg.pool_solo)
    if moment_cfg.pool_portrait_collage and not moment_cfg.pool_solo:
        import logging

        logging.getLogger(__name__).debug(
            "hppl: skip pool_portrait_collage because pool_solo=false"
        )
    if use_collage and secondary:
        changed += _ensure_secondary_portrait_collage(
            chapters,
            secondary,
            assets_by_id=assets,
            max_per_screen=moment_cfg.pool_portrait_collage_max_per_screen,
        )
        return changed

    for aid in secondary:
        if _ensure_pool_asset_solo_screen(
            chapters,
            aid,
            role="peak",
            assets_by_id=assets,
            arc_profile=arc_profile,
        ):
            changed += 1
    return changed


def ensure_moment_asset_in_chapters(
    chapters: list[dict],
    signature_id: str,
    *,
    assets_by_id: dict[str, dict] | None = None,
    arc_profile: str = "dynamic",
) -> bool:
    """Ensure signature moment is a dedicated single-slot layout-screen."""
    return bool(
        _ensure_pool_asset_solo_screen(
            chapters,
            signature_id,
            role="moment",
            assets_by_id=assets_by_id,
            arc_profile=arc_profile,
        )
    )


def preferred_secondary_hero_for_bucket(
    bucket: list[str],
    hint_ids: list[str] | None,
) -> str | None:
    if not hint_ids:
        return None
    bucket_set = set(bucket)
    for aid in hint_ids:
        if aid in bucket_set:
            return aid
    return None


def score_ranked_moment_pool(
    trip: dict,
    layout_assets: list[dict],
    chapters: list[dict] | None = None,
    *,
    cfg: MomentConfig | None = None,
    top_n: int | None = None,
) -> list[dict[str, Any]]:
    """Rank moment pool by peak_moment_score (blind-review export; not momentCandidates order)."""
    moment_cfg = cfg or MomentConfig()
    pool = list((trip.get("curation") or {}).get("momentPoolIds") or [])
    if not pool:
        return []

    assets_by_id = {str(a.get("id")): a for a in layout_assets if a.get("id")}
    ctx = _build_score_ctx(
        cfg=moment_cfg,
        layout_assets=layout_assets,
        chapters=chapters,
        trip=trip,
        arc_profile="dynamic",
        include_on_screen=True,
        featured_weight=1.35,
        aesthetic_enabled=True,
        meta_places=None,
        memory_anchors=None,
        hero_asset_ids=set(),
    )
    ranked = _rank_assets([assets_by_id[aid] for aid in pool if aid in assets_by_id], ctx)
    rows = [
        {"rank": i + 1, "assetId": aid, "score": round(score, 4)}
        for i, (aid, score) in enumerate(ranked)
    ]
    if top_n is not None:
        rows = rows[:top_n]
    return rows
