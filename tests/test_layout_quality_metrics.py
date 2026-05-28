"""Unit tests for layout quality metrics (I-G1 / I-G2 / AC-P3-C09)."""

from __future__ import annotations

from travelogue.curation.layout_metrics import (
    aspect_pattern_match_rate,
    asset_order_from_chapters,
    burst_integrity_violations,
    subject_run_score,
    time_inversion_rate,
)


def test_time_inversion_rate_zero_when_monotonic() -> None:
    chapters = [
        {
            "screens": [
                {"slots": [{"assetId": "a1"}]},
                {"slots": [{"assetId": "a2"}]},
            ]
        }
    ]
    assets = {
        "a1": {"id": "a1", "takenAt": "2025-01-01T10:00:00Z"},
        "a2": {"id": "a2", "takenAt": "2025-01-01T11:00:00Z"},
    }
    assert time_inversion_rate(chapters, assets) == 0.0


def test_time_inversion_rate_detects_swap() -> None:
    chapters = [{"screens": [{"slots": [{"assetId": "a2"}]}, {"slots": [{"assetId": "a1"}]}]}]
    assets = {
        "a1": {"id": "a1", "takenAt": "2025-01-01T10:00:00Z"},
        "a2": {"id": "a2", "takenAt": "2025-01-01T11:00:00Z"},
    }
    assert time_inversion_rate(chapters, assets) == 1.0


def test_burst_integrity_violations_counts_split_group() -> None:
    chapters = [
        {
            "screens": [
                {"slots": [{"assetId": "a1"}]},
                {"slots": [{"assetId": "a2"}]},
            ]
        }
    ]
    assets = {
        "a1": {"id": "a1", "burstGroupId": "b1"},
        "a2": {"id": "a2", "burstGroupId": "b1"},
    }
    assert burst_integrity_violations(chapters, assets) == 1


def test_subject_run_score_honors_subject_bucket() -> None:
    chapters = [
        {
            "screens": [
                {"slots": [{"assetId": "f1"}]},
                {"slots": [{"assetId": "f2"}]},
                {"slots": [{"assetId": "f3"}]},
            ]
        }
    ]
    assets = {
        "f1": {"id": "f1", "subjectBucket": "food"},
        "f2": {"id": "f2", "subjectBucket": "food"},
        "f3": {"id": "f3", "subjectBucket": "food"},
    }
    assert subject_run_score(chapters, assets) >= 0.99


def test_asset_order_from_chapters_preserves_reading_order() -> None:
    chapters = [
        {"screens": [{"slots": [{"assetId": "x"}, {"assetId": "y"}]}]},
        {"screens": [{"slots": [{"assetId": "z"}]}]},
    ]
    assert asset_order_from_chapters(chapters) == ["x", "y", "z"]


def test_aspect_pattern_match_rate_between_zero_and_one() -> None:
    chapters = [{"screens": [{"patternId": "screen-portrait-1", "slots": [{"assetId": "p1"}]}]}]
    aspects = {"p1": "portrait"}
    rate = aspect_pattern_match_rate(chapters, aspects)
    assert 0.0 <= rate <= 1.0
