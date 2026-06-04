"""Unit tests for cohort intent normalization."""

from __future__ import annotations

import pytest

from travelogue.services.cohort import normalize_featured_subjects, validate_seeds_exist
from travelogue.services.trip import apply_intent


def test_normalize_featured_subjects() -> None:
    out = normalize_featured_subjects(
        [
            {"id": "Alice", "label": "小明", "seedAssetIds": ["a1", "a1"]},
            {"id": "bob", "seedAssetIds": ["b1"]},
        ]
    )
    assert out[0]["id"] == "alice"
    assert out[0]["seedAssetIds"] == ["a1"]
    assert out[1]["id"] == "bob"


def test_normalize_rejects_bad_id() -> None:
    with pytest.raises(ValueError, match="featuredSubjects.id"):
        normalize_featured_subjects([{"id": "Bad_ID", "seedAssetIds": ["a1"]}])


def test_apply_intent_featured_subjects() -> None:
    trip = {
        "meta": {"places": ["京都"]},
        "assets": [{"id": "a1", "type": "image"}],
    }
    intent = apply_intent(
        trip,
        featured_subjects=[
            {"id": "alice", "seedAssetIds": ["a1"]},
            {"id": "bob", "seedAssetIds": ["a1"]},
        ],
    )
    assert len(intent["featuredSubjects"]) == 2


def test_validate_seeds_unknown() -> None:
    with pytest.raises(ValueError, match="unknown seed"):
        validate_seeds_exist(
            [{"id": "alice", "seedAssetIds": ["missing"]}],
            {},
        )
