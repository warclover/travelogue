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


def test_finalize_skips_journal_solo_inject_on_portfolio() -> None:
    cfg = MomentConfig(min_score=0.0, small_trip_elevated_min_score=0.0, pool_solo=True)
    trip: dict = {"studio": {"edition": "portfolio"}}
    assets = [_asset(f"a{i}", featured=(i < 3), sharp=0.9 - i * 0.01) for i in range(40)]
    chapters = [
        {
            "id": "ch-01",
            "screens": [
                {
                    "patternId": "page-1-hero-land-wide",
                    "screenId": "ch-01-sc-01",
                    "slots": [{"assetId": "a0"}],
                    "layoutGeometry": {"stageAspect": "16:9"},
                }
            ],
        },
        {
            "id": "ch-02",
            "screens": [
                {
                    "patternId": "page-1-hero-land-wide",
                    "screenId": "ch-02-sc-01",
                    "slots": [{"assetId": "a10"}],
                    "layoutGeometry": {"stageAspect": "16:9"},
                }
            ],
        },
    ]
    result = sync_trip_moments_finalize(trip, assets, chapters, cfg=cfg)
    assert result
    patterns = [sc.get("patternId") for ch in chapters for sc in (ch.get("screens") or [])]
    assert patterns == ["page-1-hero-land-wide", "page-1-hero-land-wide"]
    assert all(not sc.get("role") for ch in chapters for sc in (ch.get("screens") or []))


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
    assert curation["momentPosition"] == "inline"
    moment_screens = [s for s in chapters[0]["screens"] if s.get("role") == "moment"]
    assert len(moment_screens) == 1
    assert len(moment_screens[0]["slots"]) == 1
    moment_slots = [sl.get("assetId") for sl in moment_screens[0].get("slots") or []]
    assert result in moment_slots


def test_finalize_creates_peak_solo_screens_when_pool_has_secondaries() -> None:
    cfg = MomentConfig(min_score=0.0, small_trip_elevated_min_score=0.0, pool_min=2)
    trip: dict = {"coverAssetId": "cover"}
    assets = [_asset("cover", sharp=0.99)] + [
        _asset(f"a{i}", featured=(i == 1), sharp=0.5 + i * 0.02) for i in range(40)
    ]
    chapters = [
        {
            "curation": {"assetIds": [f"a{i}" for i in range(4)]},
            "screens": [
                {
                    "patternId": "screen-landscape-4",
                    "slots": [{"assetId": f"a{i}"} for i in range(4)],
                }
            ],
        }
    ]
    result = sync_trip_moments_finalize(trip, assets, chapters, cfg=cfg)
    assert result
    pool = trip["curation"]["momentPoolIds"]
    assert len(pool) >= 2
    peak_screens = [s for ch in chapters for s in ch["screens"] if s.get("role") == "peak"]
    moment_screens = [s for ch in chapters for s in ch["screens"] if s.get("role") == "moment"]
    assert len(moment_screens) == 1
    assert len(peak_screens) == len(pool) - 1
    peak_ids = {s["slots"][0]["assetId"] for s in peak_screens}
    assert peak_ids == set(trip["curation"]["momentSecondaryIds"])


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


def test_effective_secondary_boost_off_when_pool_solo() -> None:
    from travelogue.config.moment import effective_secondary_boost

    assert effective_secondary_boost(MomentConfig(pool_solo=True)) == 0.0
    assert effective_secondary_boost(MomentConfig(pool_solo=False, secondary_boost=0.12)) == 0.12
    assert effective_secondary_boost(MomentConfig(enabled=False)) == 0.0


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


def test_ensure_moment_asset_in_chapters_inserts_layout_screen() -> None:
    from travelogue.curation.moment_scoring import ensure_moment_asset_in_chapters

    chapters = [
        {
            "id": "ch-01",
            "curation": {"assetIds": ["a1", "sig", "a2"]},
            "screens": [{"slots": [{"assetId": "a1"}]}],
        }
    ]
    assets_by_id = {
        "a1": {"id": "a1", "width": 1600, "height": 900},
        "sig": {"id": "sig", "width": 1600, "height": 900},
    }
    assert ensure_moment_asset_in_chapters(
        chapters, "sig", assets_by_id=assets_by_id, arc_profile="dynamic"
    )
    roles = [s.get("role") for s in chapters[0]["screens"]]
    assert "moment" in roles
    moment_screen = next(s for s in chapters[0]["screens"] if s.get("role") == "moment")
    assert moment_screen["patternId"] == "screen-landscape-1"
    assert moment_screen["slots"][0]["assetId"] == "sig"
    assert len(moment_screen["slots"]) == 1


