"""Style↔asset fit scoring (API-CSE-06/12)."""

from __future__ import annotations

from typing import Any

from travelogue.cover_engine.registry import get_profile, get_style
from travelogue.cover_engine.types import CoverStyleProfile

_DEFAULT_FIT_THRESHOLD = 0.15


def _focal(asset: dict[str, Any]) -> tuple[float, float]:
    fp = asset.get("focalPoint") or {}
    try:
        fx = float(fp.get("x", 0.5))
    except (TypeError, ValueError):
        fx = 0.5
    try:
        fy = float(fp.get("y", 0.45))
    except (TypeError, ValueError):
        fy = 0.45
    return fx, fy


def style_fit_score(asset: dict[str, Any], profile: CoverStyleProfile) -> float:
    """Normalized fit contribution from profile.prefer."""
    if not profile.prefer:
        return 0.0
    score = 0.0
    fx, fy = _focal(asset)

    if "focal_y_max" in profile.prefer and fy <= float(profile.prefer["focal_y_max"]):
        score += 0.35
    if profile.prefer.get("center_subject"):
        if abs(fx - 0.5) < 0.18 and abs(fy - 0.45) < 0.22:
            score += 0.4
    if profile.prefer.get("right_weighted") and fx >= 0.45:
        score += 0.25
    if profile.prefer.get("upper_scene") and fy <= 0.5:
        score += 0.2
    if profile.prefer.get("horizon") and 0.25 <= fy <= 0.55:
        score += 0.15
    if profile.prefer.get("texture_mood"):
        try:
            aesthetic = float((asset.get("aesthetic") or {}).get("overall", 0) or 0)
        except (TypeError, ValueError):
            aesthetic = 0.0
        if aesthetic >= 0.55:
            score += 0.3
        elif aesthetic >= 0.4:
            score += 0.12
    if profile.prefer.get("short_title"):
        # Asset-level signal unused; mild baseline so monument is not always 0-fit.
        score += 0.05

    return min(1.0, score)


def style_avoid_penalty(asset: dict[str, Any], profile: CoverStyleProfile) -> float:
    """Non-negative penalty from profile.avoid."""
    if not profile.avoid:
        return 0.0
    penalty = 0.0
    fx, fy = _focal(asset)

    band = profile.avoid.get("band_safe_zone")
    if isinstance(band, (list, tuple)) and len(band) == 2:
        lo, hi = float(band[0]), float(band[1])
        if lo <= fy <= hi:
            penalty += 0.8

    if profile.avoid.get("edge_subject") and (fx < 0.18 or fx > 0.82 or fy < 0.12 or fy > 0.88):
        penalty += 0.6

    if profile.avoid.get("subject_bottom") and fy >= 0.72:
        penalty += 0.5

    if profile.avoid.get("subject_left_30") and fx < 0.30:
        penalty += 0.55

    if profile.avoid.get("face_must_read"):
        # Tight center focal ≈ face that must remain readable under heavy dim.
        if abs(fx - 0.5) < 0.12 and abs(fy - 0.42) < 0.14:
            penalty += 0.55

    if profile.avoid.get("very_light_bg"):
        try:
            luma = float(asset.get("lowerLuma", asset.get("avgLuma", 0.4)) or 0.4)
        except (TypeError, ValueError):
            luma = 0.4
        if luma >= 0.72:
            penalty += 0.45

    return penalty


def net_style_fit(asset: dict[str, Any], profile: CoverStyleProfile) -> float:
    return style_fit_score(asset, profile) - style_avoid_penalty(asset, profile)


def style_fit_below_threshold(
    asset: dict[str, Any],
    style_id: str,
    *,
    threshold: float | None = None,
) -> bool:
    rec = get_style(style_id)
    if rec is None:
        return True
    profile = get_profile(style_id)
    fit = net_style_fit(asset, profile)
    cut = _DEFAULT_FIT_THRESHOLD if threshold is None else float(threshold)
    return fit < cut
