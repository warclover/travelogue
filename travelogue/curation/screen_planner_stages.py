"""Named planning stages for chapter screen layout (used by plan_screens_for_chapter)."""

from __future__ import annotations

from dataclasses import dataclass, field

from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState
from travelogue.curation.subject_tagging import is_mundane_clusterable, mundane_run_length
from travelogue.media.image_ops import AspectKind


@dataclass
class ChapterPlanContext:
    """Mutable state shared across layout planning stages."""

    chapter_id: str
    aspects: dict[str, AspectKind]
    assets_map: dict[str, dict]
    mix_gap: float
    med_sharp: float
    trip_total: int
    burst_seconds: float
    burst_groups: dict[str, int]
    layout_state: ScreenLayoutPlannerState | None
    enable_mosaic: bool
    enable_portrait_grid8: bool
    enable_food_grid: bool
    mundane_grid_buckets: tuple[str, ...]
    use_portrait_grid8: bool
    max_per_screen: int
    portrait_heavy: bool
    skip_screen_asset_ids: set[str] = field(default_factory=set)
    preferred_hero_id: str | None = None
    include_chapter_hero: bool = True
    featured_weight: float = 1.35
    ids: list[str] = field(default_factory=list)
    screens: list[dict] = field(default_factory=list)
    pending_portraits: list[str] = field(default_factory=list)
    hero_preface: list[dict] = field(default_factory=list)
    seq: int = 0
    i: int = 0


def build_chapter_plan_context(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    *,
    chapter_id: str = "ch",
    max_per_screen: int = 9,
    assets: dict[str, dict] | None = None,
    burst_seconds: float = 3.0,
    mixed_proximity_seconds: float | None = None,
    orientation_summary: dict | None = None,
    skip_screen_asset_ids: set[str] | None = None,
    layout_state: ScreenLayoutPlannerState | None = None,
    trip_photo_total: int | None = None,
    preferred_hero_id: str | None = None,
    include_chapter_hero: bool = True,
    enable_mosaic: bool = True,
    featured_weight: float = 1.35,
    enable_portrait_grid8: bool = True,
    enable_food_grid: bool = True,
    mundane_grid_buckets: tuple[str, ...] = ("food",),
    median_sharp: float | None = None,
) -> ChapterPlanContext:
    from travelogue.curation.screen_planner import (
        MAX_SLOTS_PER_SCREEN,
        _sort_asset_ids_by_taken,
        burst_group_map,
        portrait_grid8_allowed,
    )

    summary = orientation_summary or {}
    portrait_heavy = summary.get("portrait", 0) > summary.get("landscape", 0)
    mix_gap = mixed_proximity_seconds if mixed_proximity_seconds is not None else burst_seconds
    trip_total = trip_photo_total if trip_photo_total is not None else len(asset_ids)
    use_portrait_grid8 = portrait_grid8_allowed(
        trip_total, portrait_heavy=portrait_heavy
    ) and enable_portrait_grid8
    assets_map: dict[str, dict] = assets or {}
    from travelogue.curation.curate_scoring import median_sharpness

    med_sharp = (
        median_sharp
        if median_sharp is not None
        else (median_sharpness(list(assets_map.values())) if assets_map else 0.0)
    )
    ids = _sort_asset_ids_by_taken(list(asset_ids), assets_map)
    burst_groups: dict[str, int] = {}
    if assets_map:
        burst_groups = burst_group_map(ids, assets_map, aspects, burst_seconds=burst_seconds)
    return ChapterPlanContext(
        chapter_id=chapter_id,
        aspects=aspects,
        assets_map=assets_map,
        mix_gap=mix_gap,
        med_sharp=med_sharp,
        trip_total=trip_total,
        burst_seconds=burst_seconds,
        burst_groups=burst_groups,
        layout_state=layout_state,
        enable_mosaic=enable_mosaic,
        enable_portrait_grid8=enable_portrait_grid8,
        enable_food_grid=enable_food_grid,
        mundane_grid_buckets=mundane_grid_buckets,
        use_portrait_grid8=use_portrait_grid8,
        max_per_screen=max_per_screen or MAX_SLOTS_PER_SCREEN,
        portrait_heavy=portrait_heavy,
        skip_screen_asset_ids=skip_screen_asset_ids or set(),
        preferred_hero_id=preferred_hero_id,
        include_chapter_hero=include_chapter_hero,
        featured_weight=featured_weight,
        ids=ids,
    )


