"""Drop obvious low-resolution outliers from layout/cover selection (curation re-exports)."""

from __future__ import annotations

from travelogue.media.quality import (
    apply_layout_eligibility_marks,
    asset_long_edge,
    asset_megapixels,
    asset_sharpness,
    asset_sharpness_version,
    asset_short_edge,
    backfill_native_dimensions,
    is_suspected_thumbnail_asset,
    is_upscaled_thumbnail,
    partition_low_resolution_assets,
)


def _percentile_rank(value: float, values: list[float]) -> float:
    if not values:
        return 0.5
    if len(values) == 1:
        return 1.0 if value >= values[0] else 0.0
    sorted_vals = sorted(values)
    below = sum(1 for v in sorted_vals if v < value)
    equal = sum(1 for v in sorted_vals if v == value)
    return max(0.0, min(1.0, (below + 0.5 * equal) / len(sorted_vals)))


def normalized_sharpness(
    asset: dict,
    pool: list[dict],
    *,
    bucket_by: str | None = "mediaClass",
) -> float:
    """Trip-relative sharpness in [0, 1] via percentile rank."""
    sharp = asset_sharpness(asset)
    if sharp <= 0:
        return 0.0

    if bucket_by:
        bucket_key = str(asset.get(bucket_by) or "unknown")
        bucket_assets = [
            a
            for a in pool
            if str(a.get(bucket_by) or "unknown") == bucket_key and asset_sharpness(a) > 0
        ]
        if len(bucket_assets) >= 3:
            values = [asset_sharpness(a) for a in bucket_assets]
            return _percentile_rank(sharp, values)

    values = [asset_sharpness(a) for a in pool if asset_sharpness(a) > 0]
    if not values:
        return 0.5
    return _percentile_rank(sharp, values)
