"""Hook into screen_planner_stages planning loop."""

from __future__ import annotations

from contextvars import ContextVar
from functools import cache
from typing import TYPE_CHECKING

from travelogue.config import MosaicConfig
from travelogue.curation.mosaic.compose import pick_best_window
from travelogue.curation.mosaic.legacy import append_legacy_window
from travelogue.curation.mosaic.runtime import effective_mosaic_window_sizes, ordered_mosaic_window_sizes

if TYPE_CHECKING:
    from travelogue.curation.screen_planner_stages import ChapterPlanContext

_mosaic_logs_var: ContextVar[list[dict] | None] = ContextVar("mosaic_logs", default=None)
_mosaic_dropped_var: ContextVar[list[str] | None] = ContextVar("mosaic_dropped", default=None)
_fallback_logs: list[dict] = []
_fallback_dropped: list[str] = []


def _mosaic_cfg() -> MosaicConfig:
    from travelogue.curation.mosaic.runtime import get_effective_mosaic_config

    return get_effective_mosaic_config()


def begin_mosaic_capture() -> None:
    """Start a fresh log buffer for the current curate/plan run (thread-safe)."""
    _mosaic_logs_var.set([])
    _mosaic_dropped_var.set([])


def _logs_buf() -> list[dict]:
    buf = _mosaic_logs_var.get()
    return buf if buf is not None else _fallback_logs


def _dropped_buf() -> list[str]:
    buf = _mosaic_dropped_var.get()
    return buf if buf is not None else _fallback_dropped


def window_has_candidates(
    window: list[str],
    aspects,
    assets_map: dict[str, dict],
    *,
    size: int,
    cfg: MosaicConfig,
    burst_seconds: float,
    median_sharp: float | None,
) -> bool:
    from travelogue.curation.mosaic.candidates import generate_window_candidates

    if len(window) != size:
        return False
    candidates = generate_window_candidates(
        window,
        aspects,
        assets_map,
        cfg=cfg,
        burst_seconds=burst_seconds,
        median_sharp=median_sharp,
    )
    return any(c.hard_valid for c in candidates)


def _mosaic_winner_has_main_role(
    window: list[str],
    aspects,
    assets_map: dict[str, dict],
    *,
    size: int,
    cfg: MosaicConfig,
    layout_state,
    trip_total: int,
    burst_seconds: float,
    median_sharp: float | None,
) -> bool:
    """True when MCS would consume the window with a pattern that inlines a main hero slot."""
    from travelogue.curation.mosaic.pattern_catalog import default_registry

    pick = pick_best_window(
        window,
        aspects,
        assets_map,
        cfg=cfg,
        window_size=size,
        layout_state=layout_state,
        trip_photo_total=trip_total,
        burst_seconds=burst_seconds,
        median_sharp=median_sharp,
    )
    if pick.used_legacy or not pick.screen:
        return False
    pat = default_registry().get(str(pick.screen.get("patternId") or ""))
    return bool(pat and "main" in pat.roles)


def chapter_should_skip_hero_for_mosaic(ctx: ChapterPlanContext) -> bool:
    """Skip chapter hero when the full chapter packs as one MCS window with a main hero slot."""
    from travelogue.curation.screen_planner import MIN_TRIP_PHOTOS_FOR_MOSAIC

    cfg = _mosaic_cfg()
    sizes = effective_mosaic_window_sizes(cfg) if cfg.enabled else ()
    if len(ctx.ids) not in sizes:
        return False
    size = len(ctx.ids)
    if not cfg.enabled and size == 5:
        return (
            ctx.trip_total >= MIN_TRIP_PHOTOS_FOR_MOSAIC
            and window_has_candidates(
                ctx.ids,
                ctx.aspects,
                ctx.assets_map,
                size=5,
                cfg=cfg,
                burst_seconds=ctx.mix_gap,
                median_sharp=ctx.med_sharp,
            )
        )
    if size == 5 and ctx.trip_total < MIN_TRIP_PHOTOS_FOR_MOSAIC and not cfg.enabled:
        return False
    if not cfg.enabled:
        return False
    return _mosaic_winner_has_main_role(
        ctx.ids,
        ctx.aspects,
        ctx.assets_map,
        size=size,
        cfg=cfg,
        layout_state=ctx.layout_state,
        trip_total=ctx.trip_total,
        burst_seconds=ctx.mix_gap,
        median_sharp=ctx.med_sharp,
    )


def drain_mosaic_logs() -> list[dict]:
    from travelogue.config import get_config
    from travelogue.curation.mosaic.log import format_log_entry

    level = get_config().mosaic.log_level
    buf = _logs_buf()
    out = [format_log_entry(entry, level) for entry in buf]
    if _mosaic_logs_var.get() is not None:
        _mosaic_logs_var.set([])
    else:
        buf.clear()
    return out


def drain_mosaic_dropped() -> list[str]:
    buf = _dropped_buf()
    out = list(buf)
    if _mosaic_dropped_var.get() is not None:
        _mosaic_dropped_var.set([])
    else:
        buf.clear()
    return out