def stage_chapter_hero(ctx: ChapterPlanContext) -> None:
    """Opening hero screen; removes hero asset id from ctx.ids when placed."""
    from travelogue.curation.mosaic.hook import chapter_should_skip_hero_for_mosaic
    from travelogue.curation.screen_planner import (
        CHAPTER_HERO_MIN_ASSETS,
        _can_portrait_grid8_window,
        _make_screen,
        _pick_chapter_hero,
    )

    skip_hero_for_mosaic_5 = chapter_should_skip_hero_for_mosaic(ctx)
    skip_hero_for_portrait_grid8 = (
        len(ctx.ids) == 8
        and ctx.use_portrait_grid8
        and _can_portrait_grid8_window(
            ctx.ids, ctx.aspects, ctx.assets_map, burst_seconds=ctx.mix_gap
        )
    )
    if not (
        ctx.include_chapter_hero
        and len(ctx.ids) >= CHAPTER_HERO_MIN_ASSETS
        and ctx.assets_map
        and not skip_hero_for_mosaic_5
        and not skip_hero_for_portrait_grid8
    ):
        return
    hero = _pick_chapter_hero(
        ctx.ids,
        ctx.aspects,
        ctx.assets_map,
        preferred_id=ctx.preferred_hero_id,
        median_sharp=ctx.med_sharp,
        featured_weight=ctx.featured_weight,
    )
    if not hero:
        return
    hid, pat = hero
    if hid not in ctx.skip_screen_asset_ids:
        hero_screen = _make_screen(pat, [hid], screen_id="")
        if ctx.layout_state:
            ctx.layout_state.note_screen(pat)
        ctx.hero_preface.append(hero_screen)
    ctx.ids = [aid for aid in ctx.ids if aid != hid]


def try_collage_solo_at_cursor(ctx: ChapterPlanContext) -> int | None:
    """Collage assets never share a multi-slot screen — route each to full-frame solo."""
    from travelogue.curation.collage_routing import collage_routing_enabled
    from travelogue.curation.media_classify import is_collage_asset
    from travelogue.curation.screen_planner import _make_screen

    if not collage_routing_enabled() or ctx.i >= len(ctx.ids):
        return None
    aid = ctx.ids[ctx.i]
    if not is_collage_asset(ctx.assets_map.get(aid, {})):
        return None
    append_screen(
        ctx,
        _make_screen(
            "screen-landscape-1",
            [aid],
            screen_id="",
            aspects=ctx.aspects,
            assets_map=ctx.assets_map,
        ),
    )
    return 1


def run_planning_loop(ctx: ChapterPlanContext) -> None:
    """Main cursor loop over ctx.ids."""
    from travelogue.curation.mosaic.hook import try_mosaic_window
    from travelogue.curation.screen_planner import _family_kind

    while ctx.i < len(ctx.ids):
        advance = try_collage_solo_at_cursor(ctx)
        if advance is not None:
            ctx.i += advance
            continue

        advance = try_mixed_with_pending(ctx)
        if advance is not None:
            ctx.i += advance
            continue

        mosaic_advance = try_mosaic_window(ctx, ctx.i)
        if mosaic_advance is not None:
            ctx.i += mosaic_advance
            continue

        advance = try_mixed_triple_at_cursor(ctx)
        if advance is not None:
            ctx.i += advance
            continue

        advance = try_landscape_run(ctx)
        if advance is not None:
            ctx.i += advance
            continue

        advance = try_mundane_grid(ctx)
        if advance is not None:
            ctx.i += advance
            continue

        fam = _family_kind(ctx.aspects.get(ctx.ids[ctx.i], "square"))

        if fam == "portrait":
            extra = stage_portrait_family(ctx)
            if extra is not None:
                ctx.i += extra
            continue

        advance = stage_flush_pending_for_other_family(ctx, fam)
        if advance is not None:
            ctx.i += advance
            continue

        if stage_tall_single(ctx, fam):
            continue

        stage_generic_chunk(ctx)


