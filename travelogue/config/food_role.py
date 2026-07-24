"""Food Role Policy (FRP) configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

FoodSlotPolicy = Literal["demote", "exclude", "off"]
FoodHeroPolicy = Literal["skip", "allow"]


@dataclass
class FoodRoleConfig:
    cover_policy: FoodSlotPolicy = "demote"
    cover_multiplier: float = 0.15
    closing_policy: FoodSlotPolicy = "demote"
    closing_multiplier: float = 0.15
    hero_policy: FoodHeroPolicy = "skip"
    allow_food_in_moment: bool = False
    moment_multiplier: float = 0.05
    grid_min_items: int = 2
    cluster_window_seconds: float = 3600.0
    grid_max_interruptions: int = 2


def _norm_slot_policy(raw: Any, default: FoodSlotPolicy) -> FoodSlotPolicy:
    text = str(raw or default).strip().lower()
    if text in {"demote", "exclude", "off"}:
        return text  # type: ignore[return-value]
    return default


def _norm_hero_policy(raw: Any, default: FoodHeroPolicy = "skip") -> FoodHeroPolicy:
    text = str(raw or default).strip().lower()
    if text in {"skip", "allow"}:
        return text  # type: ignore[return-value]
    return default


def food_role_config_from_dict(raw: dict[str, Any] | None) -> FoodRoleConfig:
    raw = raw or {}
    return FoodRoleConfig(
        cover_policy=_norm_slot_policy(
            raw.get("cover_policy", raw.get("coverPolicy")), "demote"
        ),
        cover_multiplier=float(
            raw.get("cover_multiplier", raw.get("coverMultiplier", 0.15))
        ),
        closing_policy=_norm_slot_policy(
            raw.get("closing_policy", raw.get("closingPolicy")), "demote"
        ),
        closing_multiplier=float(
            raw.get("closing_multiplier", raw.get("closingMultiplier", 0.15))
        ),
        hero_policy=_norm_hero_policy(
            raw.get("hero_policy", raw.get("heroPolicy")), "skip"
        ),
        allow_food_in_moment=bool(
            raw.get(
                "allow_food_in_moment",
                raw.get("allowFoodInMoment", False),
            )
        ),
        moment_multiplier=float(
            raw.get("moment_multiplier", raw.get("momentMultiplier", 0.05))
        ),
        grid_min_items=max(
            1, int(raw.get("grid_min_items", raw.get("gridMinItems", 2)))
        ),
        cluster_window_seconds=float(
            raw.get(
                "cluster_window_seconds",
                raw.get("clusterWindowSeconds", 3600.0),
            )
        ),
        grid_max_interruptions=max(
            0,
            int(
                raw.get(
                    "grid_max_interruptions",
                    raw.get("gridMaxInterruptions", 2),
                )
            ),
        ),
    )