def try_mosaic_window_mcs(
    ctx: ChapterPlanContext, start: int, size: int, cfg: MosaicConfig
) -> bool:
    from travelogue.curation.screen_planner_stages import append_screen

    if start + size > len(ctx.ids):
        return False
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
        prev_screen=ctx.screens[-1] if ctx.screens else None,
        chapter_screen_index=len(ctx.screens),
        chapter_screen_count=max(12, len(ctx.screens) + 1),
    )
    if pick.log.dropped_asset_ids:
        _dropped_buf().extend(pick.log.dropped_asset_ids)

    if pick.used_legacy:
        if append_legacy_window(ctx, window, size):
            _logs_buf().append(pick.log.to_dict())
            return True
        return False
    if pick.screen:
        _logs_buf().append(pick.log.to_dict())
        append_screen(ctx, pick.screen)
        return True
    return False


def _defer_portrait_grid8(ctx: ChapterPlanContext, start: int) -> bool:
    """Let portrait-grid-8 stage handle eight portraits when MCS 8-window is off."""
    cfg = _mosaic_cfg()
    if cfg.enabled and 8 in cfg.enabled_window_sizes:
        return False
    if not ctx.use_portrait_grid8 or start != 0:
        return False
    remaining = ctx.ids[start:]
    if len(remaining) != 8:
        return False
    from travelogue.curation.screen_planner import _can_portrait_grid8_window

    return _can_portrait_grid8_window(
        remaining,
        ctx.aspects,
        ctx.assets_map,
        burst_seconds=ctx.burst_seconds,
    )


_DENSE_PACK_SIZES = (4, 6, 9)


def _cleanly_packable(remaining: int, pack: tuple[int, ...]) -> bool:
    """Can `remaining` photos be split exactly into dense (≥4) windows?"""
    if not pack:
        return False

    @cache
    def reachable(r: int) -> bool:
        if r == 0:
            return True
        if r < 0:
            return False
        return any(reachable(r - p) for p in pack)

    return reachable(remaining)


def _collage_size_order(
    sizes: list[int], remaining: int, *, fit_limit: int
) -> list[int]:
    """Collage-first: prefer windows that leave a cleanly dense-packable tail.

    Keeps balanced/hero output untouched; only reorders MCS window attempts so a
    dense layout does not strand a trailing 1–2 photo single. Falls back to the
    greedy (largest-first) order when no size yields a packable remainder.
    """
    pack = tuple(s for s in _DENSE_PACK_SIZES if s in sizes)
    preferred = [
        s
        for s in sizes
        if s <= fit_limit and _cleanly_packable(remaining - s, pack)
    ]
    rest = [s for s in sizes if s not in preferred]
    return preferred + rest


def _window_all_std_portrait(window: list[str], aspects) -> bool:
    """True when every asset in the window is a standard (non-tall) portrait."""
    from travelogue.curation.screen_planner import _is_std_portrait_id

    return bool(window) and all(_is_std_portrait_id(x, aspects) for x in window)


def _prioritize_exact_window_fit(sizes: list[int], remaining: int) -> list[int]:
    """When the tail length matches an enabled window, try that size first."""
    if remaining in sizes:
        return [remaining] + [s for s in sizes if s != remaining]
    return sizes


def try_mosaic_window(ctx: ChapterPlanContext, start: int) -> int | None:
    """Try enabled window sizes (P21 balanced: 5→4→6). Returns advance count or None."""
    cfg = _mosaic_cfg()
    if not cfg.enabled or not ctx.enable_mosaic:
        return None
    density = getattr(ctx.layout_state, "layout_density", "balanced")
    if density == "hero_first":
        # Hero-first prefers sparse single-hero screens over dense collages
        # (intent preferMosaic=False). Defer to the legacy single/grid emitters,
        # which already honor density, instead of greedily packing MCS windows.
        return None
    if _defer_portrait_grid8(ctx, start):
        return None
    remaining = len(ctx.ids) - start
    if density == "collage_first":
        sizes = _collage_size_order(
            sorted(effective_mosaic_window_sizes(cfg), reverse=True),
            remaining,
            fit_limit=remaining,
        )
    else:
        sizes = list(ordered_mosaic_window_sizes(cfg, density=density))
    sizes = _prioritize_exact_window_fit(sizes, remaining)
    min_dense = cfg.density_budget.min_slots if cfg.density_budget.enabled else 4
    if ctx.layout_state is not None:
        ctx.layout_state.dense_collage_min_slots = min_dense
    for size in sizes:
        if start + size > len(ctx.ids):
            continue
        if (
            cfg.density_budget.enabled
            and ctx.layout_state is not None
            and size >= min_dense
            and not ctx.layout_state.can_use_dense_collage_window(size)
        ):
            continue
        window = ctx.ids[start : start + size]
        # Pair-first portrait priority: a run of consecutive standard portraits
        # must NOT collapse into a pure portrait grid (portrait-3/4/6/9). Defer
        # such windows to the portrait pending tiler, which prefers two-column
        # pairs (portrait-2) and only uses a triple as an odd-parity filler.
        if size in (3, 4, 6, 9) and _window_all_std_portrait(
            window, ctx.aspects
        ):
            continue
        if not window_has_candidates(
            window,
            ctx.aspects,
            ctx.assets_map,
            size=size,
            cfg=cfg,
            burst_seconds=ctx.mix_gap,
            median_sharp=ctx.med_sharp,
        ):
            continue
        if try_mosaic_window_mcs(ctx, start, size, cfg):
            return size
    return None


def try_mosaic_five_mcs(ctx: ChapterPlanContext, start: int, cfg: MosaicConfig) -> bool:
    return try_mosaic_window_mcs(ctx, start, 5, cfg)
