"""Mosaic composition configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.config_helpers import cfg_bool, cfg_float


@dataclass
class MosaicDensityBudgetConfig:
    """P21 · dense collage frequency caps (PRD-PHASE21)."""

    enabled: bool = True
    min_slots: int = 4
    window_order: tuple[int, ...] = (5, 4, 6, 9)
    large_mosaic_min_slots: int = 5
    max_per_template_per_trip: int = 2
    max_large_mosaic_per_chapter: int = 1


@dataclass
class MosaicConfig:
    """Phase 15 mosaic composition (DESIGN-PHASE15 · S1)."""

    enabled: bool = True
    scorer_version: str = "p15-s3"
    deterministic_strict: bool = True
    min_candidate_score: float = 0.35
    enabled_window_sizes: tuple[int, ...] = (4, 5, 6, 9)
    unified_mode: bool = True
    fallback_to_legacy: bool = True
    self_heal_enabled: bool = True
    allow_drop: bool = False
    max_drop_ratio: float = 0.5
    candidate_top_k: int = 4
    log_level: str = "window"
    density_budget: MosaicDensityBudgetConfig = field(default_factory=MosaicDensityBudgetConfig)
    # When false, restores pre-v4 hero-3-2-plus-4 geometry/scorer guards (rollback).
    hero_weighted_geometry_guard: bool = True
    # PRD-6张拼图优化 · R-MAIN-AR-01: conventional AR only for hero+tile main slot.
    main_ar_guard: bool = True
    main_ar_ladder_tol: float = 0.08
    main_ar_prefer_16_9: bool = True
    # Skip dense windows (size≥6) when the window has ≥2 standard portraits.
    skip_dense_window_multi_portrait: bool = True
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "aspect_match": 0.20,
            "sharpness": 0.15,
            "hero_separation": 0.10,
            "temporal_coherence": 0.15,
            "subject_run": 0.10,
            "layout_rhythm": 0.10,
            "diversity": 0.10,
            "category_coherence": 0.10,
            "cohort_coherence": 0.0,
        }
    )
    penalties: dict[str, float] = field(
        default_factory=lambda: {
            "face_crop": 0.30,
            "main_quality": 0.25,
            "duplicate_density": 0.20,
            "hero_narrow_tiles": 0.35,
            "hero_slot_aspect": 0.4,
            "flat_six_grid": 0.35,
            "flat_nine_grid": 0.45,
            "dense_without_hero": 0.25,
            "main_ar_ineligible": 0.95,
        }
    )
    # LSE W3b capability flags (set via layout_engine.adapter mosaic_config_from_pack)
    lse_saliency_scoring: bool = False
    lse_tone_harmony: bool = False
    lse_beat_profile: str = "flat"
    lse_hungarian_assignment: bool = False
    lse_quality_unified: bool = False
    lse_slot_max_matrix_n: int = 16
    lse_highlight_boost: float = 1.0


def _density_budget_from_dict(raw: dict[str, Any]) -> MosaicDensityBudgetConfig:
    defaults = MosaicDensityBudgetConfig()
    db = raw.get("density_budget") if isinstance(raw.get("density_budget"), dict) else {}
    if isinstance(raw.get("densityBudget"), dict):
        db = raw["densityBudget"]
    order_raw = db.get("window_order", db.get("windowOrder", defaults.window_order))
    if isinstance(order_raw, (list, tuple)):
        order = tuple(int(x) for x in order_raw)
    else:
        order = defaults.window_order
    return MosaicDensityBudgetConfig(
        enabled=cfg_bool(db, "enabled", "enabled", defaults.enabled),
        min_slots=int(db.get("min_slots", db.get("minSlots", defaults.min_slots))),
        window_order=order or defaults.window_order,
        large_mosaic_min_slots=int(
            db.get("large_mosaic_min_slots", db.get("largeMosaicMinSlots", defaults.large_mosaic_min_slots))
        ),
        max_per_template_per_trip=int(
            db.get(
                "max_per_template_per_trip",
                db.get("maxPerTemplatePerTrip", defaults.max_per_template_per_trip),
            )
        ),
        max_large_mosaic_per_chapter=int(
            db.get(
                "max_large_mosaic_per_chapter",
                db.get("maxLargeMosaicPerChapter", defaults.max_large_mosaic_per_chapter),
            )
        ),
    )


def mosaic_from_dict(raw: dict[str, Any]) -> MosaicConfig:
    defaults = MosaicConfig()
    sizes_raw = raw.get("enabled_window_sizes", raw.get("enabledWindowSizes", defaults.enabled_window_sizes))
    if isinstance(sizes_raw, (list, tuple)):
        sizes = tuple(int(x) for x in sizes_raw)
    else:
        sizes = defaults.enabled_window_sizes
    weights_raw = raw.get("weights") if isinstance(raw.get("weights"), dict) else {}
    penalties_raw = raw.get("penalties") if isinstance(raw.get("penalties"), dict) else {}
    self_heal = raw.get("self_heal") if isinstance(raw.get("self_heal"), dict) else {}
    if isinstance(raw.get("selfHeal"), dict):
        self_heal = raw["selfHeal"]
    allow_drop = bool(self_heal.get("allow_drop", self_heal.get("allowDrop", defaults.allow_drop)))
    self_heal_enabled = bool(
        self_heal.get("enabled", raw.get("self_heal_enabled", defaults.self_heal_enabled))
    )
    max_drop = self_heal.get("max_drop_ratio", self_heal.get("maxDropRatio", defaults.max_drop_ratio))
    return MosaicConfig(
        enabled=bool(raw.get("enabled", defaults.enabled)),
        scorer_version=str(raw.get("scorer_version", raw.get("scorerVersion", defaults.scorer_version))),
        deterministic_strict=cfg_bool(
            raw, "deterministic_strict", "deterministicStrict", defaults.deterministic_strict
        ),
        min_candidate_score=cfg_float(
            raw, "min_candidate_score", "minCandidateScore", defaults.min_candidate_score
        ),
        enabled_window_sizes=sizes or defaults.enabled_window_sizes,
        unified_mode=bool(raw.get("unified_mode", raw.get("unifiedMode", defaults.unified_mode))),
        fallback_to_legacy=bool(
            raw.get("fallback_to_legacy", raw.get("fallbackToLegacy", defaults.fallback_to_legacy))
        ),
        self_heal_enabled=self_heal_enabled,
        allow_drop=allow_drop,
        max_drop_ratio=float(max_drop) if max_drop is not None else defaults.max_drop_ratio,
        candidate_top_k=int(raw.get("candidate_top_k", raw.get("candidateTopK", defaults.candidate_top_k))),
        log_level=str(raw.get("log_level", raw.get("logLevel", defaults.log_level))),
        hero_weighted_geometry_guard=cfg_bool(
            raw,
            "hero_weighted_geometry_guard",
            "heroWeightedGeometryGuard",
            defaults.hero_weighted_geometry_guard,
        ),
        main_ar_guard=cfg_bool(
            raw,
            "main_ar_guard",
            "mainArGuard",
            defaults.main_ar_guard,
        ),
        main_ar_ladder_tol=cfg_float(
            raw,
            "main_ar_ladder_tol",
            "mainArLadderTol",
            defaults.main_ar_ladder_tol,
        ),
        main_ar_prefer_16_9=cfg_bool(
            raw,
            "main_ar_prefer_16_9",
            "mainArPrefer169",
            defaults.main_ar_prefer_16_9,
        ),
        skip_dense_window_multi_portrait=cfg_bool(
            raw,
            "skip_dense_window_multi_portrait",
            "skipDenseWindowMultiPortrait",
            defaults.skip_dense_window_multi_portrait,
        ),
        weights={k: float(weights_raw.get(k, defaults.weights.get(k, 0.0))) for k in defaults.weights},
        penalties={
            k: float(penalties_raw.get(k, defaults.penalties.get(k, 0.0))) for k in defaults.penalties
        },
        density_budget=_density_budget_from_dict(raw),
    )
