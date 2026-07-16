"""AAD-20 PrefixBeam — true prefix search over day-bucket screens.

Default path remains VariantRerank (``replan_day_buckets_beam``). When
``layout.scoring.prefix_beam_enabled`` is true, each day bucket expands
screen-by-screen: generate full greedy variants for the *remaining* assets,
take only the first screen of each variant, keep the top-B partial plans by
``score_screen_plan``, and continue until the bucket is drained or the search
budget is exhausted (then fall back to VariantRerank for that bucket).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace

from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState
from travelogue.layout_contract.scoring import ScoringWeights
from travelogue.layout_contract.search_budget import SearchBudget
from travelogue.layout_engine.planner.beam_scoring import score_screen_plan
from travelogue.layout_engine.planner.layout_candidates import generate_day_bucket_candidates

_log = logging.getLogger(__name__)


@dataclass
class _BeamState:
    screens: list[dict]
    remaining: list[str]
    layout_state: ScreenLayoutPlannerState
    score: float


def _clone_state(state: ScreenLayoutPlannerState) -> ScreenLayoutPlannerState:
    return replace(state)


def _screen_asset_ids(screen: dict) -> list[str]:
    out: list[str] = []
    for slot in screen.get("slots") or []:
        aid = slot.get("assetId")
        if aid:
            out.append(str(aid))
    return out


def prefix_beam_plan_bucket(
    bucket: list[str],
    aspects: dict[str, AspectKind],
    *,
    assets_by_id: dict[str, dict],
    orientation_summary: dict | None,
    skip_screen_asset_ids: set[str] | None,
    mixed_proximity_seconds: float,
    trip_photo_total: int,
    preferred_hero_id: str | None,
    layout_state: ScreenLayoutPlannerState,
    enable_food_grid: bool,
    mundane_grid_buckets: tuple[str, ...],
    beam_width: int,
    budget: SearchBudget,
    weights: ScoringWeights,
    subject_run_tolerance: int,
    enable_gravity_balance: bool,
    late_kwargs: dict,
    moment_secondary_ids: set[str] | frozenset[str] | None = None,
    moment_secondary_boost: float = 0.0,
) -> tuple[list[dict], str | None]:
    """Return (screens, fallback_reason). fallback_reason set when VariantRerank should win."""
    if not bucket:
        return [], None
    if not budget.can_evaluate() and not budget.can_generate():
        return [], "BUDGET_EXHAUSTED"

    initial = _BeamState(
        screens=[],
        remaining=list(bucket),
        layout_state=_clone_state(layout_state),
        score=0.0,
    )
    beam: list[_BeamState] = [initial]
    fallback: str | None = None

    while True:
        if not any(st.remaining for st in beam):
            break
        if not budget.trip_evaluations_remaining() or not budget.segment_evaluations_remaining():
            fallback = "BUDGET_EXHAUSTED"
            break
        if not budget.can_generate():
            fallback = "BUDGET_EXHAUSTED"
            break

        nxt: list[_BeamState] = []
        for st in beam:
            if not st.remaining:
                nxt.append(st)
                continue
            if not budget.can_generate():
                fallback = "BUDGET_EXHAUSTED"
                nxt.append(st)
                continue
            candidates = generate_day_bucket_candidates(
                st.remaining,
                aspects,
                assets_by_id=assets_by_id,
                orientation_summary=orientation_summary,
                skip_screen_asset_ids=skip_screen_asset_ids,
                mixed_proximity_seconds=mixed_proximity_seconds,
                trip_photo_total=trip_photo_total,
                preferred_hero_id=preferred_hero_id,
                layout_state=_clone_state(st.layout_state),
                enable_food_grid=enable_food_grid,
                mundane_grid_buckets=mundane_grid_buckets,
                beam_width=beam_width,
                budget=budget,
                **late_kwargs,
            )
            if not candidates:
                nxt.append(st)
                continue
            for _name, plan in candidates:
                if not plan:
                    continue
                first = plan[0]
                used = set(_screen_asset_ids(first))
                if not used:
                    continue
                new_remaining = [a for a in st.remaining if a not in used]
                # Guard against non-progress (would infinite-loop).
                if len(new_remaining) >= len(st.remaining):
                    continue
                new_state = _clone_state(st.layout_state)
                new_state.note_screen(first.get("patternId", ""))
                new_screens = st.screens + [first]
                if not budget.can_evaluate():
                    fallback = "BUDGET_EXHAUSTED"
                    nxt.append(
                        _BeamState(
                            screens=new_screens,
                            remaining=new_remaining,
                            layout_state=new_state,
                            score=st.score,
                        )
                    )
                    break
                budget.note_evaluation()
                bd = score_screen_plan(
                    new_screens,
                    aspects=aspects,
                    assets_by_id=assets_by_id,
                    weights=weights,
                    subject_run_tolerance=subject_run_tolerance,
                    featured_beam=True,
                    enable_gravity_balance=enable_gravity_balance,
                    moment_secondary_ids=moment_secondary_ids,
                    moment_secondary_boost=moment_secondary_boost,
                )
                nxt.append(
                    _BeamState(
                        screens=new_screens,
                        remaining=new_remaining,
                        layout_state=new_state,
                        score=bd.total,
                    )
                )
            if fallback:
                break
        if not nxt:
            fallback = fallback or "PREFIX_BEAM_EMPTY"
            break
        nxt.sort(key=lambda s: (-s.score, len(s.screens), len(s.remaining)))
        beam = nxt[: max(1, beam_width)]
        if fallback:
            break

    if fallback:
        _log.info("prefix_beam: falling back (%s)", fallback)
        return [], fallback
    best = max(beam, key=lambda s: (s.score, -len(s.remaining)))
    return best.screens, None
