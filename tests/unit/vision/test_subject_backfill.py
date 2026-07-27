"""subjectClass backfill before cover / FRP (late-import gap)."""

from __future__ import annotations

from travelogue.vision.subject_backfill import (
    assets_missing_subject_class,
    ensure_subject_classes,
)


def test_assets_missing_subject_class_skips_labeled_and_video() -> None:
    assets = [
        {"id": "a", "type": "image"},
        {"id": "b", "type": "image", "subjectClass": "food"},
        {"id": "c", "type": "video"},
        {"id": "d", "type": "image", "subjectClass": ""},
    ]
    missing = assets_missing_subject_class(assets)
    assert [a["id"] for a in missing] == ["a", "d"]


def test_ensure_subject_classes_soft_fails_without_trip_dir() -> None:
    trip = {"assets": [{"id": "a", "type": "image"}]}
    assert ensure_subject_classes(trip) == 0
