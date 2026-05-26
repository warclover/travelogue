"""Tests for draft inline copy patches."""

from __future__ import annotations

import copy

import pytest

from travelogue.web.copy_patch import CopyPatchError, apply_copy_patch, apply_copy_patches


def _sample_trip() -> dict:
    return {
        "meta": {"hook": "开场白"},
        "epilogue": "结语",
        "chapters": [
            {
                "id": "ch-01",
                "lead": "第一章导语",
                "items": [
                    {
                        "type": "media-card",
                        "assetId": "a1",
                        "title": "标题",
                        "caption": "图注",
                    },
                    {
                        "type": "media-row",
                        "assetIds": ["a2", "a3"],
                        "caption": "行图注",
                    },
                    {
                        "type": "media-scroll",
                        "assetIds": ["a4"],
                        "caption": "滑动画注",
                        "voice": {"transcript": "转写"},
                    },
                ],
            }
        ],
        "assets": [
            {
                "id": "a1",
                "voice": {"transcript": "语音转写"},
            }
        ],
        "pipeline": {"status": "copy_locked", "locks": {"copy": True}},
    }


def test_apply_hook_and_epilogue() -> None:
    trip = _sample_trip()
    apply_copy_patch(trip, "meta.hook", "新开场")
    apply_copy_patch(trip, "epilogue", "新结语")
    assert trip["meta"]["hook"] == "新开场"
    assert trip["epilogue"] == "新结语"
    assert trip["meta"]["edited"] is True


def test_apply_chapter_lead() -> None:
    trip = _sample_trip()
    apply_copy_patch(trip, "chapters.ch-01.lead", "新导语")
    assert trip["chapters"][0]["lead"] == "新导语"
    assert trip["chapters"][0]["edited"] is True


def test_apply_media_card_by_asset_id() -> None:
    trip = _sample_trip()
    apply_copy_patch(trip, "items.a1.title", "新标题")
    apply_copy_patch(trip, "items.a1.caption", "新图注")
    item = trip["chapters"][0]["items"][0]
    assert item["title"] == "新标题"
    assert item["caption"] == "新图注"


def test_apply_row_caption_by_item_index() -> None:
    trip = _sample_trip()
    apply_copy_patch(trip, "chapters.ch-01.items.1.caption", "新行图注")
    assert trip["chapters"][0]["items"][1]["caption"] == "新行图注"


def test_apply_scroll_voice_transcript() -> None:
    trip = _sample_trip()
    apply_copy_patch(trip, "chapters.ch-01.items.2.voice.transcript", "新转写")
    assert trip["chapters"][0]["items"][2]["voice"]["transcript"] == "新转写"


def test_apply_asset_voice_transcript() -> None:
    trip = _sample_trip()
    apply_copy_patch(trip, "assets.a1.voice.transcript", "新语音")
    assert trip["assets"][0]["voice"]["transcript"] == "新语音"


def test_patches_unlock_copy_locked() -> None:
    trip = _sample_trip()
    before = copy.deepcopy(trip)
    apply_copy_patches(trip, [{"path": "meta.hook", "value": "改"}])
    assert trip["pipeline"]["status"] == "copy_draft"
    assert trip["pipeline"]["locks"]["copy"] is False
    assert trip["updatedAt"]
    assert trip != before


def test_unknown_path_raises() -> None:
    trip = _sample_trip()
    with pytest.raises(CopyPatchError):
        apply_copy_patch(trip, "chapters.missing.lead", "x")
