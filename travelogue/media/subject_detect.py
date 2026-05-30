"""Optional face detection for ingest (OpenCV Haar when available)."""

from __future__ import annotations

import threading
from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class FaceDetectionResult:
    has_face: bool
    focal: tuple[float, float]
    tags: tuple[str, ...]
    face_count: int
    salient_box: dict[str, float] | None = None


def _opencv_available() -> bool:
    try:
        import cv2  # noqa: F401

        return True
    except ImportError:
        return False


_cascade_classifier = None
_cascade_lock = threading.Lock()


def _get_cascade_classifier():
    """P7-B1 · lazy singleton Haar cascade."""
    global _cascade_classifier
    with _cascade_lock:
        if _cascade_classifier is not None:
            return _cascade_classifier
        import cv2

        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        classifier = cv2.CascadeClassifier(cascade_path)
        if classifier.empty():
            return None
        _cascade_classifier = classifier
        return _cascade_classifier


def reset_cascade_classifier() -> None:
    """Clear cached classifier (tests)."""
    global _cascade_classifier
    _cascade_classifier = None


def detect_faces_in_image(
    img: Image.Image,
    *,
    min_size: int = 48,
) -> list[tuple[int, int, int, int]]:
    """
    Return face boxes (x, y, w, h) in pixel coords.
    Empty when OpenCV is not installed or no faces found.
    """
    if not _opencv_available():
        return []
    import cv2
    import numpy as np

    rgb = img.convert("RGB")
    arr = np.array(rgb)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    classifier = _get_cascade_classifier()
    if classifier is None:
        return []
    faces = classifier.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(min_size, min_size),
    )
    if len(faces) == 0:
        return []
    return [(int(x), int(y), int(w), int(h)) for x, y, w, h in faces]


def focal_from_faces(
    faces: list[tuple[int, int, int, int]],
    *,
    img_w: int,
    img_h: int,
    default: tuple[float, float] = (0.5, 0.45),
) -> tuple[float, float]:
    """Center of largest face box, normalized 0..1."""
    if not faces or img_w <= 0 or img_h <= 0:
        return default
    x, y, w, h = max(faces, key=lambda b: b[2] * b[3])
    cx = (x + w / 2) / img_w
    cy = (y + h / 2) / img_h
    return (min(1.0, max(0.0, cx)), min(1.0, max(0.0, cy)))


def salient_box_from_faces(
    faces: list[tuple[int, int, int, int]],
    *,
    img_w: int,
    img_h: int,
) -> dict[str, float] | None:
    """Normalized salient region from largest face box."""
    if not faces or img_w <= 0 or img_h <= 0:
        return None
    x, y, w, h = max(faces, key=lambda b: b[2] * b[3])
    return {
        "x": round(min(1.0, max(0.0, x / img_w)), 4),
        "y": round(min(1.0, max(0.0, y / img_h)), 4),
        "w": round(min(1.0, max(0.0, w / img_w)), 4),
        "h": round(min(1.0, max(0.0, h / img_h)), 4),
    }


def analyze_subject(
    img: Image.Image,
    *,
    min_face_size: int = 48,
    enabled: bool = True,
) -> FaceDetectionResult:
    """Run face detection; safe no-op when disabled or OpenCV missing."""
    default_focal = (0.5, 0.45)
    if not enabled:
        return FaceDetectionResult(False, default_focal, (), 0, None)

    faces = detect_faces_in_image(img, min_size=min_face_size)
    if not faces:
        return FaceDetectionResult(False, default_focal, (), 0, None)

    focal = focal_from_faces(faces, img_w=img.width, img_h=img.height)
    salient = salient_box_from_faces(faces, img_w=img.width, img_h=img.height)
    return FaceDetectionResult(True, focal, ("person", "face"), len(faces), salient)
