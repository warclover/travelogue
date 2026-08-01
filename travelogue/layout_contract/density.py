"""Shared layout density types (M-B4a kernel · PRD §5.2.1)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from travelogue.errors import ConfigError

LayoutDensity = Literal["balanced", "hero_first", "collage_first"]

_VALID: frozenset[str] = frozenset({"balanced", "hero_first", "collage_first"})

MIN_PHOTOS_COLLAGE_FULL_EFFECT = 35


def normalize_layout_density(raw: object, *, enabled: bool = True) -> LayoutDensity:
    """Normalize density; empty/None → balanced; illegal non-empty → ConfigError (LTN R-A2)."""
    if not enabled:
        return "balanced"
    value = str(raw or "").strip().lower()
    if not value:
        return "balanced"
    if value in _VALID:
        return value  # type: ignore[return-value]
    raise ConfigError(
        f"invalid layoutDensity={raw!r}; expected one of "
        f"{sorted(_VALID)} (LTN R-A2 fail-loud)"
    )


def layout_density_from_trip(trip: dict, *, app_cfg=None) -> LayoutDensity:
    layout = getattr(app_cfg, "layout", None)
    enabled = bool(getattr(layout, "layout_density_enabled", True))
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
            # LTN H6/S3 · floor at 1 when base max>0 so small trips keep a legal hero slot.
            if dense_max <= 0:
                return dense_min, 0
            return dense_min, max(1, int(math.floor(dense_max * 0.35)))
        cap = max(dense_max, (total_photos // 4) if total_photos > 0 else dense_max)
        new_max = min(int(math.ceil(dense_max * 1.15)), cap) if dense_max > 0 else dense_max
        if MIN_PHOTOS_COLLAGE_FULL_EFFECT <= total_photos <= 50:
            new_max = max(new_max, 3)
        return dense_min, new_max


def layout_density_params(trip: dict, *, app_cfg=None) -> LayoutDensityParams:
    return LayoutDensityParams(density=layout_density_from_trip(trip, app_cfg=app_cfg))