def stage_flush_remaining_cursor(ctx: ChapterPlanContext) -> None:
    """Emit singles for bucket ids left after the main loop (S1 · no silent drop)."""
    from travelogue.curation.screen_planner import (
        _emit_portrait_single_screens,
        _family_kind,
        _make_screen,
    )

    while ctx.i < len(ctx.ids):
        aid = ctx.ids[ctx.i]
        fam = _family_kind(ctx.aspects.get(aid, "square"))
        if fam == "portrait":
            placed = _emit_portrait_single_screens(
                [aid],
                ctx.aspects,
                assets_map=ctx.assets_map,
                layout_state=ctx.layout_state,
                pending=ctx.pending_portraits,
                solo_exclude=ctx.skip_screen_asset_ids,
            )
            for sc in placed:
                append_screen(ctx, sc)
        else:
            append_screen(
                ctx,
                _make_screen(
                    "screen-landscape-1",
                    [aid],
                    screen_id="",
                    aspects=ctx.aspects,
                    assets_map=ctx.assets_map,
                ),
            )
        ctx.i += 1


class ChapterScreenPlanner:
    """Single entry point for chapter screen planning."""

    def __init__(self, ctx: ChapterPlanContext) -> None:
        self.ctx = ctx

    @classmethod
    def create(
        cls,
        asset_ids: list[str],
        aspects: dict[str, AspectKind],
        **kwargs: object,
    ) -> ChapterScreenPlanner:
        return cls(build_chapter_plan_context(asset_ids, aspects, **kwargs))  # type: ignore[arg-type]

    def plan(self) -> list[dict]:
        stage_chapter_hero(self.ctx)
        run_planning_loop(self.ctx)
        stage_flush_remaining_cursor(self.ctx)
        if self.ctx.pending_portraits:
            stage_flush_remaining_portraits(self.ctx)
        stage_flush_remaining_food(self.ctx)
        return finalize_with_hero(self.ctx)


def assign_screen_id(ctx: ChapterPlanContext, screen: dict) -> None:
    ctx.seq += 1
    screen["screenId"] = f"{ctx.chapter_id}-sc-{ctx.seq:02d}"


def append_screen(ctx: ChapterPlanContext, screen: dict) -> None:
    from travelogue.curation.mosaic.lte_adapter import mosaic_pattern_disabled

    pid = str(screen.get("patternId") or "")
    if pid and mosaic_pattern_disabled(pid):
        raise RuntimeError(f"disabled mosaic pattern must not be appended: {pid}")
    if ctx.layout_state:
        ctx.layout_state.note_screen(screen.get("patternId", ""))
    assign_screen_id(ctx, screen)
    ctx.screens.append(screen)


def try_mixed_portrait_landscape(
    ctx: ChapterPlanContext, portrait_id: str, l1: str, l2: str
) -> bool:
    from travelogue.curation.screen_planner import (
        _can_mixed_p1_l2,
        _make_mixed_portrait_landscape_screen,
    )

    if not _can_mixed_p1_l2(
        portrait_id, [l1, l2], ctx.aspects, ctx.assets_map, burst_seconds=ctx.mix_gap
    ):
        return False
    append_screen(
        ctx,
        _make_mixed_portrait_landscape_screen(
            portrait_id, [l1, l2], assets_map=ctx.assets_map
        ),
    )
    return True


