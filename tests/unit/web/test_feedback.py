"""Feedback denoising (Phase 3a)."""

from __future__ import annotations

from travelogue.curation.feedback import (
    classify_edit_type,
    filter_edits_for_training,
    g1_edit_distance,
    record_g1_edit,
)


def test_g1_edit_distance_identical():
    plan = {"chapters": [{"items": [{"assetId": "a1"}], "screens": []}]}
    assert g1_edit_distance(plan, plan) == 0.0


def test_classify_swap_hero():
    before = {"chapterHeroAssetIds": {"ch-01": "a1"}, "chapters": []}
    after = {"chapterHeroAssetIds": {"ch-01": "a2"}, "chapters": []}
    assert classify_edit_type(before, after) == "swap_hero"


def test_filter_requires_cohort():
    records = [
        record_g1_edit("t1", {"chapters": [{"items": [{"assetId": "a1"}]}]}, {"chapters": []}),
        record_g1_edit("t2", {"chapters": [{"items": [{"assetId": "b1"}]}]}, {"chapters": []}),
    ]
    filtered = filter_edits_for_training(records, min_trip_count=3)
    assert filtered == []
