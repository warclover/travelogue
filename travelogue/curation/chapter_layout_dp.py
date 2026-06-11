"""P19 R-303 · chapter-scale window partition DP (replaces greedy MCS stepping)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from travelogue.config import MosaicConfig

if TYPE_CHECKING:
    from travelogue.curation.screen_planner_stages import ChapterPlanContext


@dataclass(frozen=True)
class _DpStep:
    size: int
    score: float


def _mosaic_window_sizes_for_dp(
    ctx: ChapterPlanContext,
    cfg: MosaicConfig,
    *,
    start: int,
) -> list[int]:
    from travelogue.curation.mosaic.hook import (
        _collage_size_order,
        _defer_portrait_grid8,
        _window_all_std_portrait,
    )
    from travelogue.curation.mosaic.runtime import effective_mosaic_window_sizes

    if _defer_portrait_grid8(ctx, start):
        return []
    sizes = [
        s
        for s in sorted(effective_mosaic_window_sizes(cfg), reverse=True)
        if s in (3, 4, 5, 6, 8, 9)
    ]
    density = getattr(ctx.layout_state, "layout_density", "balanced")
    if density == "collage_first":
        sizes = _collage_size_order(
            sizes, len(ctx.ids) - start, fit_limit=len(ctx.ids) - start
        )
    return sizes


def _window_allowed(
    ctx: ChapterPlanContext,
    start: int,
    size: int,
    cfg: MosaicConfig,
) -> bool:
    from travelogue.curation.mosaic.hook import _window_all_std_portrait, window_has_candidates

    if start + size > len(ctx.ids):
        return False
    window = ctx.ids[start : start + size]
    if size in (3, 4, 6, 9) and _window_all_std_portrait(window, ctx.aspects):
        return False
    return window_has_candidates(
        window,
        ctx.aspects,
        ctx.assets_map,
        size=size,
        cfg=cfg,
        burst_seconds=ctx.mix_gap,
        median_sharp=ctx.med_sharp,
    )


def plan_mosaic_partition_dp(
    asset_ids: list[str],
    aspects,
    assets_map: dict[str, dict],
    *,
    cfg: MosaicConfig,
    layout_state=None,
    trip_total: int = 0,
    burst_seconds: float = 12.0,
    median_sharp: float | None = None,
    chapter_id: str = "",
    max_assets: int = 45,
) -> tuple[list[tuple[int, int, dict]], float] | None:
    """
    DP partition of asset_ids into MCS windows.

    Returns list of (start_offset, size, screen_dict) and total score, or None if no full cover.
    """
    from travelogue.curation.mosaic.compose import pick_best_window
    from travelogue.curation.screen_planner_stages import ChapterPlanContext

    n = len(asset_ids)
    if n == 0 or n > max_assets:
        return None

    stub = ChapterPlanContext(
        chapter_id=chapter_id,
        aspects=aspects,
        assets_map=assets_map,
        mix_gap=burst_seconds,
        med_sharp=median_sharp or 0.0,
        trip_total=trip_total or n,
        burst_seconds=burst_seconds,
        burst_groups={},
        layout_state=layout_state,
        enable_mosaic=True,
        enable_portrait_grid8=True,
        enable_food_grid=True,
        mundane_grid_buckets=("food",),
        use_portrait_grid8=False,
        max_per_screen=9,
        portrait_heavy=False,
        ids=list(asset_ids),
    )

    sizes_at: list[list[int]] = [_mosaic_window_sizes_for_dp(stub, cfg, start=i) for i in range(n + 1)]

    best_score: list[float] = [-1.0] * (n + 1)
    best_score[n] = 0.0
    next_step: list[_DpStep | None] = [None] * (n + 1)

    for i in range(n - 1, -1, -1):
        local_best: float = -1.0
        local_step: _DpStep | None = None
        for size in sizes_at[i]:
            if not _window_allowed(stub, i, size, cfg):
                continue
            tail = best_score[i + size]
            if tail < 0:
                continue
            window = asset_ids[i : i + size]
            pick = pick_best_window(
                window,
                aspects,
                assets_map,
                cfg=cfg,
                window_size=size,
                layout_state=layout_state,
                trip_photo_total=trip_total or n,
                burst_seconds=burst_seconds,
                median_sharp=median_sharp,
                window_start=i,
                segment_id=chapter_id,
                prev_screen=None,
                chapter_screen_index=0,
                chapter_screen_count=max(12, (n + size - 1) // max(size, 1)),
            )
            if pick.used_legacy or not pick.screen:
                continue
            score = float(pick.log.winner_score or 0.0) + tail
            if score > local_best:
                local_best = score
                local_step = _DpStep(size=size, score=float(pick.log.winner_score or 0.0))
                stub.screens = [pick.screen]
        best_score[i] = local_best
        next_step[i] = local_step

    if best_score[0] < 0 or next_step[0] is None:
        return None

    out: list[tuple[int, int, dict]] = []
    i = 0
    prev_screen: dict | None = None
    screen_idx = 0
    while i < n:
        step = next_step[i]
        if step is None:
            return None
        size = step.size
        window = asset_ids[i : i + size]
        pick = pick_best_window(
            window,
            aspects,
            assets_map,
            cfg=cfg,
            window_size=size,
            layout_state=layout_state,
            trip_photo_total=trip_total or n,
            burst_seconds=burst_seconds,
            median_sharp=median_sharp,
            window_start=i,
            segment_id=chapter_id,
            prev_screen=prev_screen,
            chapter_screen_index=screen_idx,
            chapter_screen_count=max(12, screen_idx + 1),
        )
        if pick.used_legacy or not pick.screen:
            return None
        out.append((i, size, pick.screen))
        prev_screen = pick.screen
        screen_idx += 1
        i += size
    return out, best_score[0]


def chapter_dp_enabled(cfg: MosaicConfig) -> bool:
    return bool(getattr(cfg, "chapter_dp_enabled", False))


def try_plan_chapter_with_dp(ctx: ChapterPlanContext) -> bool:
    """When enabled, plan the full chapter via DP and append screens (greedy bypass)."""
    from travelogue.curation.mosaic.compose import pick_best_window
    from travelogue.curation.mosaic.hook import _logs_buf, _mosaic_cfg
    from travelogue.curation.screen_planner_stages import append_screen

    cfg = _mosaic_cfg()
    if not cfg.enabled or not ctx.enable_mosaic or not chapter_dp_enabled(cfg):
        return False
    density = getattr(ctx.layout_state, "layout_density", "balanced")
    if density == "hero_first":
        return False
    max_assets = int(getattr(cfg, "chapter_dp_max_assets", 45))
    if len(ctx.ids) > max_assets:
        return False

    planned = plan_mosaic_partition_dp(
        ctx.ids,
        ctx.aspects,
        ctx.assets_map,
        cfg=cfg,
        layout_state=ctx.layout_state,
        trip_total=ctx.trip_total,
        burst_seconds=ctx.mix_gap,
        median_sharp=ctx.med_sharp,
        chapter_id=ctx.chapter_id or "",
        max_assets=max_assets,
    )
    if planned is None:
        return False

    steps, _total = planned
    prev_screen: dict | None = None
    for start, size, _screen in steps:
        window = ctx.ids[start : start + size]
        pick = pick_best_window(
            window,
            ctx.aspects,
            ctx.assets_map,
            cfg=cfg,
            window_size=size,
            layout_state=ctx.layout_state,
            trip_photo_total=ctx.trip_total,
            burst_seconds=ctx.mix_gap,
            median_sharp=ctx.med_sharp,
            window_start=start,
            segment_id=ctx.chapter_id or "",
            prev_screen=prev_screen,
            chapter_screen_index=len(ctx.screens),
            chapter_screen_count=max(12, len(ctx.screens) + 1),
        )
        if pick.used_legacy or not pick.screen:
            return False
        if pick.log.dropped_asset_ids:
            from travelogue.curation.mosaic.hook import _dropped_buf

            _dropped_buf().extend(pick.log.dropped_asset_ids)
        _logs_buf().append(pick.log.to_dict())
        append_screen(ctx, pick.screen)
        prev_screen = pick.screen
    if sum(size for _, size, _ in steps) != len(ctx.ids):
        return False
    ctx.i = len(ctx.ids)
    return True
