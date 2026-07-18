"""Neutral asset geometry helpers (TPC W2 · shared tool decoupling)."""

from __future__ import annotations


def asset_native_ar(asset: dict) -> float | None:
    """Native width/height aspect ratio, or None when dims are missing."""
    w = int(asset.get("nativeWidth") or asset.get("width") or 0)
    h = int(asset.get("nativeHeight") or asset.get("height") or 0)
    if w > 0 and h > 0:
        return w / h
    return None
