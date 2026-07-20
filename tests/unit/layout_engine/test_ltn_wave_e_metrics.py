"""LTN Wave E / R-E2 weekly dashboard metrics."""

from __future__ import annotations

from travelogue.layout_engine.mosaic.ltn_weekly import (
    compute_ltn_weekly_metrics,
    dense_quota_utilization,
    hero_mosaic_count,
    portrait3_after_failed_mcs5_rate,
    preserve_group_honor_rate,
    studio_reject_explain_rate,
    window_size_distribution,
)


def test_window_size_distribution_winner_plan_only():
    logs = [
        {"windowSize": 5, "isWinnerPlan": True},
        {"windowSize": 5, "isWinnerPlan": False},
        {"windowSize": 4, "isWinnerPlan": True},
        {"windowSize": 4},  # no flag → keep
    ]
    assert window_size_distribution(logs) == {"4": 2, "5": 1}


def test_hero_mosaic_count_dense_with_main():
    chapters = [
        {
            "screens": [
                {
                    "patternId": "screen-mosaic-5-main-portrait-3land",
                    "slots": [{"assetId": "a1", "role": "main"}],
                },
                {
                    "patternId": "screen-landscape-1",
                    "slots": [{"assetId": "a2", "role": "main"}],
                },
                {"patternId": "screen-breath-pause", "slots": []},
            ]
        }
    ]
    assert hero_mosaic_count(chapters) == 1


def test_studio_reject_explain_rate():
    logs = [
        {
            "isWinnerPlan": True,
            "fallbackUsed": True,
            "rejectedTemplates": [{"templateId": "x", "reason": "ar"}],
        },
        {"isWinnerPlan": True, "winnerPatternId": "screen-mosaic-5-main-portrait-3land"},
    ]
    assert studio_reject_explain_rate(logs) == 0.5


def test_preserve_group_honor_rate():
    chapters = [
        {
            "screens": [
                {
                    "patternId": "screen-mosaic-5-main-portrait-3land",
                    "preserveGroup": True,
                    "slots": [
                        {"assetId": "a1", "role": "main"},
                        {"assetId": "a2"},
                        {"assetId": "a3"},
                    ],
                },
                {
                    "patternId": "screen-mosaic-4-hero-70-sidebar",
                    "preserveGroup": False,
                    "slots": [
                        {"assetId": "b1", "role": "main"},
                        {"assetId": "b2"},
                    ],
                },
            ]
        }
    ]
    assert preserve_group_honor_rate(chapters) == 0.5


def test_portrait3_proxy_matches_shared_assets():
    chapters = [
        {
            "screens": [
                {
                    "patternId": "screen-portrait-3",
                    "slots": [{"assetId": "x1"}, {"assetId": "x2"}, {"assetId": "x3"}],
                }
            ]
        }
    ]
    logs = [
        {
            "isWinnerPlan": True,
            "windowSize": 5,
            "fallbackUsed": True,
            "assetIds": ["x1", "x2", "x3", "x4", "x5"],
        },
        {
            "isWinnerPlan": True,
            "windowSize": 5,
            "fallbackUsed": True,
            "assetIds": ["z1", "z2", "z3", "z4", "z5"],
        },
    ]
    assert portrait3_after_failed_mcs5_rate(chapters, logs) == 0.5


def test_dense_quota_utilization_curated_cap():
    chapters = [
        {
            "screens": [
                {"patternId": "screen-mosaic-5-main-portrait-3land", "slots": []},
            ]
        }
    ]
    # kept=40 → P21 max=1; with cap=2 still 1 → util=1.0
    assert dense_quota_utilization(chapters, trip_photo_total=40, dense_max_cap=2) == 1.0


def test_compute_ltn_weekly_metrics_bundle():
    trip = {
        "intent": {"mode": "curated"},
        "assets": [{"id": f"a{i}"} for i in range(30)],
        "chapters": [
            {
                "screens": [
                    {
                        "patternId": "screen-mosaic-5-main-portrait-3land",
                        "preserveGroup": True,
                        "slots": [
                            {"assetId": "a1", "role": "main"},
                            {"assetId": "a2"},
                            {"assetId": "a3"},
                            {"assetId": "a4"},
                            {"assetId": "a5"},
                        ],
                    }
                ]
            }
        ],
        "curation": {
            "mosaicDecisionLog": [
                {
                    "isWinnerPlan": True,
                    "windowSize": 5,
                    "winnerPatternId": "screen-mosaic-5-main-portrait-3land",
                    "rejectedTemplates": [{"templateId": "t", "reason": "score"}],
                }
            ]
        },
    }
    m = compute_ltn_weekly_metrics(trip)
    assert m["mosaicTrack"] == "curated"
    assert m["windowSizeDistribution"] == {"5": 1}
    assert m["heroMosaicCount"] == 1
    assert m["mosaic5ExposureRate"] == 1.0
    assert m["studioRejectExplainRate"] == 1.0
    assert m["preserveGroupHonorRate"] == 1.0
    assert m["crossSceneWindowRate"] is None or m["crossSceneWindowRate"] == 0.0
