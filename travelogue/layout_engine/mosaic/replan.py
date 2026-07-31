"""Single-screen replan API (Benchmark P1 · studio / offline edits)."""

from __future__ import annotations

from typing import Any, Literal

from travelogue.config import MosaicConfig
from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_contract.rhythm import BREATH_PATTERN
from travelogue.layout_engine.mosaic.compose import score_window_candidates
from travelogue.layout_engine.mosaic.legacy import build_legacy_screen

ReplanStrategy = Literal["alt_topk", "legacy"]


class ReplanError(Exception):
    """Invalid replan request (missing screen, breath pause, missing context)."""


def _find_screen(chapters: list[dict], screen_id: str) -> tuple[int, int, dict, dict]:
    for ch_i, ch in enumerate(chapters):
        for sc_i, sc in enumerate(ch.get("screens") or []):
            if sc.get("screenId") == screen_id:
                return ch_i, sc_i, ch, sc
    raise ReplanError(f"screen not found: {screen_id!r}")


def _ordered_asset_ids(screen: dict) -> list[str]:
    slots = screen.get("slots") or []
    return [str(sl["assetId"]) for sl in slots if sl.get("assetId")]


def _pick_alt_topk(
    asset_ids: list[str],
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict],
    *,
    cfg: MosaicConfig,
    current_pattern_id: str,
    top_k: int,
    layout_state: ScreenLayoutPlannerState | None,
    trip_photo_total: int,
    burst_seconds: float,
    median_sharp: float | None,
) -> tuple[dict | None, int, str]:
    scored = score_window_candidates(
        asset_ids,
        aspects,
        assets_map,
        cfg=cfg,
        layout_state=layout_state,
        trip_photo_total=trip_photo_total,
        burst_seconds=burst_seconds,
        median_sharp=median_sharp,
    )
    if not scored:
        return None, 0, "no_candidates"

    rank = 0
    for cand, _score, _reasons, _penalties in scored[: max(1, top_k)]:
        rank += 1
        if cand.pattern_id != current_pattern_id:
            return cand.screen, rank, "alt_topk"
    if scored:
        return scored[0][0].screen, 1, "unchanged_best_only"
    return None, 0, "no_candidates"


def _sync_chapter_items(chapters: list[dict]) -> None:
    from travelogue.layout_contract.chapter_items import compact_chapter_items_for_screens

    compact_chapter_items_for_screens(chapters)


def refresh_trip_displayed_assets(trip: dict, chapters: list[dict]) -> list[str]:
    """Rebuild ``curation.displayedAssetIds`` from screens + chapter heroes."""
    from travelogue.layout_contract.chapter_items import collect_displayed_asset_ids

    hero_extra = [
        str((ch.get("curation") or {}).get("heroAssetId"))
        for ch in chapters
        if (ch.get("curation") or {}).get("heroAssetId")
    ]
    displayed = collect_displayed_asset_ids(chapters, extra_asset_ids=hero_extra)
    trip.setdefault("curation", {})["displayedAssetIds"] = displayed
    return displayed


