"""Trip/chapter-level screen attachment (extracted from screen_planner for thinner entry)."""

from __future__ import annotations

from travelogue.config import AppConfig
from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState
from travelogue.curation.screen_planner import (
    DEFAULT_FEATURED_WEIGHT,
    LAYOUT_ENGINE_SCREENS,
    _collect_asset_ids_from_chapter,
    _sort_asset_ids_by_taken,
    plan_screens_for_chapter,
)
from travelogue.media.image_ops import AspectKind


def _preferred_hero_for_bucket(
    bucket: list[str],
    asset_to_ch: dict[str, str],
    hero_by_ch: dict[str, str],
    assets_by_id: dict[str, dict],
    *,
    median_sharp: float | None = None,
    featured_weight: float = DEFAULT_FEATURED_WEIGHT,
) -> str | None:
    from travelogue.curation.curate_scoring import effective_hero_score, median_sharpness

    med = (
        median_sharp
        if median_sharp is not None
        else median_sharpness(list(assets_by_id.values()))
    )
    heroes: list[str] = []
    for aid in bucket:
        ch_id = asset_to_ch.get(aid)
        if not ch_id:
            continue
        hid = hero_by_ch.get(ch_id)
        if hid and hid in bucket:
            heroes.append(hid)
    if not heroes:
        return None
    return max(
        set(heroes),
        key=lambda h: effective_hero_score(
            assets_by_id.get(h) or {}, median_sharp=med, featured_weight=featured_weight
        ),
    )


def attach_screens_day_buckets(
    chapters: list[dict],
    day_buckets: list[list[str]],
    aspects: dict[str, AspectKind],
    *,
    assets: list[dict] | dict[str, dict] | None = None,
    burst_seconds: float = 3.0,
    mixed_proximity_seconds: float | None = None,
    orientation_summary: dict | None = None,
    skip_screen_asset_ids: set[str] | None = None,
    trip_photo_total: int | None = None,
    featured_weight: float = DEFAULT_FEATURED_WEIGHT,
    enable_food_grid: bool = True,
    mundane_grid_buckets: tuple[str, ...] = ("food",),
    layout_density: str | None = None,
) -> list[dict]:
    """
    Plan screens on each day bucket (full takenAt sequence), assign to chapters
    by the chapter that owns each screen's first asset.
    """
    assets_by_id: dict[str, dict] = {}
    if isinstance(assets, dict):
        assets_by_id = assets
    elif isinstance(assets, list):
        assets_by_id = {a["id"]: a for a in assets if a.get("id")}

    from travelogue.curation.curate_scoring import median_sharpness

    med_sharp = median_sharpness(list(assets_by_id.values())) if assets_by_id else 0.0

    asset_to_ch: dict[str, str] = {}
    out: list[dict] = []
    for ch in chapters:
        ch = dict(ch)
        for aid in _collect_asset_ids_from_chapter(ch):
            asset_to_ch[aid] = ch.get("id", "ch")
        ch["screens"] = []
        out.append(ch)

    ch_by_id = {ch["id"]: ch for ch in out}
    hero_by_ch = {
        ch["id"]: str((ch.get("curation") or {}).get("heroAssetId") or "")
        for ch in out
    }
    skip = skip_screen_asset_ids or set()
    if trip_photo_total is None:
        all_ids: set[str] = set()
        for bucket in day_buckets:
            all_ids.update(bucket)
        for ch in chapters:
            all_ids.update(_collect_asset_ids_from_chapter(ch))
        trip_photo_total = len(all_ids)
    layout_state = ScreenLayoutPlannerState.from_trip_total(
        trip_photo_total,
        density=layout_density or "balanced",
    )
    seq_per_ch: dict[str, int] = {}
    gallery_asset_ids: set[str] = set()
    for ch in out:
        if ch.get("patternId") == "gallery":
            gallery_asset_ids.update(_collect_asset_ids_from_chapter(ch))

    for ch in out:
        if ch.get("patternId") != "gallery":
            continue
        aids = _collect_asset_ids_from_chapter(ch)
        if not aids:
            continue
        sorted_aids = _sort_asset_ids_by_taken(aids, assets_by_id)
        gal_screens = plan_screens_for_chapter(
            sorted_aids,
            aspects,
            chapter_id=ch["id"],
            assets=assets_by_id or None,
            burst_seconds=burst_seconds,
            mixed_proximity_seconds=mixed_proximity_seconds,
            orientation_summary=orientation_summary,
            skip_screen_asset_ids=skip,
            layout_state=layout_state,
            trip_photo_total=trip_photo_total,
            enable_food_grid=enable_food_grid,
            mundane_grid_buckets=mundane_grid_buckets,
        )
        ch["screens"] = gal_screens

    for bucket in day_buckets:
        filtered = [a for a in bucket if a not in gallery_asset_ids and a not in skip]
        if not filtered:
            continue
        bucket = filtered
        if not bucket:
            continue
        preferred_hero = _preferred_hero_for_bucket(
            bucket,
            asset_to_ch,
            hero_by_ch,
            assets_by_id,
            median_sharp=med_sharp,
            featured_weight=featured_weight,
        )
        bucket_screens = plan_screens_for_chapter(
            bucket,
            aspects,
            chapter_id="day",
            assets=assets_by_id or None,
            burst_seconds=burst_seconds,
            mixed_proximity_seconds=mixed_proximity_seconds,
            orientation_summary=orientation_summary,
            skip_screen_asset_ids=skip,
            layout_state=layout_state,
            trip_photo_total=trip_photo_total,
            preferred_hero_id=preferred_hero,
            median_sharp=med_sharp,
            featured_weight=featured_weight,
            enable_food_grid=enable_food_grid,
            mundane_grid_buckets=mundane_grid_buckets,
        )
        for sc in bucket_screens:
            slots = sc.get("slots") or []
            if not slots:
                continue
            ch_id = asset_to_ch.get(slots[0]["assetId"])
            if not ch_id or ch_id not in ch_by_id:
                continue
            seq_per_ch[ch_id] = seq_per_ch.get(ch_id, 0) + 1
            screen = dict(sc)
            screen["screenId"] = f"{ch_id}-sc-{seq_per_ch[ch_id]:02d}"
            ch_by_id[ch_id]["screens"].append(screen)

    return out


