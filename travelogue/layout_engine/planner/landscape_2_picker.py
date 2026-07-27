"""Landscape-2 editorial · pick among fill / overlap / asym (PRD-LANDSCAPE-2-EDITORIAL-V1)."""

from __future__ import annotations

from dataclasses import dataclass

from travelogue.config.mosaic import MosaicConfig, TemplateExperimentsConfig
from travelogue.layout_contract.rhythm import is_landscape_pair_pattern
from travelogue.layout_engine.planner.portrait_2_picker import (
    StrengthSide,
    strength_side,
)

PATTERN_LANDSCAPE_2_FILL = "screen-landscape-2"
PATTERN_LANDSCAPE_2_OVERLAP_TLBR = "screen-landscape-2-overlap-tlbr"
PATTERN_LANDSCAPE_2_OVERLAP_BLTR = "screen-landscape-2-overlap-bltr"
PATTERN_LANDSCAPE_2_ASYM_LEFT = "screen-landscape-2-asymmetric-left"

# Diagonal overlap variants parked repo-wide (full-bleed ghosting dogfood).
# Keep IDs for family/rhythm recognition of existing trips; do not admit new picks.
PARKED_EXPERIMENTAL_IDS: frozenset[str] = frozenset(
    {
        PATTERN_LANDSCAPE_2_OVERLAP_TLBR,
        PATTERN_LANDSCAPE_2_OVERLAP_BLTR,
    }
)

ROTATION_EXPERIMENTAL_IDS: frozenset[str] = frozenset(
    {
        PATTERN_LANDSCAPE_2_ASYM_LEFT,
    }
)

LANDSCAPE_2_FAMILY_IDS: frozenset[str] = frozenset(
    {PATTERN_LANDSCAPE_2_FILL} | ROTATION_EXPERIMENTAL_IDS | PARKED_EXPERIMENTAL_IDS
)

_VARIANT_ROLE: dict[str, str] = {
    PATTERN_LANDSCAPE_2_FILL: "fill",
    PATTERN_LANDSCAPE_2_OVERLAP_TLBR: "overlap-tlbr",
    PATTERN_LANDSCAPE_2_OVERLAP_BLTR: "overlap-bltr",
    PATTERN_LANDSCAPE_2_ASYM_LEFT: "asymmetric-left",
}

_BASE_WEIGHT: dict[str, float] = {
    PATTERN_LANDSCAPE_2_FILL: 1.0,
    PATTERN_LANDSCAPE_2_OVERLAP_TLBR: 0.90,
    PATTERN_LANDSCAPE_2_OVERLAP_BLTR: 0.90,
    PATTERN_LANDSCAPE_2_ASYM_LEFT: 0.90,
}

_STABLE_ORDER: dict[str, int] = {
    PATTERN_LANDSCAPE_2_FILL: 0,
    PATTERN_LANDSCAPE_2_OVERLAP_TLBR: 1,
    PATTERN_LANDSCAPE_2_OVERLAP_BLTR: 2,
    PATTERN_LANDSCAPE_2_ASYM_LEFT: 3,
}


@dataclass(frozen=True)
class Landscape2Pick:
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
    if mosaic_cfg is None:
        return []
    te: TemplateExperimentsConfig | None = getattr(mosaic_cfg, "template_experiments", None)
    if te is None or not getattr(te, "enabled", False):
        return []
    allow = tuple(getattr(te, "allowlist", ()) or ())
    cohort = tuple(getattr(te, "cohort_trip_ids", ()) or ())
    if not cohort:
        return []
    tid = str(trip_id or "").strip()
    # ``*`` = all trips (product GA); otherwise require exact tripId membership.
    if "*" not in cohort and (not tid or tid not in cohort):
        return []
    out = [
        pid
        for pid in allow
        if pid in allowlist_intersect and pid not in PARKED_EXPERIMENTAL_IDS
    ]
    return sorted(out, key=lambda p: _STABLE_ORDER.get(p, 99))


def _l2_cfg(cfg) -> object | None:
    layout = getattr(cfg, "layout", None) if cfg is not None else None
    return getattr(layout, "landscape_2_editorial", None) if layout is not None else None


