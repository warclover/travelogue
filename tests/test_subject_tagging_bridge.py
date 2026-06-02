"""Phase 9 · subject_tagging CLIP bridge (P9-E)."""

from __future__ import annotations

from travelogue.curation.subject_tagging import (
    is_mundane_clusterable,
    mundane_run_length,
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


def test_is_mundane_clusterable_phase10_1_sign_ticket_shop() -> None:
    assert is_mundane_clusterable({"tags": ["sign"]}) == "sign"
    assert is_mundane_clusterable({"tags": ["ticket"]}) == "ticket"
    assert is_mundane_clusterable({"tags": ["shop"]}) == "shop"


def test_mundane_run_length_defaults_to_food_only() -> None:
    ids = ["a1", "a2", "a3", "a4"]
    assets_map = {
        "a1": {"tags": ["food"]},
        "a2": {"tags": ["sign"]},
        "a3": {"tags": ["food"]},
        "a4": {"tags": ["food"]},
    }
    # 默认只统计 food，所以 sign 会算作一次 tolerance 干扰。
    assert mundane_run_length(ids, assets_map, 0) == 3


def test_mundane_run_length_supports_custom_allowed_buckets() -> None:
    ids = ["a1", "a2", "a3", "a4"]
    assets_map = {
        "a1": {"tags": ["food"]},
        "a2": {"tags": ["sign"]},
        "a3": {"tags": ["ticket"]},
        "a4": {"tags": ["shop"]},
    }
    assert mundane_run_length(
        ids,
        assets_map,
        0,
        allowed_buckets=("food", "sign", "ticket", "shop"),
    ) == 4
