"""Epilogue stats respect displayedAssetIds when set."""

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
