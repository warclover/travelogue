"""Phase 23 · peak moment (高光池 + 签名时刻) configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MomentScoringWeights:
    arc_peak: float = 0.30
    anchor: float = 0.25
    aesthetic: float = 0.20
    on_screen: float = 0.15
    featured: float = 0.10


@dataclass
class MomentConfig:
    enabled: bool = True
    pool_ratio: float = 0.05
    pool_min: int = 1
    pool_max: int = 5
    show_exif: bool = True
    pool_solo: bool = True
    pool_exif: bool = True
    signature_label: bool = True
    # HPPL · 次要竖版优先 3→2→1（须 pool_solo=true 才生效）
    pool_portrait_collage: bool = True
    pool_portrait_collage_max_per_screen: int = 3
    pool_portrait_collage_exif: bool = False
    position: str = "inline"  # inline (layout-screen) | arc_peak (reserved)
    auto_disable_small_trip: bool = True
    small_trip_max_assets: int = 15
    secondary_boost: float = 0.12
    min_score: float = 0.35
    small_trip_elevated_min_score: float = 0.45
    scoring: MomentScoringWeights = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.scoring is None:
            self.scoring = MomentScoringWeights()


def effective_secondary_boost(cfg: MomentConfig) -> float:
    """Hero/spread planner boost for momentSecondaryIds; off when pool is solo."""
    if not cfg.enabled or cfg.pool_solo:
        return 0.0
    return cfg.secondary_boost


def moment_config_from_dict(raw: dict[str, Any] | None) -> MomentConfig:
    raw = raw or {}
    scoring_raw = raw.get("scoring") if isinstance(raw.get("scoring"), dict) else {}
    weights_raw = scoring_raw.get("weights") if isinstance(scoring_raw.get("weights"), dict) else {}
    weights = MomentScoringWeights(
        arc_peak=float(weights_raw.get("arc_peak", 0.30)),
        anchor=float(weights_raw.get("anchor", 0.25)),
        aesthetic=float(weights_raw.get("aesthetic", 0.20)),
        on_screen=float(weights_raw.get("on_screen", 0.15)),
        featured=float(weights_raw.get("featured", 0.10)),
    )
    max_per = int(raw.get("pool_portrait_collage_max_per_screen", 3))
    if max_per < 1:
        max_per = 1
    if max_per > 3:
        max_per = 3
    return MomentConfig(
        enabled=bool(raw.get("enabled", True)),
        pool_ratio=float(raw.get("pool_ratio", 0.05)),
        pool_min=int(raw.get("pool_min", 1)),
        pool_max=int(raw.get("pool_max", 5)),
        show_exif=bool(raw.get("show_exif", True)),
        pool_solo=bool(raw.get("pool_solo", True)),
        pool_exif=bool(raw.get("pool_exif", True)),
        signature_label=bool(raw.get("signature_label", True)),
        pool_portrait_collage=bool(raw.get("pool_portrait_collage", True)),
        pool_portrait_collage_max_per_screen=max_per,
        pool_portrait_collage_exif=bool(raw.get("pool_portrait_collage_exif", False)),
        position=str(raw.get("position", "inline")),
        auto_disable_small_trip=bool(raw.get("auto_disable_small_trip", True)),
        small_trip_max_assets=int(raw.get("small_trip_max_assets", 15)),
        secondary_boost=float(raw.get("secondary_boost", 0.12)),
        min_score=float(scoring_raw.get("min_score", raw.get("min_score", 0.35))),
        small_trip_elevated_min_score=float(
            scoring_raw.get(
                "small_trip_elevated_min_score",
                raw.get("small_trip_elevated_min_score", 0.45),
            )
        ),
        scoring=weights,
    )
