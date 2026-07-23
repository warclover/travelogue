"""Hook into screen_planner_stages planning loop."""

from __future__ import annotations

from contextvars import ContextVar
from functools import cache
from typing import TYPE_CHECKING

from travelogue.config import MosaicConfig
from travelogue.layout_engine.mosaic.compose import pick_best_window
from travelogue.layout_engine.mosaic.runtime import (
    effective_mosaic_window_sizes,
    planner_mosaic_window_sizes,
)

if TYPE_CHECKING:
    from travelogue.layout_engine.planner.screen_planner_stages import ChapterPlanContext

_mosaic_logs_var: ContextVar[list[dict] | None] = ContextVar("mosaic_logs", default=None)
_mosaic_dropped_var: ContextVar[list[str] | None] = ContextVar("mosaic_dropped", default=None)
_mosaic_capture_enabled_var: ContextVar[bool] = ContextVar(
    "mosaic_capture_enabled", default=True
)
_fallback_logs: list[dict] = []
_fallback_dropped: list[str] = []


def _mosaic_cfg() -> MosaicConfig:
    from travelogue.layout_engine.mosaic.runtime import get_effective_mosaic_config

    return get_effective_mosaic_config()


def begin_mosaic_capture() -> None:
    """Start a fresh log buffer for the current curate/plan run (thread-safe)."""
    _mosaic_logs_var.set([])
    _mosaic_dropped_var.set([])
    _mosaic_capture_enabled_var.set(True)


def set_mosaic_log_capture(enabled: bool) -> None:
    """LTN H2 · pause append during beam candidate generation (avoid orphan logs)."""
    _mosaic_capture_enabled_var.set(bool(enabled))


def mosaic_log_capture_enabled() -> bool:
    return bool(_mosaic_capture_enabled_var.get())


def _logs_buf() -> list[dict]:
    buf = _mosaic_logs_var.get()
    return buf if buf is not None else _fallback_logs


def _dropped_buf() -> list[str]:
    buf = _mosaic_dropped_var.get()
    return buf if buf is not None else _fallback_dropped


def _append_mosaic_log(entry: dict) -> None:
    if not mosaic_log_capture_enabled():
        return
    _logs_buf().append(entry)


def _ctx_trip_id(ctx: "ChapterPlanContext | None" = None) -> str | None:
    from travelogue.layout_engine.mosaic.lifecycle import trip_id_from_trip

    if ctx is None:
        return None
    return trip_id_from_trip(getattr(ctx, "trip", None))


def window_has_candidates(
    window: list[str],
    aspects,
    assets_map: dict[str, dict],
    *,
    size: int,
    cfg: MosaicConfig,
    burst_seconds: float,
    median_sharp: float | None,
    layout_state=None,
    trip_id: str | None = None,
) -> bool:
    from travelogue.config import get_config
    from travelogue.layout_contract.usage_context import build_window_context
    from travelogue.layout_engine.mosaic.candidates import (
        generate_window_candidates_with_rejections,
    )

    if len(window) != size:
        return False
    window_ctx = None
    if get_config().layout.usage_rules.enabled:
        window_ctx = build_window_context(
            window,
            aspects,
            assets_map,
            layout_state=layout_state,
            median_sharp=median_sharp,
        )
    result = generate_window_candidates_with_rejections(
        window,
        aspects,
        assets_map,
        cfg=cfg,
        burst_seconds=burst_seconds,
        median_sharp=median_sharp,
        window_ctx=window_ctx,
        trip_id=trip_id,
    )
    return any(c.hard_valid for c in result.candidates)


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
    trip_id: str | None = None,
) -> bool:
    """True when MCS would consume the window with a pattern that inlines a main hero slot."""
    from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState

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
        trip_id=trip_id,
    )
    if pick.used_legacy or not pick.screen:
        return False
    return ScreenLayoutPlannerState.pattern_has_main_role(
        str(pick.screen.get("patternId") or "")
    )


def chapter_should_skip_hero_for_mosaic(ctx: ChapterPlanContext) -> bool:
    """Skip chapter hero when the full chapter packs as one MCS window with a main hero slot."""
    from travelogue.layout_engine.planner.screen_planner import MIN_TRIP_PHOTOS_FOR_MOSAIC

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
                layout_state=ctx.layout_state,
                trip_id=_ctx_trip_id(ctx),
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
        trip_id=_ctx_trip_id(ctx),
    )


