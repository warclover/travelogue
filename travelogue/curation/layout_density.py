"""Studio fine-craft layout density (PRD-FINE-CRAFT-LAYOUT-DENSITY)."""

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


def resolve_import_layout_density(
    raw: object,
    *,
    import_mode: str,
    app_cfg: AppConfig | None = None,
) -> LayoutDensity | None:
    """Return density for fine_craft import; None clears field on quick_share."""
    mode = str(import_mode or "quick_share").strip().lower()
    if mode != "fine_craft":
        return None
    cfg = app_cfg or get_config()
    enabled = bool(getattr(cfg.layout, "layout_density_enabled", True))
    return normalize_layout_density(raw or "balanced", enabled=enabled)


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


def layout_density_params(trip: dict, *, app_cfg: AppConfig | None = None) -> LayoutDensityParams:
    return LayoutDensityParams(density=layout_density_from_trip(trip, app_cfg=app_cfg))


def layout_density_effect(
    trip_photo_total: int,
    density: LayoutDensity,
    *,
    import_mode: str = "fine_craft",
) -> str:
    mode = str(import_mode or "quick_share").strip().lower()
    if mode != "fine_craft":
        return "ignored_quick"
    if density == "balanced":
        return "full"
    if trip_photo_total < MIN_PHOTOS_COLLAGE_FULL_EFFECT and density == "collage_first":
        return "limited"
    return "full"


def nine_quota_adjusted(
    trip_photo_total: int,
    density: LayoutDensity,
    *,
    app_cfg: AppConfig | None = None,
) -> dict[str, int]:
    """PRD §7.7 · base vs density-adjusted nine-grid quota."""
    from travelogue.curation.screen_layout_state import nine_grid_limits_for_trip

    base_lo, base_hi = nine_grid_limits_for_trip(trip_photo_total)
    params = layout_density_params({"intent": {"layoutDensity": density}}, app_cfg=app_cfg)
    adj_lo, adj_hi = params.adjust_nine_limits(base_lo, base_hi)
    return {
        "min": adj_lo,
        "max": adj_hi,
        "baseMin": base_lo,
        "baseMax": base_hi,
    }


def intent_hints_for_density(density: LayoutDensity) -> dict[str, object]:
    if density == "balanced":
        return {}
    hints: dict[str, object] = {"layoutDensity": density}
    if density == "hero_first":
        hints["preferMosaic"] = False
        hints["nineQuotaScale"] = 0.5
    elif density == "collage_first":
        hints["preferMosaic"] = True
        hints["nineQuotaScale"] = 1.15
    return hints
