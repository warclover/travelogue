"""Shared helpers for Studio trip handlers."""

from __future__ import annotations


def is_protected_demo_trip(trip_id: str, trip: dict) -> bool:
    if trip_id == "demo-album":
        return True
    title = str((trip.get("meta") or {}).get("title") or "").strip()
    return title in ("示例旅途", "示例")
