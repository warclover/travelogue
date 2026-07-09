"""Landscape aspect-ratio buckets (layout kernel). — only group photos in the same bucket."""

from __future__ import annotations

LandscapeBucket = str  # "standard" | "classic" | "wide" | "other"


def native_aspect_ratio(asset: dict) -> float:
    w = int(asset.get("nativeWidth") or asset.get("width") or 0)
    h = int(asset.get("nativeHeight") or asset.get("height") or 0)
    if w <= 0 or h <= 0:
        return 16 / 9
    return w / h


def landscape_aspect_bucket(asset: dict) -> LandscapeBucket:
    """
    Group near-standard landscape crops (16:9, 16:10, 3:2) separately from ultrawide.
    """
    r = native_aspect_ratio(asset)
    if r >= 1.85:
        return "wide"
    if r >= 1.52:
        return "standard"
    if r >= 1.22:
        return "classic"
    return "other"


def same_landscape_bucket(a: dict, b: dict) -> bool:
    return landscape_aspect_bucket(a) == landscape_aspect_bucket(b)


def prefix_same_bucket(
    asset_ids: list[str],
    assets_map: dict[str, dict],
) -> list[str]:
    """Longest prefix of ids sharing the same landscape bucket as the first."""
    if not asset_ids:
        return []
    first = assets_map.get(asset_ids[0], {})
    bucket = landscape_aspect_bucket(first)
    out: list[str] = []
    for aid in asset_ids:
        if landscape_aspect_bucket(assets_map.get(aid, {})) == bucket:
            out.append(aid)
        else:
            break
    return out
