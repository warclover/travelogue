"""MSA · crop_risk → conditional contain + whitespace budget (S-MSA-04).

``crop_risk_for_pair`` / ``aspect_mismatch`` live in ``crop_solver`` (AEL
D-AEL-11 / AC-AEL-23). This module re-exports them so MSA call sites stay
stable. Album export must not import this file.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from travelogue.config.mosaic import SlotAdaptationConfig
from travelogue.layout_engine.crop_solver import (
    aspect_mismatch,
    asset_aspect,
    crop_risk_for_pair,
)

# Re-export: MSA tests and scorer/assign keep importing from msa_fit.
__all__ = [
    "aspect_mismatch",
    "crop_risk_for_pair",
    "contain_whitespace_fraction",
    "page_whitespace_ratio",
    "apply_crop_risk_fits",
]


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _asset_r(asset: Mapping[str, Any] | None) -> float | None:
    return asset_aspect(asset)


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