def drain_mosaic_capture() -> tuple[list[dict], list[dict]]:
    """Return (formatted_for_persist, raw_for_metrics) and clear the buffer.

    LTN H2 · AC/metrics must use the raw list; trip.curation uses formatted.
    """
    from travelogue.config import get_config
    from travelogue.layout_engine.mosaic.log import format_log_entry

    level = get_config().mosaic.log_level
    buf = _logs_buf()
    raw = [dict(entry) for entry in buf]
    formatted = [format_log_entry(entry, level) for entry in raw]
    if _mosaic_logs_var.get() is not None:
        _mosaic_logs_var.set([])
    else:
        buf.clear()
    return formatted, raw


def drain_mosaic_logs() -> list[dict]:
    """Persist-shaped logs (formatted by mosaic.log_level). Prefer drain_mosaic_capture."""
    formatted, _raw = drain_mosaic_capture()
    return formatted


def drain_mosaic_dropped() -> list[str]:
    buf = _dropped_buf()
    out = list(buf)
    if _mosaic_dropped_var.get() is not None:
        _mosaic_dropped_var.set([])
    else:
        buf.clear()
    return out


def try_mosaic_window_mcs(
    ctx: ChapterPlanContext,
    start: int,
    size: int,
    cfg: MosaicConfig,
    *,
    funnel: dict | None = None,
) -> bool:
    from travelogue.layout_engine.planner.screen_planner_stages import append_screen

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
        # LTN D2 · real chapter asset progress (not fake max(12, …) denominator).
        chapter_screen_index=max(0, int(start)),
        chapter_screen_count=max(2, len(ctx.ids)),
        trip_id=_ctx_trip_id(ctx),
        funnel=funnel,
    )
    if pick.log.dropped_asset_ids and mosaic_log_capture_enabled():
        _dropped_buf().extend(pick.log.dropped_asset_ids)

    from travelogue.layout_engine.mosaic.compose import _apply_six_hero_outcome
    from travelogue.layout_engine.mosaic.lifecycle import six_hero_family_id

    won_six = bool(
        pick.screen
        and size == 6
        and six_hero_family_id(pick.log.winner_pattern_id)
    )
    _apply_six_hero_outcome(pick.log, won_six=won_six)

    if pick.used_legacy:
        # LTN C1 · do not silent-fallback to size=3/equal legacy; try next window size.
        pick.log.fallback_reason = pick.log.fallback_reason or "mcs_no_winner"
        _append_mosaic_log(pick.log.to_dict())
        return False
    if pick.screen:
        _append_mosaic_log(pick.log.to_dict())
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
    from travelogue.layout_engine.planner.screen_planner import _can_portrait_grid8_window

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
    from travelogue.layout_engine.planner.screen_planner import _is_std_portrait_id

    return bool(window) and all(_is_std_portrait_id(x, aspects) for x in window)


def _mixed_portrait_dense_skip(
    window: list[str],
    aspects,
    size: int,
    *,
    cfg: MosaicConfig,
) -> bool:
    """True when a size≥6 dense window should be skipped (≥2 std portraits)."""
    if not cfg.skip_dense_window_multi_portrait or size < 6:
        return False
    from travelogue.layout_engine.planner.screen_planner import _is_std_portrait_id

    n = sum(1 for aid in window if _is_std_portrait_id(aid, aspects))
    return n >= 2


def _single_portrait_dense_skip(
    window: list[str],
    aspects,
    size: int,
    *,
    cfg: MosaicConfig,
) -> bool:
    """True when a 1P+5L (or denser) window should skip size≥6 for five-slot mix."""
    if not cfg.prefer_five_slot_single_portrait or size < 6:
        return False
    from travelogue.layout_engine.planner.screen_planner import (
        _is_landscape_id,
        _is_std_portrait_id,
    )

    n_p = sum(1 for aid in window if _is_std_portrait_id(aid, aspects))
    n_l = sum(1 for aid in window if _is_landscape_id(aid, aspects))
    return n_p == 1 and n_l >= 5


def _prioritize_five_slot_single_portrait(
    sizes: list[int],
    segment: list[str],
    aspects,
    remaining: int,
    *,
    cfg: MosaicConfig,
) -> list[int]:
    """When a 6-photo tail is 1P+5L with portrait in the first 5, try size=5 first."""
    if not cfg.prefer_five_slot_single_portrait or remaining != 6 or 5 not in sizes:
        return sizes
    from travelogue.layout_engine.planner.screen_planner import _is_std_portrait_id

    prefix = segment[:5]
    n_p_prefix = sum(1 for aid in prefix if _is_std_portrait_id(aid, aspects))
    n_p_total = sum(1 for aid in segment if _is_std_portrait_id(aid, aspects))
    if n_p_total != 1 or n_p_prefix != 1:
        return sizes
    return [5] + [s for s in sizes if s != 5]


