"""Drop obvious low-resolution outliers from layout/cover selection."""

from __future__ import annotations

import statistics
from pathlib import Path

from travelogue.config import AppConfig, IngestConfig, get_config


def asset_sharpness(asset: dict) -> float:
    quality = asset.get("quality")
    if isinstance(quality, dict):
        val = quality.get("sharpness")
        if isinstance(val, (int, float)):
            return float(val)
    return 0.0


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


def asset_megapixels(asset: dict) -> float:
    nw = int(asset.get("nativeWidth") or asset.get("width") or 0)
    nh = int(asset.get("nativeHeight") or asset.get("height") or 0)
    if nw <= 0 or nh <= 0:
        return 0.0
    return (nw * nh) / 1_000_000.0


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


def _absolute_low_res_ids(
    images: list[dict],
    *,
    min_short_edge_px: int,
    min_long_edge_px: int,
) -> set[str]:
    exclude_ids: set[str] = set()
    for a in images:
        if asset_short_edge(a) < min_short_edge_px:
            exclude_ids.add(a["id"])
        elif is_upscaled_thumbnail(a) and asset_long_edge(a) < min_long_edge_px:
            exclude_ids.add(a["id"])
    return exclude_ids


def _relative_low_res_ids(
    images: list[dict],
    absolute_ids: set[str],
    *,
    min_short_edge_px: int,
    min_megapixels: float,
    median_ratio: float,
    mp_ratio: float,
    min_trip_count: int,
) -> set[str]:
    """
    Batch-relative drops using short edge + megapixels (panorama-safe).

    Long-edge peak is intentionally not used — ultra-wide stitches must not
    raise the bar for normal landscape/portrait assets.
    """
    pool = [a for a in images if a["id"] not in absolute_ids]
    if len(pool) < min_trip_count:
        return set()

    short_edges = [asset_short_edge(a) for a in pool]
    megapixels = [asset_megapixels(a) for a in pool]
    median_short = int(statistics.median(short_edges))
    median_mp = statistics.median(megapixels)

    cutoff_short = max(min_short_edge_px, int(median_short * median_ratio))
    cutoff_mp = max(min_megapixels, median_mp * mp_ratio)

    relative_ids: set[str] = set()
    for a in pool:
        if asset_short_edge(a) < cutoff_short or asset_megapixels(a) < cutoff_mp:
            relative_ids.add(a["id"])
    return relative_ids


def _format_low_res_warning(
    *,
    absolute_count: int,
    relative_count: int,
    min_short_edge_px: int,
    circuit_breaker: bool,
) -> str:
    parts: list[str] = []
    if absolute_count:
        parts.append(f"绝对低清 {absolute_count} 张（短边 < {min_short_edge_px}px 或疑似缩略图）")
    if relative_count:
        parts.append(f"批内相对偏低 {relative_count} 张（短边/像素面积低于本批阈值）")
    if circuit_breaker:
        parts.append("相对阈值已熔断（剔除比例异常），仅保留绝对规则")
    total = absolute_count + relative_count
    if not parts:
        return f"已剔除 {total} 张分辨率明显偏低的照片"
    return f"已剔除 {total} 张分辨率明显偏低的照片（{'；'.join(parts)}）"


def partition_low_resolution_assets(
    assets: list[dict],
    *,
    min_long_edge_px: int = 800,
    min_short_edge_px: int = 600,
    median_ratio: float = 0.55,
    peak_ratio: float = 0.42,
    min_megapixels: float = 0.8,
    mp_ratio: float = 0.45,
    circuit_breaker_ratio: float = 0.25,
    circuit_breaker_median_short_px: int = 1200,
    min_trip_count: int = 6,
) -> tuple[list[dict], list[dict], str | None]:
    """
    Split assets into keep vs exclude for curate/layout.

    Uses nativeWidth/Height when set. Absolute rules catch thumbnails; relative
    rules compare short edge and megapixels to batch medians (not long-edge peak).
    """
    del peak_ratio  # deprecated · kept for call-site compatibility

    images = [a for a in assets if a.get("type", "image") != "video"]
    if len(images) < min_trip_count:
        return assets, [], None

    absolute_ids = _absolute_low_res_ids(
        images,
        min_short_edge_px=min_short_edge_px,
        min_long_edge_px=min_long_edge_px,
    )
    relative_ids = _relative_low_res_ids(
        images,
        absolute_ids,
        min_short_edge_px=min_short_edge_px,
        min_megapixels=min_megapixels,
        median_ratio=median_ratio,
        mp_ratio=mp_ratio,
        min_trip_count=min_trip_count,
    )

    combined_ids = absolute_ids | relative_ids
    circuit_breaker = False
    if relative_ids and len(combined_ids) / len(images) > circuit_breaker_ratio:
        drop_shorts = [asset_short_edge(a) for a in images if a["id"] in relative_ids]
        dropped_median_short = int(statistics.median(drop_shorts)) if drop_shorts else 0
        if dropped_median_short >= circuit_breaker_median_short_px:
            circuit_breaker = True
            combined_ids = absolute_ids
            relative_ids = set()

    if not combined_ids:
        if circuit_breaker:
            warn = _format_low_res_warning(
                absolute_count=len(absolute_ids),
                relative_count=0,
                min_short_edge_px=min_short_edge_px,
                circuit_breaker=True,
            )
            return assets, [], warn
        return assets, [], None

    kept = [a for a in assets if a["id"] not in combined_ids]
    dropped = [a for a in assets if a["id"] in combined_ids]
    relative_only = len(relative_ids - absolute_ids)
    warn = _format_low_res_warning(
        absolute_count=len(absolute_ids),
        relative_count=relative_only if not circuit_breaker else 0,
        min_short_edge_px=min_short_edge_px,
        circuit_breaker=circuit_breaker,
    )
    return kept, dropped, warn


def apply_layout_eligibility_marks(
    trip: dict,
    assets: list[dict] | None = None,
    *,
    cfg: IngestConfig | None = None,
    app_cfg: AppConfig | None = None,
) -> str | None:
    """
    Mark layoutEligible on each image asset and write curation.excludedLowResAssetIds.

    Low-resolution assets stay in assets[] but are excluded from cover/chapters/screens.
    """
    assets = assets if assets is not None else trip.get("assets") or []
    resolved = app_cfg or get_config()
    cfg = cfg or resolved.ingest

    for a in assets:
        if a.get("type", "image") == "video":
            continue
        a["layoutEligible"] = True
        a.pop("excludeReason", None)

    _, dropped, warn = partition_low_resolution_assets(
        assets,
        min_long_edge_px=cfg.min_long_edge_layout_px,
        min_short_edge_px=cfg.min_short_edge_layout_px,
        median_ratio=cfg.low_res_median_ratio,
        peak_ratio=cfg.low_res_peak_ratio,
        min_megapixels=cfg.low_res_min_megapixels,
        mp_ratio=cfg.low_res_mp_ratio,
        circuit_breaker_ratio=cfg.low_res_circuit_breaker_ratio,
        circuit_breaker_median_short_px=cfg.low_res_circuit_breaker_median_short_px,
    )
    dropped_ids = {a["id"] for a in dropped}
    for a in assets:
        if a["id"] in dropped_ids:
            a["layoutEligible"] = False
            a["excludeReason"] = "low_resolution"

    curation = trip.setdefault("curation", {})
    if dropped:
        curation["excludedLowResAssetIds"] = [a["id"] for a in dropped]
    else:
        curation.pop("excludedLowResAssetIds", None)
    return warn
