"""Rhythm helpers · pack → ScreenLayoutPlannerState (W1 parity)."""

from __future__ import annotations

from dataclasses import replace

from travelogue.layout_contract.constraints import FOCAL_EDGE_MARGIN
from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState
from travelogue.layout_contract.density import LayoutDensity, LayoutDensityParams
from travelogue.layout_contract.rhythm import (
    DEFAULT_CONSECUTIVE_BANS,
    PORTRAIT_PAIR_PATTERN,
    RhythmRules,
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
        from travelogue.layout_contract.rhythm import nine_grid_limits_for_trip

        return nine_grid_limits_for_trip(total_photos)
    tiers = sorted(tiers, key=lambda t: t[0])
    lo, hi = tiers[-1][1], tiers[-1][2]
    for max_photos, tmin, tmax in tiers:
        if total_photos <= max_photos:
            lo, hi = tmin, tmax
            break
    return lo, hi


def rhythm_rules_from_pack(pack: StrategyPack) -> RhythmRules:
    """接线 pack rhythm.consecutive_bans / 阈值 → RhythmRules（PR-6）。

    - ``{ kinds: [a, b], blocked: true }`` 行 → (last_kind, next_kind) 禁令对；
    - ``{ pattern: screen-portrait-2, max_streak: N }`` 行 → R-06 上限；
    - ``portrait_orientation_max_streak`` → R-08 上限。
    未声明的字段回退 config.layout.rhythm / 代码默认（与既有硬编码等价）。
    """
    base = RhythmRules.from_config()
    rhythm = pack.raw.get("rhythm") or {}
    rows = rhythm.get("consecutive_bans")
    bans: set[tuple[str, str]] = set()
    pair_max = base.max_portrait_pair_streak
    declared_bans = False
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            kinds = row.get("kinds")
            if isinstance(kinds, list) and len(kinds) == 2:
                declared_bans = True
                if bool(row.get("blocked", True)):
                    bans.add((str(kinds[0]), str(kinds[1])))
                continue
            if str(row.get("pattern") or "") == PORTRAIT_PAIR_PATTERN:
                try:
                    pair_max = int(row.get("max_streak", pair_max))
                except (TypeError, ValueError):
                    pass
    orientation_max = base.max_portrait_orientation_streak
    try:
        orientation_max = int(
            rhythm.get("portrait_orientation_max_streak", orientation_max)
        )
    except (TypeError, ValueError):
        pass
    return RhythmRules(
        max_portrait_pair_streak=pair_max,
        max_portrait_orientation_streak=orientation_max,
        consecutive_bans=frozenset(bans) if declared_bans else DEFAULT_CONSECUTIVE_BANS,
    )


def layout_state_from_pack(
    total_photos: int,
    pack: StrategyPack,
    *,
    density: LayoutDensity | None = None,
    density_params: LayoutDensityParams | None = None,
) -> ScreenLayoutPlannerState:
    """Build planner state from pack rhythm + config-path P21 quotas (dense/large mosaic)."""
    params = density_params or LayoutDensityParams(density=density or "balanced")
    rhythm = rhythm_rules_from_pack(pack)
    state = ScreenLayoutPlannerState.from_trip_total(
        total_photos,
        density_params=params,
        rhythm=rhythm,
    )
    lo, hi = nine_grid_limits_for_trip_from_pack(total_photos, pack)
    lo, hi = params.adjust_nine_limits(lo, hi)
    rhythm_section = pack.raw.get("rhythm") or {}
    pg8_min = int(rhythm_section.get("portrait_grid8_min_photos", 50))
    pg8_max = portrait_grid8_max_for_trip(total_photos) if total_photos > pg8_min else 0
    return replace(
        state,
        nine_min=lo,
        nine_max=hi,
        portrait_grid8_max=pg8_max,
    )
