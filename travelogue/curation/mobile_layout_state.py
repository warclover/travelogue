"""Trip-level mobile puzzle grids when photo count > 30 (landscape 8 · portrait 4)."""

from __future__ import annotations

from dataclasses import dataclass

MOBILE_PUZZLE_MIN_PHOTOS = 30
MOBILE_GRID8_ROW_LAYOUT = "mobile-landscape-grid-8"
MOBILE_GRID8_SLOT_COUNT = 8
MOBILE_GRID4_ROW_LAYOUT = "mobile-portrait-grid-4"
MOBILE_GRID4_SLOT_COUNT = 4
MOBILE_PERSON_GRID4_HINT = "person-grid-4"


def mobile_grid8_max_for_trip(total_photos: int) -> int:
    """
    Max 8-slot landscape puzzle blocks per trip (only when total > MOBILE_PUZZLE_MIN_PHOTOS).

    31–80: 2; 81–150: 5; >150: 8.
    """
    if total_photos <= MOBILE_PUZZLE_MIN_PHOTOS:
        return 0
    if total_photos <= 80:
        return 2
    if total_photos <= 150:
        return 5
    return 8


def mobile_grid4_max_for_trip(total_photos: int) -> int:
    """
    Max 4-slot portrait 2×2 blocks per trip (only when total > MOBILE_PUZZLE_MIN_PHOTOS).

    31–80: 4; 81–150: 8; >150: 12.
    """
    if total_photos <= MOBILE_PUZZLE_MIN_PHOTOS:
        return 0
    if total_photos <= 80:
        return 4
    if total_photos <= 150:
        return 8
    return 12


def mobile_puzzle_enabled(total_photos: int) -> bool:
    return total_photos > MOBILE_PUZZLE_MIN_PHOTOS


@dataclass
class MobilePuzzlePlannerState:
    grid8_max: int
    grid4_max: int
    grid8_used: int = 0
    grid4_used: int = 0

    @classmethod
    def from_trip_total(cls, total_photos: int) -> MobilePuzzlePlannerState:
        return cls(
            grid8_max=mobile_grid8_max_for_trip(total_photos),
            grid4_max=mobile_grid4_max_for_trip(total_photos),
        )

    def can_use_grid8(self) -> bool:
        return self.grid8_used < self.grid8_max

    def can_use_grid4(self) -> bool:
        return self.grid4_used < self.grid4_max

    def note_grid8(self) -> None:
        self.grid8_used += 1

    def note_grid4(self) -> None:
        self.grid4_used += 1
