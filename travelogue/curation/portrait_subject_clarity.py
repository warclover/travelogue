"""PRD §6.3 · inject portrait factors into aesthetic.subjectClarity."""

from __future__ import annotations

import math
from typing import Any

from travelogue.config.portrait import PortraitConfig, portrait_from_dict


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def read_portrait_block(asset: dict) -> dict[str, Any] | None:
    q = asset.get("quality")
    if not isinstance(q, dict):
        return None
    p = q.get("portrait")
    return p if isinstance(p, dict) else None


def portrait_has_signal(asset: dict, *, min_confidence: float = 0.5) -> bool:
    p = read_portrait_block(asset)
    if not p:
        return False
    try:
        conf = float(p.get("confidence") or 0.0)
    except (TypeError, ValueError):
        return False
    if conf < min_confidence:
        return False
    return p.get("eyesOpenScore") is not None or p.get("faceSharpness") is not None


def norm_face_sharpness(raw: float | None, *, k: float = 800.0) -> float:
    if raw is None:
        return 0.5
    val = max(0.0, float(raw))
    return _clamp01(val / (val + k))


def penalty_eyes_closed(
    eyes_open: float,
    *,
    threshold: float = 0.35,
    penalty_max: float = 0.25,
    temperature: float = 0.08,
) -> float:
    x = (threshold - eyes_open) / max(temperature, 1e-6)
    sig = 1.0 / (1.0 + math.exp(-x))
    return penalty_max * sig


def penalty_blur_face(
    face_sharp_norm: float,
    *,
    threshold: float = 0.35,
    penalty_max: float = 0.25,
    temperature: float = 0.08,
) -> float:
    """Soft penalty when normalized face sharpness is below threshold (§6.3 / blur_face)."""
    x = (threshold - face_sharp_norm) / max(temperature, 1e-6)
    sig = 1.0 / (1.0 + math.exp(-x))
    return penalty_max * sig


def compute_portrait_subject_clarity(
    *,
    norm_sharp: float,
    portrait: dict[str, Any],
    cfg: PortraitConfig | None = None,
) -> tuple[float, dict[str, float]]:
    """Return (subjectClarity, signal extras) when portrait block is usable."""
    cfg = cfg or PortraitConfig()
    w = cfg.subject_clarity_weights
    eyes_raw = portrait.get("eyesOpenScore")
    face_raw = portrait.get("faceSharpness")
    eyes = float(eyes_raw) if eyes_raw is not None else 0.5
    face_norm = norm_face_sharpness(
        float(face_raw) if face_raw is not None else None,
    )
    frontal = 0.5  # W2 placeholder
    base = _clamp01(norm_sharp)
    score = (
        w.face_sharp * face_norm
        + w.eyes * _clamp01(eyes)
        + w.frontal * frontal
        + w.base * base
    )
    pen = penalty_eyes_closed(
        eyes,
        threshold=cfg.eyes_threshold(),
        penalty_max=cfg.eyes_closed.penalty_max,
        temperature=cfg.eyes_closed.temperature,
    )
    face_pen = 0.0
    if face_raw is not None:
        face_pen = penalty_blur_face(
            face_norm,
            threshold=cfg.eyes_threshold(),
            penalty_max=cfg.eyes_closed.penalty_max,
            temperature=cfg.eyes_closed.temperature,
        )
    cap = cfg.subject_clarity_penalty_cap
    score = _clamp01(score - min(cap, pen + face_pen))
    signals = {
        "portraitEyesOpen": round(_clamp01(eyes), 4),
        "portraitFaceSharpPct": round(face_norm, 4),
        "portraitApplied": 1.0,
    }
    return round(score, 4), signals


def portrait_cover_defect_penalty(asset: dict, *, cfg: PortraitConfig | None = None) -> float:
    """Closed-eye + blur-face penalty for cover/hero key slots (PRD §6.3 / P3-3)."""
    from travelogue.config.portrait import PortraitConfig as PC

    p_cfg = cfg or PC()
    if not p_cfg.enabled or not p_cfg.gate_changes_on_signal:
        return 0.0
    if not portrait_has_signal(asset, min_confidence=p_cfg.min_confidence):
        return 0.0
    block = read_portrait_block(asset) or {}
    total = 0.0
    eyes = block.get("eyesOpenScore")
    if eyes is not None:
        total += penalty_eyes_closed(
            float(eyes),
            threshold=p_cfg.eyes_threshold(),
            penalty_max=p_cfg.eyes_closed.penalty_max,
            temperature=p_cfg.eyes_closed.temperature,
        )
    face_raw = block.get("faceSharpness")
    if face_raw is not None:
        face_norm = norm_face_sharpness(float(face_raw))
        total += penalty_blur_face(
            face_norm,
            threshold=p_cfg.eyes_threshold(),
            penalty_max=p_cfg.eyes_closed.penalty_max,
            temperature=p_cfg.eyes_closed.temperature,
        )
    return min(p_cfg.subject_clarity_penalty_cap, total)


def portrait_cover_eyes_penalty(asset: dict, *, cfg: PortraitConfig | None = None) -> float:
    """Backward-compatible alias; prefer ``portrait_cover_defect_penalty``."""
    return portrait_cover_defect_penalty(asset, cfg=cfg)


def resolve_portrait_config(raw: dict[str, Any] | None) -> PortraitConfig:
    cull = raw if isinstance(raw, dict) else {}
    nested = cull.get("portrait")
    if isinstance(nested, dict):
        return portrait_from_dict(nested)
    return portrait_from_dict(cull)
