"""Phase 9 · subject_tagging CLIP bridge (P9-E)."""

from __future__ import annotations

from travelogue.curation.subject_tagging import subject_class_for_asset, subject_tags_for_asset


def test_clip_food_overrides_landscape_tags() -> None:
    asset = {
        "subjectClass": "food",
        "subjectConfidence": 0.9,
        "tags": ["landscape", "scenery"],
        "subjectBucket": "landscape",
    }
    assert subject_class_for_asset(asset) == "food"


def test_clip_person_maps_directly() -> None:
    asset = {"subjectClass": "person", "subjectConfidence": 0.8}
    assert subject_class_for_asset(asset) == "person"


def test_clip_temple_maps_to_landscape() -> None:
    asset = {"subjectClass": "temple", "subjectConfidence": 0.7}
    assert subject_class_for_asset(asset) == "landscape"


def test_low_confidence_clip_falls_back_to_heuristic() -> None:
    asset = {
        "subjectClass": "food",
        "subjectConfidence": 0.2,
        "tags": ["landscape"],
        "subjectBucket": "landscape",
    }
    assert subject_class_for_asset(asset) == "landscape"


def test_no_subject_class_matches_legacy_heuristic() -> None:
    asset = {"tags": ["food", "meal"], "subjectBucket": "food"}
    assert subject_class_for_asset(asset) == "food"


def test_subject_tags_include_clip_mirror() -> None:
    tags = subject_tags_for_asset({"subjectClass": "food", "faces": [{}]})
    assert "clip:food" in tags
    assert "has_face" in tags
