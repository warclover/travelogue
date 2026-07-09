"""Low-resolution outlier exclusion."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.curation.asset_quality import (
    asset_long_edge,
    asset_megapixels,
    asset_short_edge,
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


def _native(aid: str, w: int, h: int) -> dict:
    return {
        "id": aid,
        "type": "image",
        "nativeWidth": w,
        "nativeHeight": h,
        "width": min(w, 1600),
        "height": int(min(w, 1600) * h / w) if w else 0,
    }


def test_partition_drops_clear_outliers() -> None:
    assets = [_img(f"a{i}", edge) for i, edge in enumerate([3200, 3000, 2800, 2400, 2200, 640], 1)]
    kept, dropped, warn = partition_low_resolution_assets(assets, min_long_edge_px=800)
    assert len(dropped) == 1
    assert dropped[0]["id"] == "a6"
    assert len(kept) == 5
    assert warn and "不参与排版" in warn


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


def test_panorama_outlier_does_not_poison_batch() -> None:
    """318-regression · ultra-wide stitch must not drop normal 4K landscapes."""
    assets = [
        _native(f"n{i}", 4987, 2778)
        for i in range(200)
    ]
    assets.append(_native("pano", 13549, 2499))
    kept, dropped, warn = partition_low_resolution_assets(assets)
    assert len(kept) >= 195
    assert len(dropped) <= 10
    assert warn is None or "熔断" not in warn


def test_mao_mixed_wechat_compression() -> None:
    """WeChat saves among camera originals — drop compressed, keep high-res."""
    assets = [_native(f"big{i}", 5760, 4320) for i in range(20)]
    assets.extend(_native(f"wx{i}", 1080, 1919) for i in range(9))
    kept, dropped, warn = partition_low_resolution_assets(assets)
    dropped_ids = {a["id"] for a in dropped}
    assert len(dropped) >= 7
    assert all(aid.startswith("wx") for aid in dropped_ids)
    assert len(kept) == 20
    assert warn and "相对偏低" in warn


def test_maomi_uniform_high_res_untouched() -> None:
    assets = [_native(f"a{i}", 3000, 4000) for i in range(33)]
    kept, dropped, warn = partition_low_resolution_assets(assets)
    assert len(kept) == 33
    assert not dropped
    assert warn is None


def test_circuit_breaker_when_relative_would_drop_high_res_batch() -> None:
    """Fuse relative rules when they would cull many photos that are still high short-edge."""
    assets = [_native(f"h{i}", 4987, 2778) for i in range(200)]
    assets.extend(_native(f"m{i}", 2500, 1800) for i in range(50))
    kept, dropped, warn = partition_low_resolution_assets(
        assets,
        circuit_breaker_ratio=0.15,
        circuit_breaker_median_short_px=1200,
    )
    assert len(kept) == 250
    assert not dropped
    assert warn and "熔断" in warn


def test_asset_megapixels_and_short_edge_helpers() -> None:
    a = _native("x", 4987, 2778)
    assert asset_short_edge(a) == 2778
    assert asset_megapixels(a) == pytest.approx(4987 * 2778 / 1_000_000, rel=1e-3)


@pytest.mark.skipif(
    not Path("trips/demo-318/trip.json").is_file(),
    reason="local demo-318 trip not present",
)
def test_demo_318_trip_eligible_count_regression() -> None:
    trip = json.loads(Path("trips/demo-318/trip.json").read_text(encoding="utf-8"))
    apply_low_resolution_exclusion(trip, trip_dir=Path("trips/demo-318"))
    eligible = [a for a in trip["assets"] if a.get("layoutEligible", True)]
    assert len(eligible) >= 180
    aspects = {a.get("aspectKind") for a in eligible}
    assert "landscape" in aspects
    assert len(aspects) > 1