def test_ensure_pool_assets_solo_screens_splits_all_pool_members() -> None:
    from travelogue.curation.moment_scoring import ensure_pool_assets_solo_screens

    chapters = [
        {
            "id": "ch-01",
            "curation": {"assetIds": ["a1", "sig", "peak2"]},
            "screens": [
                {
                    "patternId": "screen-landscape-2",
                    "slots": [
                        {"assetId": "a1", "slot": 0},
                        {"assetId": "sig", "slot": 1},
                    ],
                }
            ],
        },
        {
            "id": "ch-02",
            "curation": {"assetIds": ["peak2", "a3"]},
            "screens": [
                {
                    "patternId": "screen-landscape-2",
                    "slots": [
                        {"assetId": "peak2", "slot": 0},
                        {"assetId": "a3", "slot": 1},
                    ],
                }
            ],
        },
    ]
    assets_by_id = {
        aid: {"id": aid, "type": "image", "width": 1600, "height": 900, "layoutEligible": True}
        for aid in ("a1", "sig", "peak2", "a3")
    }
    pool = ["sig", "peak2"]
    changed = ensure_pool_assets_solo_screens(
        chapters, pool, "sig", assets_by_id=assets_by_id, arc_profile="dynamic"
    )
    assert changed == 2
    moment_screens = [s for ch in chapters for s in ch["screens"] if s.get("role") == "moment"]
    peak_screens = [s for ch in chapters for s in ch["screens"] if s.get("role") == "peak"]
    assert len(moment_screens) == 1
    assert len(peak_screens) == 1
    assert moment_screens[0]["slots"][0]["assetId"] == "sig"
    assert peak_screens[0]["slots"][0]["assetId"] == "peak2"
    all_solo_ids = [
        s["slots"][0]["assetId"]
        for ch in chapters
        for s in ch["screens"]
        if s.get("role") in ("moment", "peak") and len(s.get("slots") or []) == 1
    ]
    assert sorted(all_solo_ids) == ["peak2", "sig"]
    mosaic_slots = [
        sl["assetId"]
        for ch in chapters
        for s in ch["screens"]
        if s.get("role") not in ("moment", "peak")
        for sl in s.get("slots") or []
    ]
    assert "sig" not in mosaic_slots
    assert "peak2" not in mosaic_slots


def test_extract_moment_from_portrait_triple_to_portrait_pair() -> None:
    from travelogue.curation.moment_scoring import ensure_pool_assets_solo_screens

    chapters = [
        {
            "id": "ch-01",
            "screens": [
                {
                    "patternId": "screen-portrait-3",
                    "slots": [
                        {"assetId": "p1", "slot": 0},
                        {"assetId": "peak", "slot": 1},
                        {"assetId": "p2", "slot": 2},
                    ],
                }
            ],
        }
    ]
    assets_by_id = {
        aid: {
            "id": aid,
            "type": "image",
            "width": 900,
            "height": 1600,
            "layoutEligible": True,
        }
        for aid in ("p1", "peak", "p2", "sig")
    }
    assets_by_id["sig"] = {
        "id": "sig",
        "type": "image",
        "width": 1600,
        "height": 900,
        "layoutEligible": True,
    }
    ensure_pool_assets_solo_screens(
        chapters, ["sig", "peak"], "sig", assets_by_id=assets_by_id
    )
    host_screens = [
        s for s in chapters[0]["screens"] if s.get("role") not in ("peak", "moment")
    ]
    assert len(host_screens) == 1
    assert host_screens[0]["patternId"] == "screen-portrait-2"
    assert [sl["assetId"] for sl in host_screens[0]["slots"]] == ["p1", "p2"]


