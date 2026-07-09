"""Shared layout density types (M-B4a kernel · PRD §5.2.1)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from travelogue.config import AppConfig, get_config

LayoutDensity = Literal["balanced", "hero_first", "collage_first"]

_VALID: frozenset[str] = frozenset({"balanced", "hero_first", "collage_first"})

MIN_PHOTOS_COLLAGE_FULL_EFFECT = 35


def normalize_layout_density(raw: object, *, enabled: bool = True) -> LayoutDensity:
    if not enabled:
        return "balanced"
    value = str(raw or "").strip().lower()
    if value in _VALID:
        return value  # type: ignore[return-value]
    return "balanced"


def layout_density_from_trip(trip: dict, *, app_cfg: AppConfig | None = None) -> LayoutDensity:
    cfg = app_cfg or get_config()
    enabled = bool(getattr(cfg.layout, "layout_density_enabled", True))
    intent = trip.get("intent") or {}
    return normalize_layout_density(intent.get("layoutDensity"), enabled=enabled)


@dataclass(frozen=True)
class LayoutDensityParams:
    density: LayoutDensity = "balanced"

    def adjust_nine_limits(self, nine_min: int, nine_max: int) -> tuple[int, int]:
        if self.density == "balanced":
            return nine_min, nine_max
        if self.density == "hero_first":
            return max(0, int(math.floor(nine_min * 0.25))), max(0, int(math.floor(nine_max * 0.6)))
        new_max = min(int(math.ceil(nine_max * 1.1)), 10) if nine_max > 0 else nine_max
        new_min = min(int(math.ceil(nine_min * 1.2)), new_max) if nine_min > 0 else 0
        return new_min, new_max

    def adjust_dense_collage_limits(
        self,
        dense_min: int,
        dense_max: int,
        *,
        total_photos: int = 0,
    ) -> tuple[int, int]:
        if self.density == "balanced":
            return dense_min, dense_max
        if self.density == "hero_first":
            return dense_min, max(0, int(math.floor(dense_max * 0.35)))
        cap = max(dense_max, (total_photos // 4) if total_photos > 0 else dense_max)
        new_max = min(int(math.ceil(dense_max * 1.15)), cap) if dense_max > 0 else dense_max
        if MIN_PHOTOS_COLLAGE_FULL_EFFECT <= total_photos <= 50:
            new_max = max(new_max, 3)
        return dense_min, new_max


def layout_density_params(trip: dict, *, app_cfg: AppConfig | None = None) -> LayoutDensityParams:
    return LayoutDensityParams(density=layout_density_from_trip(trip, app_cfg=app_cfg))
