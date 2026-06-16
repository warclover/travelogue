"""Curation pipeline configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.config.moment import MomentConfig
from travelogue.curation.cover_scoring_params import CoverScoringParams


def _default_cover_scoring_v2() -> Any:
    from travelogue.curation.cover_scoring_v2 import CoverScoringParamsV2

    return CoverScoringParamsV2()


def cover_scoring_v2_from_dict(curate_raw: dict[str, Any]) -> Any:
    raw = curate_raw.get("cover_scoring_v2") or curate_raw.get("coverScoringV2")
    if not raw:
        return _default_cover_scoring_v2()
    from travelogue.curation.cover_scoring_v2 import CoverScoringParamsV2

    return CoverScoringParamsV2.from_mapping(raw)


@dataclass
class CurateConfig:
    segment_gap_days: int = 14
    city_gap_days: int = 3
    min_bucket_size: int = 3
    chapter_balance_enabled: bool = True
    chapter_balance_ratio: float = 0.55
    arc_mode: str = "legacy"  # legacy | v2_adaptive | v2_five_beat (alias)
    arc_flat_variance_threshold: float = 0.08
    featured_weight: float = 1.35
    featured_min_for_cover_pool: int = 2
    cover_scoring: CoverScoringParams = field(default_factory=CoverScoringParams)
    cover_scoring_version: str = "v2"  # v1 | v2
    cover_scoring_v2: Any = field(default_factory=_default_cover_scoring_v2)
    enable_gravity_balance: bool = True
    enable_mmr_diversity: bool = True
    max_consecutive_same_pattern: int = 2
    longshot_mmr_lambda: float = 0.72
    enable_arc_breath: bool = True
    enable_food_grid: bool = True
    mundane_grid_buckets: tuple[str, ...] = ("food",)
    moment: MomentConfig = field(default_factory=MomentConfig)
