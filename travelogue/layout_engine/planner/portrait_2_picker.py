"""P2VF · pick among portrait-2 family variants (PRD-PORTRAIT-2-VARIANT-FAMILY-V1).

Planner hard-emit path only. MCS lifecycle does not auto-gate these ids;
visibility is decided here via template_experiments + portrait_2_variants.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from travelogue.config.mosaic import MosaicConfig
from travelogue.layout_contract.quality import asset_sharpness
from travelogue.layout_contract.rhythm import (
    PORTRAIT_PAIR_PATTERN,
    is_portrait_pair_pattern,
)
from travelogue.layout_contract.scoring import aesthetic_overall
from travelogue.layout_contract.subject import asset_has_person
from travelogue.layout_engine.planner.template_experiments_gate import (
    disabled_template_ids,
)
from travelogue.layout_engine.planner.template_experiments_gate import (
    experimental_members_visible as _experiments_visible,
)

StrengthSide = Literal["left", "right", "tie"]

PATTERN_PORTRAIT_2_FILL = PORTRAIT_PAIR_PATTERN
PATTERN_PORTRAIT_2_GALLERY = "screen-portrait-2-gallery"
PATTERN_PORTRAIT_2_ASYM_LEFT = "screen-portrait-2-asymmetric-left"
PATTERN_PORTRAIT_2_ASYM_RIGHT = "screen-portrait-2-asymmetric-right"

ROTATION_EXPERIMENTAL_IDS: frozenset[str] = frozenset(
    {
        PATTERN_PORTRAIT_2_GALLERY,
        PATTERN_PORTRAIT_2_ASYM_LEFT,
        PATTERN_PORTRAIT_2_ASYM_RIGHT,
    }
)

PORTRAIT_2_FAMILY_IDS: frozenset[str] = frozenset(
    {PATTERN_PORTRAIT_2_FILL} | ROTATION_EXPERIMENTAL_IDS
)

_VARIANT_ROLE: dict[str, str] = {
    PATTERN_PORTRAIT_2_FILL: "fill",
    PATTERN_PORTRAIT_2_GALLERY: "gallery",
    PATTERN_PORTRAIT_2_ASYM_LEFT: "asymmetric-left",
    PATTERN_PORTRAIT_2_ASYM_RIGHT: "asymmetric-right",
}

_BASE_WEIGHT: dict[str, float] = {
    PATTERN_PORTRAIT_2_FILL: 1.0,
    PATTERN_PORTRAIT_2_GALLERY: 0.90,
    PATTERN_PORTRAIT_2_ASYM_LEFT: 0.90,
    PATTERN_PORTRAIT_2_ASYM_RIGHT: 0.90,
}

_STABLE_ORDER: dict[str, int] = {
    PATTERN_PORTRAIT_2_FILL: 0,
    PATTERN_PORTRAIT_2_GALLERY: 1,
    PATTERN_PORTRAIT_2_ASYM_LEFT: 2,
    PATTERN_PORTRAIT_2_ASYM_RIGHT: 3,
}


@dataclass(frozen=True)
class Portrait2Pick:
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
    """Picker-side experiments gate (D-15). Empty cohort ⇒ nobody."""
    return _experiments_visible(
        mosaic_cfg=mosaic_cfg,
        trip_id=trip_id,
        allowlist_intersect=allowlist_intersect,
        stable_order=_STABLE_ORDER,
    )


def strength_side(
    asset_left: dict,
    asset_right: dict,
    *,
    tie_epsilon: float = 0.08,
) -> StrengthSide:
    """Relative strength without swapping slots (D-13). Missing features ⇒ tie."""
    left = _strength_score(asset_left)
    right = _strength_score(asset_right)
    if left is None or right is None:
        return "tie"
    delta = left - right
    if abs(delta) < tie_epsilon:
        return "tie"
    return "left" if delta > 0 else "right"


def _strength_score(asset: dict) -> float | None:
    ae = aesthetic_overall(asset)
    sharp = asset_sharpness(asset)
    if ae is None and sharp <= 0:
        return None
    aesthetic01 = max(0.0, min(1.0, float(ae))) if ae is not None else 0.5
    # sharpness is often 0–100ish; normalize softly into 0–1
    if sharp <= 0:
        sharp01 = 0.5
    elif sharp <= 1.0:
        sharp01 = sharp
    else:
        sharp01 = max(0.0, min(1.0, sharp / 100.0))
    tier = str(asset.get("userTier") or "").strip().lower()
    featured = 1.0 if tier == "featured" or bool(asset.get("hero")) else 0.0
    return 0.50 * aesthetic01 + 0.30 * sharp01 + 0.20 * featured


def _portrait_2_cfg(cfg) -> object | None:
    layout = getattr(cfg, "layout", None) if cfg is not None else None
    return getattr(layout, "portrait_2_variants", None) if layout is not None else None


def _disabled_ids(cfg) -> set[str]:
    return disabled_template_ids(cfg)


def recent_family_pattern_ids(
    recent_pattern_ids: list[str] | None,
    *,
    k: int = 2,
) -> list[str]:
    if not recent_pattern_ids or k <= 0:
        return []
    family = [pid for pid in recent_pattern_ids if is_portrait_pair_pattern(pid)]
    return family[-k:]


def pick_portrait_2_variant(
    asset_ids: list[str],
    *,
    assets_map: dict[str, dict] | None = None,
    cfg=None,
    trip_id: str | None = None,
    recent_pattern_ids: list[str] | None = None,
    prev_was_dense: bool = False,
) -> Portrait2Pick:
    """Authoritative picker (PRD §5.2). OFF / person / invisible ⇒ fill."""
    assets_map = assets_map or {}
    fill = PATTERN_PORTRAIT_2_FILL
    p2 = _portrait_2_cfg(cfg)
    enabled = bool(getattr(p2, "enabled", False)) if p2 is not None else False
    if not enabled:
        return Portrait2Pick(fill, "default_off", "tie", "fill")

    if len(asset_ids) != 2:
        return Portrait2Pick(fill, "fallback_fill", "tie", "fill")

    a0 = assets_map.get(asset_ids[0], {}) or {}
    a1 = assets_map.get(asset_ids[1], {}) or {}
    if asset_has_person(a0) or asset_has_person(a1):
        return Portrait2Pick(fill, "person_fill", "tie", "fill")

    mosaic_cfg = getattr(cfg, "mosaic", None) if cfg is not None else None
    visible = experimental_members_visible(mosaic_cfg=mosaic_cfg, trip_id=trip_id)
    disabled = _disabled_ids(cfg)
    candidates = [fill] + [pid for pid in visible if pid not in disabled]
    if not candidates or candidates == [fill]:
        return Portrait2Pick(fill, "fallback_fill", "tie", "fill")

    eps = float(getattr(p2, "strength_tie_epsilon", 0.08) or 0.08)
    side = strength_side(a0, a1, tie_epsilon=eps)

    pool: list[str] = []
    for pid in candidates:
        role = variant_role(pid)
        if role in ("asymmetric-left", "asymmetric-right"):
            if side == "tie":
                continue
            if side == "left" and role != "asymmetric-left":
                continue
            if side == "right" and role != "asymmetric-right":
                continue
        pool.append(pid)

    if not pool:
        pool = [fill] + [p for p in candidates if variant_role(p) == "gallery"]
    if not pool:
        return Portrait2Pick(fill, "fallback_fill", side, "fill")

    recent_window = int(getattr(p2, "recent_window", 2) or 2)
    recent = recent_family_pattern_ids(recent_pattern_ids, k=recent_window)
    repeat_penalty = float(getattr(p2, "repeat_penalty", 0.55) or 0.55)
    prefer_breath = bool(getattr(p2, "prefer_breath_after_dense", True))

    scored: list[tuple[float, int, str]] = []
    for pid in pool:
        s = _BASE_WEIGHT.get(pid, 0.90)
        if pid in recent:
            s *= repeat_penalty
        if prefer_breath and prev_was_dense and variant_role(pid) == "gallery":
            s += 0.08
        scored.append((s, -_STABLE_ORDER.get(pid, 99), pid))

    # max by (score, -order) then pid for full determinism
    best = max(scored, key=lambda t: (t[0], t[1], t[2]))
    pid = best[2]
    reason = "rotate" if pid != fill else "weight"
    if pid == fill and fill not in recent and len(pool) == 1:
        reason = "fallback_fill"
    return Portrait2Pick(pid, reason, side, variant_role(pid))
