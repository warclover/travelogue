"""Low-resolution outlier exclusion."""

from __future__ import annotations

from travelogue.curation.asset_quality import partition_low_resolution_assets
from travelogue.curation.curate import apply_low_resolution_exclusion, layout_eligible_assets


def _img(aid: str, edge: int) -> dict:
    return {"id": aid, "type": "image", "width": edge, "height": int(edge * 0.75)}


def test_partition_drops_clear_outliers() -> None:
    assets = [_img(f"a{i}", edge) for i, edge in enumerate([3200, 3000, 2800, 2400, 2200, 640], 1)]
    kept, dropped, warn = partition_low_resolution_assets(assets, min_long_edge_px=800)
    assert len(dropped) == 1
    assert dropped[0]["id"] == "a6"
    assert len(kept) == 5
    assert warn and "剔除" in warn


def test_apply_exclusion_writes_curation() -> None:
    trip = {
        "assets": [_img(f"a{i}", e) for i, e in enumerate([3000, 2800, 2600, 2400, 2200, 500], 1)],
        "curation": {},
    }
    msg = apply_low_resolution_exclusion(trip)
    assert msg
    assert trip["curation"]["excludedLowResAssetIds"] == ["a6"]
    assert len(layout_eligible_assets(trip)) == 5
