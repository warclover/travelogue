"""Rhythm helpers · pack → ScreenLayoutPlannerState (W1 parity)."""

from __future__ import annotations

from travelogue.curation.layout_density import LayoutDensity, LayoutDensityParams
from travelogue.curation.screen_layout_state import (
    ScreenLayoutPlannerState,
    portrait_grid8_max_for_trip,
)
from travelogue.layout_engine.registry import StrategyPack


def nine_grid_limits_from_pack(pack: StrategyPack) -> list[tuple[int, int, int]]:
    """Return (max_photos, min, max) tiers from pack rhythm."""
    rhythm = pack.raw.get("rhythm") or {}
    rows = rhythm.get("nine_grid_limits") or []
    out: list[tuple[int, int, int]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        out.append(
            (
                int(row.get("max_photos", 0)),
                int(row.get("min", 0)),
                int(row.get("max", 0)),
            )
        )
    return out


def nine_grid_limits_for_trip_from_pack(
    total_photos: int,
    pack: StrategyPack,
) -> tuple[int, int]:
    tiers = nine_grid_limits_from_pack(pack)
    if not tiers:
        from travelogue.curation.screen_layout_state import nine_grid_limits_for_trip

        return nine_grid_limits_for_trip(total_photos)
    tiers = sorted(tiers, key=lambda t: t[0])
    lo, hi = tiers[-1][1], tiers[-1][2]
    for max_photos, tmin, tmax in tiers:
        if total_photos <= max_photos:
            lo, hi = tmin, tmax
            break
    return lo, hi


def layout_state_from_pack(
    total_photos: int,
    pack: StrategyPack,
    *,
    density: LayoutDensity | None = None,
    density_params: LayoutDensityParams | None = None,
) -> ScreenLayoutPlannerState:
    lo, hi = nine_grid_limits_for_trip_from_pack(total_photos, pack)
    params = density_params or LayoutDensityParams(density=density or "balanced")
    lo, hi = params.adjust_nine_limits(lo, hi)
    rhythm = pack.raw.get("rhythm") or {}
    pg8_min = int(rhythm.get("portrait_grid8_min_photos", 50))
    pg8_max = portrait_grid8_max_for_trip(total_photos) if total_photos > pg8_min else 0
    return ScreenLayoutPlannerState(
        nine_min=lo,
        nine_max=hi,
        portrait_grid8_max=pg8_max,
        layout_density=params.density,
    )