def _prioritize_exact_window_fit(sizes: list[int], remaining: int) -> list[int]:
    """When the tail length matches an enabled window, try that size first."""
    if remaining in sizes:
        return [remaining] + [s for s in sizes if s != remaining]
    return sizes


def _prioritize_six_hero_opportunity(sizes: list[int]) -> list[int]:
    """SUP-04 · admit six → try 6 before 5/4 (keep other sizes after)."""
    preferred = [s for s in (6, 5, 4) if s in sizes]
    rest = [s for s in sizes if s not in preferred]
    return preferred + rest


def _try_mcs_single_hero_rescue(ctx: ChapterPlanContext, start: int) -> int | None:
    """LTN C1 · single-asset hero rescue when all MCS window sizes fail.

    Portrait cursor (MTSO / S-MTSO-02) → ``screen-portrait-1``.
    Landscape cursor → ``screen-landscape-1`` when main-eligible with hero gap.
    """
    from travelogue.config import get_config
    from travelogue.layout_contract.usage_context import build_window_context
    from travelogue.layout_engine.mosaic.constants import PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
    from travelogue.layout_engine.mosaic.log import MosaicWindowLog
    from travelogue.layout_engine.mosaic.main_eligibility import (
        asset_eligible_for_main_slot,
        pick_best_main_eligible,
        resolve_main_ar_ladder_tol,
    )
    from travelogue.layout_engine.planner.screen_planner import (
        _is_std_portrait_id,
        _make_screen,
    )
    from travelogue.layout_engine.planner.screen_planner_stages import append_screen
    from travelogue.layout_engine.usage_rules.context import (
        main_eligible_hero_score_gap,
        portrait_is_window_hero_max,
    )

    if start >= len(ctx.ids):
        return None
    look = ctx.ids[start : start + min(6, len(ctx.ids) - start)]
    cursor = ctx.ids[start]
    asset = ctx.assets_map.get(cursor) or {}

    # S-MTSO-02 · strong portrait rescue (independent of mosaic-6 main AR).
    if _is_std_portrait_id(cursor, ctx.aspects):
        wctx = build_window_context(
            look,
            ctx.aspects,
            ctx.assets_map,
            median_sharp=ctx.med_sharp,
        )
        if not portrait_is_window_hero_max(wctx):
            return None
        screen = _make_screen(
            "screen-portrait-1",
            [cursor],
            screen_id="",
            aspects=ctx.aspects,
            assets_map=ctx.assets_map,
        )
        append_screen(ctx, screen)
        log = MosaicWindowLog(
            segment_id=ctx.chapter_id or "",
            window_size=1,
            window_start=start,
            winner_pattern_id=str(screen.get("patternId") or "screen-portrait-1"),
            winner_score=1.0,
            fallback_used=True,
            fallback_reason="mcs_single_hero_rescue",
            planner_path="mosaic",
            winner_reason_codes=["R_MCS_SINGLE_HERO_RESCUE", "R_PORTRAIT_1_RESCUE"],
        )
        _append_mosaic_log(log.to_dict())
        return 1

    pattern_id = PATTERN_MOSAIC_6_MAIN_HERO_PLUS_5
    tol = resolve_main_ar_ladder_tol(pattern_id, _mosaic_cfg())
    ok, _ = asset_eligible_for_main_slot(asset, pattern_id=pattern_id, tol=tol)
    if not ok:
        return None
    best = pick_best_main_eligible(
        look,
        ctx.assets_map,
        pattern_id=pattern_id,
        median_sharp=ctx.med_sharp,
        cfg=_mosaic_cfg(),
    )
    if best != cursor:
        return None
    wctx = build_window_context(
        look,
        ctx.aspects,
        ctx.assets_map,
        median_sharp=ctx.med_sharp,
    )
    gap, _scores = main_eligible_hero_score_gap(wctx, pattern_id)
    thr = float(get_config().layout.usage_rules.hero_gap_threshold)
    if gap < thr:
        return None
    screen = _make_screen(
        "screen-landscape-1",
        [cursor],
        screen_id="",
        aspects=ctx.aspects,
        assets_map=ctx.assets_map,
    )
    append_screen(ctx, screen)
    log = MosaicWindowLog(
        segment_id=ctx.chapter_id or "",
        window_size=1,
        window_start=start,
        winner_pattern_id=str(screen.get("patternId") or "screen-landscape-1"),
        winner_score=1.0,
        fallback_used=True,
        fallback_reason="mcs_single_hero_rescue",
        planner_path="mosaic",
        winner_reason_codes=["R_MCS_SINGLE_HERO_RESCUE"],
    )
    _append_mosaic_log(log.to_dict())
    return 1


