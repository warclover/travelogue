"""Closing pick helpers shared by api + domain re-export."""

from __future__ import annotations

from typing import Any

from travelogue.cover_engine.closing.gate import (
    build_closing_candidates,
    moment_exclude_ids,
)
from travelogue.cover_engine.closing.scorer import pick_best_closing_scored
from travelogue.cover_engine.pairing.policy import filter_pairing_hard
from travelogue.domain.closing_view import cover_ids_to_exclude


def pick_closing_with_meta(
    trip: dict,
    *,
    prefer_landscape: bool = False,
    exclude_ids: set[str] | None = None,
    assets: dict[str, dict] | None = None,
    soft_weight: float = 0.35,
    near_dup_seconds: float = 3.0,
    require_hard: bool = True,
) -> dict[str, Any]:
    """Run gate → PAIR-H → ClosingScorer. Never reuses cover ids."""
    moment_excluded = sorted(moment_exclude_ids(trip))
    candidates, screen_used, assets_map = build_closing_candidates(
        trip, exclude_ids=exclude_ids, assets=assets
    )
    hard_filtered = 0
    if require_hard:
        candidates, hard_filtered = filter_pairing_hard(
            candidates,
            assets_map,
            trip,
            near_dup_seconds=near_dup_seconds,
        )

    from travelogue.curation.food_policy import (
        filter_food_for_policy,
        get_food_role_config,
        is_food_asset,
    )

    role = get_food_role_config()
    food_fallback = False
    if role.closing_policy == "exclude" and candidates:
        candidate_assets = [assets_map[aid] for aid in candidates if aid in assets_map]
        kept_assets, food_fallback = filter_food_for_policy(
            candidate_assets, policy="exclude"
        )
        kept_ids = {str(a.get("id")) for a in kept_assets if a.get("id")}
        if not food_fallback:
            candidates = [aid for aid in candidates if aid in kept_ids]

    cover = None
    for cid in cover_ids_to_exclude(trip):
        if cid in assets_map:
            cover = assets_map[cid]
            break

    picked, scores = pick_best_closing_scored(
        trip,
        candidates,
        assets_map,
        screen_used_ids=screen_used,
        prefer_landscape=prefer_landscape,
        cover=cover,
        soft_weight=soft_weight,
    )
    # B3 · optional VL rerank (default off → leave scorer pick alone)
    try:
        from travelogue.cover_engine.plugins.vl import (
            apply_closing_vl_rerank,
            closing_vl_enabled,
        )

        if closing_vl_enabled() and scores:
            rows = sorted(
                [
                    {"assetId": aid, "score": float(sc)}
                    for aid, sc in scores.items()
                ],
                key=lambda r: -float(r.get("score") or 0),
            )
            reranked = apply_closing_vl_rerank(
                trip,
                rows,
                cover_asset_id=str(cover.get("id") if cover else "") or None,
            )
            if reranked and isinstance(reranked, list):
                top = str((reranked[0] or {}).get("assetId") or "")
                if top and top in scores:
                    picked = top
    except Exception:
        pass

    degraded = picked is None
    unused = bool(picked and picked not in screen_used)
    food_policy = "none"
    if role.closing_policy == "off":
        food_policy = "none"
    elif food_fallback:
        food_policy = "fallback"
    elif role.closing_policy == "exclude":
        food_policy = "exclude"
    elif picked and is_food_asset(assets_map.get(picked) or {}):
        food_policy = "demote"
    elif role.closing_policy == "demote":
        food_policy = "demote"

    from travelogue.curation.food_policy import annotate_trip_food_policy

    annotate_trip_food_policy(trip, slot="closing", applied=food_policy)
    if food_fallback:
        trip.setdefault("curation", {})["closingFoodFallback"] = True

    return {
        "closing_asset_id": picked,
        "degraded": degraded,
        "scores": scores,
        "hard_filtered": hard_filtered,
        "unused": unused,
        "screen_used": screen_used,
        "assets": assets_map,
        "excluded_by_moment": moment_excluded,
        "food_policy": food_policy,
        "closingFoodFallback": bool(food_fallback),
    }
