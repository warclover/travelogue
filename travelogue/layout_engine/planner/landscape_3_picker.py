"""Landscape-3 editorial · pick among fill / asym-left / asym-right."""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.config.mosaic import MosaicConfig
from travelogue.layout_contract.rhythm import is_landscape_triple_pattern
from travelogue.layout_engine.planner.portrait_2_picker import (
    StrengthSide,
    strength_side,
)
from travelogue.layout_engine.planner.template_experiments_gate import (
    disabled_template_ids,
    experimental_members_visible as _experiments_visible,
)

PATTERN_LANDSCAPE_3_FILL = "screen-landscape-3"
PATTERN_LANDSCAPE_3_ASYM_LEFT = "screen-landscape-3-asymmetric-left"
PATTERN_LANDSCAPE_3_ASYM_RIGHT = "screen-landscape-3-asymmetric-right"

ROTATION_EXPERIMENTAL_IDS: frozenset[str] = frozenset(
    {
        PATTERN_LANDSCAPE_3_ASYM_LEFT,
        PATTERN_LANDSCAPE_3_ASYM_RIGHT,
    }
)

LANDSCAPE_3_FAMILY_IDS: frozenset[str] = frozenset(
    {PATTERN_LANDSCAPE_3_FILL} | ROTATION_EXPERIMENTAL_IDS
)

_VARIANT_ROLE: dict[str, str] = {
    PATTERN_LANDSCAPE_3_FILL: "fill",
    PATTERN_LANDSCAPE_3_ASYM_LEFT: "asymmetric-left",
    PATTERN_LANDSCAPE_3_ASYM_RIGHT: "asymmetric-right",
}

_BASE_WEIGHT: dict[str, float] = {
    PATTERN_LANDSCAPE_3_FILL: 1.0,
    PATTERN_LANDSCAPE_3_ASYM_LEFT: 0.90,
    PATTERN_LANDSCAPE_3_ASYM_RIGHT: 0.90,
}

_STABLE_ORDER: dict[str, int] = {
    PATTERN_LANDSCAPE_3_FILL: 0,
    PATTERN_LANDSCAPE_3_ASYM_LEFT: 1,
    PATTERN_LANDSCAPE_3_ASYM_RIGHT: 2,
}


@dataclass(frozen=True)
class Landscape3Pick:
    pattern_id: str
    reason: str
    strength_side: StrengthSide
    variant_role: str


def variant_role(pattern_id: str) -> str:
    return _VARIANT_ROLE.get(pattern_id, "unknown")


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


def _l3_cfg(cfg) -> object | None:
    layout = getattr(cfg, "layout", None) if cfg is not None else None
    return getattr(layout, "landscape_3_editorial", None) if layout is not None else None


def _disabled_ids(cfg) -> set[str]:
    return disabled_template_ids(cfg)


def recent_family_pattern_ids(
    recent_pattern_ids: list[str] | None,
    *,
    k: int = 2,
) -> list[str]:
    if not recent_pattern_ids or k <= 0:
        return []
    family = [pid for pid in recent_pattern_ids if is_landscape_triple_pattern(pid)]
    return family[-k:]


def pick_landscape_3_variant(
    asset_ids: list[str],
    *,
    assets_map: dict[str, dict] | None = None,
    cfg=None,
    trip_id: str | None = None,
    recent_pattern_ids: list[str] | None = None,
) -> Landscape3Pick:
    """Authoritative picker. OFF / invisible ⇒ fill stack."""
    assets_map = assets_map or {}
    fill = PATTERN_LANDSCAPE_3_FILL
    l3 = _l3_cfg(cfg)
    enabled = bool(getattr(l3, "enabled", False)) if l3 is not None else False
    if not enabled:
        return Landscape3Pick(fill, "default_off", "tie", "fill")

    if len(asset_ids) != 3:
        return Landscape3Pick(fill, "fallback_fill", "tie", "fill")

    a0 = assets_map.get(asset_ids[0], {}) or {}
    a2 = assets_map.get(asset_ids[2], {}) or {}
    mosaic_cfg = getattr(cfg, "mosaic", None) if cfg is not None else None
    visible = experimental_members_visible(mosaic_cfg=mosaic_cfg, trip_id=trip_id)
    disabled = _disabled_ids(cfg)
    candidates = [fill] + [pid for pid in visible if pid not in disabled]
    if candidates == [fill]:
        return Landscape3Pick(fill, "fallback_fill", "tie", "fill")

    eps = float(getattr(l3, "strength_tie_epsilon", 0.08) or 0.08)
    # First vs last: left-hero vs right-hero positions in time order.
    side = strength_side(a0, a2, tie_epsilon=eps)

    # AC-L3E-04: tie → asym mirrors only (not fill). Preferred side missing → fill.
    pool: list[str] = list(candidates)
    if side == "left" and PATTERN_LANDSCAPE_3_ASYM_LEFT in pool:
        pool = [PATTERN_LANDSCAPE_3_ASYM_LEFT]
    elif side == "right" and PATTERN_LANDSCAPE_3_ASYM_RIGHT in pool:
        pool = [PATTERN_LANDSCAPE_3_ASYM_RIGHT]
    elif side == "tie":
        asyms = [
            p
            for p in pool
            if variant_role(p) in ("asymmetric-left", "asymmetric-right")
        ]
        pool = asyms or [fill]
    else:
        # Preferred asym not in pool (disabled / not allowlisted) → fail closed to fill.
        pool = [fill]

    if not pool:
        pool = [fill]

    recent_window = int(getattr(l3, "recent_window", 2) or 2)
    recent = recent_family_pattern_ids(recent_pattern_ids, k=recent_window)
    repeat_penalty = float(getattr(l3, "repeat_penalty", 0.55) or 0.55)

    scored: list[tuple[float, int, str]] = []
    for pid in pool:
        s = _BASE_WEIGHT.get(pid, 0.90)
        if pid in recent:
            s *= repeat_penalty
        scored.append((s, -_STABLE_ORDER.get(pid, 99), pid))

    best = max(scored, key=lambda t: (t[0], t[1], t[2]))
    pid = best[2]
    reason = "rotate" if pid != fill else "weight"
    if side in ("left", "right") and variant_role(pid).startswith("asymmetric"):
        reason = "strength"
    if side == "tie" and variant_role(pid).startswith("asymmetric"):
        reason = "asym_tie"
    if pid == fill and fill not in recent and len(pool) == 1:
        reason = "fallback_fill"
    return Landscape3Pick(pid, reason, side, variant_role(pid))
