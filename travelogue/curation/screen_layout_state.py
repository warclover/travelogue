"""Trip-level Web screens rhythm state (quotas + consecutive layout bans)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from travelogue.curation.layout_density import (
    LayoutDensity,
    LayoutDensityParams,
    layout_density_params,
)

LayoutKind = Literal[
    "none", "nine", "triple", "six", "portrait_single", "portrait_pair", "other"
]

_PATTERN_SLOTS_RE = re.compile(r"^screen-(?:portrait|landscape|square)-(\d+)$")

PORTRAIT_GRID8_MIN_PHOTOS = 50

# P21 · dense collage（≥4 槽）卷级配额与相邻禁令
DENSE_COLLAGE_SLOT_MIN = 4

# ---------------------------------------------------------------------------
# 节奏规则单一来源（排版规则优化 v0.5 · R-01~R-08 / V-08 / V-09）。
# 规划期硬约束（ScreenLayoutPlannerState）与事后审计（layout_constraints）
# 共用本模块的常量与判定，禁止在别处复制阈值。
# ---------------------------------------------------------------------------

# R-06 · 两张并排竖版（portrait-2 / person-pair 等价）连续上限。
MAX_PORTRAIT_PAIR_STREAK = 2
# R-08 · 同朝向（全竖版屏）连续上限（触顶强制换气）。
MAX_PORTRAIT_ORIENTATION_STREAK = 6

PORTRAIT_PAIR_PATTERN = "screen-portrait-2"
PORTRAIT_PAIR_PATTERNS = frozenset({PORTRAIT_PAIR_PATTERN})
PORTRAIT_SINGLE_PATTERNS = frozenset({"screen-portrait-1", "screen-tall-1"})
# V-08/V-09 · 满屏竖图等价类（plate 仅 sole portrait slot 时计入，见
# layout_constraints.is_full_bleed_portrait_screen）。
FULL_BLEED_PORTRAIT_PATTERNS = frozenset(
    {"screen-portrait-1", "screen-tall-1", "screen-plate"}
)
# R-08 · 计入「全竖版屏」朝向 streak 的 patternId。
PORTRAIT_ORIENTATION_PATTERNS = frozenset(
    {"screen-portrait-1", "screen-portrait-2", "screen-portrait-3", "screen-tall-1"}
)

# (last_kind, next_kind) 连续禁令对 — 与历史硬编码 can_emit_pattern 等价：
# 禁连 *-9 / *-3 / *-6、禁 *-3 与 *-6 相邻、禁连满屏竖单。
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
class RhythmRules:
    """节奏阈值集合（默认值 = 历史硬编码，保证输出等价）。

    来源优先级：LSE 策略包（rhythm 段） > config.layout.rhythm > 代码默认。
    """

    max_portrait_pair_streak: int = MAX_PORTRAIT_PAIR_STREAK
    max_portrait_orientation_streak: int = MAX_PORTRAIT_ORIENTATION_STREAK
    portrait_carry_max_hops: int = 0
    consecutive_bans: frozenset[tuple[str, str]] = DEFAULT_CONSECUTIVE_BANS

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
        return cls(
            max_portrait_pair_streak=int(rhythm.max_portrait_pair_streak),
            max_portrait_orientation_streak=int(rhythm.max_portrait_orientation_streak),
            portrait_carry_max_hops=int(getattr(rhythm, "portrait_carry_max_hops", 0)),
        )


def pattern_slot_count(pattern_id: str) -> int | None:
    m = _PATTERN_SLOTS_RE.match(pattern_id)
    return int(m.group(1)) if m else None


def dense_collage_limits_for_trip(total_photos: int) -> tuple[int, int]:
    """P21 · max dense collage screens (slot≥4) per trip; no min quota."""
    if total_photos <= 50:
        return 0, 1
    if total_photos <= 100:
        return 0, 3
    if total_photos <= 200:
        return 0, 5
    return 0, 7


def pattern_dense_slot_count(pattern_id: str) -> int | None:
    """Slot count for dense collage budgeting (LTE + legacy grid patterns)."""
    n = pattern_slot_count(pattern_id)
    if n is not None:
        return n
    if pattern_id == "screen-portrait-grid-8":
        return 8
    if pattern_id.startswith("screen-mosaic-"):
        try:
            from travelogue.curation.mosaic.lte_adapter import _mosaic_slot_count

            return _mosaic_slot_count(pattern_id)
        except Exception:
            return None
    return None


def is_dense_collage_pattern(pattern_id: str, *, min_slots: int = DENSE_COLLAGE_SLOT_MIN) -> bool:
    n = pattern_dense_slot_count(pattern_id)
    return n is not None and n >= min_slots


def is_large_mosaic_pattern(
    pattern_id: str,
    *,
    min_slots: int = 5,
) -> bool:
    """True for mosaic/grid patterns with at least ``min_slots`` photo slots."""
    n = pattern_dense_slot_count(pattern_id)
    return n is not None and n >= min_slots


def large_mosaic_limits_from_config() -> tuple[int, int, int]:
    """(min_slots, max_per_template_trip, max_per_chapter) from mosaic.density_budget."""
    from travelogue.config import get_config

    db = get_config().mosaic.density_budget
    return (
        int(db.large_mosaic_min_slots),
        int(db.max_per_template_per_trip),
        int(db.max_large_mosaic_per_chapter),
    )


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


def is_portrait_single_pattern(pattern_id: str | None) -> bool:
    return pattern_id in PORTRAIT_SINGLE_PATTERNS


def is_portrait_pair_pattern(pattern_id: str | None) -> bool:
    """R-06 · 两张竖版并排（含 person-pair 等价 patternId）。"""
    return pattern_id in PORTRAIT_PAIR_PATTERNS


def is_portrait_orientation_pattern(pattern_id: str | None) -> bool:
    """R-08 · 计入「全竖版屏」朝向 streak 的 patternId。"""
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


@dataclass
class ScreenLayoutPlannerState:
    """
    Nine-grid quota + consecutive bans: *-9, *-3, *-6, *-3+*-6, portrait-1/tall-1.
    Portrait 8-grid (2×4) has a separate quota (layout_kind other).
    """

    nine_min: int
    nine_max: int
    dense_collage_max: int = 0
    portrait_grid8_max: int = 0
    nine_used: int = 0
    dense_collage_used: int = 0
    portrait_grid8_used: int = 0
    last_kind: LayoutKind = "none"
    last_was_dense_collage: bool = False
    dense_collage_min_slots: int = DENSE_COLLAGE_SLOT_MIN
    large_mosaic_min_slots: int = 5
    large_mosaic_max_per_template_trip: int = 2
    large_mosaic_max_per_chapter: int = 1
    large_mosaic_chapter_used: int = 0
    last_pattern_id: str = ""
    pattern_streak: int = 0
    portrait_orientation_streak: int = 0
    layout_density: LayoutDensity = "balanced"
    pattern_counts: dict[str, int] = field(default_factory=dict)
    rhythm: RhythmRules = field(default_factory=RhythmRules)

    @classmethod
    def from_trip_total(
        cls,
        total_photos: int,
        *,
        density: LayoutDensity | None = None,
        density_params: LayoutDensityParams | None = None,
        rhythm: RhythmRules | None = None,
    ) -> ScreenLayoutPlannerState:
        lo, hi = nine_grid_limits_for_trip(total_photos)
        _dense_lo, dense_hi = dense_collage_limits_for_trip(total_photos)
        params = density_params or LayoutDensityParams(density=density or "balanced")
        lo, hi = params.adjust_nine_limits(lo, hi)
        _dense_lo, dense_hi = params.adjust_dense_collage_limits(
            _dense_lo, dense_hi, total_photos=total_photos
        )
        lm_min, lm_trip, lm_ch = large_mosaic_limits_from_config()
        return cls(
            nine_min=lo,
            nine_max=hi,
            dense_collage_max=dense_hi,
            portrait_grid8_max=portrait_grid8_max_for_trip(total_photos),
            layout_density=params.density,
            rhythm=rhythm if rhythm is not None else RhythmRules.from_config(),
            large_mosaic_min_slots=lm_min,
            large_mosaic_max_per_template_trip=lm_trip,
            large_mosaic_max_per_chapter=lm_ch,
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
        return cls.from_trip_total(
            total_photos,
            density_params=params,
            rhythm=RhythmRules.from_config(app_cfg),
        )

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

    def can_use_dense_collage(self, pattern_id: str) -> bool:
        """P21 · dense collage quota + consecutive ban."""
        if not is_dense_collage_pattern(pattern_id, min_slots=self.dense_collage_min_slots):
            return True
        if self.dense_collage_used >= self.dense_collage_max:
            return False
        return not self.last_was_dense_collage

    def can_use_dense_collage_window(self, window_size: int) -> bool:
        """True when an MCS window of this size may consume dense budget."""
        if window_size < self.dense_collage_min_slots:
            return True
        if not self.can_use_large_mosaic_window(window_size):
            return False
        if self.dense_collage_used >= self.dense_collage_max:
            return False
        return not self.last_was_dense_collage

    def begin_chapter_bucket(self) -> None:
        """Reset per-chapter large-mosaic counter at each day/chapter bucket."""
        self.large_mosaic_chapter_used = 0

    def can_use_large_mosaic_window(self, window_size: int) -> bool:
        if window_size < self.large_mosaic_min_slots:
            return True
        return self.large_mosaic_chapter_used < self.large_mosaic_max_per_chapter

    def can_use_large_mosaic(self, pattern_id: str) -> bool:
        if not is_large_mosaic_pattern(pattern_id, min_slots=self.large_mosaic_min_slots):
            return True
        if self.large_mosaic_chapter_used >= self.large_mosaic_max_per_chapter:
            return False
        used = self.pattern_counts.get(pattern_id, 0)
        return used < self.large_mosaic_max_per_template_trip

    def sync_large_mosaic_chapter_used(self, pattern_ids: list[str]) -> None:
        self.large_mosaic_chapter_used = sum(
            1
            for pid in pattern_ids
            if is_large_mosaic_pattern(pid, min_slots=self.large_mosaic_min_slots)
        )

    def can_pick_grid_size(self, size: int) -> bool:
        if size == 9:
            return self.can_use_nine()
        if size == 3:
            return self.last_kind not in ("triple", "six")
        if size == 6:
            return self.last_kind not in ("six", "triple")
        return True

    def can_emit_pattern(self, pattern_id: str) -> bool:
        from travelogue.curation.mosaic.lte_adapter import (
            mosaic_pattern_disabled,
            template_rhythm_max_per_chapter,
        )

        if mosaic_pattern_disabled(pattern_id):
            return False
        max_ch = template_rhythm_max_per_chapter(pattern_id)
        if max_ch is not None and self.pattern_counts.get(pattern_id, 0) >= max_ch:
            return False
        if not self.can_use_dense_collage(pattern_id):
            return False
        if not self.can_use_large_mosaic(pattern_id):
            return False
        kind = layout_kind_from_pattern(pattern_id)
        if kind == "nine" and self.nine_used >= self.nine_max:
            return False
        if (self.last_kind, kind) in self.rhythm.consecutive_bans:
            return False
        if kind == "portrait_pair":
            return (
                self.current_portrait_pair_streak()
                < self.rhythm.max_portrait_pair_streak
            )
        return True

    def current_portrait_pair_streak(self) -> int:
        """R-06 · 已连续出屏的 portrait-2 数（供批量出屏路径取种子）。"""
        if self.last_pattern_id == PORTRAIT_PAIR_PATTERN:
            return self.pattern_streak
        return 0

    def orientation_budget(self) -> int:
        """R-08 · 触发强制换气前还允许连续出的「全竖版屏」数。"""
        return max(
            0,
            self.rhythm.max_portrait_orientation_streak
            - self.portrait_orientation_streak,
        )

    def note_screen(self, pattern_id: str) -> None:
        if pattern_id:
            self.pattern_counts[pattern_id] = self.pattern_counts.get(pattern_id, 0) + 1
        kind = layout_kind_from_pattern(pattern_id)
        if kind == "nine":
            self.nine_used += 1
        if is_dense_collage_pattern(pattern_id, min_slots=self.dense_collage_min_slots):
            self.dense_collage_used += 1
            self.last_was_dense_collage = True
        elif pattern_id:
            self.last_was_dense_collage = False
        if is_large_mosaic_pattern(pattern_id, min_slots=self.large_mosaic_min_slots):
            self.large_mosaic_chapter_used += 1
        self.last_kind = kind if kind != "other" else "other"
        if pattern_id and pattern_id == self.last_pattern_id:
            self.pattern_streak += 1
        else:
            self.pattern_streak = 1 if pattern_id else 0
        self.last_pattern_id = pattern_id or ""
        # R-08 · 朝向 streak：全竖版屏累计，任何其他 content pattern 打断。
        if pattern_id and is_portrait_orientation_pattern(pattern_id):
            self.portrait_orientation_streak += 1
        elif pattern_id:
            self.portrait_orientation_streak = 0

