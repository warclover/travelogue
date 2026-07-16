"""Asset layout-family helpers (layout kernel · AAD-11)."""

from __future__ import annotations

from travelogue.layout_contract.orientations import (
    AspectKind,
    is_std_landscape,
    is_std_portrait,
)

# Solo ultra-wide stage only when native w/h ≥ this (aligns with render ultra tier).
ULTRA_WIDE_SOLO_AR = 2.8


def family_kind(kind: AspectKind) -> str:
    if kind == "panorama":
        return "panorama"
    if kind == "tall":
        return "tall"
    if kind == "square":
        return "square"
    if is_std_portrait(kind):
        return "portrait"
    if is_std_landscape(kind):
        return "landscape"
    return "landscape"


def asset_native_aspect_ratio(asset: dict) -> float | None:
    w = int(asset.get("nativeWidth") or asset.get("width") or 0)
    h = int(asset.get("nativeHeight") or asset.get("height") or 0)
    if w > 0 and h > 0:
        return w / h
    return None


def layout_family_for_asset(
    aid: str,
    aspects: dict[str, AspectKind],
    assets_map: dict[str, dict] | None = None,
) -> str:
    """Map ingest panorama (≥2:1) to landscape unless truly ultra-wide."""
    fam = family_kind(aspects.get(aid, "square"))
    if fam != "panorama" or not assets_map:
        return fam
    ar = asset_native_aspect_ratio(assets_map.get(aid, {}))
    if ar is not None and ar < ULTRA_WIDE_SOLO_AR:
        return "landscape"
    return "panorama"
