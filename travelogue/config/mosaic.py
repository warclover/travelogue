"""Mosaic composition configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.config_helpers import cfg_bool, cfg_float


@dataclass
class MosaicConfig:
    """Phase 15 mosaic composition (DESIGN-PHASE15 · S1)."""

    enabled: bool = True
    scorer_version: str = "p15-s2"
    deterministic_strict: bool = True
    min_candidate_score: float = 0.35
    enabled_window_sizes: tuple[int, ...] = (3, 4, 5, 6, 8, 9)
    unified_mode: bool = True
    fallback_to_legacy: bool = True
    self_heal_enabled: bool = True
    allow_drop: bool = False
    max_drop_ratio: float = 0.5
    candidate_top_k: int = 4
    log_level: str = "window"
    # When false, restores pre-v4 hero-3-2-plus-4 geometry/scorer guards (rollback).
    hero_weighted_geometry_guard: bool = True
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
        }
    )


def mosaic_from_dict(raw: dict[str, Any]) -> MosaicConfig:
    defaults = MosaicConfig()
    sizes_raw = raw.get("enabled_window_sizes", raw.get("enabledWindowSizes", [5]))
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
        weights={k: float(weights_raw.get(k, defaults.weights.get(k, 0.0))) for k in defaults.weights},
        penalties={
            k: float(penalties_raw.get(k, defaults.penalties.get(k, 0.0))) for k in defaults.penalties
        },
    )