def attach_screens_to_chapters(
    chapters: list[dict],
    aspects: dict[str, AspectKind],
    *,
    assets: list[dict] | dict[str, dict] | None = None,
    burst_seconds: float = 3.0,
    mixed_proximity_seconds: float | None = None,
    orientation_summary: dict | None = None,
    plan_scope: str | None = None,
    day_buckets: list[list[str]] | None = None,
    skip_screen_asset_ids: set[str] | None = None,
    trip_photo_total: int | None = None,
    featured_weight: float = DEFAULT_FEATURED_WEIGHT,
    cfg: AppConfig | None = None,
    enable_food_grid: bool | None = None,
    mundane_grid_buckets: tuple[str, ...] | None = None,
    layout_density: str | None = None,
) -> list[dict]:
    """Add screens[] to each chapter (per-chapter or per-day bucket scope)."""
    from travelogue.config import (
        default_enable_food_grid,
        default_mundane_grid_buckets,
        default_screen_plan_scope,
    )

    scope = (plan_scope or default_screen_plan_scope(cfg=cfg)).strip().lower()
    food_grid_enabled = (
        default_enable_food_grid(cfg=cfg)
        if enable_food_grid is None
        else enable_food_grid
    )
    grid_buckets = (
        default_mundane_grid_buckets(cfg=cfg)
        if mundane_grid_buckets is None
        else (mundane_grid_buckets or ("food",))
    )
    if scope == "day" and day_buckets:
        return attach_screens_day_buckets(
            chapters,
            day_buckets,
            aspects,
            assets=assets,
            burst_seconds=burst_seconds,
            mixed_proximity_seconds=mixed_proximity_seconds,
            orientation_summary=orientation_summary,
            skip_screen_asset_ids=skip_screen_asset_ids,
            trip_photo_total=trip_photo_total,
            featured_weight=featured_weight,
            enable_food_grid=food_grid_enabled,
            mundane_grid_buckets=tuple(str(x).strip().lower() for x in grid_buckets if str(x).strip()),
            layout_density=layout_density,
        )

    assets_by_id: dict[str, dict] = {}
    if isinstance(assets, dict):
        assets_by_id = assets
    elif isinstance(assets, list):
        assets_by_id = {a["id"]: a for a in assets if a.get("id")}

    if trip_photo_total is None:
        trip_photo_total = len(assets_by_id) if assets_by_id else sum(
            len(_collect_asset_ids_from_chapter(ch)) for ch in chapters
        )
    layout_state = ScreenLayoutPlannerState.from_trip_total(
        trip_photo_total,
        density=layout_density or "balanced",
    )

    out: list[dict] = []
    for ch in chapters:
        ch = dict(ch)
        asset_ids = _collect_asset_ids_from_chapter(ch)

        if asset_ids:
            hero_id = (ch.get("curation") or {}).get("heroAssetId")
            ch["screens"] = plan_screens_for_chapter(
                asset_ids,
                aspects,
                chapter_id=ch.get("id", "ch"),
                assets=assets_by_id or None,
                burst_seconds=burst_seconds,
                mixed_proximity_seconds=mixed_proximity_seconds,
                orientation_summary=orientation_summary,
                skip_screen_asset_ids=skip_screen_asset_ids,
                layout_state=layout_state,
                trip_photo_total=trip_photo_total,
                preferred_hero_id=hero_id,
                featured_weight=featured_weight,
                enable_food_grid=food_grid_enabled,
                mundane_grid_buckets=tuple(str(x).strip().lower() for x in grid_buckets if str(x).strip()),
            )
        else:
            ch["screens"] = []
        out.append(ch)
    return out


def gallery_chapter_uses_screens_not_scroll(chapter: dict, *, layout_engine: str) -> bool:
    """Gallery chapters: screens engine uses mosaic screens, not media-scroll in render."""
    return layout_engine == LAYOUT_ENGINE_SCREENS and chapter.get("patternId") == "gallery"
