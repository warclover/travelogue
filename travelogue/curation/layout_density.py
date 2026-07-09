"""Studio fine-craft layout density (PRD-FINE-CRAFT-LAYOUT-DENSITY)."""

from __future__ import annotations

from travelogue.config import AppConfig
from travelogue.layout_contract.density import (
    MIN_PHOTOS_COLLAGE_FULL_EFFECT,
    LayoutDensity,
    LayoutDensityParams,
    layout_density_from_trip,
    layout_density_params,
    normalize_layout_density,
)

__all__ = [
    "MIN_PHOTOS_COLLAGE_FULL_EFFECT",
    "LayoutDensity",
    "LayoutDensityParams",
    "dense_collage_quota_adjusted",
    "intent_hints_for_density",
    "layout_density_effect",
    "layout_density_from_trip",
    "layout_density_params",
    "nine_quota_adjusted",
    "normalize_layout_density",
    "resolve_import_layout_density",
]


def resolve_import_layout_density(
    raw: object,
    *,
    import_mode: str,
    app_cfg: AppConfig | None = None,
) -> LayoutDensity | None:
    mode = str(import_mode or "quick_share").strip().lower()
    if mode != "fine_craft":
        return None
    from travelogue.config import get_config

    cfg = app_cfg or get_config()
    enabled = bool(getattr(cfg.layout, "layout_density_enabled", True))
    return normalize_layout_density(raw or "balanced", enabled=enabled)


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


def dense_collage_quota_adjusted(
    trip_photo_total: int,
    density: LayoutDensity,
    *,
    app_cfg: AppConfig | None = None,
) -> dict[str, int]:
    from travelogue.layout_contract.rhythm import dense_collage_limits_for_trip

    base_lo, base_hi = dense_collage_limits_for_trip(trip_photo_total)
    params = layout_density_params({"intent": {"layoutDensity": density}}, app_cfg=app_cfg)
    adj_lo, adj_hi = params.adjust_dense_collage_limits(
        base_lo, base_hi, total_photos=trip_photo_total
    )
    return {
        "min": adj_lo,
        "max": adj_hi,
        "baseMin": base_lo,
        "baseMax": base_hi,
    }


def nine_quota_adjusted(
    trip_photo_total: int,
    density: LayoutDensity,
    *,
    app_cfg: AppConfig | None = None,
) -> dict[str, int]:
    from travelogue.layout_contract.rhythm import nine_grid_limits_for_trip

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