def try_mosaic_five(ctx: ChapterPlanContext, start: int) -> bool:
    from travelogue.config import get_config
    from travelogue.curation.mosaic.hook import try_mosaic_window
    from travelogue.curation.screen_planner import (
        MIN_TRIP_PHOTOS_FOR_MOSAIC,
        _can_mosaic_5_main_portrait_3land,
        _make_mosaic_5_main_portrait_3land_screen,
    )

    if not ctx.enable_mosaic:
        return False
    mosaic_cfg = get_config().mosaic
    if 5 not in mosaic_cfg.enabled_window_sizes:
        return False
    if mosaic_cfg.enabled:
        return try_mosaic_window(ctx, start) == 5
    if ctx.trip_total < MIN_TRIP_PHOTOS_FOR_MOSAIC:
        return False
    if ctx.pending_portraits or start + 4 >= len(ctx.ids):
        return False
    ordered = _can_mosaic_5_main_portrait_3land(
        ctx.ids[start : start + 5],
        ctx.aspects,
        ctx.assets_map,
        burst_seconds=ctx.mix_gap,
        median_sharp=ctx.med_sharp,
    )
    if not ordered:
        return False
    append_screen(
        ctx, _make_mosaic_5_main_portrait_3land_screen(ordered, assets_map=ctx.assets_map)
    )
    return True


def try_drain_portrait_grid8(ctx: ChapterPlanContext) -> bool:
    from travelogue.curation.screen_planner import (
        _can_portrait_grid8_window,
        _is_std_portrait_id,
        _make_portrait_grid8_screen,
    )

    if not ctx.enable_portrait_grid8 or not ctx.use_portrait_grid8:
        return False
    if ctx.layout_state is not None and not ctx.layout_state.can_use_portrait_grid8():
        return False
    buf = [a for a in ctx.pending_portraits if _is_std_portrait_id(a, ctx.aspects)]
    if len(buf) < 8:
        return False
    window = buf[:8]
    if not _can_portrait_grid8_window(
        window, ctx.aspects, ctx.assets_map, burst_seconds=ctx.mix_gap
    ):
        return False
    append_screen(ctx, _make_portrait_grid8_screen(window, assets_map=ctx.assets_map))
    if ctx.layout_state:
        ctx.layout_state.note_portrait_grid8()
    removed = 0
    kept: list[str] = []
    for aid in ctx.pending_portraits:
        if removed < 8 and _is_std_portrait_id(aid, ctx.aspects):
            removed += 1
            continue
        kept.append(aid)
    ctx.pending_portraits[:] = kept
    return True


def try_mixed_with_pending(ctx: ChapterPlanContext) -> int | None:
    """One pending portrait + two landscapes at cursor."""
    if len(ctx.pending_portraits) != 1 or ctx.i + 1 >= len(ctx.ids):
        return None
    p_id = ctx.pending_portraits[0]
    l1, l2 = ctx.ids[ctx.i], ctx.ids[ctx.i + 1]
    if not try_mixed_portrait_landscape(ctx, p_id, l1, l2):
        return None
    ctx.pending_portraits.clear()
    return 2


def try_mixed_triple_at_cursor(ctx: ChapterPlanContext) -> int | None:
    """P+L+L or L+L+P triple at cursor."""
    from travelogue.curation.screen_planner import _is_landscape_id, _is_std_portrait_id

    if ctx.i + 2 >= len(ctx.ids):
        return None
    a, b, c = ctx.ids[ctx.i], ctx.ids[ctx.i + 1], ctx.ids[ctx.i + 2]
    if (
        _is_std_portrait_id(a, ctx.aspects)
        and _is_landscape_id(b, ctx.aspects)
        and _is_landscape_id(c, ctx.aspects)
        and try_mixed_portrait_landscape(ctx, a, b, c)
    ):
        return 3
    if (
        _is_landscape_id(a, ctx.aspects)
        and _is_landscape_id(b, ctx.aspects)
        and _is_std_portrait_id(c, ctx.aspects)
        and try_mixed_portrait_landscape(ctx, c, a, b)
    ):
        return 3
    return None


def try_landscape_run(ctx: ChapterPlanContext) -> int | None:
    """2–3 consecutive landscapes → single landscape-1 screens each."""
    from travelogue.curation.screen_planner import _make_screen, _run_length

    fam, run_len = _run_length(
        ctx.ids[ctx.i :], ctx.aspects, assets_map=ctx.assets_map
    )
    if fam != "landscape" or run_len not in (2, 3) or ctx.pending_portraits:
        return None
    for j in range(run_len):
        append_screen(
            ctx,
            _make_screen(
                "screen-landscape-1",
                [ctx.ids[ctx.i + j]],
                screen_id="",
                aspects=ctx.aspects,
                assets_map=ctx.assets_map,
            ),
        )
    return run_len


