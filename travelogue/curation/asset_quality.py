"""Drop obvious low-resolution outliers from layout/cover selection."""

from __future__ import annotations

import statistics
from pathlib import Path
from typing import Any


def asset_long_edge(asset: dict) -> int:
    """Use native (source) pixels when present — not upscaled WebP export size."""
    nw = int(asset.get("nativeWidth") or asset.get("width") or 0)
    nh = int(asset.get("nativeHeight") or asset.get("height") or 0)
    return max(nw, nh)


def asset_short_edge(asset: dict) -> int:
    nw = int(asset.get("nativeWidth") or asset.get("width") or 0)
    nh = int(asset.get("nativeHeight") or asset.get("height") or 0)
    if nw <= 0 or nh <= 0:
        return 0
    return min(nw, nh)


def is_suspected_thumbnail_asset(
    asset: dict,
    *,
    min_short_edge_px: int = 600,
) -> bool:
    """True when native pixels look like a thumbnail or upscaled small source."""
    if asset_short_edge(asset) < min_short_edge_px:
        return True
    return is_upscaled_thumbnail(asset)


def is_upscaled_thumbnail(asset: dict) -> bool:
    """Source was small but display metadata was upscaled on export."""
    nw = int(asset.get("nativeWidth") or 0)
    w = int(asset.get("width") or 0)
    if nw <= 0 or w <= 0:
        return False
    return nw < int(w * 0.6)


def backfill_native_dimensions(trip: dict, trip_dir: Path) -> int:
    """Read source JPEG dimensions into assets missing nativeWidth/Height."""
    from PIL import Image

    updated = 0
    for asset in trip.get("assets") or []:
        if asset.get("type", "image") == "video":
            continue
        if asset.get("nativeWidth") and asset.get("nativeHeight"):
            continue
        rel = asset.get("sourceFile") or ""
        src = trip_dir / rel
        if not src.is_file():
            continue
        try:
            with Image.open(src) as im:
                asset["nativeWidth"] = im.width
                asset["nativeHeight"] = im.height
                updated += 1
        except OSError:
            continue
    return updated


def partition_low_resolution_assets(
    assets: list[dict],
    *,
    min_long_edge_px: int = 800,
    min_short_edge_px: int = 600,
    median_ratio: float = 0.55,
    peak_ratio: float = 0.42,
    min_trip_count: int = 6,
) -> tuple[list[dict], list[dict], str | None]:
    """
    Split assets into keep vs exclude for curate/layout.

    Uses nativeWidth/Height when set; excludes short-edge thumbnails and trip outliers.
    """
    images = [a for a in assets if a.get("type", "image") != "video"]
    if len(images) < min_trip_count:
        return assets, [], None

    exclude_ids: set[str] = set()
    for a in images:
        if asset_short_edge(a) < min_short_edge_px:
            exclude_ids.add(a["id"])
        elif is_upscaled_thumbnail(a) and asset_long_edge(a) < min_long_edge_px:
            exclude_ids.add(a["id"])

    edges = [asset_long_edge(a) for a in images if a["id"] not in exclude_ids]
    if len(edges) >= min_trip_count:
        median_edge = int(statistics.median(edges))
        peak_edge = max(edges)
        cutoff = max(
            min_long_edge_px,
            int(median_edge * median_ratio),
            int(peak_edge * peak_ratio),
        )
        for a in images:
            if a["id"] in exclude_ids:
                continue
            if asset_long_edge(a) < cutoff:
                exclude_ids.add(a["id"])

    if not exclude_ids:
        return assets, [], None

    kept = [a for a in assets if a["id"] not in exclude_ids]
    dropped = [a for a in assets if a["id"] in exclude_ids]
    warn = (
        f"已剔除 {len(dropped)} 张分辨率明显偏低的照片"
        f"（原生短边 < {min_short_edge_px}px 或长边低于本批阈值；误传缩略图）"
    )
    return kept, dropped, warn
