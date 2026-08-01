"""MSA · crop_risk → conditional contain + whitespace budget (S-MSA-04)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from travelogue.config.mosaic import SlotAdaptationConfig
from travelogue.layout_engine.crop_solver import solve_slot_focal

# PRD §6.5 proxy weights
_ALPHA_MISMATCH = 0.85
_BETA_FOCAL_EDGE = 0.35
_GAMMA_PERSON = 0.55
_FOCAL_EDGE_MARGIN = 0.12


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _focal_near_edge(asset: Mapping[str, Any], margin: float = _FOCAL_EDGE_MARGIN) -> bool:
    fp = asset.get("focalPoint") or {}
    x, y = fp.get("x"), fp.get("y")
    if x is None or y is None:
        return False
    try:
        xf, yf = float(x), float(y)
    except (TypeError, ValueError):
        return False
    return bool(xf < margin or xf > 1.0 - margin or yf < margin or yf > 1.0 - margin)


def _asset_r(asset: Mapping[str, Any] | None) -> float | None:
    if not asset:
        return None
    try:
        w = float(asset.get("width"))
        h = float(asset.get("height"))
    except (TypeError, ValueError):
        return None
    if w <= 0 or h <= 0:
        return None
    return w / h


def aspect_mismatch(photo_r: float, slot_r: float) -> float:
    """``1 - min/max`` in [0, 1]."""
    if photo_r <= 0 or slot_r <= 0:
        return 0.0
    return 1.0 - (min(photo_r, slot_r) / max(photo_r, slot_r))


def crop_risk_for_pair(
    asset: Mapping[str, Any] | None,
    slot_display_aspect: float,
    *,
    alpha: float = _ALPHA_MISMATCH,
    beta: float = _BETA_FOCAL_EDGE,
    gamma: float = _GAMMA_PERSON,
) -> float:
    """Cover-crop risk proxy (PRD §6.5) + person-safe face IoU after solve."""
    pr = _asset_r(asset)
    if pr is None or slot_display_aspect <= 0:
        return 0.0
    mismatch = aspect_mismatch(pr, float(slot_display_aspect))
    edge = 1.0 if asset is not None and _focal_near_edge(asset) else 0.0
    base = alpha * mismatch + beta * edge

    solved = solve_slot_focal(asset, float(slot_display_aspect))
    safety = solved.safety
    # Hard floor only when faces are actually clipped after solve. Oversized
    # half-body protect infeasibility is a soft signal (protectContainment),
    # not a contain mandate — otherwise 3:2 heroes in 16:9 bleed get letterboxed.
    if safety.face_clipped:
        return round(_clamp01(max(base, 0.92)), 4)
    person_pen = 0.0
    if safety.has_person:
        person_pen = gamma * (1.0 - float(safety.protect_containment))
        if not solved.feasible:
            person_pen = max(person_pen, 0.45)
    return round(_clamp01(base + person_pen), 4)


def contain_whitespace_fraction(photo_r: float, slot_r: float) -> float:
    """Fraction of slot area that is non-image under object-fit:contain."""
    if photo_r <= 0 or slot_r <= 0:
        return 0.0
    return aspect_mismatch(photo_r, slot_r)


def page_whitespace_ratio(
    slots: Sequence[Mapping[str, Any]],
    *,
    assets_map: Mapping[str, Any],
    slot_areas: Sequence[float],
) -> float:
    """Area-weighted whitespace from slots with fit=contain."""
    total = 0.0
    for i, slot in enumerate(slots):
        if str(slot.get("fit") or "") != "contain":
            continue
        aid = slot.get("assetId")
        asset = assets_map.get(aid) if aid else None
        pr = _asset_r(asset if isinstance(asset, Mapping) else None)
        try:
            sr = float(slot.get("displayAspect") or 0.0)
        except (TypeError, ValueError):
            sr = 0.0
        if pr is None or sr <= 0:
            continue
        area = float(slot_areas[i]) if i < len(slot_areas) else 0.0
        total += contain_whitespace_fraction(pr, sr) * max(0.0, area)
    return round(_clamp01(total), 4)


def _is_protected_fit(slot: Mapping[str, Any], role: str | None) -> bool:
    """Respect portrait_fit / explicit contain already chosen outside MSA."""
    fit = str(slot.get("fit") or "")
    if fit == "contain" and not slot.get("msaContain"):
        return True
    if role == "portrait" and fit == "contain":
        return True
    return False


def apply_crop_risk_fits(
    screen: dict[str, Any],
    *,
    assets_map: Mapping[str, Any] | None,
    slot_areas: Sequence[float],
    cfg: SlotAdaptationConfig,
) -> tuple[list[float], float]:
    """Mutate slots[].fit under crop_risk + whitespace_max (AC-MSA-06).

    Returns ``(crop_risk_per_slot, whitespace_ratio)``.
    """
    assets_map = assets_map or {}
    theta = float(cfg.crop_risk_contain_threshold)
    wmax = float(cfg.whitespace_max)
    slots = list(screen.get("slots") or [])
    risks: list[float] = []
    # Candidates sorted by risk desc so high-risk get contain first under budget.
    candidates: list[tuple[int, float, float]] = []  # idx, risk, ws_contrib

    for i, slot in enumerate(slots):
        try:
            sr = float(slot.get("displayAspect") or 0.0)
        except (TypeError, ValueError):
            sr = 0.0
        aid = slot.get("assetId")
        asset = assets_map.get(aid) if aid else None
        asset_m = asset if isinstance(asset, Mapping) else None
        risk = crop_risk_for_pair(asset_m, sr)
        risks.append(risk)
        role = str(slot.get("role") or "") or None
        if _is_protected_fit(slot, role):
            continue
        if risk < theta:
            continue
        pr = _asset_r(asset_m)
        if pr is None or sr <= 0:
            continue
        area = float(slot_areas[i]) if i < len(slot_areas) else 0.0
        contrib = contain_whitespace_fraction(pr, sr) * max(0.0, area)
        candidates.append((i, risk, contrib))

    candidates.sort(key=lambda t: (-t[1], t[0]))
    used_ws = 0.0
    # Count whitespace already committed by protected contain slots
    used_ws = page_whitespace_ratio(slots, assets_map=assets_map, slot_areas=slot_areas)

    for idx, _risk, contrib in candidates:
        if used_ws + contrib > wmax + 1e-9:
            continue
        slot = slots[idx]
        slot["fit"] = "contain"
        slot["msaContain"] = True
        used_ws += contrib

    screen["slots"] = slots
    ws = page_whitespace_ratio(slots, assets_map=assets_map, slot_areas=slot_areas)
    return risks, ws
