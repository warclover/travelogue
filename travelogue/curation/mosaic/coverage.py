"""Layout coverage metrics (DESIGN §8 · eligible_to_screen_coverage)."""

from __future__ import annotations

from typing import Any

# Canonical telemetry key; snake_case and dotted aliases are written for backward compatibility.
CANONICAL_ELIGIBLE_COVERAGE_KEY = "eligible_to_screen_coverage"


def compute_coverage_metrics(
    *,
    displayed_asset_ids: list[str] | None,
    layout_eligible_assets: list[dict] | None,
    dropped_asset_ids: list[str] | None = None,
    planned_asset_ids: set[str] | None = None,
    geo_recovered_asset_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Ratio of layout-eligible assets that appear on screens (via displayedAssetIds).

    When ``planned_asset_ids`` is set (bucket union from curate), the denominator
    excludes layout-eligible assets never assigned to a chapter bucket (e.g. cover-only).
    """
    if not layout_eligible_assets:
        return {}
    eligible = {
        str(a["id"])
        for a in layout_eligible_assets
        if a.get("id") and a.get("layoutEligible", True) is not False
    }
    if planned_asset_ids is not None:
        eligible &= planned_asset_ids
    if not eligible:
        return {}
    displayed = set(displayed_asset_ids or [])
    shown = displayed & eligible
    coverage = round(len(shown) / len(eligible), 6)
    dropped = [d for d in (dropped_asset_ids or []) if d in eligible]
    drop_rate = round(len(dropped) / len(eligible), 6) if eligible else 0.0
    out: dict[str, Any] = {
        CANONICAL_ELIGIBLE_COVERAGE_KEY: coverage,
        "eligibleToScreenCoverage": coverage,
        "layout.eligible_to_screen_coverage": coverage,
        "mosaicDropRate": drop_rate,
        "layout.mosaic_v2.drop_rate": drop_rate,
        "layoutEligibleCount": len(eligible),
        "displayedOnScreenCount": len(shown),
    }
    recovered = [str(aid) for aid in (geo_recovered_asset_ids or []) if aid]
    if recovered:
        out["geoRecoveredAssetIds"] = recovered
        out["geoRecoveredCount"] = len(recovered)
    return out
