"""LSE-CAP-08 QualityFeatures · trip-internal percentiles (§4.5.8)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from travelogue.layout_engine.scoring.aesthetic import aesthetic_overall


def _asset_sharpness(asset: dict) -> float | None:
    q = asset.get("quality") or {}
    try:
        sharp = float(q.get("sharpness") or 0.0)
        return sharp if sharp > 0 else None
    except (TypeError, ValueError):
        return None


def _percentile_rank(values: list[float], x: float) -> float:
    if not values:
        return 0.5
    sorted_vals = sorted(values)
    below = sum(1 for v in sorted_vals if v < x)
    equal = sum(1 for v in sorted_vals if v == x)
    return (below + 0.5 * equal) / len(sorted_vals)


@dataclass(frozen=True)
class AssetQuality:
    sharp_pct: float
    aesthetic_pct: float


@dataclass
class QualityPool:
    """Trip-scoped quality percentiles for unified hero/mosaic selection."""

    by_id: dict[str, AssetQuality]

    def for_asset(self, asset_id: str) -> AssetQuality:
        return self.by_id.get(str(asset_id), AssetQuality(sharp_pct=0.5, aesthetic_pct=0.5))

    def sharp_pct(self, asset_id: str) -> float:
        return self.for_asset(asset_id).sharp_pct

    def aesthetic_pct(self, asset_id: str) -> float:
        return self.for_asset(asset_id).aesthetic_pct


def build_quality_pool(assets: list[dict]) -> QualityPool:
    sharp_vals: list[float] = []
    aesthetic_vals: list[float] = []
    sharp_by_id: dict[str, float] = {}
    aesthetic_by_id: dict[str, float] = {}

    for asset in assets:
        aid = str(asset.get("id") or "")
        if not aid:
            continue
        sharp = _asset_sharpness(asset)
        if sharp is not None:
            sharp_vals.append(sharp)
            sharp_by_id[aid] = sharp
        overall = aesthetic_overall(asset)
        if overall is not None:
            aesthetic_vals.append(float(overall))
            aesthetic_by_id[aid] = float(overall)

    by_id: dict[str, AssetQuality] = {}
    for asset in assets:
        aid = str(asset.get("id") or "")
        if not aid:
            continue
        sharp_pct = 0.5
        if aid in sharp_by_id and sharp_vals:
            sharp_pct = _percentile_rank(sharp_vals, sharp_by_id[aid])
        aesthetic_pct = 0.5
        if aid in aesthetic_by_id and aesthetic_vals:
            aesthetic_pct = _percentile_rank(aesthetic_vals, aesthetic_by_id[aid])
        elif not aesthetic_vals:
            aesthetic_pct = 0.5
        by_id[aid] = AssetQuality(
            sharp_pct=round(sharp_pct, 4),
            aesthetic_pct=round(aesthetic_pct, 4),
        )
    return QualityPool(by_id=by_id)


def quality_summary(pool: QualityPool) -> dict[str, Any]:
    return {"assetCount": len(pool.by_id)}
