"""Epilogue / 辑封 stats · displayedAssetIds + kept_n 同源（AC-FST-14）。"""

from __future__ import annotations

from travelogue.render.context import build_epilogue_stats


def test_epilogue_photo_count_uses_displayed_asset_ids():
    trip = {
        "assets": [
            {"id": "a1", "type": "image", "layoutEligible": True},
            {"id": "a2", "type": "image", "layoutEligible": True},
            {"id": "a3", "type": "image", "layoutEligible": True},
        ],
        "chapters": [],
        "curation": {"displayedAssetIds": ["a1", "a2"]},
    }
    stats = build_epilogue_stats(trip)
    assert stats["photoCount"] == 2


def test_epilogue_photo_count_uses_cull_summary_kept_n():
    """无 displayedAssetIds 时与 FirstSuccess / recipe kept_n 同源。"""
    trip = {
        "assets": [
            {"id": "a1", "type": "image", "layoutEligible": True},
            {"id": "a2", "type": "image", "layoutEligible": True},
            {"id": "a3", "type": "image", "layoutEligible": False},
        ],
        "chapters": [],
        "curation": {
            "cullSummary": {
                "finalLayoutEligibleCount": 7,
                "layoutEligibleCount": 9,
            }
        },
    }
    stats = build_epilogue_stats(trip)
    assert stats["photoCount"] == 7
    assert "7 张照片" in stats["summaryLine"]
