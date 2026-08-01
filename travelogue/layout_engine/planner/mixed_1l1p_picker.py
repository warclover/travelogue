"""Mixed 1L1P · pick L|P vs P|L mirror (PRD-MIXED-1L1P-V1).

No GA fill: OFF / invisible experiments ⇒ pattern_id=None (caller splits to singles).
"""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.config.mosaic import MosaicConfig
from travelogue.layout_contract.rhythm import is_mixed_1l1p_pattern
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

PATTERN_MIXED_LP = "screen-landscape-1-portrait-1"
PATTERN_MIXED_PL = "screen-portrait-1-landscape-1"

MIXED_1L1P_EXPERIMENTAL_IDS: frozenset[str] = frozenset(
    {PATTERN_MIXED_LP, PATTERN_MIXED_PL}
)

_VARIANT_ROLE: dict[str, str] = {
    PATTERN_MIXED_LP: "landscape-left",
    PATTERN_MIXED_PL: "portrait-left",
}

_BASE_WEIGHT: dict[str, float] = {
    PATTERN_MIXED_LP: 0.92,
    PATTERN_MIXED_PL: 0.92,
}

_STABLE_ORDER: dict[str, int] = {
    PATTERN_MIXED_LP: 0,
    PATTERN_MIXED_PL: 1,
}


@dataclass(frozen=True)
class Mixed1l1pPick:
    pattern_id: str | None
    reason: str
    strength_side: StrengthSide
    variant_role: str


def variant_role(pattern_id: str) -> str:
    return _VARIANT_ROLE.get(pattern_id, "unknown")


def experimental_members_visible(
    *,
    mosaic_cfg: MosaicConfig | None,
    trip_id: str | None,
    allowlist_intersect: frozenset[str] = MIXED_1L1P_EXPERIMENTAL_IDS,
) -> list[str]:
    return _experiments_visible(
        mosaic_cfg=mosaic_cfg,
        trip_id=trip_id,
        allowlist_intersect=allowlist_intersect,
        stable_order=_STABLE_ORDER,
    )


def _mixed_cfg(cfg) -> object | None:
    layout = getattr(cfg, "layout", None) if cfg is not None else None
    return getattr(layout, "mixed_1l1p", None) if layout is not None else None


def _disabled_ids(cfg) -> set[str]:
    return disabled_template_ids(cfg)


def recent_family_pattern_ids(
    recent_pattern_ids: list[str] | None,
    *,
    k: int = 2,
) -> list[str]:
    if not recent_pattern_ids or k <= 0:
        return []
    family = [pid for pid in recent_pattern_ids if is_mixed_1l1p_pattern(pid)]
    return family[-k:]


def pick_mixed_1l1p_variant(
    *,
    portrait_id: str,
    landscape_id: str,
    assets_map: dict[str, dict] | None = None,
    cfg=None,
    trip_id: str | None = None,
    recent_pattern_ids: list[str] | None = None,
) -> Mixed1l1pPick:
    """Pick mirror. None pattern_id ⇒ caller must not emit mixed screen."""
    assets_map = assets_map or {}
    mcfg = _mixed_cfg(cfg)
    enabled = bool(getattr(mcfg, "enabled", False)) if mcfg is not None else False
    if not enabled:
        return Mixed1l1pPick(None, "default_off", "tie", "none")

    mosaic_cfg = getattr(cfg, "mosaic", None) if cfg is not None else None
    visible = experimental_members_visible(mosaic_cfg=mosaic_cfg, trip_id=trip_id)
    disabled = _disabled_ids(cfg)
    candidates = [pid for pid in visible if pid not in disabled]
    if not candidates:
        return Mixed1l1pPick(None, "fallback_split", "tie", "none")

    a_p = assets_map.get(portrait_id, {}) or {}
    a_l = assets_map.get(landscape_id, {}) or {}
    eps = float(getattr(mcfg, "strength_tie_epsilon", 0.08) or 0.08)
    side = _strength_side(a_p, a_l, tie_epsilon=eps)
    # left ⇒ portrait stronger ⇒ prefer P|L; right ⇒ landscape stronger ⇒ L|P
    preferred: str | None
    if side == "left":
        preferred = PATTERN_MIXED_PL
    elif side == "right":
        preferred = PATTERN_MIXED_LP
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
        s = _BASE_WEIGHT.get(pid, 0.92)
        if preferred and pid == preferred:
            s += 0.10
        if pid in recent:
            s *= repeat_penalty
        scored.append((s, -_STABLE_ORDER.get(pid, 99), pid))

    best = max(scored, key=lambda t: (t[0], t[1], t[2]))
    pid = best[2]
    reason = "strength" if preferred and pid == preferred else "rotate"
    return Mixed1l1pPick(pid, reason, side, variant_role(pid))
