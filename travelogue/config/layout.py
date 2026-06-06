"""Layout engine and scoring configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.config_helpers import cfg_bool


@dataclass
class LayoutScoringConfig:
    """V2 layout search (ADR-002); disabled by default = legacy behavior."""

    enabled: bool = False
    beam_width: int = 3
    max_screens_per_chapter: int = 12
    min_layout_eligible: int = 3
    min_aspect_kinds: int = 1
    search_timeout_ms: int = 2000
    max_candidates_per_bucket: int = 12
    max_evaluations_per_trip: int = 500
    max_evaluations_per_segment: int = 0
    allow_burst_split: bool = False
    subject_run_tolerance: int = 1
    skip_duplicate_signatures: bool = True
    incremental: bool = False
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "aspect_match": 0.0,
            "sharpness": 0.0,
            "hero_separation": 0.0,
            "temporal_coherence": 0.0,
            "diversity": 0.0,
            "arc_fit": 0.0,
            "burst_integrity": 0.0,
            "luminance_continuity": 0.0,
            "subject_run": 0.0,
            "tone_continuity": 0.0,
            "layout_rhythm": 0.0,
            "gravity_balance": 0.0,
            "category_coherence": 0.0,
        }
    )


@dataclass
class LayoutFeedbackConfig:
    enabled: bool = False
    log_path: str | None = None


@dataclass
class LayoutConfig:
    """Web layout engine default when exportLayout is web (see docs/web端模板升级计划.md)."""

    web_layout_engine: str = "screens"  # legacy | screens
    screen_plan_scope: str = "day"  # chapter | day — day = 按策展日桶全序列组屏
    mixed_proximity_seconds: float = 12.0  # 1竖+2横混排 takenAt 跨度上限
    layout_density_enabled: bool = True  # PRD-FINE-CRAFT-LAYOUT-DENSITY · false → balanced
    scoring: LayoutScoringConfig = field(default_factory=LayoutScoringConfig)
    feedback: LayoutFeedbackConfig = field(default_factory=LayoutFeedbackConfig)


def layout_scoring_from_dict(raw: dict[str, Any]) -> LayoutScoringConfig:
    weights_raw = raw.get("weights") if isinstance(raw.get("weights"), dict) else {}
    default_weights = LayoutScoringConfig().weights
    weights = {k: float(weights_raw.get(k, default_weights.get(k, 0.0))) for k in default_weights}
    return LayoutScoringConfig(
        enabled=bool(raw.get("enabled", False)),
        beam_width=int(raw.get("beam_width", 3)),
        max_screens_per_chapter=int(raw.get("max_screens_per_chapter", 12)),
        min_layout_eligible=int(raw.get("min_layout_eligible", 3)),
        min_aspect_kinds=int(raw.get("min_aspect_kinds", 1)),
        search_timeout_ms=int(raw.get("search_timeout_ms", 2000)),
        max_candidates_per_bucket=int(raw.get("max_candidates_per_bucket", 12)),
        max_evaluations_per_trip=int(raw.get("max_evaluations_per_trip", 500)),
        max_evaluations_per_segment=int(
            raw.get("max_evaluations_per_segment", raw.get("maxEvaluationsPerSegment", 0))
        ),
        allow_burst_split=bool(raw.get("allow_burst_split", False)),
        subject_run_tolerance=int(raw.get("subject_run_tolerance", 1)),
        skip_duplicate_signatures=cfg_bool(
            raw, "skip_duplicate_signatures", "skipDuplicateSignatures", True
        ),
        incremental=bool(raw.get("incremental", False)),
        weights=weights,
    )


def layout_feedback_from_dict(raw: dict[str, Any]) -> LayoutFeedbackConfig:
    log_path = raw.get("log_path")
    return LayoutFeedbackConfig(
        enabled=bool(raw.get("enabled", False)),
        log_path=str(log_path).strip() if log_path else None,
    )
