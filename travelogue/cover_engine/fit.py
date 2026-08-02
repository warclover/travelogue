"""Style↔asset fit scoring (API-CSE-06/12)."""

from __future__ import annotations

from typing import Any

from travelogue.cover_engine.registry import get_profile, get_style
from travelogue.cover_engine.types import CoverStyleProfile

_DEFAULT_FIT_THRESHOLD = 0.15
_DEFAULT_FOCAL_X = 0.5
_DEFAULT_FOCAL_Y = 0.45
# Cameo must be a true circular crop candidate — not "roughly mid-frame".
_CAMEO_CENTER_DX = 0.10
_CAMEO_CENTER_DY = 0.12
_CAMEO_CENTER_BONUS = 0.40


def _focal(asset: dict[str, Any]) -> tuple[float, float]:
    fp = asset.get("focalPoint") or {}
    try:
        fx = float(fp.get("x", _DEFAULT_FOCAL_X))
    except (TypeError, ValueError):
        fx = _DEFAULT_FOCAL_X
    try:
        fy = float(fp.get("y", _DEFAULT_FOCAL_Y))
    except (TypeError, ValueError):
        fy = _DEFAULT_FOCAL_Y
    return fx, fy


def _has_face_signal(asset: dict[str, Any]) -> bool:
    faces = asset.get("faces")
    if isinstance(faces, (list, tuple)) and len(faces) > 0:
        return True
    for key in ("faceCount", "face_count", "numFaces"):
        raw = asset.get(key)
        if raw is None:
            continue
        try:
            if int(raw) > 0:
                return True
        except (TypeError, ValueError):
            continue
    return False


def focal_is_trusted(asset: dict[str, Any]) -> bool:
    """True when focal is measured — not missing / subject_detect sentinel."""
    fp = asset.get("focalPoint")
    if not isinstance(fp, dict):
        return False
    if fp.get("x") is None and fp.get("y") is None:
        return False
    fx, fy = _focal(asset)
    # Default written when face detection finds nothing (subject_detect).
    if abs(fx - _DEFAULT_FOCAL_X) < 1e-9 and abs(fy - _DEFAULT_FOCAL_Y) < 1e-9:
        return _has_face_signal(asset)
    return True


def _is_cameo_center(fx: float, fy: float) -> bool:
    return abs(fx - _DEFAULT_FOCAL_X) < _CAMEO_CENTER_DX and abs(
        fy - _DEFAULT_FOCAL_Y
    ) < _CAMEO_CENTER_DY


def style_fit_score(asset: dict[str, Any], profile: CoverStyleProfile) -> float:
    """Normalized fit contribution from profile.prefer."""
    if not profile.prefer:
        return 0.0
    score = 0.0
    fx, fy = _focal(asset)
    trusted = focal_is_trusted(asset)

    if "focal_y_max" in profile.prefer and fy <= float(profile.prefer["focal_y_max"]):
        score += 0.35
    if profile.prefer.get("center_subject"):
        # Unknown / sentinel focals must not inflate cameo (distribution collapse).
        if trusted and _is_cameo_center(fx, fy):
            score += _CAMEO_CENTER_BONUS
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
    if profile.prefer.get("pair_scene_person"):
        # Diptych primary prefers non-person landscape/scene.
        from travelogue.layout_contract.subject import asset_has_person

        if not asset_has_person(asset):
            score += 0.28
        elif trusted and fy <= 0.55:
            score += 0.08

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
        # Person covers: band-cut 题带横切腰线；加罚以倾向其它 opening style
        from travelogue.layout_contract.subject import asset_has_person

        if asset_has_person(asset) and fy >= 0.45:
            penalty += 0.95

    if profile.avoid.get("edge_subject") and (fx < 0.18 or fx > 0.82 or fy < 0.12 or fy > 0.88):
        penalty += 0.6

    if profile.avoid.get("subject_bottom") and fy >= 0.72:
        penalty += 0.5

    if profile.avoid.get("subject_left_30") and fx < 0.30:
        penalty += 0.55

    if profile.avoid.get("face_must_read"):
        # Tight center focal ≈ face that must remain readable under heavy dim.
        if focal_is_trusted(asset) and abs(fx - 0.5) < 0.12 and abs(fy - 0.42) < 0.14:
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