def _collect_mundane_ids_for_grid(
    ids: list[str],
    assets_map: dict[str, dict],
    start: int,
    *,
    target_bucket: str,
    allowed_buckets: tuple[str, ...],
    max_items: int = 9,
    tolerance: int = 1,
) -> list[str]:
    if start < 0 or start >= len(ids):
        return []
    out: list[str] = []
    misses = 0
    i = start
    allowed = set(allowed_buckets)
    while i < len(ids) and len(out) < max_items:
        aid = ids[i]
        bucket = is_mundane_clusterable(assets_map.get(aid, {}))
        if bucket == target_bucket and bucket in allowed:
            out.append(aid)
            i += 1
            continue
        misses += 1
        if misses > tolerance:
            break
        i += 1
    return out


def _remove_ids_once(ids: list[str], remove_ids: list[str], *, start: int) -> None:
    if not remove_ids:
        return
    remove_set = set(remove_ids)
    seen: set[str] = set()
    i = start
    while i < len(ids):
        aid = ids[i]
        if aid in remove_set and aid not in seen:
            ids.pop(i)
            seen.add(aid)
            if len(seen) == len(remove_set):
                break
            continue
        i += 1


def _pick_mundane_bucket_at_cursor(ctx: ChapterPlanContext, *, tolerance: int = 1) -> str | None:
    """Pick a bucket that can actually form a grid at cursor.

    In multi-bucket mode, a simple "first bucket hit" can disagree with
    mundane_run_length(allowed_buckets=...), causing run>=3 but chosen bucket<3.
    Prefer the bucket that can collect the most ids (and at least 3).
    """
    best_bucket: str | None = None
    best_count = 0
    for bucket in ctx.mundane_grid_buckets:
        target_ids = _collect_mundane_ids_for_grid(
            ctx.ids,
            ctx.assets_map,
            ctx.i,
            target_bucket=bucket,
            allowed_buckets=ctx.mundane_grid_buckets,
            max_items=9,
            tolerance=tolerance,
        )
        count = len(target_ids)
        if count >= 3 and count > best_count:
            best_bucket = bucket
            best_count = count
    if best_bucket:
        return best_bucket
    return None


def try_mundane_grid(ctx: ChapterPlanContext) -> int | None:
    from travelogue.curation.screen_planner import _make_mundane_grid_screen

    if not ctx.enable_food_grid or ctx.pending_portraits:
        return None
    run = mundane_run_length(
        ctx.ids,
        ctx.assets_map,
        ctx.i,
        allowed_buckets=ctx.mundane_grid_buckets,
    )
    if run < 3:
        return None
    bucket = _pick_mundane_bucket_at_cursor(ctx)
    if not bucket:
        return None
    target_ids = _collect_mundane_ids_for_grid(
        ctx.ids,
        ctx.assets_map,
        ctx.i,
        target_bucket=bucket,
        allowed_buckets=ctx.mundane_grid_buckets,
        max_items=min(run, 9),
    )
    if len(target_ids) < 3:
        return None
    append_screen(
        ctx,
        _make_mundane_grid_screen(target_ids, bucket=bucket, assets_map=ctx.assets_map),
    )
    _remove_ids_once(ctx.ids, target_ids, start=ctx.i)
    return 0


def try_food_grid(ctx: ChapterPlanContext) -> int | None:
    return try_mundane_grid(ctx)


