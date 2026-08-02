"""Generate alternative screen plans for beam search (V2 PRD §6.3)."""

from __future__ import annotations

from dataclasses import replace

from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_contract.search_budget import SearchBudget
from travelogue.layout_engine.planner.screen_planner import (
    MIN_TRIP_PHOTOS_FOR_MOSAIC,
    _can_mosaic_5_main_portrait_3land,
    _sort_asset_ids_by_taken,
    plan_screens_for_chapter,
)


def _plan_signature(screens: list[dict]) -> tuple[tuple[str, tuple[str, ...]], ...]:
    sig: list[tuple[str, tuple[str, ...]]] = []
    for s in screens:
        aids = tuple(
            slot.get("assetId")
            for slot in (s.get("slots") or [])
            if slot.get("assetId")
        )
        sig.append((s.get("patternId") or "", aids))
    return tuple(sig)


def _clone_layout_state(state: ScreenLayoutPlannerState | None) -> ScreenLayoutPlannerState | None:
    if state is None:
        return None
    return replace(state)


def bucket_has_mosaic_window(
    bucket: list[str],
    aspects: dict[str, AspectKind],
    assets_by_id: dict[str, dict],
    *,
    mixed_proximity_seconds: float,
    trip_photo_total: int,
) -> bool:
    from travelogue.layout_engine.mosaic.runtime import five_slot_mosaic_enabled

    if not five_slot_mosaic_enabled() or trip_photo_total < MIN_TRIP_PHOTOS_FOR_MOSAIC or len(bucket) < 5:
        return False
    ordered = _sort_asset_ids_by_taken(list(bucket), assets_by_id)
    for i in range(len(ordered) - 4):
        if _can_mosaic_5_main_portrait_3land(
            ordered[i : i + 5],
            aspects,
            assets_by_id,
            burst_seconds=mixed_proximity_seconds,
        ):
            return True
    return False


def generate_day_bucket_candidates(
    bucket: list[str],
    aspects: dict[str, AspectKind],
    *,
    assets_by_id: dict[str, dict],
    orientation_summary: dict | None,
    skip_screen_asset_ids: set[str] | None,
    mixed_proximity_seconds: float,
    trip_photo_total: int,
    preferred_hero_id: str | None,
    layout_state: ScreenLayoutPlannerState | None,
    enable_food_grid: bool = True,
    mundane_grid_buckets: tuple[str, ...] = ("food",),
    beam_width: int = 3,
    budget: SearchBudget | None = None,
    late_chapter_active: bool = False,
    flush_lookahead_portraits: int = 0,
) -> list[tuple[str, list[dict]]]:
    """Return up to beam_width distinct (variant_name, screen_plan) pairs for one day bucket."""
    cap = beam_width
    if budget is not None:
        cap = min(cap, budget.max_candidates_per_bucket)

    common = dict(
        aspects=aspects,
        chapter_id="day",
        assets=assets_by_id or None,
        mixed_proximity_seconds=mixed_proximity_seconds,
        orientation_summary=orientation_summary,
        skip_screen_asset_ids=skip_screen_asset_ids,
        trip_photo_total=trip_photo_total,
        enable_food_grid=enable_food_grid,
        mundane_grid_buckets=mundane_grid_buckets,
        late_chapter_active=late_chapter_active,
        flush_lookahead_portraits=flush_lookahead_portraits,
    )
    has_mosaic = bucket_has_mosaic_window(
        bucket,
        aspects,
        assets_by_id,
        mixed_proximity_seconds=mixed_proximity_seconds,
        trip_photo_total=trip_photo_total,
    )
    variants: list[tuple[str, dict]] = [
        ("with_hero", dict(include_chapter_hero=True, preferred_hero_id=preferred_hero_id)),
    ]
    if has_mosaic:
        variants.append(
            (
                "no_mosaic",
                dict(
                    include_chapter_hero=True,
                    preferred_hero_id=preferred_hero_id,
                    enable_mosaic=False,
                ),
            )
        )
    # ALG-V3 W3-C3 · prune always-on hero variants when they are no-ops.
    # Without a preferred hero, no_hero / hero_no_pref collapse toward with_hero.
    if preferred_hero_id is not None:
        variants.extend(
            [
                ("no_hero", dict(include_chapter_hero=False, preferred_hero_id=preferred_hero_id)),
                (
                    "hero_no_pref",
                    dict(include_chapter_hero=True, preferred_hero_id=None),
                ),
            ]
        )
        if has_mosaic:
            variants.append(
                (
                    "no_hero_no_mosaic",
                    dict(
                        include_chapter_hero=False,
                        preferred_hero_id=preferred_hero_id,
                        enable_mosaic=False,
                    ),
                )
            )

    from travelogue.layout_engine.mosaic.hook import set_mosaic_log_capture

    seen: set[tuple[tuple[str, tuple[str, ...]], ...]] = set()
    candidates: list[tuple[str, list[dict]]] = []
    # LTN H2 · beam variants must not pollute mosaicDecisionLog.
    set_mosaic_log_capture(False)
    try:
        for name, extra in variants:
            if len(candidates) >= cap:
                break
            if budget is not None and not budget.can_generate():
                break
            state = _clone_layout_state(layout_state)
            plan = plan_screens_for_chapter(bucket, layout_state=state, **common, **extra)
            if budget is not None:
                budget.note_generation()
            sig = _plan_signature(plan)
            if sig in seen or not plan:
                continue
            seen.add(sig)
            candidates.append((name, plan))
        if not candidates and (budget is None or budget.can_generate()):
            if budget is not None:
                budget.note_generation()
            fallback = plan_screens_for_chapter(
                bucket,
                layout_state=_clone_layout_state(layout_state),
                **common,
                include_chapter_hero=True,
                preferred_hero_id=preferred_hero_id,
            )
            candidates.append(("with_hero", fallback))
    finally:
        set_mosaic_log_capture(True)
    return candidates[:cap]
