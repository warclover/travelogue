"""PA-T10 · Studio aesthetic explain payload tests."""

from __future__ import annotations

from travelogue.curation.aesthetic_score import compute_aesthetic
from travelogue.web.studio_aesthetic import (
    build_aesthetic_entry_summary,
    build_aesthetic_studio_payload,
    build_asset_aesthetic_studio_row,
    displayed_asset_ids,
)


def _asset(aid: str, **overrides) -> dict:
    base = {
        "id": aid,
        "type": "image",
        "displayFile": f"media/{aid}.webp",
        "quality": {
            "aesthetic": {
                "version": "pa-v0.1",
                "source": "rules",
                "overall": 0.55,
                "confidence": 0.7,
                "dims": {
                    "composition": 0.8,
                    "exposure": 0.5,
                    "color": 0.6,
                    "lighting": 0.4,
                    "subjectClarity": 0.7,
                },
                "signals": {},
                "critique": None,
            }
        },
    }
    base.update(overrides)
    return base


def test_displayed_asset_ids_follows_chapter_order():
    trip = {
        "chapters": [
            {
                "screens": [
                    {"slots": [{"assetId": "a1"}, {"assetId": "a2"}]},
                    {"slots": [{"assetId": "a1"}]},
                ]
            },
            {"screens": [{"slots": [{"assetId": "a3"}]}]},
        ]
    }
    assert displayed_asset_ids(trip) == ["a1", "a2", "a3"]


def test_build_asset_aesthetic_studio_row_includes_explain():
    row = build_asset_aesthetic_studio_row(_asset("x"))
    assert row is not None
    assert row["id"] == "x"
    assert len(row["explain"]) == 3
    assert row["explain"][0]["code"] == "composition"


def test_build_aesthetic_studio_payload_limits_to_displayed():
    trip = {
        "assets": [_asset("a1"), _asset("a2"), _asset("hidden")],
        "chapters": [{"screens": [{"slots": [{"assetId": "a1"}, {"assetId": "a2"}]}]}],
    }
    payload = build_aesthetic_studio_payload(trip, enabled=True)
    assert payload["enabled"] is True
    assert payload["scoredCount"] == 3
    assert [r["id"] for r in payload["assets"]] == ["a1", "a2"]


def test_build_aesthetic_studio_payload_single_asset_filter():
    trip = {"assets": [_asset("a1"), _asset("a2")], "chapters": []}
    payload = build_aesthetic_studio_payload(trip, asset_ids=["a2"], enabled=True)
    assert [r["id"] for r in payload["assets"]] == ["a2"]


def test_build_aesthetic_entry_summary_counts():
    trip = {
        "assets": [_asset("a1"), _asset("a2"), {"id": "v1", "type": "video"}],
        "chapters": [{"screens": [{"slots": [{"assetId": "a1"}]}]}],
    }
    summary = build_aesthetic_entry_summary(trip, enabled=True)
    assert summary["enabled"] is True
    assert summary["scoredCount"] == 2
    assert summary["displayedCount"] == 1
    assert summary["displayedScoredCount"] == 1


def test_build_aesthetic_studio_payload_fail_open_without_blocks():
    trip = {"assets": [{"id": "plain", "type": "image"}], "chapters": []}
    payload = build_aesthetic_studio_payload(trip, enabled=True)
    assert payload["assets"] == []


def test_real_compute_aesthetic_round_trips_through_studio_row():
    block = compute_aesthetic(
        {"id": "z", "quality": {"sharpness": 200.0}},
        signals={"dynamicRange": 0.6, "colorHarmony": 0.7, "balance": 0.5},
    )
    asset = {"id": "z", "type": "image", "quality": {"aesthetic": block}}
    row = build_asset_aesthetic_studio_row(asset)
    assert row is not None
    assert row["overall"] == block["overall"]
    assert len(row["explain"]) <= 3
