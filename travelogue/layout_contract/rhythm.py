"""Rhythm constants and pure pattern helpers (M-B4a layout kernel)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

LayoutKind = Literal[
    "none", "nine", "triple", "six", "portrait_single", "portrait_pair", "other"
]

_PATTERN_SLOTS_RE = re.compile(r"^screen-(?:portrait|landscape|square)-(\d+)$")

PORTRAIT_GRID8_MIN_PHOTOS = 50
DENSE_COLLAGE_SLOT_MIN = 4
BREATH_PATTERN = "screen-breath-pause"

MAX_PORTRAIT_PAIR_STREAK = 2
MAX_PORTRAIT_ORIENTATION_STREAK = 6

PORTRAIT_PAIR_PATTERN = "screen-portrait-2"
PORTRAIT_PAIR_PATTERNS = frozenset({PORTRAIT_PAIR_PATTERN})
PORTRAIT_SINGLE_PATTERNS = frozenset({"screen-portrait-1", "screen-tall-1"})
FULL_BLEED_PORTRAIT_PATTERNS = frozenset(
    {"screen-portrait-1", "screen-tall-1", "screen-plate"}
)
PORTRAIT_ORIENTATION_PATTERNS = frozenset(
    {
        "screen-portrait-1",
        "screen-portrait-2",
        "screen-portrait-3",
        "screen-portrait-3-editorial",
        "screen-tall-1",
    }
)

PATTERN_PORTRAIT_3_EDITORIAL = "screen-portrait-3-editorial"

DEFAULT_CONSECUTIVE_BANS: frozenset[tuple[str, str]] = frozenset(
    {
        ("nine", "nine"),
        ("triple", "triple"),
        ("triple", "six"),
        ("six", "triple"),
        ("six", "six"),
        ("portrait_single", "portrait_single"),
    }
)


@dataclass(frozen=True)
class LateChapterPairingPolicy:
    from_chapter_index: int = 3
    reset_orientation_streak: bool = True
    reset_pair_streak: bool = True
    no_outward_portrait_carry: bool = True
    flush_lookahead_portraits: int = 3
    beam_portrait_single_penalty: float = 0.12
    beam_portrait_pair_bonus: float = 0.06

    def is_late_chapter(self, chapter_index_1based: int) -> bool:
        return chapter_index_1based >= self.from_chapter_index


@dataclass(frozen=True)
class RhythmRules:
    max_portrait_pair_streak: int = MAX_PORTRAIT_PAIR_STREAK
    max_portrait_orientation_streak: int = MAX_PORTRAIT_ORIENTATION_STREAK
    portrait_carry_max_hops: int = 0
    consecutive_bans: frozenset[tuple[str, str]] = DEFAULT_CONSECUTIVE_BANS
    late_chapter_pairing: LateChapterPairingPolicy = LateChapterPairingPolicy()

    @classmethod
    def from_config(cls, cfg=None) -> RhythmRules:
        try:
            from travelogue.config import get_config

            app = cfg if cfg is not None else get_config()
        except Exception:
            return cls()
        rhythm = getattr(getattr(app, "layout", None), "rhythm", None)
        if rhythm is None:
            return cls()
        late = getattr(rhythm, "late_chapter_pairing", None)
        late_policy = LateChapterPairingPolicy(
            from_chapter_index=int(getattr(late, "from_chapter_index", 3)),
            reset_orientation_streak=bool(getattr(late, "reset_orientation_streak", True)),
            reset_pair_streak=bool(getattr(late, "reset_pair_streak", True)),
            no_outward_portrait_carry=bool(getattr(late, "no_outward_portrait_carry", True)),
            flush_lookahead_portraits=int(getattr(late, "flush_lookahead_portraits", 3)),
            beam_portrait_single_penalty=float(
                getattr(late, "beam_portrait_single_penalty", 0.12)
            ),
            beam_portrait_pair_bonus=float(getattr(late, "beam_portrait_pair_bonus", 0.06)),
        )
        return cls(
            max_portrait_pair_streak=int(rhythm.max_portrait_pair_streak),
            max_portrait_orientation_streak=int(rhythm.max_portrait_orientation_streak),
            portrait_carry_max_hops=int(getattr(rhythm, "portrait_carry_max_hops", 0)),
            late_chapter_pairing=late_policy,
        )


def pattern_slot_count(pattern_id: str) -> int | None:
    match = _PATTERN_SLOTS_RE.match(pattern_id)
    return int(match.group(1)) if match else None


def dense_collage_limits_for_trip(total_photos: int) -> tuple[int, int]:
    if total_photos <= 50:
        return 0, 1
    if total_photos <= 100:
        return 0, 3
    if total_photos <= 200:
        return 0, 5
    return 0, 7


def nine_grid_limits_for_trip(total_photos: int) -> tuple[int, int]:
    if total_photos <= 50:
        return 0, 1
    if total_photos <= 100:
        return 2, 5
    if total_photos <= 200:
        return 4, 8
    return 6, 10


def portrait_grid8_max_for_trip(total_photos: int) -> int:
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
    if pattern_id == PATTERN_PORTRAIT_3_EDITORIAL:
        return True
    return pattern_slot_count(pattern_id) == 3


def is_six_grid_pattern(pattern_id: str) -> bool:
    return pattern_slot_count(pattern_id) == 6


def is_portrait_single_pattern(pattern_id: str | None) -> bool:
    return pattern_id in PORTRAIT_SINGLE_PATTERNS


def is_portrait_pair_pattern(pattern_id: str | None) -> bool:
    return pattern_id in PORTRAIT_PAIR_PATTERNS


def is_portrait_orientation_pattern(pattern_id: str | None) -> bool:
    return pattern_id in PORTRAIT_ORIENTATION_PATTERNS


def layout_kind_from_pattern(pattern_id: str) -> LayoutKind:
    if is_nine_grid_pattern(pattern_id):
        return "nine"
    if is_triple_row_pattern(pattern_id):
        return "triple"
    if is_six_grid_pattern(pattern_id):
        return "six"
    if is_portrait_single_pattern(pattern_id):
        return "portrait_single"
    if is_portrait_pair_pattern(pattern_id):
        return "portrait_pair"
    return "other"
