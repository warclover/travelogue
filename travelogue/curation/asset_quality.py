"""Drop obvious low-resolution outliers from layout/cover selection."""

from __future__ import annotations

import statistics
from typing import Any


def asset_long_edge(asset: dict) -> int:
    w = int(asset.get("width") or 0)
    h = int(asset.get("height") or 0)
    return max(w, h)


def partition_low_resolution_assets(
    assets: list[dict],
    *,
    min_long_edge_px: int = 800,
    median_ratio: float = 0.55,
    peak_ratio: float = 0.42,
    min_trip_count: int = 6,
) -> tuple[list[dict], list[dict], str | None]:
    """
    Split assets into keep vs exclude for curate/layout.

    Excludes images whose long edge is clearly below trip norms (not tiny ingest floor only).
    """
    images = [a for a in assets if a.get("type", "image") != "video"]
    if len(images) < min_trip_count:
        return assets, [], None

    edges = [asset_long_edge(a) for a in images]
    median_edge = int(statistics.median(edges))
    peak_edge = max(edges)
    cutoff = max(
        min_long_edge_px,
        int(median_edge * median_ratio),
        int(peak_edge * peak_ratio),
    )

    exclude_ids = {a["id"] for a in images if asset_long_edge(a) < cutoff}
    if not exclude_ids:
        return assets, [], None

    kept = [a for a in assets if a["id"] not in exclude_ids]
    dropped = [a for a in assets if a["id"] in exclude_ids]
    warn = (
        f"已剔除 {len(dropped)} 张分辨率明显偏低的照片（长边 < {cutoff}px，"
        f"本批中位 {median_edge}px）"
    )
    return kept, dropped, warn