def _drain_portrait_run_pair_first(ctx: ChapterPlanContext) -> None:
    """Tile a collected portrait run pair-first (portrait-2 > portrait-3 > portrait-1).

    Drains only when ≥3 standard portraits are buffered, deferring a ≤2 tail to
    ``_finish_portrait_pending_tail`` so a 1-portrait tail can still fold into a
    mixed portrait-1-landscape-2 screen and a 2-portrait tail stays a single
    two-column pair even when it mixes a person + scenery shot. Pairs are
    preferred, with a single triple absorbing any odd remainder; a lone portrait
    is only ever produced as a last resort.
    """
    from travelogue.curation.screen_planner import (
        _flush_portrait_pending,
        _is_std_portrait_id,
    )

    std = [a for a in ctx.pending_portraits if _is_std_portrait_id(a, ctx.aspects)]
    if len(std) < 3:
        return
    # force=True: the portrait run is fully collected, so there is no later
    # portrait to batch with — bypass the consecutive-pattern variety ban so a
    # 3-group stays a clean triple (never degraded to pair + lone single) and
    # consecutive pairs from a 4/6-run are emitted as-is.
    for sc in _flush_portrait_pending(
        ctx.pending_portraits,
        ctx.aspects,
        assets_map=ctx.assets_map,
        layout_state=ctx.layout_state,
        force=True,
        solo_exclude=ctx.skip_screen_asset_ids,
    ):
        append_screen(ctx, sc)


def _finish_portrait_pending_tail(ctx: ChapterPlanContext) -> int | None:
    """After portrait run: mixed 1+2 or portrait-2 pair. Returns i advance or None."""
    from travelogue.curation.screen_planner import (
        _emit_person_portrait_screens,
        _is_std_portrait_id,
        _make_screen,
        asset_has_person,
    )

    if len(ctx.pending_portraits) == 1 and ctx.i + 1 < len(ctx.ids):
        p_id = ctx.pending_portraits[0]
        l1, l2 = ctx.ids[ctx.i], ctx.ids[ctx.i + 1]
        if try_mixed_portrait_landscape(ctx, p_id, l1, l2):
            ctx.pending_portraits.clear()
            return 2
    if len(ctx.pending_portraits) == 2:
        pair = [a for a in ctx.pending_portraits if _is_std_portrait_id(a, ctx.aspects)]
        if pair and all(asset_has_person(ctx.assets_map.get(aid, {})) for aid in pair):
            for sc in _emit_person_portrait_screens(
                pair,
                ctx.aspects,
                assets_map=ctx.assets_map,
                layout_state=ctx.layout_state,
                pending=ctx.pending_portraits,
            ):
                append_screen(ctx, sc)
        else:
            append_screen(
                ctx,
                _make_screen(
                    "screen-portrait-2",
                    pair,
                    screen_id="",
                    aspects=ctx.aspects,
                    assets_map=ctx.assets_map,
                ),
            )
        ctx.pending_portraits.clear()
    return None


def stage_portrait_family(ctx: ChapterPlanContext) -> int | None:
    """Accumulate portrait run at cursor, drain batches; return extra i advance if mixed."""
    from travelogue.curation.screen_planner import _family_kind

    if _family_kind(ctx.aspects.get(ctx.ids[ctx.i], "square")) != "portrait":
        return None
    run_len = 1
    while (
        ctx.i + run_len < len(ctx.ids)
        and _family_kind(ctx.aspects.get(ctx.ids[ctx.i + run_len], "square")) == "portrait"
    ):
        run_len += 1
    for aid in ctx.ids[ctx.i : ctx.i + run_len]:
        ctx.pending_portraits.append(aid)
    ctx.i += run_len
    while len(ctx.pending_portraits) >= 8 and try_drain_portrait_grid8(ctx):
        pass
    _drain_portrait_run_pair_first(ctx)
    return _finish_portrait_pending_tail(ctx)


def stage_flush_pending_for_other_family(ctx: ChapterPlanContext, fam: str) -> int | None:
    """Flush pending portraits before non-portrait asset; may consume mixed pair."""
    from travelogue.curation.screen_planner import _flush_portrait_pending

    if not ctx.pending_portraits:
        return None
    if len(ctx.pending_portraits) == 1 and fam == "landscape" and ctx.i + 1 < len(ctx.ids):
        if try_mixed_portrait_landscape(
            ctx, ctx.pending_portraits[0], ctx.ids[ctx.i], ctx.ids[ctx.i + 1]
        ):
            ctx.pending_portraits.clear()
            return 2
    for sc in _flush_portrait_pending(
        ctx.pending_portraits,
        ctx.aspects,
        assets_map=ctx.assets_map,
        layout_state=ctx.layout_state,
        force=True,
        solo_exclude=ctx.skip_screen_asset_ids,
    ):
        append_screen(ctx, sc)
    return 0


