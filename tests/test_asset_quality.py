"""Low-resolution outlier exclusion."""

from __future__ import annotations

from travelogue.curation.asset_quality import (
    asset_long_edge,
    backfill_native_dimensions,
    partition_low_resolution_assets,
)
from travelogue.curation.curate import apply_low_resolution_exclusion, layout_eligible_assets


def _img(aid: str, edge: int, *, native: int | None = None) -> dict:
    n = native if native is not None else edge
    return {
        "id": aid,
        "type": "image",
        "nativeWidth": n,
        "nativeHeight": int(n * 0.75),
        "width": edge,
        "height": int(edge * 0.75),
    }


def test_partition_drops_clear_outliers() -> None:
    assets = [_img(f"a{i}", edge) for i, edge in enumerate([3200, 3000, 2800, 2400, 2200, 640], 1)]
    kept, dropped, warn = partition_low_resolution_assets(assets, min_long_edge_px=800)
    assert len(dropped) == 1
    assert dropped[0]["id"] == "a6"
    assert len(kept) == 5
    assert warn and "剔除" in warn


def test_partition_drops_short_edge_thumbnail() -> None:
    """438×640 native thumbnail upscaled to 1600 in width metadata."""
    assets = [_img(f"a{i}", 1600) for i in range(1, 6)]
    assets.append(
        {
            "id": "thumb",
            "type": "image",
            "nativeWidth": 438,
            "nativeHeight": 640,
            "width": 1600,
            "height": 2338,
        }
    )
    _, dropped, _ = partition_low_resolution_assets(assets, min_short_edge_px=600)
    assert any(a["id"] == "thumb" for a in dropped)


def test_apply_exclusion_writes_curation() -> None:
    trip = {
        "assets": [_img(f"a{i}", e) for i, e in enumerate([3000, 2800, 2600, 2400, 2200, 500], 1)],
        "curation": {},
    }
    msg = apply_low_resolution_exclusion(trip)
    assert msg
    assert trip["curation"]["excludedLowResAssetIds"] == ["a6"]
    assert len(layout_eligible_assets(trip)) == 5
    dropped = next(a for a in trip["assets"] if a["id"] == "a6")
    assert dropped["layoutEligible"] is False
    assert dropped["excludeReason"] == "low_resolution"


def test_asset_long_edge_prefers_native() -> None:
    a = {"width": 1600, "height": 1200, "nativeWidth": 438, "nativeHeight": 640}
    assert asset_long_edge(a) == 640
