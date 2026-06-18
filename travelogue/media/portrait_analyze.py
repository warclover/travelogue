"""Portrait quality analysis at ingest (PRD §5.1 · M1)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from PIL import Image

from travelogue.config.portrait import PortraitConfig
from travelogue.media.portrait_backends import (
    FaceLandmarkBackend,
    FaceLandmarks,
    MediaPipeBackend,
    OpenCVEyeBackend,
    map_ear_to_eyes_open,
    resolve_backend,
)

PORTRAIT_VERSION = "pc-v1"


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def pad_bbox(
    x: int,
    y: int,
    w: int,
    h: int,
    *,
    img_w: int,
    img_h: int,
    pad_ratio: float = 0.20,
) -> tuple[int, int, int, int]:
    pad_x = int(w * pad_ratio)
    pad_y = int(h * pad_ratio)
    x0 = max(0, x - pad_x)
    y0 = max(0, y - pad_y)
    x1 = min(img_w, x + w + pad_x)
    y1 = min(img_h, y + h + pad_y)
    return x0, y0, max(1, x1 - x0), max(1, y1 - y0)


def _downscale(img: Image.Image, max_edge: int) -> tuple[Image.Image, float]:
    if max_edge <= 0:
        return img, 1.0
    w, h = img.size
    long_edge = max(w, h)
    if long_edge <= max_edge:
        return img, 1.0
    scale = max_edge / long_edge
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return img.resize(new_size, Image.Resampling.BILINEAR), scale


def laplacian_variance(img: Image.Image, box: tuple[int, int, int, int] | None = None) -> float:
    try:
        import cv2
        import numpy as np
    except ImportError:
        return 0.0
    rgb = img.convert("RGB")
    arr = np.array(rgb)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    if box is not None:
        x, y, w, h = box
        gray = gray[y : y + h, x : x + w]
    if gray.size == 0:
        return 0.0
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


@dataclass(frozen=True)
class PerFacePortrait:
    bbox: tuple[int, int, int, int]
    eyes_open_score: float | None
    face_sharpness: float
    eye_focus_raw: float
    confidence: float


@dataclass(frozen=True)
class PortraitAnalyzeResult:
    eyes_open_score: float | None
    face_sharpness: float | None
    eye_focus_raw: float | None
    confidence: float
    per_face: tuple[PerFacePortrait, ...] = ()
    backend: str = "null"

    def to_quality_dict(self, *, cfg: PortraitConfig | None = None) -> dict[str, Any]:
        out: dict[str, Any] = {
            "version": PORTRAIT_VERSION,
            "confidence": round(self.confidence, 4),
            "backend": self.backend,
        }
        if self.eyes_open_score is not None:
            out["eyesOpenScore"] = round(self.eyes_open_score, 4)
        if self.face_sharpness is not None:
            out["faceSharpness"] = round(self.face_sharpness, 2)
        if self.eye_focus_raw is not None:
            out["eyeFocusRaw"] = round(self.eye_focus_raw, 2)
        if cfg and cfg.debug_per_face and self.per_face:
            out["perFace"] = [
                {
                    "bbox": list(f.bbox),
                    "eyesOpenScore": f.eyes_open_score,
                    "faceSharpness": round(f.face_sharpness, 2),
                    "eyeFocusRaw": round(f.eye_focus_raw, 2),
                    "confidence": round(f.confidence, 4),
                }
                for f in self.per_face
            ]
        return out


def _upper_face_eyes_proxy(crop: Image.Image) -> float:
    """Heuristic eyes-open proxy from upper vs lower face sharpness."""
    w, h = crop.size
    if h < 20 or w < 20:
        return 0.5
    upper = laplacian_variance(crop, (0, 0, w, max(4, int(h * 0.45))))
    lower = laplacian_variance(crop, (0, max(0, h - int(h * 0.45)), w, max(4, int(h * 0.45))))
    denom = upper + lower + 1e-6
    ratio = upper / denom
    return map_ear_to_eyes_open(ratio, center=0.52, scale=0.08)


def _confidence_from_face(
    *,
    completeness: float,
    size_factor: float,
    face_sharp: float,
) -> float:
    """Blend landmark completeness with face ROI sharpness; small faces still gate in."""
    effective_size = 0.42 + 0.58 * _clamp01(size_factor)
    sharp_term = min(1.0, face_sharp / 250.0)
    base = 0.38 + 0.45 * sharp_term + 0.17 * _clamp01(completeness)
    return _clamp01(effective_size * base)


def _eyes_open_from_backend(
    backend: FaceLandmarkBackend,
    crop: Image.Image,
    lm: FaceLandmarks,
) -> float:
    if isinstance(backend, OpenCVEyeBackend):
        score = backend.eyes_open_from_landmarks(lm, crop=crop)
        if score is not None:
            return score
    elif isinstance(backend, MediaPipeBackend):
        score = backend.eyes_open_from_landmarks(lm, crop=crop)
        if score is not None:
            return score
    elif lm.left_eye is not None and lm.right_eye is not None:
        dx = abs(lm.left_eye[0] - lm.right_eye[0])
        return map_ear_to_eyes_open(dx * 0.5, center=0.15, scale=0.05)
    elif lm.left_eye is not None:
        return 0.55
    return _upper_face_eyes_proxy(crop)


def _analyze_one_face(
    img: Image.Image,
    bbox: tuple[int, int, int, int],
    *,
    backend: FaceLandmarkBackend,
    cfg: PortraitConfig,
    min_face_px: int,
) -> PerFacePortrait | None:
    x, y, w, h = bbox
    if min(w, h) < min_face_px:
        return None
    img_w, img_h = img.size
    px, py, pw, ph = pad_bbox(x, y, w, h, img_w=img_w, img_h=img_h, pad_ratio=cfg.bbox_pad_ratio)
    crop = img.crop((px, py, px + pw, py + ph))
    face_sharp = laplacian_variance(crop)
    lm = backend.landmarks(crop)
    if lm is None:
        eyes = _upper_face_eyes_proxy(crop)
        size_factor = _clamp01(min(w, h) / 120.0)
        confidence = _confidence_from_face(
            completeness=0.35,
            size_factor=size_factor,
            face_sharp=face_sharp,
        )
        return PerFacePortrait(
            bbox=bbox,
            eyes_open_score=eyes,
            face_sharpness=face_sharp,
            eye_focus_raw=laplacian_variance(
                crop,
                (0, 0, crop.size[0], max(4, int(crop.size[1] * 0.45))),
            ),
            confidence=confidence,
        )
    eyes = _eyes_open_from_backend(backend, crop, lm)
    eye_focus = 0.0
    if lm.left_eye and lm.right_eye:
        cw, ch = crop.size
        for pt in (lm.left_eye, lm.right_eye):
            cx, cy = int(pt[0] * cw), int(pt[1] * ch)
            half = max(4, min(cw, ch) // 10)
            eye_focus = max(
                eye_focus,
                laplacian_variance(
                    crop,
                    (
                        max(0, cx - half),
                        max(0, cy - half),
                        min(cw, 2 * half),
                        min(ch, 2 * half),
                    ),
                ),
            )
    size_factor = _clamp01(min(w, h) / 120.0)
    confidence = _confidence_from_face(
        completeness=lm.completeness,
        size_factor=size_factor,
        face_sharp=face_sharp,
    )
    return PerFacePortrait(
        bbox=bbox,
        eyes_open_score=eyes,
        face_sharpness=face_sharp,
        eye_focus_raw=eye_focus,
        confidence=confidence,
    )


def aggregate_portrait_faces(
    faces: tuple[PerFacePortrait, ...],
    *,
    primary_blend: float = 0.7,
) -> PortraitAnalyzeResult:
    if not faces:
        return PortraitAnalyzeResult(None, None, None, 0.0, (), "null")
    primary = max(faces, key=lambda f: f.bbox[2] * f.bbox[3])
    others = [f for f in faces if f is not primary]
    eyes_vals = [v for v in (f.eyes_open_score for f in faces) if v is not None]
    if eyes_vals:
        primary_eyes = primary.eyes_open_score if primary.eyes_open_score is not None else 0.5
        if others:
            mean_other = sum(
                f.eyes_open_score if f.eyes_open_score is not None else primary_eyes for f in others
            ) / len(others)
            eyes = primary_blend * primary_eyes + (1.0 - primary_blend) * mean_other
        else:
            eyes = primary_eyes
    else:
        eyes = None
    return PortraitAnalyzeResult(
        eyes_open_score=eyes,
        face_sharpness=primary.face_sharpness,
        eye_focus_raw=primary.eye_focus_raw,
        confidence=primary.confidence,
        per_face=faces,
    )


def analyze_portrait(
    img: Image.Image,
    faces: list[tuple[int, int, int, int]],
    *,
    cfg: PortraitConfig | None = None,
    min_face_px: int = 48,
    backend: FaceLandmarkBackend | None = None,
) -> PortraitAnalyzeResult:
    """Analyze portrait signals for detected face bboxes; fail-open on errors."""
    cfg = cfg or PortraitConfig()
    if not cfg.enabled or not faces:
        return PortraitAnalyzeResult(None, None, None, 0.0, (), "null")
    backend = backend or resolve_backend(cfg.backend)
    work, scale = _downscale(img, cfg.analyze_max_edge)
    scaled_faces = faces
    if scale < 1.0:
        inv = 1.0 / scale
        scaled_faces = [
            (int(x * inv), int(y * inv), int(w * inv), int(h * inv)) for x, y, w, h in faces
        ]
    per: list[PerFacePortrait] = []
    for bbox in scaled_faces:
        one = _analyze_one_face(
            work,
            bbox,
            backend=backend,
            cfg=cfg,
            min_face_px=min_face_px,
        )
        if one is not None:
            per.append(one)
    agg = aggregate_portrait_faces(
        tuple(per),
        primary_blend=cfg.multi_face_eyes_blend_primary,
    )
    return PortraitAnalyzeResult(
        eyes_open_score=agg.eyes_open_score,
        face_sharpness=agg.face_sharpness,
        eye_focus_raw=agg.eye_focus_raw,
        confidence=agg.confidence,
        per_face=agg.per_face,
        backend=getattr(backend, "name", "null"),
    )


def eyes_open_lite(
    img: Image.Image,
    bbox: tuple[int, int, int, int],
    *,
    cfg: PortraitConfig | None = None,
    backend: FaceLandmarkBackend | None = None,
) -> float | None:
    """Lightweight eyes score for ingest burst tiebreak (§5.1.4b)."""
    cfg = cfg or PortraitConfig()
    backend = backend or resolve_backend(cfg.backend)
    one = _analyze_one_face(
        img,
        bbox,
        backend=backend,
        cfg=cfg,
        min_face_px=48,
    )
    if one is None:
        return None
    return one.eyes_open_score
