"""P19 R-304 · explicit per-asset single screens when dense layouts are infeasible."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from travelogue.curation.layout_planner import AspectKind

if TYPE_CHECKING:
    from travelogue.curation.screen_planner_stages import ChapterPlanContext

_log = logging.getLogger(__name__)


def build_explicit_single_screen_plan(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    *,
    assets_map: dict[str, dict] | None = None,
) -> list[dict]:
    """One portrait-1 / landscape-1 per asset — safe rhythm fallback."""
    from travelogue.curation.screen_planner import (
        _family_kind,
        _is_std_portrait_id,
        _make_screen,
    )

    screens: list[dict] = []
    for aid in asset_ids:
        fam = _family_kind(aspects.get(aid, "square"))
        if fam == "portrait" and _is_std_portrait_id(aid, aspects):
            pid = "screen-portrait-1"
        elif fam == "portrait":
            pid = "screen-tall-1"
        else:
            pid = "screen-landscape-1"
        screens.append(
            _make_screen(
                pid,
                [aid],
                screen_id="",
                aspects=aspects,
                assets_map=assets_map or {},
            )
        )
    return screens


def append_explicit_single_fallback(
    ctx: ChapterPlanContext,
    window: list[str],
    *,
    reason: str,
) -> bool:
    """Emit per-asset singles when MCS + legacy window packing both fail."""
    from travelogue.curation.screen_planner import _emit_portrait_single_screens
    from travelogue.curation.screen_planner_stages import append_screen

    if not window:
        return False
    placed = 0
    for aid in window:
        fam = ctx.aspects.get(aid, "square")
        from travelogue.curation.screen_planner import _family_kind

        if _family_kind(fam) == "portrait":
            for sc in _emit_portrait_single_screens(
                [aid],
                ctx.aspects,
                assets_map=ctx.assets_map,
                layout_state=ctx.layout_state,
                pending=ctx.pending_portraits,
                solo_exclude=ctx.skip_screen_asset_ids,
                force=True,
            ):
                append_screen(ctx, sc)
                placed += 1
        else:
            plan = build_explicit_single_screen_plan(
                [aid],
                ctx.aspects,
                assets_map=ctx.assets_map,
            )
            for sc in plan:
                append_screen(ctx, sc)
                placed += 1
    if placed:
        _log.warning(
            "mosaic.explicit_single_fallback: reason=%s window=%d placed=%d chapter=%s",
            reason,
            len(window),
            placed,
            ctx.chapter_id,
        )
    return placed > 0
