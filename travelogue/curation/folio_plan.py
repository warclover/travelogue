"""Folio full plan · featured-grid dedupe (PRD-EXPERIENCE appendix C · E7)."""

from __future__ import annotations

from typing import Any

from travelogue.curation.layout_planner import aspect_kind_for_asset

FEATURED_GRID_MIN = 4
FEATURED_GRID_MAX = 12


def collect_screen_asset_ids(chapters: list[dict]) -> set[str]:
    out: set[str] = set()
    for ch in chapters:
        for sc in ch.get("screens") or []:
            for slot in sc.get("slots") or []:
                aid = slot.get("assetId")
                if isinstance(aid, str) and aid:
                    out.add(aid)
    return out


def pick_featured_grid_asset_ids(
    layout_assets: list[dict],
    *,
    min_count: int = FEATURED_GRID_MIN,
    max_count: int = FEATURED_GRID_MAX,
    featured_weight: float = 1.35,
    exclude_ids: set[str] | frozenset[str] | None = None,
) -> list[str]:
    """Portrait-first featured pool for featured-grid (≥ min_count or empty)."""
    from travelogue.curation.curate_scoring import effective_hero_score, median_sharpness

    excluded = set(exclude_ids or set())
    featured = [
        a
        for a in layout_assets
        if a.get("userTier") == "featured"
        and a.get("layoutEligible", True)
        and a.get("type") != "video"
        and a.get("id")
        and str(a.get("id")) not in excluded
    ]
    if len(featured) < min_count:
        return []

    med = median_sharpness(featured)
    portraits = [
        a for a in featured if aspect_kind_for_asset(a) in ("portrait", "tall", "square")
    ]
    pool = portraits if len(portraits) >= min_count else featured
    scored = sorted(
        pool,
        key=lambda a: effective_hero_score(a, median_sharp=med, featured_weight=featured_weight),
        reverse=True,
    )
    return [str(a["id"]) for a in scored[:max_count]]


def strip_assets_from_screens(chapters: list[dict], exclude: set[str]) -> int:
    """Remove grid asset slots from chapter screens; drop empty screens."""
    if not exclude:
        return 0
    removed = 0
    for ch in chapters:
        screens = ch.get("screens") or []
        kept: list[dict] = []
        for sc in screens:
            slots = sc.get("slots") or []
            new_slots = [s for s in slots if s.get("assetId") not in exclude]
            removed += len(slots) - len(new_slots)
            if not new_slots:
                continue
            if len(new_slots) != len(slots):
                sc = dict(sc)
                sc["slots"] = new_slots
            kept.append(sc)
        ch["screens"] = kept
    return removed


def plate_asset_ids_from_chapters(chapters: list[dict]) -> list[str]:
    out: list[str] = []
    for ch in chapters:
        screens = ch.get("screens") or []
        if not screens:
            continue
        slots = screens[0].get("slots") or []
        if not slots:
            continue
        aid = slots[0].get("assetId")
        if isinstance(aid, str) and aid:
            out.append(aid)
    return out


def build_folio_plan(
    trip: dict,
    chapters: list[dict],
    layout_assets: list[dict],
    *,
    featured_weight: float = 1.35,
    mutate_screens: bool = False,
    exclude_grid_ids: set[str] | frozenset[str] | None = None,
) -> dict[str, Any]:
    """
    Plan folio full blocks; optionally strip featured-grid assets from screens.

    ADR-003: featured-grid assets must not repeat in chapter screens.
    Pass ``mutate_screens=True`` explicitly when persisting layout (curate).
    """
    first_ch = (trip.get("chapters") or [{}])[0]
    has_foreword = bool(str(first_ch.get("lead") or "").strip())

    grid_ids = pick_featured_grid_asset_ids(
        layout_assets,
        featured_weight=featured_weight,
        exclude_ids=exclude_grid_ids,
    )
    plan: dict[str, Any] = {
        "index": True,
        "foreword": has_foreword,
        "featuredGrid": False,
        "featuredGridAssetIds": [],
        "plateAssetIds": [],
    }

    if len(grid_ids) >= FEATURED_GRID_MIN:
        plan["featuredGrid"] = True
        plan["featuredGridAssetIds"] = grid_ids
        if mutate_screens:
            strip_assets_from_screens(chapters, set(grid_ids))

    plan["plateAssetIds"] = plate_asset_ids_from_chapters(chapters)
    return plan


def resolve_folio_plan(
    trip: dict,
    chapters: list[dict],
    layout_assets: list[dict] | None = None,
) -> dict[str, Any]:
    """Read persisted plan or compute ephemeral plan for render."""
    raw = (trip.get("curation") or {}).get("folioPlan")
    if isinstance(raw, dict) and raw.get("featuredGridAssetIds") is not None:
        return raw
    assets = layout_assets or [
        a for a in (trip.get("assets") or []) if a.get("layoutEligible", True)
    ]
    return build_folio_plan(trip, chapters, assets, mutate_screens=False)