def test_extract_peak_from_mosaic_six_decomposes_without_empty_slot() -> None:
    from travelogue.curation.moment_scoring import ensure_pool_assets_solo_screens

    chapters = [
        {
            "id": "ch-02",
            "screens": [
                {
                    "patternId": "screen-mosaic-6-main-hero-plus-5",
                    "slots": [
                        {"assetId": "main", "slot": 0, "role": "main"},
                        {"assetId": "side1", "slot": 1, "role": "portrait"},
                        {"assetId": "side2", "slot": 2, "role": "portrait"},
                        {"assetId": "bot1", "slot": 3, "role": "landscape"},
                        {"assetId": "bot2", "slot": 4, "role": "landscape"},
                        {"assetId": "peak", "slot": 5, "role": "landscape"},
                    ],
                }
            ],
        }
    ]
    assets_by_id = {
        "main": {"id": "main", "width": 3200, "height": 1800, "layoutEligible": True},
        "side1": {"id": "side1", "width": 3200, "height": 4480, "layoutEligible": True},
        "side2": {"id": "side2", "width": 3200, "height": 4480, "layoutEligible": True},
        "bot1": {"id": "bot1", "width": 3200, "height": 2070, "layoutEligible": True},
        "bot2": {"id": "bot2", "width": 3200, "height": 1800, "layoutEligible": True},
        "peak": {"id": "peak", "width": 3200, "height": 1800, "layoutEligible": True},
        "sig": {"id": "sig", "width": 3200, "height": 1800, "layoutEligible": True},
    }
    ensure_pool_assets_solo_screens(
        chapters, ["sig", "peak"], "sig", assets_by_id=assets_by_id
    )
    peak_screens = [s for s in chapters[0]["screens"] if s.get("role") == "peak"]
    assert len(peak_screens) == 1
    assert peak_screens[0]["slots"][0]["assetId"] == "peak"
    remainder = [
        s
        for s in chapters[0]["screens"]
        if s.get("role") not in ("peak", "moment")
    ]
    assert all("mosaic-6" not in str(s.get("patternId") or "") for s in remainder)
    remainder_ids = [
        sl["assetId"] for s in remainder for sl in s.get("slots") or []
    ]
    assert sorted(remainder_ids) == sorted(["main", "side1", "side2", "bot1", "bot2"])
    assert len(remainder_ids) == 5


def test_extract_moment_from_mosaic_to_solo_screen() -> None:
    from travelogue.curation.moment_scoring import ensure_moment_asset_in_chapters

    chapters = [
        {
            "id": "ch-01",
            "screens": [
                {
                    "patternId": "screen-landscape-4",
                    "slots": [
                        {"assetId": "a1", "slot": 0, "fit": "cover"},
                        {"assetId": "sig", "slot": 1, "fit": "cover"},
                        {"assetId": "a2", "slot": 2, "fit": "cover"},
                        {"assetId": "a3", "slot": 3, "fit": "cover"},
                    ],
                }
            ],
        }
    ]
    assets_by_id = {
        aid: {"id": aid, "type": "image", "width": 1600, "height": 900, "layoutEligible": True}
        for aid in ("a1", "sig", "a2", "a3")
    }
    assert ensure_moment_asset_in_chapters(chapters, "sig", assets_by_id=assets_by_id)
    moment_screens = [s for ch in chapters for s in ch["screens"] if s.get("role") == "moment"]
    assert len(moment_screens) == 1
    assert len(moment_screens[0]["slots"]) == 1
    assert moment_screens[0]["slots"][0]["assetId"] == "sig"
    host_screens = [s for s in chapters[0]["screens"] if s.get("role") != "moment"]
    assert len(host_screens) == 1
    assert "sig" not in [sl["assetId"] for sl in host_screens[0]["slots"]]
    assert len(host_screens[0]["slots"]) == 3
    assert host_screens[0]["patternId"] == "screen-landscape-3"


def test_peak_on_plate_moves_solo_after_first_screen() -> None:
    from travelogue.curation.moment_scoring import ensure_pool_assets_solo_screens

    chapters = [
        {
            "id": "ch-01",
            "curation": {"assetIds": ["peak2", "sig"]},
            "screens": [
                {"slots": [{"assetId": "peak2"}]},
                {"slots": [{"assetId": "sig"}]},
            ],
        }
    ]
    assets_by_id = {
        aid: {"id": aid, "type": "image", "width": 1600, "height": 900, "layoutEligible": True}
        for aid in ("peak2", "sig")
    }
    ensure_pool_assets_solo_screens(
        chapters, ["sig", "peak2"], "sig", assets_by_id=assets_by_id
    )
    first_screen = chapters[0]["screens"][0]
    assert first_screen["slots"][0]["assetId"] == "sig"
    peak_screens = [s for s in chapters[0]["screens"] if s.get("role") == "peak"]
    assert len(peak_screens) == 1
    assert peak_screens[0]["slots"][0]["assetId"] == "peak2"
    assert chapters[0]["screens"].index(peak_screens[0]) > 0


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


