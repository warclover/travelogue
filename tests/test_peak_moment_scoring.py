"""Phase 23 · moment pool + signature selection."""

from __future__ import annotations

from travelogue.config.moment import MomentConfig
from travelogue.curation.moment_scoring import (
    build_moment_pool,
    moment_pool_target_size,
    sync_trip_moments_finalize,
    sync_trip_moments_preflight,
)


def _asset(aid: str, *, featured: bool = False, sharp: float = 0.8) -> dict:
    return {
        "id": aid,
        "type": "image",
        "layoutEligible": True,
        "width": 1600,
        "height": 900,
        "userTier": "featured" if featured else "material",
        "quality": {"sharpness": sharp},
    }


def test_moment_pool_target_size_clamps() -> None:
    cfg = MomentConfig(pool_ratio=0.05, pool_min=1, pool_max=5)
    assert moment_pool_target_size(100, cfg) == 5
    assert moment_pool_target_size(20, cfg) == 1
    assert moment_pool_target_size(40, cfg) == 2


def test_build_moment_pool_excludes_cover() -> None:
    cfg = MomentConfig()
    trip = {"coverAssetId": "cover"}
    assets = [_asset("cover"), _asset("a1"), _asset("a2", featured=True)]
    pool = build_moment_pool(trip, assets, cfg=cfg)
    assert "cover" not in pool
    assert len(pool) >= 1


def test_preflight_writes_secondary_hints() -> None:
    cfg = MomentConfig()
    trip: dict = {}
    assets = [_asset(f"a{i}", featured=(i == 0)) for i in range(40)]
    pool = sync_trip_moments_preflight(trip, assets, cfg=cfg)
    assert len(pool) >= 2
    hints = (trip.get("curation") or {}).get("momentSecondaryHintIds") or []
    assert hints == pool[1:]


def test_finalize_skips_small_trip() -> None:
    cfg = MomentConfig(auto_disable_small_trip=True, small_trip_max_assets=15)
    trip: dict = {}
    assets = [_asset(f"a{i}") for i in range(10)]
    chapters = [{"screens": [{"slots": [{"assetId": "a0"}]}]}]
    result = sync_trip_moments_finalize(trip, assets, chapters, cfg=cfg)
    assert result is None
    assert trip.get("curation", {}).get("momentSkipped") == "small_trip"
    assert "momentAssetId" not in trip


def test_finalize_disabled_clears_moment() -> None:
    cfg = MomentConfig(enabled=False)
    trip: dict = {"momentAssetId": "old", "curation": {"momentPoolIds": ["old"]}}
    assets = [_asset(f"a{i}") for i in range(20)]
    chapters = [{"screens": [{"slots": [{"assetId": "a0"}]}]}]
    result = sync_trip_moments_finalize(trip, assets, chapters, cfg=cfg)
    assert result is None
    assert trip.get("curation", {}).get("momentSkipped") == "disabled"
    assert "momentAssetId" not in trip


def test_finalize_skips_cover_for_signature() -> None:
    cfg = MomentConfig(min_score=0.0, small_trip_elevated_min_score=0.0)
    trip: dict = {"coverAssetId": "cover"}
    assets = [_asset("cover", sharp=0.99)] + [_asset(f"a{i}", sharp=0.4 + i * 0.01) for i in range(20)]
    chapters = [{"screens": [{"slots": [{"assetId": "a5"}]}]}]
    result = sync_trip_moments_finalize(trip, assets, chapters, cfg=cfg)
    assert result
    assert result != "cover"
    assert trip["momentAssetId"] == result


def test_finalize_picks_signature_and_secondaries() -> None:
    cfg = MomentConfig(min_score=0.0, small_trip_elevated_min_score=0.0)
    trip: dict = {"coverAssetId": "cover"}
    assets = [_asset("cover")] + [_asset(f"a{i}", featured=(i == 1), sharp=0.5 + i * 0.05) for i in range(20)]
    chapters = [
        {
            "curation": {"patternHint": "peak"},
            "screens": [{"slots": [{"assetId": "a10"}]}],
        }
    ]
    result = sync_trip_moments_finalize(trip, assets, chapters, cfg=cfg)
    assert result
    assert trip["momentAssetId"] == result
    curation = trip["curation"]
    assert result in curation["momentPoolIds"]
    assert curation["momentSecondaryIds"] == [aid for aid in curation["momentPoolIds"] if aid != result]
    assert curation["momentPosition"] == "before_closing"


def test_score_ranked_moment_pool_uses_peak_score_order() -> None:
    from travelogue.curation.moment_scoring import score_ranked_moment_pool

    trip = {
        "curation": {"momentPoolIds": ["a1", "a2", "a3"]},
    }
    assets = [
        _asset("a1", sharp=0.5),
        _asset("a2", sharp=0.6),
        _asset("a3", sharp=0.9),
    ]
    ranked = score_ranked_moment_pool(trip, assets, [], top_n=3)
    assert ranked[0]["assetId"] == "a3"
    assert ranked[0]["score"] >= ranked[1]["score"] >= ranked[2]["score"]


def test_resolve_closing_excludes_moment_asset() -> None:
    from travelogue.render.cover_closing import resolve_closing_asset_id

    trip = {
        "chapters": [
            {"screens": [{"slots": [{"assetId": "moment"}]}, {"slots": [{"assetId": "last"}]}]},
        ]
    }
    assets = {
        "moment": _asset("moment"),
        "last": _asset("last"),
    }
    assert resolve_closing_asset_id(trip, assets, exclude_ids={"moment"}) == "last"


def test_moment_secondary_plan_bonus_peak_only() -> None:
    from travelogue.curation.layout_scoring import moment_secondary_plan_bonus

    screens = [{"slots": [{"assetId": "sec1"}]}]
    assert moment_secondary_plan_bonus(
        screens,
        arc_segment="peak",
        secondary_ids={"sec1"},
        boost=0.12,
    ) == 0.12
    assert moment_secondary_plan_bonus(
        screens,
        arc_segment="rise",
        secondary_ids={"sec1"},
        boost=0.12,
    ) == 0.0
    assert moment_secondary_plan_bonus(
        [{"slots": [{"assetId": "a"}]}, {"slots": [{"assetId": "sec1"}]}],
        arc_segment="peak",
        secondary_ids={"sec1"},
        boost=0.12,
    ) == 0.12


def test_featured_grid_excludes_moment_signature() -> None:
    from travelogue.curation.folio_plan import pick_featured_grid_asset_ids

    assets = [
        {**_asset(f"f{i}", featured=True), "width": 1200, "height": 1600}
        for i in range(6)
    ]
    assets[0]["id"] = "moment"
    ids = pick_featured_grid_asset_ids(assets, exclude_ids={"moment"})
    assert "moment" not in ids
    assert len(ids) >= 4
