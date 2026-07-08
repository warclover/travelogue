"""Asset indexing and tier helpers (M-C4)."""

from __future__ import annotations

from typing import Any


def assets_by_id(trip: dict) -> dict[str, dict]:
    return {str(a["id"]): a for a in (trip.get("assets") or []) if a.get("id")}


def get_asset(trip: dict, asset_id: str) -> dict | None:
    return assets_by_id(trip).get(str(asset_id))


def set_asset_tier(trip: dict, asset_id: str, tier: str) -> None:
    asset = get_asset(trip, asset_id)
    if asset is None:
        raise KeyError(asset_id)
    asset["tier"] = tier


def featured_asset_ids(trip: dict) -> list[str]:
    return [
        str(a["id"])
        for a in (trip.get("assets") or [])
        if a.get("id") and str(a.get("tier") or "").lower() == "featured"
    ]