def _portrait_asset(aid: str, *, taken_at: str = "") -> dict:
    out = {
        "id": aid,
        "type": "image",
        "width": 900,
        "height": 1600,
        "layoutEligible": True,
    }
    if taken_at:
        out["takenAt"] = taken_at
    return out


def test_hppl_secondary_portraits_prefer_triple() -> None:
    from travelogue.config.moment import MomentConfig
    from travelogue.curation.moment_scoring import ensure_pool_assets_solo_screens

    chapters = [
        {
            "id": "ch-01",
            "curation": {"assetIds": ["sig", "p1", "p2", "p3", "filler"]},
            "screens": [
                {"patternId": "screen-landscape-1", "slots": [{"assetId": "filler", "slot": 0}]},
                {
                    "patternId": "screen-portrait-3",
                    "slots": [
                        {"assetId": "p1", "slot": 0},
                        {"assetId": "p2", "slot": 1},
                        {"assetId": "p3", "slot": 2},
                    ],
                },
            ],
        }
    ]
    assets_by_id = {
        "sig": {
            "id": "sig",
            "type": "image",
            "width": 1600,
            "height": 900,
            "layoutEligible": True,
        },
        "filler": {
            "id": "filler",
            "type": "image",
            "width": 1600,
            "height": 900,
            "layoutEligible": True,
        },
        "p1": _portrait_asset("p1", taken_at="2024-01-01T10:00:00"),
        "p2": _portrait_asset("p2", taken_at="2024-01-01T10:05:00"),
        "p3": _portrait_asset("p3", taken_at="2024-01-01T10:10:00"),
    }
    ensure_pool_assets_solo_screens(
        chapters,
        ["sig", "p1", "p2", "p3"],
        "sig",
        assets_by_id=assets_by_id,
        cfg=MomentConfig(pool_portrait_collage=True),
    )
    moment_screens = [s for s in chapters[0]["screens"] if s.get("role") == "moment"]
    peak_screens = [s for s in chapters[0]["screens"] if s.get("role") == "peak"]
    assert len(moment_screens) == 1
    assert len(moment_screens[0]["slots"]) == 1
    assert moment_screens[0]["slots"][0]["assetId"] == "sig"
    assert len(peak_screens) == 1
    assert peak_screens[0]["patternId"] == "screen-portrait-3"
    assert [sl["assetId"] for sl in peak_screens[0]["slots"]] == ["p1", "p2", "p3"]


def test_hppl_secondary_two_portraits_pair() -> None:
    from travelogue.config.moment import MomentConfig
    from travelogue.curation.moment_scoring import ensure_pool_assets_solo_screens

    chapters = [
        {
            "id": "ch-01",
            "curation": {"assetIds": ["sig", "p1", "p2"]},
            "screens": [
                {"patternId": "screen-portrait-1", "slots": [{"assetId": "p1", "slot": 0}]},
                {"patternId": "screen-portrait-1", "slots": [{"assetId": "p2", "slot": 0}]},
            ],
        }
    ]
    assets_by_id = {
        "sig": {
            "id": "sig",
            "type": "image",
            "width": 1600,
            "height": 900,
            "layoutEligible": True,
        },
        "p1": _portrait_asset("p1"),
        "p2": _portrait_asset("p2"),
    }
    ensure_pool_assets_solo_screens(
        chapters,
        ["sig", "p1", "p2"],
        "sig",
        assets_by_id=assets_by_id,
        cfg=MomentConfig(pool_portrait_collage=True),
    )
    peak_screens = [s for s in chapters[0]["screens"] if s.get("role") == "peak"]
    assert len(peak_screens) == 1
    assert peak_screens[0]["patternId"] == "screen-portrait-2"
    assert len(peak_screens[0]["slots"]) == 2


