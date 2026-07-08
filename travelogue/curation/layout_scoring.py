"""Layout candidate scoring (V2 PRD §4). Default weights yield legacy-equivalent ranking."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_contract.scoring import (
    FEATURED_BEAM_BONUS_PER_ASSET,
    FEATURED_HERO_SEPARATION_HALVED,
    IncrementalScoreState,
    ScoreBreakdown,
    ScoringWeights,
    moment_secondary_plan_bonus,
    screen_dominant_tone,
)

PHASE2_WEIGHTS = ScoringWeights(
    aspect_match=0.15,
    sharpness=0.05,
    temporal_coherence=0.12,
    burst_integrity=0.08,
    diversity=0.10,
    arc_fit=0.12,
    hero_separation=0.06,
).normalized()

# Phase-3a: adds luminance continuity + soft subject run
PHASE3_WEIGHTS = ScoringWeights(
    aspect_match=0.13,
    sharpness=0.05,
    temporal_coherence=0.10,
    burst_integrity=0.08,
    diversity=0.08,
    arc_fit=0.10,
    hero_separation=0.06,
    luminance_continuity=0.08,
    subject_run=0.06,
).normalized()

# Phase-3b: dominantTone ΔE spread (requires ingest backfill)
PHASE3B_WEIGHTS = ScoringWeights(
    aspect_match=0.12,
    sharpness=0.05,
    temporal_coherence=0.09,
    burst_integrity=0.08,
    diversity=0.07,
    arc_fit=0.09,
    hero_separation=0.06,
    luminance_continuity=0.06,
    tone_continuity=0.08,
    subject_run=0.05,
    layout_rhythm=0.05,
).normalized()

# Phase-6: cross-screen focal gravity continuity (M25-B)
PHASE6_WEIGHTS = ScoringWeights(
    aspect_match=0.11,
    sharpness=0.05,
    temporal_coherence=0.08,
    burst_integrity=0.08,
    diversity=0.07,
    arc_fit=0.08,
    hero_separation=0.06,
    luminance_continuity=0.06,
    tone_continuity=0.07,
    subject_run=0.05,
    layout_rhythm=0.05,
    gravity_balance=0.05,
).normalized()


def _weights_raw_sum(weights: ScoringWeights) -> float:
    return (
        weights.aspect_match
        + weights.sharpness
        + weights.hero_separation
        + weights.temporal_coherence
        + weights.diversity
        + weights.arc_fit
        + weights.burst_integrity
        + weights.luminance_continuity
        + weights.subject_run
        + weights.tone_continuity
        + weights.layout_rhythm
        + weights.gravity_balance
        + weights.category_coherence
        + weights.cohort_coherence
    )


def resolve_scoring_weights(
    weights: ScoringWeights,
    *,
    scoring_enabled: bool,
    has_color_metrics: bool,
    enable_gravity_balance: bool = True,
) -> ScoringWeights:
    """P5-C1 / D7 / P6-D1: default weight presets when config weights are all zero."""
    if not scoring_enabled:
        return weights
    if weights.is_aspect_only():
        return weights
    if _weights_raw_sum(weights) <= 1e-9:
        if enable_gravity_balance:
            return PHASE6_WEIGHTS
        return PHASE3B_WEIGHTS if has_color_metrics else PHASE3_WEIGHTS
    if enable_gravity_balance and weights.gravity_balance <= 1e-9:
        patched = ScoringWeights(**{**weights.__dict__, "gravity_balance": 0.05})
        return patched.normalized()
    return weights




__all__ = [
    "FEATURED_BEAM_BONUS_PER_ASSET",
    "FEATURED_HERO_SEPARATION_HALVED",
    "IncrementalScoreState",
    "PHASE2_WEIGHTS",
    "PHASE3_WEIGHTS",
    "PHASE3B_WEIGHTS",
    "PHASE6_WEIGHTS",
    "ScoreBreakdown",
    "ScoringWeights",
    "asset_mean_luma",
    "moment_secondary_plan_bonus",
    "rank_screens",
    "resolve_scoring_weights",
    "score_aspect_match",
    "score_burst_integrity",
    "score_category_coherence",
    "score_cohort_coherence",
    "score_gravity_balance",
    "score_layout_rhythm",
    "score_luminance_continuity",
    "score_screen",
    "score_screen_plan",
    "score_sharpness",
    "score_subject_run_soft",
    "score_temporal_coherence",
    "score_tone_continuity",
    "screen_dominant_tone",
    "screen_mean_luma",
    "screen_visual_center",
]

_BEAM_EXPORTS = frozenset({'asset_mean_luma', 'rank_screens', 'score_aspect_match', 'score_burst_integrity', 'score_category_coherence', 'score_cohort_coherence', 'score_gravity_balance', 'score_layout_rhythm', 'score_luminance_continuity', 'score_screen', 'score_screen_plan', 'score_sharpness', 'score_subject_run_soft', 'score_temporal_coherence', 'score_tone_continuity', 'screen_mean_luma', 'screen_visual_center'})

def __getattr__(name: str):
    if name in _BEAM_EXPORTS:
        import importlib
        mod = importlib.import_module('travelogue.layout_engine.planner.beam_scoring')
        return getattr(mod, name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
