"""Mixed 1P2L · pick p1l2 fill vs L2|P mirror."""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.config.mosaic import MosaicConfig
from travelogue.layout_contract.rhythm import is_mixed_1p2l_pattern
from travelogue.layout_engine.planner.portrait_2_picker import (
    StrengthSide,
)
from travelogue.layout_engine.planner.portrait_2_picker import (
    strength_side as _strength_side,
)
from travelogue.layout_engine.planner.template_experiments_gate import (
    disabled_template_ids,
)
from travelogue.layout_engine.planner.template_experiments_gate import (
    experimental_members_visible as _experiments_visible,
)

PATTERN_MIXED_1P2L_FILL = "screen-portrait-1-landscape-2"
PATTERN_MIXED_L2P1 = "screen-landscape-2-portrait-1"

ROTATION_EXPERIMENTAL_IDS: frozenset[str] = frozenset({PATTERN_MIXED_L2P1})

MIXED_1P2L_FAMILY_IDS: frozenset[str] = frozenset(
    {PATTERN_MIXED_1P2L_FILL} | ROTATION_EXPERIMENTAL_IDS
)

_VARIANT_ROLE: dict[str, str] = {
    PATTERN_MIXED_1P2L_FILL: "portrait-left",
    PATTERN_MIXED_L2P1: "landscape-left",
}

_BASE_WEIGHT: dict[str, float] = {
    PATTERN_MIXED_1P2L_FILL: 1.0,
    PATTERN_MIXED_L2P1: 0.92,
}

_STABLE_ORDER: dict[str, int] = {
    PATTERN_MIXED_1P2L_FILL: 0,
    PATTERN_MIXED_L2P1: 1,
}


@dataclass(frozen=True)
class Mixed1p2lPick:
    pattern_id: str
    reason: str
    strength_side: StrengthSide
    variant_role: str


def variant_role(pattern_id: str) -> str:
    return _VARIANT_ROLE.get(pattern_id, "fill")


def experimental_members_visible(
    *,
    mosaic_cfg: MosaicConfig | None,
    trip_id: str | None,
    allowlist_intersect: frozenset[str] = ROTATION_EXPERIMENTAL_IDS,
) -> list[str]:
    return _experiments_visible(
        mosaic_cfg=mosaic_cfg,
        trip_id=trip_id,
        allowlist_intersect=allowlist_intersect,
        stable_order=_STABLE_ORDER,
    )


def _m1p2l_cfg(cfg) -> object | None:
    layout = getattr(cfg, "layout", None) if cfg is not None else None
    return getattr(layout, "mixed_1p2l", None) if layout is not None else None


def _disabled_ids(cfg) -> set[str]:
    return disabled_template_ids(cfg)


def recent_family_pattern_ids(
    recent_pattern_ids: list[str] | None,
    *,
    k: int = 2,
) -> list[str]:
    if not recent_pattern_ids or k <= 0:
        return []
    family = [pid for pid in recent_pattern_ids if is_mixed_1p2l_pattern(pid)]
    return family[-k:]


def pick_mixed_1p2l_variant(
    *,
    portrait_id: str,
    landscape_ids: list[str],
    assets_map: dict[str, dict] | None = None,
    cfg=None,
    trip_id: str | None = None,
    recent_pattern_ids: list[str] | None = None,
) -> Mixed1p2lPick:
    """Pick fill vs mirror. OFF / invisible ⇒ fill."""
    assets_map = assets_map or {}
    fill = PATTERN_MIXED_1P2L_FILL
    mcfg = _m1p2l_cfg(cfg)
    enabled = bool(getattr(mcfg, "enabled", False)) if mcfg is not None else False
    if not enabled:
        return Mixed1p2lPick(fill, "default_off", "tie", "portrait-left")

    if len(landscape_ids) != 2:
        return Mixed1p2lPick(fill, "fallback_fill", "tie", "portrait-left")

    mosaic_cfg = getattr(cfg, "mosaic", None) if cfg is not None else None
    visible = experimental_members_visible(mosaic_cfg=mosaic_cfg, trip_id=trip_id)
    disabled = _disabled_ids(cfg)
    candidates = [fill] + [pid for pid in visible if pid not in disabled]
    if candidates == [fill]:
        return Mixed1p2lPick(fill, "fallback_fill", "tie", "portrait-left")

    a_p = assets_map.get(portrait_id, {}) or {}
    # Compare portrait vs first landscape (time-order left of the L pair).
    a_l0 = assets_map.get(landscape_ids[0], {}) or {}
    eps = float(getattr(mcfg, "strength_tie_epsilon", 0.08) or 0.08)
    side = _strength_side(a_p, a_l0, tie_epsilon=eps)
    # left ⇒ portrait stronger ⇒ prefer fill P|L2; right ⇒ landscapes ⇒ mirror
    preferred: str | None
    if side == "left":
        preferred = PATTERN_MIXED_1P2L_FILL
    elif side == "right":
        preferred = PATTERN_MIXED_L2P1 if PATTERN_MIXED_L2P1 in candidates else fill
    else:
        preferred = None

    pool = list(candidates)
    if preferred and preferred in pool:
        pool = [preferred] + [p for p in pool if p != preferred]

    recent_window = int(getattr(mcfg, "recent_window", 2) or 2)
    recent = recent_family_pattern_ids(recent_pattern_ids, k=recent_window)
    repeat_penalty = float(getattr(mcfg, "repeat_penalty", 0.55) or 0.55)

    scored: list[tuple[float, int, str]] = []
    for pid in pool:
        # Tie: equal base so recent_window can rotate fill ↔ mirror
        # (fill base_weight 1.0 must not permanently suppress the experimental).
        if side == "tie":
            s = 1.0
        else:
            s = _BASE_WEIGHT.get(pid, 0.92)
            if preferred and pid == preferred:
                s += 0.10
        if pid in recent:
            s *= repeat_penalty
        scored.append((s, -_STABLE_ORDER.get(pid, 99), pid))

    best = max(scored, key=lambda t: (t[0], t[1], t[2]))
    pid = best[2]
    reason = "strength" if preferred and pid == preferred else "rotate"
    if pid == fill and not preferred:
        reason = "rotate"
    return Mixed1p2lPick(pid, reason, side, variant_role(pid))
