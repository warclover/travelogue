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


def _eligible_moment_candidates(assets: list[dict], *, exclude: set[str]) -> list[dict]:
    out: list[dict] = []
    for asset in assets:
        aid = str(asset.get("id") or "").strip()
        if not aid or aid in exclude:
            continue
        if asset.get("type") != "image":
            continue
        if not asset.get("layoutEligible", True):
            continue
        if asset.get("mediaClass") in _EXCLUDED_MEDIA:
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
    from travelogue.layout_engine.highlight_windows import detect_highlight_windows

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
    exclude = _cover_ids_to_exclude(trip)
    candidates = _eligible_moment_candidates(layout_assets, exclude=exclude)
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
    from travelogue.render.cover_closing import resolve_closing_asset_id

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


def _build_moment_solo_screen(
    signature_id: str,
    *,
    source_slot: dict | None = None,
    assets_by_id: dict[str, dict] | None = None,
) -> dict:
    asset = (assets_by_id or {}).get(signature_id, {})
    pattern = _solo_pattern_for_asset(asset)
    fit = str((source_slot or {}).get("fit") or "cover")
    role = (source_slot or {}).get("role")
    slot: dict = {"assetId": signature_id, "slot": 0, "fit": fit}
    if role:
        slot["role"] = role
    return {"patternId": pattern, "role": "moment", "slots": [slot]}


def _normalize_screen_after_slot_removal(
    screen: dict,
    *,
    assets_by_id: dict[str, dict],
) -> dict | None:
    slots = [dict(s) for s in (screen.get("slots") or [])]
    if not slots:
        return None
    for i, slot in enumerate(slots):
        slot["slot"] = i
    out = dict(screen)
    out.pop("role", None)
    out.pop("layoutGeometry", None)
    n = len(slots)
    if n == 1:
        aid = str(slots[0].get("assetId") or "")
        out["patternId"] = _solo_pattern_for_asset(assets_by_id.get(aid, {}))
        out["slots"] = slots
        return out
    downgrade = {
        2: "screen-landscape-2",
        3: "screen-landscape-3",
        4: "screen-landscape-4",
    }
    if n in downgrade:
        out["patternId"] = downgrade[n]
        out["slots"] = slots
        return out
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


def ensure_moment_asset_in_chapters(
    chapters: list[dict],
    signature_id: str,
    *,
    assets_by_id: dict[str, dict] | None = None,
    arc_profile: str = "dynamic",
) -> bool:
    """Ensure signature moment is a dedicated single-slot layout-screen."""
    if not signature_id or not chapters:
        return False

    assets = assets_by_id or {}
    host = _find_moment_host(chapters, signature_id)
    if host is None:
        ch_idx = _pick_moment_chapter_index(chapters, signature_id, arc_profile=arc_profile)
        chapter = chapters[ch_idx]
        screens = list(chapter.get("screens") or [])
        insert_at = max(1, len(screens) // 2) if screens else 0
        screens.insert(
            insert_at,
            _build_moment_solo_screen(signature_id, assets_by_id=assets),
        )
        chapter["screens"] = screens
        return True

    ch_idx, screen_idx, slot_idx = host
    chapter = chapters[ch_idx]
    screens = list(chapter.get("screens") or [])
    host_screen = dict(screens[screen_idx])
    slots = list(host_screen.get("slots") or [])
    if len(slots) == 1 and str(slots[0].get("assetId") or "").strip() == signature_id:
        host_screen["role"] = "moment"
        screens[screen_idx] = host_screen
        chapter["screens"] = screens
        return True

    source_slot = dict(slots[slot_idx])
    remaining = [dict(s) for i, s in enumerate(slots) if i != slot_idx]
    normalized = _normalize_screen_after_slot_removal(
        {**host_screen, "slots": remaining},
        assets_by_id=assets,
    )
    solo = _build_moment_solo_screen(
        signature_id,
        source_slot=source_slot,
        assets_by_id=assets,
    )
    if normalized is None:
        screens.pop(screen_idx)
        screens.insert(screen_idx, solo)
    else:
        screens[screen_idx] = normalized
        screens.insert(screen_idx + 1, solo)
    chapter["screens"] = screens
    return True


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
