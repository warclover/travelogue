"""Unit tests for layout_scoring."""

from __future__ import annotations

from travelogue.curation.layout_scoring import ScoringWeights, score_aspect_match, PHASE2_WEIGHTS, score_screen


def test_aspect_match_full_for_portrait_roles():
    screen = {
        "patternId": "screen-portrait-3",
        "slots": [
            {"assetId": "p1", "role": "portrait"},
            {"assetId": "p2", "role": "portrait"},
            {"assetId": "p3", "role": "portrait"},
        ],
    }
    aspects = {"p1": "portrait", "p2": "portrait", "p3": "portrait"}
    assert score_aspect_match(screen, aspects) == 1.0


def test_aspect_only_weights_total_equals_aspect_match():
    screen = {
        "patternId": "screen-portrait-2",
        "slots": [
            {"assetId": "p1", "role": "portrait"},
            {"assetId": "p2", "role": "portrait"},
        ],
    }
    aspects = {"p1": "portrait", "p2": "portrait"}
    weights = ScoringWeights(aspect_match=1.0)
    bd = score_screen(screen, aspects=aspects, assets_by_id={}, weights=weights)
    assert bd.total == bd.aspect_match
    assert weights.is_aspect_only()


def test_is_aspect_only_false_when_extra_weights():
    w = ScoringWeights(aspect_match=0.5, sharpness=0.5)
    assert not w.is_aspect_only()


def test_phase2_weights_sum_to_one():
    w = PHASE2_WEIGHTS
    total = (
        w.aspect_match
        + w.sharpness
        + w.hero_separation
        + w.temporal_coherence
        + w.diversity
        + w.arc_fit
        + w.burst_integrity
        + w.luminance_continuity
        + w.subject_run
    )
    assert abs(total - 1.0) < 1e-6


def test_phase3_weights_sum_to_one():
    from travelogue.curation.layout_scoring import PHASE3_WEIGHTS

    w = PHASE3_WEIGHTS
    total = (
        w.aspect_match
        + w.sharpness
        + w.hero_separation
        + w.temporal_coherence
        + w.diversity
        + w.arc_fit
        + w.burst_integrity
        + w.luminance_continuity
        + w.subject_run
    )
    assert abs(total - 1.0) < 1e-6


def test_luminance_continuity_smooth():
    from travelogue.curation.layout_scoring import score_luminance_continuity

    assets = {
        "a1": {"id": "a1", "tags": ["bright"]},
        "a2": {"id": "a2", "tags": ["bright"]},
    }
    screens = [
        {"slots": [{"assetId": "a1"}]},
        {"slots": [{"assetId": "a2"}]},
    ]
    assert score_luminance_continuity(screens, assets) == 1.0


def test_subject_run_soft_allows_one_outlier():
    from travelogue.curation.layout_scoring import score_subject_run_soft

    assets = {
        "a1": {"id": "a1", "tags": ["landscape"]},
        "a2": {"id": "a2", "tags": ["landscape"]},
        "a3": {"id": "a3", "tags": ["person"]},
        "a4": {"id": "a4", "tags": ["landscape"]},
    }
    score = score_subject_run_soft(
        ["a1", "a2", "a3", "a4"], assets, target_run=3, tolerance=1
    )
    assert score >= 0.5