def _log_mcs_all_sizes_failed(
    ctx: ChapterPlanContext, start: int, tried_sizes: list[int]
) -> None:
    """LTN C1 · fail-loud when every MCS size (and rescue) failed."""
    from travelogue.layout_engine.mosaic.log import MosaicWindowLog

    log = MosaicWindowLog(
        segment_id=ctx.chapter_id or "",
        window_size=0,
        window_start=start,
        fallback_used=True,
        fallback_reason="mcs_all_sizes_failed",
        planner_path="legacy",
        winner_reason_codes=[f"tried_sizes={tried_sizes}"],
    )
    _append_mosaic_log(log.to_dict())
    if ctx.layout_state is not None:
        ctx.layout_state.release_hero_reserve()

def try_mosaic_window(ctx: ChapterPlanContext, start: int) -> int | None:
    """Try enabled window sizes (P21 balanced: 5→4→6). Returns advance count or None."""
    cfg = _mosaic_cfg()
    if not cfg.enabled or not ctx.enable_mosaic:
        return None
    density = getattr(ctx.layout_state, "layout_density", "balanced")
    # LTN C2 · hero_first no longer hard-skips MCS; flat dense is down-weighted
    # via density params / scoring instead of closing the mosaic pipe.
    if _defer_portrait_grid8(ctx, start):
        return None
    remaining = len(ctx.ids) - start
    if density == "collage_first":
        sizes = _collage_size_order(
            list(planner_mosaic_window_sizes(cfg, density="collage_first")),
            remaining,
            fit_limit=remaining,
        )
    else:
        sizes = list(planner_mosaic_window_sizes(cfg, density=density))
    base_order = list(sizes)
    segment = ctx.ids[start : start + remaining]
    min_dense = cfg.density_budget.min_slots if cfg.density_budget.enabled else 4
    if ctx.layout_state is not None:
        ctx.layout_state.dense_collage_min_slots = min_dense
    # LTN C4 · never open a mosaic window across coarse segment boundaries.
    from travelogue.layout_engine.mosaic.coarse_segments import max_window_size_in_segment
    from travelogue.layout_engine.mosaic.compose import _mtso_quota_snapshot
    from travelogue.layout_engine.mosaic.hero_six import (
        effective_hero_six_opportunity_enabled,
        qualify_hero_six,
    )

    seg_cap = max_window_size_in_segment(getattr(ctx, "coarse_segments", None), start)
    structural_six = False
    admit_six = False
    qualify_reason = ""
    reorder_reason: str | None = None
    allow_six_hero = False
    six_opportunity_on = (
        effective_hero_six_opportunity_enabled(cfg) and density != "collage_first"
    )
    if six_opportunity_on and remaining >= 6 and 6 in sizes:
        from travelogue.layout_engine.mosaic.hero_six import six_hero_outcome_label
        from travelogue.layout_engine.mosaic.log import MosaicWindowLog

        six_window = ctx.ids[start : start + 6]
        q = qualify_hero_six(
            six_window,
            ctx.aspects,
            ctx.assets_map,
            cfg=cfg,
            layout_state=ctx.layout_state,
            seg_cap=seg_cap,
            median_sharp=ctx.med_sharp,
        )
        structural_six = bool(q.structural)
        admit_six = bool(q.admit)
        qualify_reason = str(q.reason or "")
        if structural_six and ctx.layout_state is not None:
            ctx.layout_state.arm_hero_six_opportunity(start)
        if admit_six:
            sizes = _prioritize_six_hero_opportunity(sizes)
            reorder_reason = "structurally_qualified_six"
            allow_six_hero = True
        else:
            if structural_six and ctx.layout_state is not None:
                # Dense/large unavailable → release opportunity (SUP-05 path family).
                ctx.layout_state.release_hero_six_opportunity()
            # AC-03 · precheck miss probe; dedupe by qualify reason per chapter.
            reason_key = qualify_reason or "unknown"
            seen = (
                getattr(ctx.layout_state, "hero_six_probe_reasons", None)
                if ctx.layout_state is not None
                else None
            )
            emit_probe = structural_six or seen is None or reason_key not in seen
            if emit_probe:
                if isinstance(seen, set):
                    seen.add(reason_key)
                probe = MosaicWindowLog(
                    segment_id=ctx.chapter_id or "",
                    window_size=6,
                    window_start=start,
                    fallback_used=True,
                    fallback_reason="six_hero_precheck",
                    planner_path="mosaic",
                    base_window_order=list(base_order),
                    effective_window_order=list(sizes),
                    reorder_reason=reorder_reason,
                    structurally_qualified_six=structural_six,
                    admit_six_hero=False,
                    six_hero_opportunity_state=(
                        getattr(ctx.layout_state, "hero_six_opportunity", "idle")
                        if ctx.layout_state is not None
                        else "idle"
                    ),
                    six_hero_qualify_reason=qualify_reason or None,
                    six_hero_outcome=six_hero_outcome_label(
                        structural=structural_six,
                        admit=False,
                        reason=qualify_reason,
                        attempted_six=False,
                        won_six=False,
                    ),
                    quota_snapshot=_mtso_quota_snapshot(ctx.layout_state),
                )
                _append_mosaic_log(probe.to_dict())
    if not admit_six:
        sizes = _prioritize_exact_window_fit(sizes, remaining)
        if reorder_reason is None and sizes and sizes[0] == remaining and remaining in base_order:
            reorder_reason = "exact_tail_fit"
        before_sp = list(sizes)
        sizes = _prioritize_five_slot_single_portrait(
            sizes, segment, ctx.aspects, remaining, cfg=cfg
        )
        if reorder_reason is None and sizes != before_sp:
            reorder_reason = "single_portrait_tail"

    funnel = {
        "base_window_order": base_order,
        "effective_window_order": list(sizes),
        "reorder_reason": reorder_reason,
        "structurally_qualified_six": structural_six,
        "admit_six_hero": admit_six,
        "six_hero_qualify_reason": qualify_reason or None,
        "six_hero_opportunity_state": (
            getattr(ctx.layout_state, "hero_six_opportunity", "idle")
            if ctx.layout_state is not None
            else "idle"
        ),
        "quota_snapshot": _mtso_quota_snapshot(ctx.layout_state),
    }

    for size in sizes:
        if start + size > len(ctx.ids):
            continue
        if size > seg_cap:
            continue
        if (
            cfg.density_budget.enabled
            and ctx.layout_state is not None
            and size >= min_dense
            and not ctx.layout_state.can_use_dense_collage_window(size)
        ):
            continue
        if (
            ctx.layout_state is not None
            and size >= ctx.layout_state.large_mosaic_min_slots
            and not ctx.layout_state.can_use_large_mosaic_window(size)
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
        if _mixed_portrait_dense_skip(window, ctx.aspects, size, cfg=cfg):
            continue
        if (
            not allow_six_hero
            and _single_portrait_dense_skip(window, ctx.aspects, size, cfg=cfg)
        ):
            continue
        # LTN C1 · size=3 aux short-circuit removed; portrait tiler owns explicit triples.
        # AC-04 · admitted six always runs MCS (funnel attempt) even if cheap prefilter misses.
        has_cands = window_has_candidates(
            window,
            ctx.aspects,
            ctx.assets_map,
            size=size,
            cfg=cfg,
            burst_seconds=ctx.mix_gap,
            median_sharp=ctx.med_sharp,
            layout_state=ctx.layout_state,
            trip_id=_ctx_trip_id(ctx),
        )
        if not has_cands and not (size == 6 and allow_six_hero):
            continue
        attempt_funnel = {
            **funnel,
            "six_hero_opportunity_state": (
                getattr(ctx.layout_state, "hero_six_opportunity", "idle")
                if ctx.layout_state is not None
                else "idle"
            ),
        }
        if try_mosaic_window_mcs(ctx, start, size, cfg, funnel=attempt_funnel):
            return size
        if (
            size == 6
            and allow_six_hero
            and ctx.layout_state is not None
            and ctx.layout_state.hero_six_opportunity == "armed"
        ):
            # SUP-05 · size6 attempt failed → released
            ctx.layout_state.release_hero_six_opportunity()
            funnel["six_hero_opportunity_state"] = "released"
    rescued = _try_mcs_single_hero_rescue(ctx, start)
    if rescued is not None:
        return rescued
    _log_mcs_all_sizes_failed(ctx, start, list(sizes))
    return None


def try_mosaic_five_mcs(ctx: ChapterPlanContext, start: int, cfg: MosaicConfig) -> bool:
    return try_mosaic_window_mcs(ctx, start, 5, cfg)
