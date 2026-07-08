"""Unit tests for layout_scoring."""

from __future__ import annotations

import pytest

from travelogue.curation.layout_scoring import (
    PHASE2_WEIGHTS,
    PHASE3_WEIGHTS,
    PHASE3B_WEIGHTS,
    PHASE6_WEIGHTS,
    ScoringWeights,
    resolve_scoring_weights,
    score_aspect_match,
    score_category_coherence,
    score_screen,
)


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
        + w.category_coherence
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
        + w.category_coherence
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


def test_category_coherence_rewards_same_semantic_category() -> None:
    ids = ["a1", "a2", "a3"]
    assets = {
        "a1": {"semanticTag": {"category": "food"}},
        "a2": {"semanticTag": {"category": "food"}},
        "a3": {"semanticTag": {"category": "food"}},
    }
    assert score_category_coherence(ids, assets) == 1.0


def test_category_coherence_penalizes_switches() -> None:
    ids = ["a1", "a2", "a3"]
    assets = {
        "a1": {"semanticTag": {"category": "food"}},
        "a2": {"semanticTag": {"category": "landscape"}},
        "a3": {"semanticTag": {"category": "person"}},
    }
    assert score_category_coherence(ids, assets) == 0.0


def test_featured_beam_bonus_per_asset_in_plan() -> None:
    from travelogue.curation.layout_scoring import FEATURED_BEAM_BONUS_PER_ASSET, score_screen_plan

    weights = ScoringWeights(aspect_match=1.0)
    screen = {
        "patternId": "screen-portrait-2",
        "slots": [
            {"assetId": "f1", "role": "portrait"},
            {"assetId": "f2", "role": "portrait"},
        ],
    }
    aspects = {"f1": "portrait", "f2": "portrait"}
    assets = {
        "f1": {"id": "f1", "userTier": "featured"},
        "f2": {"id": "f2", "userTier": "featured"},
    }
    base = score_screen_plan(
        [screen], aspects=aspects, assets_by_id=assets, weights=weights, featured_beam=False
    )
    boosted = score_screen_plan(
        [screen], aspects=aspects, assets_by_id=assets, weights=weights, featured_beam=True
    )
    assert boosted.total - base.total == pytest.approx(2 * FEATURED_BEAM_BONUS_PER_ASSET)


def test_featured_beam_halves_hero_separation_when_hero_reused() -> None:
    from travelogue.curation.layout_scoring import FEATURED_HERO_SEPARATION_HALVED

    weights = ScoringWeights(hero_separation=1.0)
    screen = {"patternId": "screen-landscape-1", "slots": [{"assetId": "hero1"}]}
    hero_ids = {"hero1"}

    feat = score_screen(
        screen,
        aspects={},
        assets_by_id={"hero1": {"id": "hero1", "userTier": "featured"}},
        weights=weights,
        hero_asset_ids=hero_ids,
        featured_beam=True,
    )
    mat = score_screen(
        screen,
        aspects={},
        assets_by_id={"hero1": {"id": "hero1", "userTier": "material"}},
        weights=weights,
        hero_asset_ids=hero_ids,
        featured_beam=True,
    )
    assert feat.hero_separation == FEATURED_HERO_SEPARATION_HALVED
    assert mat.hero_separation == 0.0
    assert feat.total > mat.total


def test_resolve_scoring_weights_preserves_aspect_only() -> None:
    aspect_only = ScoringWeights(aspect_match=1.0)
    resolved = resolve_scoring_weights(
        aspect_only,
        scoring_enabled=True,
        has_color_metrics=True,
        enable_gravity_balance=True,
    )
    assert resolved.is_aspect_only()


def test_resolve_scoring_weights_zero_fallback_phase6_default() -> None:
    zero = ScoringWeights()
    resolved = resolve_scoring_weights(
        zero,
        scoring_enabled=True,
        has_color_metrics=True,
    )
    assert resolved == PHASE6_WEIGHTS


def test_resolve_scoring_weights_zero_fallback_phase3b_when_gravity_off() -> None:
    zero = ScoringWeights()
    resolved = resolve_scoring_weights(
        zero,
        scoring_enabled=True,
        has_color_metrics=True,
        enable_gravity_balance=False,
    )
    assert resolved == PHASE3B_WEIGHTS


def test_resolve_scoring_weights_zero_fallback_phase3_without_tone() -> None:
    zero = ScoringWeights()
    resolved = resolve_scoring_weights(
        zero,
        scoring_enabled=True,
        has_color_metrics=False,
        enable_gravity_balance=False,
    )
    assert resolved == PHASE3_WEIGHTS


def test_resolve_scoring_weights_disabled_keeps_zero() -> None:
    zero = ScoringWeights()
    assert resolve_scoring_weights(zero, scoring_enabled=False, has_color_metrics=True) == zero


def test_resolve_scoring_weights_custom_unchanged() -> None:
    custom = ScoringWeights(aspect_match=0.5, sharpness=0.5)
    assert (
        resolve_scoring_weights(
            custom,
            scoring_enabled=True,
            has_color_metrics=True,
            enable_gravity_balance=False,
        )
        == custom
    )


def test_score_layout_rhythm_alternation_bonus() -> None:
    from travelogue.curation.layout_scoring import score_layout_rhythm

    hero = {"patternId": "screen-portrait-1", "slots": [{"assetId": "a1"}]}
    grid = {"patternId": "screen-portrait-3", "slots": [{"assetId": "a2"}, {"assetId": "a3"}]}
    assert score_layout_rhythm([hero, grid, hero]) > score_layout_rhythm([grid, grid, grid])


def test_score_layout_rhythm_same_pattern_zero() -> None:
    from travelogue.curation.layout_scoring import score_layout_rhythm

    grid = {"patternId": "screen-portrait-3", "slots": [{"assetId": "a1"}, {"assetId": "a2"}]}
    assert score_layout_rhythm([grid, grid]) == 0.0


def test_phase3b_includes_layout_rhythm_weight() -> None:
    from travelogue.curation.layout_scoring import PHASE3B_WEIGHTS

    assert PHASE3B_WEIGHTS.layout_rhythm > 0
