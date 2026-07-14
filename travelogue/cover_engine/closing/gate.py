"""Closing candidate gate (exclude covers / moment / PAIR-H*)."""

from __future__ import annotations

from typing import Any

from travelogue.domain.closing_view import (
    _asset_valid_for_closing,
    _closing_candidate_ids,
    collect_layout_screen_asset_ids,
    cover_ids_to_exclude,
)


def _assets_by_id(trip: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for asset in trip.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        aid = str(asset.get("id") or "").strip()
        if aid:
            out[aid] = asset
    return out


def moment_exclude_ids(trip: dict) -> set[str]:
    """Read-only moment signature exclude (T-B2A-06)."""
    curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    if curation.get("momentSkipped"):
        return set()
    mid = str(trip.get("momentAssetId") or "").strip()
    return {mid} if mid else set()


def build_closing_candidates(
    trip: dict,
    *,
    exclude_ids: set[str] | None = None,
    assets: dict[str, dict] | None = None,
) -> tuple[list[str], set[str], dict[str, dict]]:
    """Ordered candidate ids after cover/moment excludes (before PAIR-H)."""
    assets_map = assets if assets is not None else _assets_by_id(trip)
    screen_used = collect_layout_screen_asset_ids(trip)
    excluded = set(exclude_ids or set())
    excluded |= cover_ids_to_exclude(trip)
    excluded |= moment_exclude_ids(trip)
    ordered = _closing_candidate_ids(
        trip,
        assets_map,
        screen_used_ids=screen_used,
        exclude_ids=excluded,
    )
    # Keep only valid layout-eligible images
    filtered = [
        aid
        for aid in ordered
        if _asset_valid_for_closing(aid, assets_map) and aid not in excluded
    ]
    return filtered, screen_used, assets_map


def trip_has_screens(trip: dict, screens: Any = None) -> bool:
    if screens:
        return True
    if isinstance(trip.get("screens"), list) and trip.get("screens"):
        return True
    return bool(collect_layout_screen_asset_ids(trip))
