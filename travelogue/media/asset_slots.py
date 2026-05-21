"""Map asset IDs to render crop slots from trip structure."""

from __future__ import annotations


def asset_display_slots(trip: dict) -> dict[str, str]:
    """cover | scroll | media — used when re-exporting WebP from source."""
    slots: dict[str, str] = {}
    cover = trip.get("coverAssetId")
    if cover:
        slots[str(cover)] = "cover"

    for ch in trip.get("chapters", []):
        for it in ch.get("items", []):
            itype = it.get("type")
            if itype == "media-scroll":
                for aid in it.get("assetIds") or []:
                    slots[str(aid)] = "scroll"
            elif itype == "media-row":
                for aid in it.get("assetIds") or []:
                    slots.setdefault(str(aid), "media")
            elif itype == "media-card":
                aid = it.get("assetId")
                if aid:
                    slots.setdefault(str(aid), "media")
    return slots
