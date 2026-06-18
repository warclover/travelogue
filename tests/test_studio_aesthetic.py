"""PA-T10 · Studio aesthetic explain payload tests."""

from __future__ import annotations

from travelogue.curation.aesthetic_score import compute_aesthetic
from travelogue.curation.algorithm_profile import write_curate_profile
from travelogue.web.studio_aesthetic import (
    build_aesthetic_entry_summary,
    build_aesthetic_studio_payload,
    build_album_profile_studio_summary,
    build_asset_aesthetic_studio_row,
    build_stratum_preference_studio_summary,
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
    assert row["stratum"] == "general"
    assert "purposes" in row
    assert "cover" in row["purposes"]


def test_build_asset_aesthetic_studio_row_includes_mllm_and_critique():
    asset = _asset(
        "m",
        quality={
            "aesthetic": {
                "version": "pa-v0.1",
                "source": "rules+ml",
                "overall": 0.62,
                "confidence": 0.7,
                "dims": {
                    "composition": 0.8,
                    "exposure": 0.5,
                    "color": 0.6,
                    "lighting": 0.4,
                    "subjectClarity": 0.7,
                },
                "signals": {"mllmScore": 0.71},
                "critique": "光线柔和，主体清晰",
            }
        },
        tags=["person", "face"],
    )
    row = build_asset_aesthetic_studio_row(asset)
    assert row is not None
    assert row["mllmScore"] == 0.71
    assert row["critique"] == "光线柔和，主体清晰"
    assert row["stratum"] == "person"


def test_build_aesthetic_studio_payload_limits_to_displayed():
    trip = {
        "assets": [_asset("a1"), _asset("a2"), _asset("hidden")],
        "chapters": [{"screens": [{"slots": [{"assetId": "a1"}, {"assetId": "a2"}]}]}],
        "curation": {
            "albumProfile": {
                "version": "1",
                "eligibleImages": 3,
                "strata": {"general": 1.0},
                "dominantStratum": "general",
                "isSkewed": True,
            }
        },
    }
    payload = build_aesthetic_studio_payload(trip, enabled=True)
    assert payload["enabled"] is True
    assert payload["scoredCount"] == 3
    assert [r["id"] for r in payload["assets"]] == ["a1", "a2"]
    assert payload["albumProfile"]["dominantStratum"] == "general"
    assert payload["purposeLabels"]["cover"] == "封面"


def test_build_aesthetic_studio_payload_single_asset_filter():
    trip = {"assets": [_asset("a1"), _asset("a2")], "chapters": []}
    payload = build_aesthetic_studio_payload(trip, asset_ids=["a2"], enabled=True)
    assert [r["id"] for r in payload["assets"]] == ["a2"]


def test_build_aesthetic_entry_summary_counts():
    trip = {
        "assets": [_asset("a1"), _asset("a2"), {"id": "v1", "type": "video"}],
        "chapters": [{"screens": [{"slots": [{"assetId": "a1"}]}]}],
    }
    write_curate_profile(trip)
    summary = build_aesthetic_entry_summary(trip, enabled=True)
    assert summary["enabled"] is True
    assert summary["scoredCount"] == 2
    assert summary["displayedCount"] == 1
    assert summary["displayedScoredCount"] == 1
    assert summary["stale"] is False
    assert summary["staleHint"] is None
    assert summary["albumProfile"]["dominantStratum"] == "general"


def test_build_album_profile_studio_summary_labels():
    trip = {
        "assets": [
            _asset("p1", tags=["person", "face"]),
            _asset("l1", tags=["landscape"]),
        ],
        "chapters": [],
    }
    summary = build_album_profile_studio_summary(trip)
    assert summary["dominantStratum"] in ("person", "general", "landscape")
    assert "strataPct" in summary


def test_build_stratum_preference_studio_summary():
    trip = {"curation": {"stratumPreference": "landscape"}}
    summary = build_stratum_preference_studio_summary(trip)
    assert summary["value"] == "landscape"
    assert summary["label"] == "更偏风景"
    assert len(summary["options"]) == 3


def test_build_aesthetic_studio_payload_includes_stratum_preference():
    trip = {"assets": [_asset("a1")], "chapters": []}
    payload = build_aesthetic_studio_payload(trip, enabled=True)
    assert payload["stratumPreference"]["value"] == "auto"
    assert "selectionHint" in payload["stratumPreference"]


def test_build_aesthetic_entry_summary_flags_stale_trip():
    trip = {
        "assets": [{"id": "plain", "type": "image"}],
        "chapters": [],
    }
    summary = build_aesthetic_entry_summary(trip, enabled=True)
    assert summary["stale"] is True
    assert summary["staleHint"]
    payload = build_aesthetic_studio_payload(trip, enabled=True)
    assert payload["stale"] is True
    assert summary["staleHint"]
    assert payload["staleHint"]


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
