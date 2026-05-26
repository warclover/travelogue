"""Tests for per-asset caption helpers."""

from __future__ import annotations

from travelogue.curation.asset_caption import (
    apply_caption_to_trip,
    migrate_captions_to_assets,
    resolve_caption,
)
from travelogue.web.copy_patch import apply_copy_patch


def test_resolve_caption_prefers_item() -> None:
    item = {"caption": "item"}
    asset = {"caption": "asset"}
    assert resolve_caption(item, asset) == "item"


def test_migrate_captions_to_assets() -> None:
    trip = {
        "assets": [{"id": "a1"}, {"id": "a2"}],
        "chapters": [
            {
                "items": [
                    {"type": "media-card", "assetId": "a1", "caption": "图一"},
                    {"type": "media-card", "assetId": "a2", "caption": "图二"},
                ]
            }
        ],
    }
    migrated = migrate_captions_to_assets(trip)
    assert migrated == ["a1", "a2"]
    assert trip["assets"][0]["caption"] == "图一"
    assert trip["assets"][1]["caption"] == "图二"


def test_apply_caption_to_trip_writes_asset_and_item() -> None:
    trip = {
        "assets": [{"id": "a1"}],
        "chapters": [
            {
                "id": "ch-01",
                "items": [{"type": "media-card", "assetId": "a1"}],
            }
        ],
    }
    labels = apply_caption_to_trip(trip, "a1", "新图注")
    assert "assets.a1.caption" in labels
    assert trip["assets"][0]["caption"] == "新图注"
    assert trip["chapters"][0]["items"][0]["caption"] == "新图注"


def test_empty_caption_sets_skip_caption() -> None:
    from travelogue.curation.asset_caption import apply_caption_to_trip, resolve_caption

    trip = {
        "assets": [{"id": "a1", "caption": "旧"}],
        "chapters": [{"id": "ch-01", "items": [{"type": "media-card", "assetId": "a1", "caption": "旧"}]}],
    }
    apply_caption_to_trip(trip, "a1", "")
    assert trip["assets"][0].get("skipCaption") is True
    assert "caption" not in trip["assets"][0]
    assert resolve_caption(trip["chapters"][0]["items"][0], trip["assets"][0]) == ""


def test_copy_patch_assets_caption_roundtrip() -> None:
    trip = {"assets": [{"id": "a1"}], "chapters": []}
    apply_copy_patch(trip, "assets.a1.caption", "保存图注")
    assert trip["assets"][0]["caption"] == "保存图注"
