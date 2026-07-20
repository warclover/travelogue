"""Trip/chapter-level screen attachment (extracted from screen_planner for thinner entry)."""

from __future__ import annotations

from travelogue.config import AppConfig
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_contract.rhythm import RhythmRules
from travelogue.layout_engine.adapter import ChapterPlanRequest, plan_chapter_screens
from travelogue.layout_engine.planner.screen_planner import (
    DEFAULT_FEATURED_WEIGHT,
    LAYOUT_ENGINE_SCREENS,
    _collect_asset_ids_from_chapter,
    _sort_asset_ids_by_taken,
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
    from travelogue.layout_contract.scoring import median_sharpness
    from travelogue.layout_engine.scoring.hero import effective_hero_score

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


# Cross-chapter carry: a lone portrait may flow forward through subsequent
# chapter/day buckets trying to pair before force-emitted as a single.
# ``portrait_carry_max_hops=0`` (default) = auto: carry through all remaining buckets.
_DEFAULT_PORTRAIT_CARRY_MAX_HOPS = 0


def _portrait_carry_hop_limit(
    bucket_index: int,
    total_buckets: int,
    rhythm: RhythmRules,
) -> int:
    """Max defer hops from ``bucket_index`` (0-based) before force-emit."""
    chapter_index = bucket_index + 1
    if (
        rhythm.late_chapter_pairing.is_late_chapter(chapter_index)
        and rhythm.late_chapter_pairing.no_outward_portrait_carry
    ):
        return 0
    configured = int(getattr(rhythm, "portrait_carry_max_hops", _DEFAULT_PORTRAIT_CARRY_MAX_HOPS))
    if configured > 0:
        return configured
    return max(0, total_buckets - bucket_index - 1)


def _longest_portrait_run_insert_at(
    plan_ids: list[str],
    aspects: dict[str, AspectKind],
) -> int:
    """Index after the longest contiguous std-portrait run (for carry inject)."""
    from travelogue.layout_engine.planner.screen_planner import _is_std_portrait_id

    best_start = 0
    best_len = 0
    i = 0
    while i < len(plan_ids):
        if _is_std_portrait_id(plan_ids[i], aspects):
            j = i
            while j < len(plan_ids) and _is_std_portrait_id(plan_ids[j], aspects):
                j += 1
            run_len = j - i
            if run_len > best_len:
                best_len = run_len
                best_start = i
            i = j
        else:
            i += 1
    if best_len > 0:
        return best_start + best_len
    for idx, aid in enumerate(plan_ids):
        if _is_std_portrait_id(aid, aspects):
            return idx + 1
    return 0


def _rebuild_layout_state(
    base: ScreenLayoutPlannerState,
    noted_patterns: list[str],
) -> ScreenLayoutPlannerState:
    """AC-RHY-05 · 以「实际落章屏」重放节奏 state，剔除被 carry 延期屏的污染。

    被 defer 的单竖在规划期已 note_screen；这里用 kept 屏序列重建配额与
    streak，使后续天桶的节奏判定与最终阅读序一致（V-08/V-10）。
    """
    from travelogue.layout_engine.planner.screen_planner import PATTERN_PORTRAIT_GRID_8

    state = ScreenLayoutPlannerState(
        nine_min=base.nine_min,
        nine_max=base.nine_max,
        portrait_grid8_max=base.portrait_grid8_max,
        layout_density=base.layout_density,
        rhythm=base.rhythm,
        dense_collage_max=base.dense_collage_max,
        dense_collage_opportunity_min=base.dense_collage_opportunity_min,
        large_mosaic_min_slots=base.large_mosaic_min_slots,
        large_mosaic_max_per_template_trip=base.large_mosaic_max_per_template_trip,
        large_mosaic_max_per_chapter=base.large_mosaic_max_per_chapter,
    )
    for pid in noted_patterns:
        state.note_screen(pid)
        if pid == PATTERN_PORTRAIT_GRID_8:
            state.note_portrait_grid8()
    return state


def _carry_inject_ids(
    plan_ids: list[str],
    carry_ids: list[str],
    aspects: dict[str, AspectKind],
    *,
    late_chapter: bool = False,
) -> list[str]:
    """Insert carried lone portraits after the bucket's first or longest portrait run.

    Placing them as the *follower* (not the leader) keeps screen->chapter
    assignment (by first slot) anchored on the later bucket, so a carried photo
    renders forward (with the later chapter) rather than dragging a later photo
    backward into the carried photo's origin chapter.
    """
    if not carry_ids:
        return plan_ids
    from travelogue.layout_engine.planner.screen_planner import _is_std_portrait_id

    seq = list(plan_ids)
    insert_at = (
        _longest_portrait_run_insert_at(seq, aspects)
        if late_chapter
        else 0
    )
    if not late_chapter:
        for idx, aid in enumerate(seq):
            if _is_std_portrait_id(aid, aspects):
                insert_at = idx + 1
                break
    seq[insert_at:insert_at] = carry_ids
    return seq


def _consolidate_adjacent_portrait_singles(
    screens: list[dict],
    aspects: dict[str, AspectKind],
) -> list[dict]:
    """Late chapter: merge consecutive portrait-1/tall-1 into portrait-2."""
    from travelogue.layout_engine.planner.screen_planner import _make_screen

    single = frozenset({"screen-portrait-1", "screen-tall-1"})
    out: list[dict] = []
    i = 0
    while i < len(screens):
        sc = screens[i]
        pid = str(sc.get("patternId") or "")
        if pid in single and i + 1 < len(screens):
            nxt = screens[i + 1]
            npid = str(nxt.get("patternId") or "")
            if npid in single:
                slots1 = sc.get("slots") or []
                slots2 = nxt.get("slots") or []
                if len(slots1) == 1 and len(slots2) == 1:
                    aids = [slots1[0]["assetId"], slots2[0]["assetId"]]
                    out.append(
                        _make_screen(
                            "screen-portrait-2",
                            aids,
                            screen_id="",
                            aspects=aspects,
                        )
                    )
                    i += 2
                    continue
        out.append(sc)
        i += 1
    return out


def _late_chapter_planning_kwargs(
    rhythm: RhythmRules,
    chapter_index: int,
) -> dict[str, object]:
    """Kwargs for plan_chapter_screens when bucket is in the late-chapter zone."""
    late = rhythm.late_chapter_pairing
    if not late.is_late_chapter(chapter_index):
        return {}
    return {
        "late_chapter_active": True,
        "flush_lookahead_portraits": late.flush_lookahead_portraits,
    }


def assign_bucket_screens_with_portrait_carry(
    bucket_screens: list[dict],
    *,
    bucket_idx: int,
    total_buckets: int,
    carry_age: dict[str, int],
    layout_state: ScreenLayoutPlannerState,
    noted_patterns: list[str],
    asset_to_ch: dict[str, str],
    ch_by_id: dict[str, dict],
    seq_per_ch: dict[str, int],
    assets_by_id: dict[str, dict],
    hero_ids: set[str],
    trip: dict | None = None,
) -> tuple[list[str], dict[str, int], ScreenLayoutPlannerState]:
    """Assign kept screens to chapters; defer lone portraits to the next bucket."""
    hop_limit = _portrait_carry_hop_limit(
        bucket_idx, total_buckets, layout_state.rhythm
    )
    next_carry: list[str] = []
    next_carry_age: dict[str, int] = {}
    deferred: set[int] = set()
    for sc in bucket_screens:
        aid = _carry_eligible_single(
            sc, assets_by_id=assets_by_id, hero_ids=hero_ids
        )
        if aid is None:
            continue
        new_age = carry_age.get(aid, 0) + 1
        if new_age > hop_limit:
            continue
        deferred.add(id(sc))
        next_carry.append(aid)
        next_carry_age[aid] = new_age
    for sc in bucket_screens:
        if id(sc) in deferred:
            continue
        slots = sc.get("slots") or []
        if not slots:
            continue
        ch_id = asset_to_ch.get(slots[0]["assetId"])
        if not ch_id or ch_id not in ch_by_id:
            continue
        seq_per_ch[ch_id] = seq_per_ch.get(ch_id, 0) + 1
        screen = dict(sc)
        screen["screenId"] = f"{ch_id}-sc-{seq_per_ch[ch_id]:02d}"
        from travelogue.layout_engine.editorial.portrait_row import apply_editorial_row_slot_fits

        screen = apply_editorial_row_slot_fits(screen, assets_by_id, trip=trip)
        ch_by_id[ch_id]["screens"].append(screen)
    noted_patterns.extend(
        str(sc.get("patternId") or "")
        for sc in bucket_screens
        if id(sc) not in deferred
    )
    kept_patterns = [
        str(sc.get("patternId") or "")
        for sc in bucket_screens
        if id(sc) not in deferred
    ]
    layout_state = _rebuild_layout_state(layout_state, noted_patterns)
    layout_state.sync_large_mosaic_chapter_used(kept_patterns)
    layout_state.sync_editorial_composite_chapter_used(kept_patterns)
    return next_carry, next_carry_age, layout_state


def _carry_eligible_single(
    screen: dict,
    *,
    assets_by_id: dict[str, dict],
    hero_ids: set[str],
) -> str | None:
    """Return the asset id when ``screen`` is a deferrable lone portrait, else None.

    Featured assets and chapter heroes are never deferred: a single, well-placed
    portrait is intentional for them, not a leftover to be consolidated away.
    """
    pid = str(screen.get("patternId") or "")
    if pid not in ("screen-portrait-1", "screen-tall-1"):
        return None
    slots = screen.get("slots") or []
    if len(slots) != 1:
        return None
    aid = slots[0].get("assetId")
    if not aid or aid in hero_ids:
        return None
    asset = assets_by_id.get(aid) or {}
    if asset.get("userTier") == "featured":
        return None
    return aid


def _flush_portrait_carry_tail(
    carry: list[str],
    aspects: dict[str, AspectKind],
    *,
    assets_by_id: dict[str, dict],
    asset_to_ch: dict[str, str],
    ch_by_id: dict[str, dict],
    seq_per_ch: dict[str, int],
    layout_state: ScreenLayoutPlannerState,
    skip: set[str],
    burst_seconds: float,
    mixed_proximity_seconds: float | None,
    orientation_summary: dict | None,
    trip_photo_total: int | None,
    median_sharp: float | None,
    featured_weight: float,
    enable_food_grid: bool,
    mundane_grid_buckets: tuple[str, ...],
    cfg: AppConfig | None,
    trip: dict | None = None,
) -> None:
    """Tile any unplaced carried portraits at trip end and distribute by ownership.

    Two or more leftovers pair/triple among themselves; a final lone portrait
    falls back to a single in its origin chapter.
    """
    if not carry:
        return
    late_kwargs = _late_chapter_planning_kwargs(
        layout_state.rhythm, layout_state.rhythm.late_chapter_pairing.from_chapter_index
    )
    tail_screens = plan_chapter_screens(
        ChapterPlanRequest(
            carry,
            aspects,
            chapter_id="day",
            assets=assets_by_id or None,
            burst_seconds=burst_seconds,
            mixed_proximity_seconds=mixed_proximity_seconds,
            orientation_summary=orientation_summary,
            skip_screen_asset_ids=skip,
            layout_state=layout_state,
            trip_photo_total=trip_photo_total,
            median_sharp=median_sharp,
            featured_weight=featured_weight,
            enable_food_grid=enable_food_grid,
            mundane_grid_buckets=mundane_grid_buckets,
            **late_kwargs,
        ),
        cfg=cfg,
    )
    if late_kwargs:
        tail_screens = _consolidate_adjacent_portrait_singles(tail_screens, aspects)
    for sc in tail_screens:
        slots = sc.get("slots") or []
        if not slots:
            continue
        ch_id = asset_to_ch.get(slots[0]["assetId"])
        if not ch_id or ch_id not in ch_by_id:
            continue
        seq_per_ch[ch_id] = seq_per_ch.get(ch_id, 0) + 1
        screen = dict(sc)
        screen["screenId"] = f"{ch_id}-sc-{seq_per_ch[ch_id]:02d}"
        from travelogue.layout_engine.editorial.portrait_row import apply_editorial_row_slot_fits

        screen = apply_editorial_row_slot_fits(screen, assets_by_id, trip=trip)
        ch_by_id[ch_id]["screens"].append(screen)


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
    cfg: AppConfig | None = None,
    trip: dict | None = None,
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

    from travelogue.layout_contract.scoring import median_sharpness

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
    from travelogue.layout_engine.adapter import lse_enabled, resolve_attach_layout_state

    layout_state = resolve_attach_layout_state(
        trip_photo_total,
        cfg=cfg,
        density=layout_density or "balanced",
    )
    seq_per_ch: dict[str, int] = {}
    gallery_asset_ids: set[str] = set()
    for ch in out:
        if ch.get("patternId") == "gallery":
            gallery_asset_ids.update(_collect_asset_ids_from_chapter(ch))

    noted_patterns_gallery: list[str] = []
    for ch in out:
        if ch.get("patternId") != "gallery":
            continue
        aids = _collect_asset_ids_from_chapter(ch)
        if not aids:
            continue
        sorted_aids = _sort_asset_ids_by_taken(aids, assets_by_id)
        gal_screens = plan_chapter_screens(
            ChapterPlanRequest(
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
                trip=trip,
            ),
            cfg=cfg,
        )
        ch["screens"] = gal_screens
        noted_patterns_gallery.extend(
            str(sc.get("patternId") or "") for sc in gal_screens
        )

    carry: list[str] = []
    carry_age: dict[str, int] = {}
    hero_ids = {h for h in hero_by_ch.values() if h}
    # AC-RHY-05 · 实际落章屏 pattern 序（不含被 defer 的 carry 单竖）。
    noted_patterns: list[str] = list(noted_patterns_gallery)

    for bucket_idx, bucket in enumerate(day_buckets):
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
        highlight_active = False
        if cfg is not None and lse_enabled(cfg):
            from travelogue.layout_engine.adapter import resolve_pack
            from travelogue.layout_engine.capabilities import effective_capabilities
            from travelogue.layout_engine.highlight_windows import (
                begin_chapter_highlight_windows,
                clear_chapter_highlight_windows,
                detect_highlight_windows,
                highlight_windows_from_pack,
            )

            pack = resolve_pack(cfg)
            caps = effective_capabilities(cfg, pack)
            hl_cfg = highlight_windows_from_pack(pack.raw if pack else None)
            if caps.highlight_windows or hl_cfg.get("enabled"):
                windows = detect_highlight_windows(
                    bucket,
                    assets_by_id,
                    window_sizes=hl_cfg.get("window_sizes") or (5, 8, 12),
                    max_windows=int(hl_cfg.get("max_windows") or 2),
                )
                begin_chapter_highlight_windows(windows)
                highlight_active = True
        plan_ids = _carry_inject_ids(
            bucket,
            carry,
            aspects,
            late_chapter=layout_state.rhythm.late_chapter_pairing.is_late_chapter(
                bucket_idx + 1
            ),
        )
        layout_state.begin_chapter_bucket(chapter_index=bucket_idx + 1)
        late_kwargs = _late_chapter_planning_kwargs(
            layout_state.rhythm, bucket_idx + 1
        )
        try:
            bucket_screens = plan_chapter_screens(
                ChapterPlanRequest(
                    plan_ids,
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
                    **late_kwargs,
                    trip=trip,
                ),
                cfg=cfg,
            )
        finally:
            if highlight_active:
                from travelogue.layout_engine.highlight_windows import (
                    clear_chapter_highlight_windows,
                )

                clear_chapter_highlight_windows()
        if late_kwargs:
            bucket_screens = _consolidate_adjacent_portrait_singles(
                bucket_screens, aspects
            )
        carry, carry_age, layout_state = assign_bucket_screens_with_portrait_carry(
            bucket_screens,
            bucket_idx=bucket_idx,
            total_buckets=len(day_buckets),
            carry_age=carry_age,
            layout_state=layout_state,
            noted_patterns=noted_patterns,
            asset_to_ch=asset_to_ch,
            ch_by_id=ch_by_id,
            seq_per_ch=seq_per_ch,
            assets_by_id=assets_by_id,
            hero_ids=hero_ids,
            trip=trip,
        )

    _flush_portrait_carry_tail(
        carry,
        aspects,
        assets_by_id=assets_by_id,
        asset_to_ch=asset_to_ch,
        ch_by_id=ch_by_id,
        seq_per_ch=seq_per_ch,
        layout_state=layout_state,
        skip=skip,
        burst_seconds=burst_seconds,
        mixed_proximity_seconds=mixed_proximity_seconds,
        orientation_summary=orientation_summary,
        trip_photo_total=trip_photo_total,
        median_sharp=med_sharp,
        featured_weight=featured_weight,
        enable_food_grid=enable_food_grid,
        mundane_grid_buckets=mundane_grid_buckets,
        cfg=cfg,
        trip=trip,
    )
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
    trip: dict | None = None,
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
    chapter_buckets = [
        _collect_asset_ids_from_chapter(ch)
        for ch in chapters
        if _collect_asset_ids_from_chapter(ch)
    ]
    effective_day_buckets = day_buckets
    if effective_day_buckets is None and scope == "chapter" and len(chapter_buckets) > 1:
        # Web per-chapter scope: still run cross-chapter portrait carry (PRD V-05).
        effective_day_buckets = chapter_buckets
    if effective_day_buckets and (scope == "day" or len(chapter_buckets) > 1):
        return attach_screens_day_buckets(
            chapters,
            effective_day_buckets,
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
            cfg=cfg,
            trip=trip,
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
    from travelogue.layout_engine.adapter import resolve_attach_layout_state

    layout_state = resolve_attach_layout_state(
        trip_photo_total,
        cfg=cfg,
        density=layout_density or "balanced",
    )

    out: list[dict] = []
    for ch in chapters:
        ch = dict(ch)
        asset_ids = _collect_asset_ids_from_chapter(ch)

        if asset_ids:
            from travelogue.layout_engine.editorial.portrait_row import (
                apply_editorial_row_slot_fits,
            )

            hero_id = (ch.get("curation") or {}).get("heroAssetId")
            ch["screens"] = [
                apply_editorial_row_slot_fits(sc, assets_by_id, trip=trip)
                for sc in plan_chapter_screens(
                ChapterPlanRequest(
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
                    mundane_grid_buckets=tuple(
                        str(x).strip().lower() for x in grid_buckets if str(x).strip()
                    ),
                    trip=trip,
                ),
                cfg=cfg,
            )
            ]
        else:
            ch["screens"] = []
        out.append(ch)
    return out


def gallery_chapter_uses_screens_not_scroll(chapter: dict, *, layout_engine: str) -> bool:
    """Gallery chapters: screens engine uses mosaic screens, not media-scroll in render."""
    return layout_engine == LAYOUT_ENGINE_SCREENS and chapter.get("patternId") == "gallery"
