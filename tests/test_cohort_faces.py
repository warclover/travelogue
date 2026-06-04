"""Tests for featured-subject cohort tagging."""

from __future__ import annotations

import numpy as np

from travelogue.curation.cohort_faces import (
    asset_cohort_duo,
    featured_subjects_from_trip,
    score_cohort_coherence,
    _match_present_subjects,
)
from travelogue.curation.cohort_faces import SubjectTemplate
from travelogue.curation.layout_scoring import ScoringWeights, score_cohort_coherence as layout_cohort_score
from travelogue.curation.cohort_faces import merge_cohort_weight
from travelogue.config import CohortConfig
from travelogue.media.face_embed import cosine_similarity, face_crop_embedding, l2_normalize, mean_embedding


def test_featured_subjects_from_intent() -> None:
    trip = {
        "intent": {
            "version": "1",
            "featuredSubjects": [
                {"id": "alice", "label": "A", "seedAssetIds": ["s1"]},
                {"id": "bob", "seedAssetIds": ["s2", "s3"]},
            ],
        }
    }
    subs = featured_subjects_from_trip(trip)
    assert len(subs) == 2
    assert subs[0]["id"] == "alice"
    assert subs[1]["seedAssetIds"] == ["s2", "s3"]


def test_match_present_subjects_duo() -> None:
    tpl_a = SubjectTemplate("alice", "A", l2_normalize(np.array([1.0, 0.0, 0.0])))
    tpl_b = SubjectTemplate("bob", "B", l2_normalize(np.array([0.0, 1.0, 0.0])))
    emb_a = l2_normalize(np.array([0.95, 0.05, 0.0]))
    emb_b = l2_normalize(np.array([0.05, 0.95, 0.0]))
    present, conf, _rows = _match_present_subjects(
        [emb_a, emb_b], [tpl_a, tpl_b], threshold=0.7
    )
    assert present == {"alice", "bob"}
    assert conf >= 0.7


def test_score_cohort_coherence_adjacent_duo() -> None:
    assets = {
        "a1": {"curation": {"cohort": {"duo": True}}},
        "a2": {"curation": {"cohort": {"duo": True}}},
        "a3": {"curation": {"cohort": {"duo": False}}},
    }
    assert score_cohort_coherence(["a1", "a2"], assets) == 1.0
    assert score_cohort_coherence(["a2", "a3"], assets) == 0.55
    assert layout_cohort_score(["a1", "a2", "a3"], assets) > 0.5


def test_asset_cohort_duo() -> None:
    assert asset_cohort_duo({"curation": {"cohort": {"duo": True}}})
    assert not asset_cohort_duo({"curation": {"cohort": {"duo": False}}})


def test_merge_cohort_weight_injects_dimension() -> None:
    w = ScoringWeights(aspect_match=1.0)
    out = merge_cohort_weight(w, CohortConfig(enabled=True, layout_weight=0.06))
    assert out.cohort_coherence > 0.0
    assert abs(out.aspect_match + out.cohort_coherence - 1.0) < 1e-5


def test_face_embed_cosine_identical() -> None:
    v = l2_normalize(np.arange(12, dtype=np.float64))
    assert cosine_similarity(v, v) == 1.0


def test_mean_embedding() -> None:
    v1 = l2_normalize(np.array([1.0, 0.0]))
    v2 = l2_normalize(np.array([0.9, 0.1]))
    m = mean_embedding([v1, v2])
    assert m is not None
    assert cosine_similarity(m, v1) > 0.95
