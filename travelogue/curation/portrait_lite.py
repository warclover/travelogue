"""AA · Portrait L1 lite heuristics (faceCount / faceRatio / sharpness)."""

from __future__ import annotations

from travelogue.curation.asset_quality import asset_sharpness


def _norm_sharp(asset: dict) -> float:
    s = max(0.0, float(asset_sharpness(asset)))
    return s / (s + 150.0) if s else 0.0


def _face_count(asset: dict) -> int:
    q = asset.get("quality")
    if isinstance(q, dict) and q.get("faceCount") is not None:
        try:
            return max(0, int(q["faceCount"]))
        except (TypeError, ValueError):
            pass
    faces = asset.get("faces")
    if isinstance(faces, list):
        return len(faces)
    return 0


def _face_ratio(asset: dict) -> float:
    q = asset.get("quality")
    if isinstance(q, dict) and q.get("faceRatio") is not None:
        try:
            return max(0.0, float(q["faceRatio"]))
        except (TypeError, ValueError):
            pass
    return 0.0


def portrait_lite_subject_clarity_factor(asset: dict) -> float:
    """Lightweight multiplier for ``subjectClarity`` before aesthetic dims finalize."""
    faces = _face_count(asset)
    ratio = _face_ratio(asset)
    sharp = _norm_sharp(asset)
    if faces >= 2:
        if ratio < 0.02:
            return 0.90
        if ratio >= 0.05 and sharp >= 0.55:
            return 1.04
        if sharp < 0.35:
            return 0.88
        return 1.0
    if faces == 1:
        if ratio >= 0.12 and sharp >= 0.60:
            return 1.05
        if ratio >= 0.06 and sharp < 0.40:
            return 0.92
    return 1.0