def replan_screen(
    chapters: list[dict],
    screen_id: str,
    *,
    strategy: ReplanStrategy = "alt_topk",
    top_k: int = 3,
    aspects: dict[str, AspectKind] | None = None,
    assets_map: dict[str, dict] | None = None,
    cfg: MosaicConfig | None = None,
    layout_state: ScreenLayoutPlannerState | None = None,
    trip_photo_total: int = 0,
    burst_seconds: float = 12.0,
    median_sharp: float | None = None,
    sync_chapter_items: bool = True,
) -> dict[str, Any]:
    """
    Replace one screen in ``chapters`` (in place) using MCS alternates or legacy rules.

    Mutates ``chapters`` in place. When ``sync_chapter_items`` is true (default), rebuilds
    ``items[]`` from ``screens[]`` per D-MCS-13 after a successful apply.
    """
    if top_k < 1:
        raise ReplanError("top_k must be >= 1")
    if aspects is None or assets_map is None:
        raise ReplanError("aspects and assets_map are required for replan_screen")

    ch_i, sc_i, _ch, screen = _find_screen(chapters, screen_id)
    pattern_id = str(screen.get("patternId") or "")
    if pattern_id == BREATH_PATTERN or not screen.get("slots"):
        raise ReplanError(f"screen {screen_id!r} has no replannable photo slots")

    asset_ids = _ordered_asset_ids(screen)
    if len(asset_ids) < 3:
        raise ReplanError(
            f"screen {screen_id!r} has {len(asset_ids)} assets; replan supports 3–9 slot windows"
        )

    from travelogue.layout_engine.mosaic.runtime import get_effective_mosaic_config

    mosaic_cfg = cfg or get_effective_mosaic_config()
    window_size = len(asset_ids)
    previous = dict(screen)

    if strategy == "legacy":
        new_screen = build_legacy_screen(
            asset_ids,
            window_size,
            aspects,
            assets_map,
            burst_seconds=burst_seconds,
            median_sharp=median_sharp,
            trip_total=trip_photo_total,
            app_cfg=None,
        )
        reason = "legacy" if new_screen else "legacy_failed"
        rank = 0
        # BLK-10 / D-TPC-12: legacy replan must not emit patterns rejected by
        # usage_rules (parity with append_legacy_window).
        if new_screen:
            from travelogue.layout_contract.usage_context import build_window_context
            from travelogue.layout_engine.usage_rules.evaluator import evaluate_reject

            window_ctx = build_window_context(
                asset_ids,
                aspects,
                assets_map,
                layout_state=layout_state,
                median_sharp=median_sharp,
            )
            pid = str(new_screen.get("patternId") or "")
            reject, _rule_id, _detail = evaluate_reject(
                pid, window_ctx, screen=new_screen
            )
            if reject:
                new_screen = None
                reason = "legacy_usage_rejected"
    else:
        new_screen, rank, reason = _pick_alt_topk(
            asset_ids,
            aspects,
            assets_map,
            cfg=mosaic_cfg,
            current_pattern_id=pattern_id,
            top_k=top_k,
            layout_state=layout_state,
            trip_photo_total=trip_photo_total,
            burst_seconds=burst_seconds,
            median_sharp=median_sharp,
        )

    if not new_screen:
        return {
            "screenId": screen_id,
            "strategy": strategy,
            "applied": False,
            "reason": reason,
            "previousPatternId": pattern_id,
            "rank": rank,
            "itemsSynced": False,
        }

    new_screen = dict(new_screen)
    new_screen["screenId"] = screen_id
    # alt_topk candidates are already solidified in builders, but the ``legacy``
    # strategy returns raw screen_planner output that bypasses
    # ``_finalize_mosaic_screen``. Solidify here so every replan write carries
    # LTE geometry + role-aware fit (idempotent on already-solidified screens;
    # a no-op for pattern ids absent from the LTE registry).
    from travelogue.layout_engine.mosaic.lte_adapter import read_templates_from_lte

    if read_templates_from_lte():
        from travelogue.layout_templates.geometry_solidify import (
            solidify_screen_geometry,
        )

        solidify_screen_geometry(
            new_screen,
            str(new_screen.get("patternId") or ""),
            assets_map=assets_map,
        )
    chapters[ch_i]["screens"][sc_i] = new_screen
    if sync_chapter_items:
        _sync_chapter_items(chapters)

    return {
        "screenId": screen_id,
        "strategy": strategy,
        "applied": True,
        "reason": reason,
        "previousPatternId": pattern_id,
        "newPatternId": new_screen.get("patternId"),
        "rank": rank,
        "screen": new_screen,
        "previousScreen": previous,
        "itemsSynced": sync_chapter_items,
    }