def test_hppl_no_cross_chapter_collage() -> None:
    from travelogue.config.moment import MomentConfig
    from travelogue.curation.moment_scoring import ensure_pool_assets_solo_screens

    chapters = [
        {
            "id": "ch-01",
            "curation": {"assetIds": ["sig", "p1", "p2"]},
            "screens": [
                {"patternId": "screen-portrait-1", "slots": [{"assetId": "p1", "slot": 0}]},
                {"patternId": "screen-portrait-1", "slots": [{"assetId": "p2", "slot": 0}]},
            ],
        },
        {
            "id": "ch-02",
            "curation": {"assetIds": ["p3", "p4"]},
            "screens": [
                {"patternId": "screen-portrait-1", "slots": [{"assetId": "p3", "slot": 0}]},
                {"patternId": "screen-portrait-1", "slots": [{"assetId": "p4", "slot": 0}]},
            ],
        },
    ]
    assets_by_id = {
        "sig": {
            "id": "sig",
            "type": "image",
            "width": 1600,
            "height": 900,
            "layoutEligible": True,
        },
        **{aid: _portrait_asset(aid) for aid in ("p1", "p2", "p3", "p4")},
    }
    ensure_pool_assets_solo_screens(
        chapters,
        ["sig", "p1", "p2", "p3", "p4"],
        "sig",
        assets_by_id=assets_by_id,
        cfg=MomentConfig(pool_portrait_collage=True),
    )
    peaks_ch1 = [s for s in chapters[0]["screens"] if s.get("role") == "peak"]
    peaks_ch2 = [s for s in chapters[1]["screens"] if s.get("role") == "peak"]
    assert len(peaks_ch1) == 1 and peaks_ch1[0]["patternId"] == "screen-portrait-2"
    assert len(peaks_ch2) == 1 and peaks_ch2[0]["patternId"] == "screen-portrait-2"
    assert "p3" not in [sl["assetId"] for sl in peaks_ch1[0]["slots"]]


def test_hppl_off_keeps_all_solo() -> None:
    from travelogue.config.moment import MomentConfig
    from travelogue.curation.moment_scoring import ensure_pool_assets_solo_screens

    chapters = [
        {
            "id": "ch-01",
            "curation": {"assetIds": ["sig", "p1", "p2", "p3"]},
            "screens": [
                {
                    "patternId": "screen-portrait-3",
                    "slots": [
                        {"assetId": "p1", "slot": 0},
                        {"assetId": "p2", "slot": 1},
                        {"assetId": "p3", "slot": 2},
                    ],
                }
            ],
        }
    ]
    assets_by_id = {
        "sig": {
            "id": "sig",
            "type": "image",
            "width": 1600,
            "height": 900,
            "layoutEligible": True,
        },
        **{aid: _portrait_asset(aid) for aid in ("p1", "p2", "p3")},
    }
    ensure_pool_assets_solo_screens(
        chapters,
        ["sig", "p1", "p2", "p3"],
        "sig",
        assets_by_id=assets_by_id,
        cfg=MomentConfig(pool_portrait_collage=False),
    )
    peak_screens = [s for s in chapters[0]["screens"] if s.get("role") == "peak"]
    assert len(peak_screens) == 3
    assert all(len(s.get("slots") or []) == 1 for s in peak_screens)


def test_hppl_signature_never_in_collage() -> None:
    from travelogue.config.moment import MomentConfig
    from travelogue.curation.moment_scoring import ensure_pool_assets_solo_screens

    chapters = [
        {
            "id": "ch-01",
            "curation": {"assetIds": ["sig", "p1", "p2"]},
            "screens": [
                {
                    "patternId": "screen-portrait-3",
                    "slots": [
                        {"assetId": "sig", "slot": 0},
                        {"assetId": "p1", "slot": 1},
                        {"assetId": "p2", "slot": 2},
                    ],
                }
            ],
        }
    ]
    assets_by_id = {
        "sig": _portrait_asset("sig"),
        "p1": _portrait_asset("p1"),
        "p2": _portrait_asset("p2"),
    }
    ensure_pool_assets_solo_screens(
        chapters,
        ["sig", "p1", "p2"],
        "sig",
        assets_by_id=assets_by_id,
        cfg=MomentConfig(pool_portrait_collage=True),
    )
    moment_screens = [s for s in chapters[0]["screens"] if s.get("role") == "moment"]
    peak_screens = [s for s in chapters[0]["screens"] if s.get("role") == "peak"]
    assert len(moment_screens) == 1
    assert len(moment_screens[0]["slots"]) == 1
    assert moment_screens[0]["slots"][0]["assetId"] == "sig"
    assert all(
        "sig" not in [sl["assetId"] for sl in s.get("slots") or []]
        for s in peak_screens
    )


