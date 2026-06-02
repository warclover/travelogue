"""Phase 9 · subject_tagging CLIP bridge (P9-E)."""

from __future__ import annotations

from travelogue.curation.subject_tagging import (
    is_mundane_clusterable,
    subject_class_for_asset,
    subject_tags_for_asset,
)


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


def test_invalid_confidence_clip_falls_back_to_heuristic_without_crash() -> None:
    asset = {
        "subjectClass": "food",
        "subjectConfidence": "bad",
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


def test_is_mundane_clusterable_accepts_clip_food() -> None:
    asset = {"subjectClass": "food", "subjectConfidence": 0.8, "tags": []}
    assert is_mundane_clusterable(asset) == "food"


def test_is_mundane_clusterable_accepts_food_tag_vocabulary() -> None:
    asset = {"tags": ["meal"]}
    assert is_mundane_clusterable(asset) == "food"


def test_is_mundane_clusterable_ignores_non_food_subject() -> None:
    asset = {"subjectClass": "landscape", "tags": ["sky", "mountain"]}
    assert is_mundane_clusterable(asset) is None


def test_is_mundane_clusterable_accepts_semantic_category_food() -> None:
    asset = {"semanticTag": {"category": "food"}}
    assert is_mundane_clusterable(asset) == "food"


def test_is_mundane_clusterable_accepts_curation_subject_tags_clip_food() -> None:
    asset = {"curation": {"subjectTags": ["clip:food"]}}
    assert is_mundane_clusterable(asset) == "food"