def _disabled_ids(cfg) -> set[str]:
    te = getattr(getattr(cfg, "layout", None), "template_engine", None) if cfg else None
    raw = getattr(te, "overrides_disable", ()) if te is not None else ()
    return {str(x) for x in (raw or ()) if x} | set(PARKED_EXPERIMENTAL_IDS)


def recent_family_pattern_ids(
    recent_pattern_ids: list[str] | None,
    *,
    k: int = 2,
) -> list[str]:
    if not recent_pattern_ids or k <= 0:
        return []
    family = [pid for pid in recent_pattern_ids if is_landscape_pair_pattern(pid)]
    return family[-k:]


def pick_landscape_2_variant(
    asset_ids: list[str],
    *,
    assets_map: dict[str, dict] | None = None,
    cfg=None,
    trip_id: str | None = None,
    recent_pattern_ids: list[str] | None = None,
) -> Landscape2Pick:
    """Authoritative picker. OFF / invisible ⇒ fill."""
    assets_map = assets_map or {}
    fill = PATTERN_LANDSCAPE_2_FILL
    l2 = _l2_cfg(cfg)
    enabled = bool(getattr(l2, "enabled", False)) if l2 is not None else False
    if not enabled:
        return Landscape2Pick(fill, "default_off", "tie", "fill")

    if len(asset_ids) != 2:
        return Landscape2Pick(fill, "fallback_fill", "tie", "fill")

    a0 = assets_map.get(asset_ids[0], {}) or {}
    a1 = assets_map.get(asset_ids[1], {}) or {}
    mosaic_cfg = getattr(cfg, "mosaic", None) if cfg is not None else None
    visible = experimental_members_visible(mosaic_cfg=mosaic_cfg, trip_id=trip_id)
    disabled = _disabled_ids(cfg)
    candidates = [fill] + [pid for pid in visible if pid not in disabled]
    if candidates == [fill]:
        return Landscape2Pick(fill, "fallback_fill", "tie", "fill")

    eps = float(getattr(l2, "strength_tie_epsilon", 0.08) or 0.08)
    side = strength_side(a0, a1, tie_epsilon=eps)

    pool: list[str] = []
    for pid in candidates:
        role = variant_role(pid)
        if role == "asymmetric-left" and side != "left":
            continue
        pool.append(pid)

    # PRD §4: clear left strength → asym-left; tie → overlap diagonal rotate;
    # right / no-eligible-experiment → keep fill (+ overlaps when present).
    if side == "left" and PATTERN_LANDSCAPE_2_ASYM_LEFT in pool:
        pool = [PATTERN_LANDSCAPE_2_ASYM_LEFT]
    elif side == "tie":
        overlaps = [
            p
            for p in pool
            if variant_role(p) in ("overlap-tlbr", "overlap-bltr")
        ]
        if overlaps:
            pool = overlaps
        else:
            pool = [p for p in pool if variant_role(p) != "asymmetric-left"]
    else:
        pool = [p for p in pool if variant_role(p) != "asymmetric-left"]

    if not pool:
        pool = [fill]

    recent_window = int(getattr(l2, "recent_window", 2) or 2)
    recent = recent_family_pattern_ids(recent_pattern_ids, k=recent_window)
    repeat_penalty = float(getattr(l2, "repeat_penalty", 0.55) or 0.55)

    scored: list[tuple[float, int, str]] = []
    for pid in pool:
        s = _BASE_WEIGHT.get(pid, 0.90)
        if pid in recent:
            s *= repeat_penalty
        scored.append((s, -_STABLE_ORDER.get(pid, 99), pid))

    best = max(scored, key=lambda t: (t[0], t[1], t[2]))
    pid = best[2]
    reason = "rotate" if pid != fill else "weight"
    if side == "tie" and variant_role(pid) in ("overlap-tlbr", "overlap-bltr"):
        reason = "overlap_tie"
    if pid == fill and fill not in recent and len(pool) == 1:
        reason = "fallback_fill"
    return Landscape2Pick(pid, reason, side, variant_role(pid))