def test_moment_config_pool_portrait_collage_defaults_on() -> None:
    from travelogue.config.moment import MomentConfig, moment_config_from_dict

    assert MomentConfig().pool_portrait_collage is True
    assert moment_config_from_dict({}).pool_portrait_collage is True
    assert moment_config_from_dict({"pool_portrait_collage": False}).pool_portrait_collage is False


def test_hppl_single_secondary_portrait_solo() -> None:
    from travelogue.config.moment import MomentConfig
    from travelogue.curation.moment_scoring import ensure_pool_assets_solo_screens

    chapters = [
        {
            "id": "ch-01",
            "curation": {"assetIds": ["sig", "p1"]},
            "screens": [
                {"patternId": "screen-portrait-1", "slots": [{"assetId": "p1", "slot": 0}]},
            ],
        }
    ]
    assets_by_id = {
        "sig": {
            "id": "sig",
            "type": "image",
            "width": 1600,
            "height": 900,
            "layoutEligible": True,
        },
        "p1": _portrait_asset("p1"),
    }
    ensure_pool_assets_solo_screens(
        chapters,
        ["sig", "p1"],
        "sig",
        assets_by_id=assets_by_id,
        cfg=MomentConfig(pool_portrait_collage=True),
    )
    peaks = [s for s in chapters[0]["screens"] if s.get("role") == "peak"]
    assert len(peaks) == 1
    assert peaks[0]["patternId"] == "screen-portrait-1"
    assert len(peaks[0]["slots"]) == 1


def test_hppl_landscape_secondary_stays_solo() -> None:
    from travelogue.config.moment import MomentConfig
    from travelogue.curation.moment_scoring import ensure_pool_assets_solo_screens

    chapters = [
        {
            "id": "ch-01",
            "curation": {"assetIds": ["sig", "l1", "l2"]},
            "screens": [
                {
                    "patternId": "screen-landscape-2",
                    "slots": [
                        {"assetId": "l1", "slot": 0},
                        {"assetId": "l2", "slot": 1},
                    ],
                }
            ],
        }
    ]
    assets_by_id = {
        aid: {
            "id": aid,
            "type": "image",
            "width": 1600,
            "height": 900,
            "layoutEligible": True,
        }
        for aid in ("sig", "l1", "l2")
    }
    ensure_pool_assets_solo_screens(
        chapters,
        ["sig", "l1", "l2"],
        "sig",
        assets_by_id=assets_by_id,
        cfg=MomentConfig(pool_portrait_collage=True),
    )
    peaks = [s for s in chapters[0]["screens"] if s.get("role") == "peak"]
    assert len(peaks) == 2
    assert all(s["patternId"] == "screen-landscape-1" for s in peaks)
    assert all(len(s.get("slots") or []) == 1 for s in peaks)


def test_hppl_highlight_screens_not_adjacent() -> None:
    from travelogue.config.moment import MomentConfig
    from travelogue.curation.moment_scoring import ensure_pool_assets_solo_screens

    chapters = [
        {
            "id": "ch-01",
            "curation": {"assetIds": ["sig", "p1", "p2", "a", "b", "c", "d"]},
            "screens": [
                {"patternId": "screen-landscape-1", "slots": [{"assetId": "a", "slot": 0}]},
                {"patternId": "screen-landscape-1", "slots": [{"assetId": "b", "slot": 0}]},
                {"patternId": "screen-landscape-1", "slots": [{"assetId": "c", "slot": 0}]},
                {"patternId": "screen-landscape-1", "slots": [{"assetId": "d", "slot": 0}]},
                {"patternId": "screen-portrait-1", "slots": [{"assetId": "p1", "slot": 0}]},
                {"patternId": "screen-portrait-1", "slots": [{"assetId": "p2", "slot": 0}]},
            ],
        }
    ]
    assets_by_id = {
        "sig": {
            "id": "sig",
            "type": "image",
            "width": 1600,
            "height": 900,
            "layoutEligible": True,
        },
        **{
            aid: {
                "id": aid,
                "type": "image",
                "width": 1600,
                "height": 900,
                "layoutEligible": True,
            }
            for aid in ("a", "b", "c", "d")
        },
        "p1": _portrait_asset("p1"),
        "p2": _portrait_asset("p2"),
    }
    ensure_pool_assets_solo_screens(
        chapters,
        ["sig", "p1", "p2"],
        "sig",
        assets_by_id=assets_by_id,
        cfg=MomentConfig(pool_portrait_collage=True),
    )
    roles = [str(s.get("role") or "") for s in chapters[0]["screens"]]
    for i in range(len(roles) - 1):
        if roles[i] in ("moment", "peak") and roles[i + 1] in ("moment", "peak"):
            raise AssertionError(f"adjacent highlight screens at {i}: {roles}")