def stage_tall_single(ctx: ChapterPlanContext, fam: str) -> bool:
    from travelogue.curation.screen_planner import _make_screen

    if fam != "tall":
        return False
    append_screen(
        ctx,
        _make_screen("screen-tall-1", [ctx.ids[ctx.i]], screen_id="", aspects=ctx.aspects),
    )
    ctx.i += 1
    return True


def stage_generic_chunk(ctx: ChapterPlanContext) -> None:
    from travelogue.curation.screen_planner import _plan_one_screen

    chunk = ctx.ids[ctx.i : ctx.i + ctx.max_per_screen]
    screen, consumed = _plan_one_screen(
        chunk,
        ctx.aspects,
        burst_groups=ctx.burst_groups,
        portrait_heavy=ctx.portrait_heavy,
        assets_map=ctx.assets_map,
        layout_state=ctx.layout_state,
        solo_exclude=ctx.skip_screen_asset_ids,
    )
    if not screen or consumed < 1:
        ctx.i += 1
        return
    append_screen(ctx, screen)
    ctx.i += consumed


def stage_flush_remaining_portraits(ctx: ChapterPlanContext) -> None:
    from travelogue.curation.screen_planner import (
        _emit_portrait_single_screens,
        _flush_portrait_pending,
    )

    while len(ctx.pending_portraits) >= 8 and try_drain_portrait_grid8(ctx):
        pass
    for sc in _flush_portrait_pending(
        ctx.pending_portraits,
        ctx.aspects,
        assets_map=ctx.assets_map,
        layout_state=ctx.layout_state,
        force=True,
        solo_exclude=ctx.skip_screen_asset_ids,
    ):
        append_screen(ctx, sc)
    if ctx.pending_portraits:
        for aid in list(ctx.pending_portraits):
            for sc in _emit_portrait_single_screens(
                [aid],
                ctx.aspects,
                assets_map=ctx.assets_map,
                layout_state=ctx.layout_state,
                pending=ctx.pending_portraits,
                force=True,
                solo_exclude=ctx.skip_screen_asset_ids,
            ):
                append_screen(ctx, sc)
            if aid in ctx.pending_portraits:
                ctx.pending_portraits.remove(aid)


def stage_flush_remaining_food(ctx: ChapterPlanContext) -> None:
    if not ctx.enable_food_grid:
        return
    # Flush should only inspect assets that haven't been consumed by prior screens.
    # Otherwise we may duplicate ids already emitted by stage_generic_chunk.
    consumed_ids = {
        str(slot.get("assetId"))
        for sc in ctx.screens
        for slot in (sc.get("slots") or [])
        if slot.get("assetId")
    }
    if consumed_ids:
        ctx.ids = [aid for aid in ctx.ids if aid not in consumed_ids]
    i = 0
    while i < len(ctx.ids):
        run = mundane_run_length(
            ctx.ids,
            ctx.assets_map,
            i,
            allowed_buckets=ctx.mundane_grid_buckets,
        )
        if run < 3:
            i += 1
            continue
        ctx.i = i
        placed = try_mundane_grid(ctx)
        if placed is None:
            i += 1
            continue
        i += placed


def finalize_with_hero(ctx: ChapterPlanContext) -> list[dict]:
    if not ctx.hero_preface:
        return ctx.screens
    reordered: list[dict] = []
    seq = 0
    for sc in ctx.hero_preface + ctx.screens:
        seq += 1
        sc = dict(sc)
        sc["screenId"] = f"{ctx.chapter_id}-sc-{seq:02d}"
        reordered.append(sc)
    return reordered
