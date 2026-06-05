"""Trip-level Web screens rhythm state (quotas + consecutive layout bans)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from travelogue.curation.layout_density import LayoutDensity, LayoutDensityParams, layout_density_params

LayoutKind = Literal["none", "nine", "triple", "six", "portrait_single", "other"]

_PATTERN_SLOTS_RE = re.compile(r"^screen-(?:portrait|landscape|square)-(\d+)$")

PORTRAIT_GRID8_MIN_PHOTOS = 50


def pattern_slot_count(pattern_id: str) -> int | None:
    m = _PATTERN_SLOTS_RE.match(pattern_id)
    return int(m.group(1)) if m else None


def nine_grid_limits_for_trip(total_photos: int) -> tuple[int, int]:
    """
    Min/max nine-grid screens (pattern with 9 slots) by layout-eligible photo count.

    ≤50: 0–1; 51–100: 2–5; 101–200: 4–8; >200: 6–10.
    """
    if total_photos <= 50:
        return 0, 1
    if total_photos <= 100:
        return 2, 5
    if total_photos <= 200:
        return 4, 8
    return 6, 10


def portrait_grid8_max_for_trip(total_photos: int) -> int:
    """Max 8-portrait 2×4 screens when total > PORTRAIT_GRID8_MIN_PHOTOS."""
    if total_photos <= PORTRAIT_GRID8_MIN_PHOTOS:
        return 0
    if total_photos <= 100:
        return 2
    if total_photos <= 200:
        return 4
    return 6


def portrait_grid8_allowed(total_photos: int, *, portrait_heavy: bool) -> bool:
    return total_photos > PORTRAIT_GRID8_MIN_PHOTOS and portrait_heavy


def is_nine_grid_pattern(pattern_id: str) -> bool:
    return pattern_slot_count(pattern_id) == 9


def is_triple_row_pattern(pattern_id: str) -> bool:
    return pattern_slot_count(pattern_id) == 3


def is_six_grid_pattern(pattern_id: str) -> bool:
    return pattern_slot_count(pattern_id) == 6


def is_portrait_single_pattern(pattern_id: str) -> bool:
    return pattern_id in ("screen-portrait-1", "screen-tall-1")


def layout_kind_from_pattern(pattern_id: str) -> LayoutKind:
    if is_nine_grid_pattern(pattern_id):
        return "nine"
    if is_triple_row_pattern(pattern_id):
        return "triple"
    if is_six_grid_pattern(pattern_id):
        return "six"
    if is_portrait_single_pattern(pattern_id):
        return "portrait_single"
    return "other"


@dataclass
class ScreenLayoutPlannerState:
    """
    Nine-grid quota + consecutive bans: *-9, *-3, *-6, *-3+*-6, portrait-1/tall-1.
    Portrait 8-grid (2×4) has a separate quota (layout_kind other).
    """

    nine_min: int
    nine_max: int
    portrait_grid8_max: int = 0
    nine_used: int = 0
    portrait_grid8_used: int = 0
    last_kind: LayoutKind = "none"
    layout_density: LayoutDensity = "balanced"

    @classmethod
    def from_trip_total(
        cls,
        total_photos: int,
        *,
        density: LayoutDensity | None = None,
        density_params: LayoutDensityParams | None = None,
    ) -> ScreenLayoutPlannerState:
        lo, hi = nine_grid_limits_for_trip(total_photos)
        params = density_params or LayoutDensityParams(density=density or "balanced")
        lo, hi = params.adjust_nine_limits(lo, hi)
        return cls(
            nine_min=lo,
            nine_max=hi,
            portrait_grid8_max=portrait_grid8_max_for_trip(total_photos),
            layout_density=params.density,
        )

    @classmethod
    def from_trip(
        cls,
        trip: dict,
        total_photos: int,
        *,
        app_cfg=None,
    ) -> ScreenLayoutPlannerState:
        params = layout_density_params(trip, app_cfg=app_cfg)
        return cls.from_trip_total(total_photos, density_params=params)

    @property
    def min_count(self) -> int:
        return self.nine_min

    @property
    def max_count(self) -> int:
        return self.nine_max

    @property
    def used(self) -> int:
        return self.nine_used

    @property
    def last_was_nine(self) -> bool:
        return self.last_kind == "nine"

    def needs_nine_quota(self) -> bool:
        return self.nine_used < self.nine_min

    def can_use_nine(self) -> bool:
        return self.last_kind != "nine" and self.nine_used < self.nine_max

    def should_prefer_nine(self) -> bool:
        if self.layout_density == "hero_first":
            return False
        return self.needs_nine_quota() and self.can_use_nine()

    def can_use_portrait_grid8(self) -> bool:
        return self.portrait_grid8_used < self.portrait_grid8_max

    def note_portrait_grid8(self) -> None:
        self.portrait_grid8_used += 1

    def can_pick_grid_size(self, size: int) -> bool:
        if size == 9:
            return self.can_use_nine()
        if size == 3:
            return self.last_kind not in ("triple", "six")
        if size == 6:
            return self.last_kind not in ("six", "triple")
        return True

    def can_emit_pattern(self, pattern_id: str) -> bool:
        from travelogue.curation.mosaic.pattern_policy import mosaic_pattern_disabled

        if mosaic_pattern_disabled(pattern_id):
            return False
        kind = layout_kind_from_pattern(pattern_id)
        if kind == "nine":
            return self.can_use_nine()
        if kind == "triple":
            return self.last_kind not in ("triple", "six")
        if kind == "six":
            return self.last_kind not in ("six", "triple")
        if kind == "portrait_single":
            return self.last_kind != "portrait_single"
        return True

    def note_screen(self, pattern_id: str) -> None:
        kind = layout_kind_from_pattern(pattern_id)
        if kind == "nine":
            self.nine_used += 1
        self.last_kind = kind if kind != "other" else "other"


NineGridPlannerState = ScreenLayoutPlannerState