def test_hppl_pool_solo_false_skips_collage() -> None:
    from travelogue.config.moment import MomentConfig
    from travelogue.curation.moment_scoring import ensure_pool_assets_solo_screens

    chapters = [
        {
            "id": "ch-01",
            "curation": {"assetIds": ["sig", "p1", "p2", "p3"]},
            "screens": [
                {
                    "patternId": "screen-portrait-3",
                    "slots": [
                        {"assetId": "p1", "slot": 0},
                        {"assetId": "p2", "slot": 1},
                        {"assetId": "p3", "slot": 2},
                    ],
                }
            ],
        }
    ]
    assets_by_id = {
        "sig": {
            "id": "sig",
            "type": "image",
            "width": 1600,
            "height": 900,
            "layoutEligible": True,
        },
        **{aid: _portrait_asset(aid) for aid in ("p1", "p2", "p3")},
    }
    # pool_solo=false → collage must not run even if pool_portrait_collage=true
    ensure_pool_assets_solo_screens(
        chapters,
        ["sig", "p1", "p2", "p3"],
        "sig",
        assets_by_id=assets_by_id,
        cfg=MomentConfig(pool_solo=False, pool_portrait_collage=True),
    )
    # Signature still solo; secondaries follow non-collage path (each solo peak)
    moment_screens = [s for s in chapters[0]["screens"] if s.get("role") == "moment"]
    peak_screens = [s for s in chapters[0]["screens"] if s.get("role") == "peak"]
    assert len(moment_screens) == 1
    assert len(peak_screens) == 3
    assert all(len(s.get("slots") or []) == 1 for s in peak_screens)


def test_hppl_degrades_pair_when_pair_streak_maxed() -> None:
    from travelogue.config.moment import MomentConfig
    from travelogue.curation.moment_scoring import (
        ensure_pool_assets_solo_screens,
        get_hppl_last_stats,
    )

    chapters = [
        {
            "id": "ch-01",
            "curation": {"assetIds": ["sig", "p1", "p2", "x1", "x2", "x3", "x4"]},
            "screens": [
                {
                    "patternId": "screen-portrait-2",
                    "slots": [
                        {"assetId": "x1", "slot": 0},
                        {"assetId": "x2", "slot": 1},
                    ],
                },
                {
                    "patternId": "screen-portrait-2",
                    "slots": [
                        {"assetId": "x3", "slot": 0},
                        {"assetId": "x4", "slot": 1},
                    ],
                },
                {"patternId": "screen-portrait-1", "slots": [{"assetId": "p1", "slot": 0}]},
                {"patternId": "screen-portrait-1", "slots": [{"assetId": "p2", "slot": 0}]},
            ],
        }
    ]
    assets_by_id = {
        "sig": {
            "id": "sig",
            "type": "image",
            "width": 1600,
            "height": 900,
            "layoutEligible": True,
        },
        **{aid: _portrait_asset(aid) for aid in ("p1", "p2", "x1", "x2", "x3", "x4")},
    }
    ensure_pool_assets_solo_screens(
        chapters,
        ["sig", "p1", "p2"],
        "sig",
        assets_by_id=assets_by_id,
        cfg=MomentConfig(pool_portrait_collage=True),
    )
    peak_screens = [s for s in chapters[0]["screens"] if s.get("role") == "peak"]
    # Either nudged away from the pair streak wall, or degraded to solos.
    multi = [s for s in peak_screens if len(s.get("slots") or []) > 1]
    if multi:
        # If a pair remains, it must not sit immediately after two portrait-2 screens
        idx = chapters[0]["screens"].index(multi[0])
        prev_pids = [
            str(chapters[0]["screens"][i].get("patternId") or "")
            for i in range(max(0, idx - 2), idx)
        ]
        assert not (
            len(prev_pids) == 2
            and all(p == "screen-portrait-2" for p in prev_pids)
        )
    else:
        assert len(peak_screens) == 2
        assert get_hppl_last_stats().get("collage_fallback", 0) >= 1
