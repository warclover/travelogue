"""Pure asset quality readers for layout contracts."""

from __future__ import annotations


def asset_sharpness(asset: dict) -> float:
    quality = asset.get("quality")
    if isinstance(quality, dict):
        val = quality.get("sharpness")
        if isinstance(val, (int, float)):
            return float(val)
    return 0.0


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
