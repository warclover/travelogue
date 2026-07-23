"""Trip-level Web screens rhythm state (quotas + consecutive layout bans)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from travelogue.layout_contract.density import (
    LayoutDensity,
    LayoutDensityParams,
    layout_density_params,
)

HeroReserve = Literal["idle", "armed", "consumed", "released"]
HeroSixOpportunity = Literal["idle", "armed", "consumed", "released"]
from travelogue.layout_contract.patterns import is_editorial_composite_pattern
from travelogue.layout_contract.rhythm import (  # re-export for curation callers
    DEFAULT_CONSECUTIVE_BANS,
    DENSE_COLLAGE_SLOT_MIN,
    FULL_BLEED_PORTRAIT_PATTERNS,
    MAX_PORTRAIT_ORIENTATION_STREAK,
    MAX_PORTRAIT_PAIR_STREAK,
    PATTERN_PORTRAIT_3_EDITORIAL,
    PORTRAIT_GRID8_MIN_PHOTOS,
    PORTRAIT_ORIENTATION_PATTERNS,
    PORTRAIT_PAIR_PATTERN,
    PORTRAIT_PAIR_PATTERNS,
    PORTRAIT_SINGLE_PATTERNS,
    LateChapterPairingPolicy,
    LayoutKind,
    RhythmRules,
    dense_collage_limits_for_trip,
    is_nine_grid_pattern,
    is_portrait_orientation_pattern,
    is_portrait_pair_pattern,
    is_portrait_single_pattern,
    is_six_grid_pattern,
    is_triple_row_pattern,
    layout_kind_from_pattern,
    nine_grid_limits_for_trip,
    pattern_slot_count,
    portrait_grid8_allowed,
    portrait_grid8_max_for_trip,
)

__all__ = [
    "DEFAULT_CONSECUTIVE_BANS",
    "DENSE_COLLAGE_SLOT_MIN",
    "FULL_BLEED_PORTRAIT_PATTERNS",
    "LateChapterPairingPolicy",
    "LayoutKind",
    "MAX_PORTRAIT_ORIENTATION_STREAK",
    "MAX_PORTRAIT_PAIR_STREAK",
    "PATTERN_PORTRAIT_3_EDITORIAL",
    "PORTRAIT_GRID8_MIN_PHOTOS",
    "PORTRAIT_ORIENTATION_PATTERNS",
    "PORTRAIT_PAIR_PATTERN",
    "PORTRAIT_PAIR_PATTERNS",
    "PORTRAIT_SINGLE_PATTERNS",
    "RhythmRules",
    "ScreenLayoutPlannerState",
    "dense_collage_limits_for_trip",
    "is_dense_collage_pattern",
    "is_large_mosaic_pattern",
    "is_nine_grid_pattern",
    "is_portrait_orientation_pattern",
    "is_portrait_pair_pattern",
    "is_portrait_single_pattern",
    "is_six_grid_pattern",
    "is_triple_row_pattern",
    "large_mosaic_limits_from_config",
    "layout_kind_from_pattern",
    "nine_grid_limits_for_trip",
    "pattern_dense_slot_count",
    "pattern_slot_count",
    "portrait_grid8_allowed",
    "portrait_grid8_max_for_trip",
]


_MOSAIC_WINDOW_SLOTS_RE = re.compile(r"^screen-mosaic-(\d+)(?:-|$)")


def pattern_dense_slot_count(pattern_id: str) -> int | None:
    n = pattern_slot_count(pattern_id)
    if n is not None:
        return n
    if pattern_id == "screen-portrait-grid-8":
        return 8
    # Parse window size from pattern id (e.g. screen-mosaic-5-...) without importing LTE.
    mosaic = _MOSAIC_WINDOW_SLOTS_RE.match(pattern_id)
    if mosaic:
        return int(mosaic.group(1))
    return None


def is_dense_collage_pattern(pattern_id: str, *, min_slots: int = DENSE_COLLAGE_SLOT_MIN) -> bool:
    if is_editorial_composite_pattern(pattern_id):
        return False
    n = pattern_dense_slot_count(pattern_id)
    return n is not None and n >= min_slots


def is_large_mosaic_pattern(
    pattern_id: str,
    *,
    min_slots: int = 5,
) -> bool:
    n = pattern_dense_slot_count(pattern_id)
    return n is not None and n >= min_slots


def large_mosaic_limits_from_config(cfg=None) -> tuple[int, int, int]:
    db = getattr(getattr(cfg, "mosaic", None), "density_budget", None)
    if db is None:
        return 5, 2, 1
    return (
        int(db.large_mosaic_min_slots),
        int(db.max_per_template_per_trip),
        int(db.max_large_mosaic_per_chapter),
    )


@dataclass
class ScreenLayoutPlannerState:
    """Nine-grid quota + consecutive bans (implementation stays in curation until M-B4b)."""

    nine_min: int
    nine_max: int
    dense_collage_max: int = 0
    # LTN E4 · soft aspirational floor (never forces emit; see asymmetric_quota.py)
    dense_collage_opportunity_min: int = 0
    dense_opportunity_seen: int = 0
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
    editorial_composite_chapter_used: int = 0
    last_pattern_id: str = ""
    pattern_streak: int = 0
    portrait_orientation_streak: int = 0
    layout_density: LayoutDensity = "balanced"
    pattern_counts: dict[str, int] = field(default_factory=dict)
    rhythm: RhythmRules = field(default_factory=RhythmRules)
    # LTN C5 · opportunity reserve (no extra quota; P21 / adjacent bans still apply)
    hero_reserve: HeroReserve = "idle"
    # MTSO PR-B · cursor-bound six-hero opportunity (orthogonal to hero_reserve)
    hero_six_opportunity: HeroSixOpportunity = "idle"
    hero_six_armed_cursor: int | None = None

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
        from travelogue.layout_contract.asymmetric_quota import dense_opportunity_min_for

        return cls(
            nine_min=lo,
            nine_max=hi,
            dense_collage_max=dense_hi,
            dense_collage_opportunity_min=dense_opportunity_min_for(
                dense_max=dense_hi, track=None
            ),
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
        state = cls.from_trip_total(
            total_photos,
            density_params=params,
            rhythm=RhythmRules.from_config(app_cfg),
        )
        lm_min, lm_trip, lm_ch = large_mosaic_limits_from_config(app_cfg)
        state.large_mosaic_min_slots = lm_min
        state.large_mosaic_max_per_template_trip = lm_trip
        state.large_mosaic_max_per_chapter = lm_ch
        return state

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
        if not is_dense_collage_pattern(pattern_id, min_slots=self.dense_collage_min_slots):
            return True
        if self.dense_collage_used >= self.dense_collage_max:
            return False
        return not self.last_was_dense_collage

    def should_force_dense_emit(self) -> bool:
        """LTN E4 · asymmetric quota invariant: opportunity min never forces emit."""
        return False

    def needs_dense_opportunity(self) -> bool:
        """Soft gap vs opportunity min (observability only — does not gate emit)."""
        return self.dense_collage_used < self.dense_collage_opportunity_min

    def note_dense_opportunity(self) -> None:
        """Count a legal dense/mosaic candidate window (scored > 0)."""
        self.dense_opportunity_seen += 1

    def asymmetric_dense_snapshot(self) -> dict:
        from travelogue.layout_contract.asymmetric_quota import asymmetric_dense_snapshot

        return asymmetric_dense_snapshot(
            dense_max=self.dense_collage_max,
            dense_used=self.dense_collage_used,
            opportunity_min=self.dense_collage_opportunity_min,
            opportunity_seen=self.dense_opportunity_seen,
        )

    def can_use_dense_collage_window(self, window_size: int) -> bool:
        if window_size < self.dense_collage_min_slots:
            return True
        if not self.can_use_large_mosaic_window(window_size):
            return False
        if self.dense_collage_used >= self.dense_collage_max:
            return False
        return not self.last_was_dense_collage

    def begin_chapter_bucket(
        self,
        *,
        chapter_index: int = 1,
    ) -> None:
        self.large_mosaic_chapter_used = 0
        self.editorial_composite_chapter_used = 0
        # LTN C5 · unused armed opportunity dies with the chapter.
        if self.hero_reserve == "armed":
            self.hero_reserve = "released"
        else:
            self.hero_reserve = "idle"
        if self.hero_six_opportunity == "armed":
            self.hero_six_opportunity = "released"
        else:
            self.hero_six_opportunity = "idle"
        self.hero_six_armed_cursor = None
        late = self.rhythm.late_chapter_pairing
        if not late.is_late_chapter(chapter_index):
            return
        if late.reset_orientation_streak:
            self.portrait_orientation_streak = 0
        if late.reset_pair_streak and self.last_pattern_id == PORTRAIT_PAIR_PATTERN:
            self.last_pattern_id = ""
            self.pattern_streak = 0

    def arm_hero_reserve(self) -> None:
        if self.hero_reserve in ("idle", "released"):
            self.hero_reserve = "armed"

    def consume_hero_reserve(self) -> None:
        if self.hero_reserve == "armed":
            self.hero_reserve = "consumed"

    def release_hero_reserve(self) -> None:
        if self.hero_reserve == "armed":
            self.hero_reserve = "released"

    def arm_hero_six_opportunity(self, cursor: int) -> None:
        """Arm six-hero opportunity for this cursor (may re-arm after consumed)."""
        self.hero_six_opportunity = "armed"
        self.hero_six_armed_cursor = int(cursor)

    def consume_hero_six_opportunity(self) -> None:
        if self.hero_six_opportunity == "armed":
            self.hero_six_opportunity = "consumed"
            self.hero_six_armed_cursor = None

    def release_hero_six_opportunity(self) -> None:
        if self.hero_six_opportunity == "armed":
            self.hero_six_opportunity = "released"
            self.hero_six_armed_cursor = None

    @staticmethod
    def pattern_has_main_role(pattern_id: str) -> bool:
        if not pattern_id:
            return False
        try:
            from travelogue.layout_engine.mosaic.pattern_catalog import default_registry

            pat = default_registry().get(pattern_id)
        except Exception:
            return False
        return bool(pat and "main" in pat.roles)

    def is_equal_weight_dense(self, pattern_id: str) -> bool:
        """Dense collage without a main/hero slot — yields while reserve is armed."""
        if not is_dense_collage_pattern(
            pattern_id, min_slots=self.dense_collage_min_slots
        ):
            return False
        return not self.pattern_has_main_role(pattern_id)

    def blocks_dense_for_hero_reserve(self, pattern_id: str) -> bool:
        return self.hero_reserve == "armed" and self.is_equal_weight_dense(pattern_id)

    def can_use_large_mosaic_window(self, window_size: int) -> bool:
        if window_size < self.large_mosaic_min_slots:
            return True
        return self.large_mosaic_chapter_used < self.large_mosaic_max_per_chapter

    def _large_mosaic_quota_key(self, pattern_id: str) -> str:
        # SUP-07 · twin six-hero family shares trip template quota
        try:
            from travelogue.layout_engine.mosaic.lifecycle import six_hero_family_id

            fam = six_hero_family_id(pattern_id)
            if fam:
                return fam
        except Exception:
            pass
        return pattern_id

    def can_use_large_mosaic(self, pattern_id: str) -> bool:
        if not is_large_mosaic_pattern(pattern_id, min_slots=self.large_mosaic_min_slots):
            return True
        if self.large_mosaic_chapter_used >= self.large_mosaic_max_per_chapter:
            return False
        key = self._large_mosaic_quota_key(pattern_id)
        used = self.pattern_counts.get(key, 0)
        return used < self.large_mosaic_max_per_template_trip

    def sync_large_mosaic_chapter_used(self, pattern_ids: list[str]) -> None:
        self.large_mosaic_chapter_used = sum(
            1
            for pid in pattern_ids
            if is_large_mosaic_pattern(pid, min_slots=self.large_mosaic_min_slots)
        )

    def sync_editorial_composite_chapter_used(self, pattern_ids: list[str]) -> None:
        self.editorial_composite_chapter_used = sum(
            1 for pid in pattern_ids if is_editorial_composite_pattern(pid)
        )

    def can_emit_editorial_composite(self) -> bool:
        return self.editorial_composite_chapter_used < 1

    def can_pick_grid_size(self, size: int) -> bool:
        if size == 9:
            return self.can_use_nine()
        if size == 3:
            return self.last_kind not in ("triple", "six")
        if size == 6:
            return self.last_kind not in ("six", "triple")
        return True

    def can_emit_pattern(self, pattern_id: str) -> bool:
        # Template-specific rhythm gates live in layout_engine; keep this kernel layer pure.
        max_ch = None
        if is_editorial_composite_pattern(pattern_id) and not self.can_emit_editorial_composite():
            return False
        if max_ch is not None and self.pattern_counts.get(pattern_id, 0) >= max_ch:
            return False
        if self.blocks_dense_for_hero_reserve(pattern_id):
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
            return self.current_portrait_pair_streak() < self.rhythm.max_portrait_pair_streak
        return True

    def current_portrait_pair_streak(self) -> int:
        if self.last_pattern_id == PORTRAIT_PAIR_PATTERN:
            return self.pattern_streak
        return 0

    def orientation_budget(self) -> int:
        return max(
            0,
            self.rhythm.max_portrait_orientation_streak - self.portrait_orientation_streak,
        )

    def note_screen(self, pattern_id: str) -> None:
        if pattern_id:
            self.pattern_counts[pattern_id] = self.pattern_counts.get(pattern_id, 0) + 1
            fam_key = self._large_mosaic_quota_key(pattern_id)
            if fam_key != pattern_id:
                self.pattern_counts[fam_key] = self.pattern_counts.get(fam_key, 0) + 1
            if self.pattern_has_main_role(pattern_id):
                self.consume_hero_reserve()
            elif self.hero_reserve == "armed":
                # LTN C5 · non-hero emit while armed ⇒ opportunity assets consumed.
                self.release_hero_reserve()
            try:
                from travelogue.layout_engine.mosaic.lifecycle import six_hero_family_id

                if six_hero_family_id(pattern_id):
                    self.consume_hero_six_opportunity()
                elif self.hero_six_opportunity == "armed":
                    self.release_hero_six_opportunity()
            except Exception:
                pass
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
        if is_editorial_composite_pattern(pattern_id):
            self.editorial_composite_chapter_used += 1
        self.last_kind = kind if kind != "other" else "other"
        if pattern_id and pattern_id == self.last_pattern_id:
            self.pattern_streak += 1
        else:
            self.pattern_streak = 1 if pattern_id else 0
        self.last_pattern_id = pattern_id or ""
        if pattern_id and is_portrait_orientation_pattern(pattern_id):
            self.portrait_orientation_streak += 1
        elif pattern_id:
            self.portrait_orientation_streak = 0
