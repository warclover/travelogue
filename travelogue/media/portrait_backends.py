"""Face landmark backends for portrait_analyze (PRD §5.1.4 · D6)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from PIL import Image


@dataclass(frozen=True)
class FaceLandmarks:
    """Normalized landmark points in [0,1] relative to the face crop."""

    left_eye: tuple[float, float] | None = None
    right_eye: tuple[float, float] | None = None
    nose: tuple[float, float] | None = None
    mouth_left: tuple[float, float] | None = None
    mouth_right: tuple[float, float] | None = None
    completeness: float = 0.0


class FaceLandmarkBackend(Protocol):
    name: str

    def landmarks(self, crop: Image.Image) -> FaceLandmarks | None:
        """Return landmarks for a padded face crop, or None on failure."""


class NullBackend:
    name = "null"

    def landmarks(self, crop: Image.Image) -> FaceLandmarks | None:
        return None


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def ear_from_eye_points(
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    p4: tuple[float, float],
    p5: tuple[float, float],
    p6: tuple[float, float],
) -> float:
    """Eye aspect ratio from six eye contour points (vertical / horizontal)."""
    vert = math.dist(p2, p6) + math.dist(p3, p5)
    horiz = math.dist(p1, p4)
    if horiz <= 1e-6:
        return 0.0
    return vert / (2.0 * horiz)


def map_ear_to_eyes_open(ear: float, *, center: float = 0.25, scale: float = 0.08) -> float:
    """Sigmoid map raw EAR → eyesOpenScore ∈ [0,1] (high = open)."""
    x = (ear - center) / max(scale, 1e-6)
    return _clamp01(1.0 / (1.0 + math.exp(-x)))


class OpenCVEyeBackend:
    """Fallback backend using Haar eye cascade inside the face crop."""

    name = "opencv_eye"

    def __init__(self) -> None:
        self._available = False
        self._eye_cascade = None
        try:
            import cv2  # noqa: F401

            cascade_path = cv2.data.haarcascades + "haarcascade_eye.xml"
            classifier = cv2.CascadeClassifier(cascade_path)
            if not classifier.empty():
                self._eye_cascade = classifier
                self._available = True
        except ImportError:
            pass

    @property
    def available(self) -> bool:
        return self._available

    def landmarks(self, crop: Image.Image) -> FaceLandmarks | None:
        if not self._available or self._eye_cascade is None:
            return None
        import cv2
        import numpy as np

        rgb = crop.convert("RGB")
        arr = np.array(rgb)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        h, w = gray.shape[:2]
        if h < 24 or w < 24:
            return None
        eyes = self._eye_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(max(8, w // 12), max(8, h // 12)),
        )
        if len(eyes) == 0:
            return FaceLandmarks(completeness=0.35)
        boxes = sorted(eyes, key=lambda b: b[2] * b[3], reverse=True)[:2]
        pts: list[tuple[float, float]] = []
        for x, y, ew, eh in boxes:
            cx = (x + ew / 2) / w
            cy = (y + eh / 2) / h
            pts.append((_clamp01(cx), _clamp01(cy)))
        left = pts[0]
        right = pts[1] if len(pts) > 1 else None
        if right and left[0] > right[0]:
            left, right = right, left
        completeness = 0.55 if right is None else 0.75
        return FaceLandmarks(left_eye=left, right_eye=right, completeness=completeness)

    def eyes_open_from_landmarks(self, lm: FaceLandmarks, *, crop: Image.Image) -> float | None:
        if lm.left_eye is None:
            return None
        if lm.right_eye is None:
            return 0.55
        import cv2
        import numpy as np

        rgb = crop.convert("RGB")
        arr = np.array(rgb)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        h, w = gray.shape[:2]

        def _eye_var(pt: tuple[float, float]) -> float:
            cx, cy = int(pt[0] * w), int(pt[1] * h)
            half = max(4, min(w, h) // 10)
            x0 = max(0, cx - half)
            y0 = max(0, cy - half)
            x1 = min(w, cx + half)
            y1 = min(h, cy + half)
            roi = gray[y0:y1, x0:x1]
            if roi.size == 0:
                return 0.0
            return float(cv2.Laplacian(roi, cv2.CV_64F).var())

        lv = _eye_var(lm.left_eye)
        rv = _eye_var(lm.right_eye)
        eye_sep = abs(lm.left_eye[0] - lm.right_eye[0])
        pseudo_ear = min(lv, rv) / 120.0 + eye_sep * 0.15
        return map_ear_to_eyes_open(pseudo_ear, center=0.35, scale=0.12)


class MediaPipeBackend:
    name = "mediapipe"

    def __init__(self) -> None:
        self._available = False
        self._landmarker = None
        try:
            import mediapipe as mp  # noqa: F401

            self._available = True
        except ImportError:
            pass

    @property
    def available(self) -> bool:
        return self._available

    def landmarks(self, crop: Image.Image) -> FaceLandmarks | None:
        if not self._available:
            return None
        try:
            import mediapipe as mp
            import numpy as np

            rgb = crop.convert("RGB")
            arr = np.array(rgb)
            h, w = arr.shape[:2]
            if h < 24 or w < 24:
                return None
            # Lazy init FaceMesh on first use (expensive).
            if self._landmarker is None:
                self._landmarker = mp.solutions.face_mesh.FaceMesh(
                    static_image_mode=True,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                )
            result = self._landmarker.process(arr)
            if not result.multi_face_landmarks:
                return None
            fl = result.multi_face_landmarks[0]
            # MediaPipe indices: left eye outer 33, right 263, nose 1, mouth 61/291
            idx = {33, 133, 159, 145, 263, 362, 386, 374, 1, 61, 291}
            present = sum(1 for i in idx if i < len(fl.landmark))
            completeness = present / len(idx)

            def _pt(i: int) -> tuple[float, float]:
                p = fl.landmark[i]
                return (_clamp01(p.x), _clamp01(p.y))

            left_eye = (
                (_pt(33)[0] + _pt(133)[0] + _pt(159)[0] + _pt(145)[0]) / 4,
                (_pt(33)[1] + _pt(133)[1] + _pt(159)[1] + _pt(145)[1]) / 4,
            )
            right_eye = (
                (_pt(263)[0] + _pt(362)[0] + _pt(386)[0] + _pt(374)[0]) / 4,
                (_pt(263)[1] + _pt(362)[1] + _pt(386)[1] + _pt(374)[1]) / 4,
            )
            return FaceLandmarks(
                left_eye=left_eye,
                right_eye=right_eye,
                nose=_pt(1),
                mouth_left=_pt(61),
                mouth_right=_pt(291),
                completeness=completeness,
            )
        except Exception:
            return None

    def eyes_open_from_landmarks(self, lm: FaceLandmarks, *, crop: Image.Image) -> float | None:
        if lm.left_eye is None or lm.right_eye is None:
            return None
        # Approximate EAR from eye center distance vs vertical spread proxy.
        dx = abs(lm.left_eye[0] - lm.right_eye[0])
        dy = abs(lm.left_eye[1] - lm.right_eye[1])
        pseudo_ear = dx * 0.6 - dy * 0.2
        return map_ear_to_eyes_open(pseudo_ear, center=0.18, scale=0.05)


def resolve_backend(preference: str = "auto") -> FaceLandmarkBackend:
    pref = str(preference or "auto").lower()
    if pref in ("off", "none", "null"):
        return NullBackend()
    if pref == "mediapipe":
        mp = MediaPipeBackend()
        return mp if mp.available else NullBackend()
    if pref == "opencv":
        cv = OpenCVEyeBackend()
        return cv if cv.available else NullBackend()
    # auto
    mp = MediaPipeBackend()
    if mp.available:
        return mp
    cv = OpenCVEyeBackend()
    if cv.available:
        return cv
    return NullBackend()
