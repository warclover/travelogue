"""Optional face detection for ingest (OpenCV Haar when available)."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class FaceDetectionResult:
    has_face: bool
    focal: tuple[float, float]
    tags: tuple[str, ...]
    face_count: int


def _opencv_available() -> bool:
    try:
        import cv2  # noqa: F401

        return True
    except ImportError:
        return False


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
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    classifier = cv2.CascadeClassifier(cascade_path)
    if classifier.empty():
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


def analyze_subject(
    img: Image.Image,
    *,
    min_face_size: int = 48,
    enabled: bool = True,
) -> FaceDetectionResult:
    """Run face detection; safe no-op when disabled or OpenCV missing."""
    default_focal = (0.5, 0.45)
    if not enabled:
        return FaceDetectionResult(False, default_focal, (), 0)

    faces = detect_faces_in_image(img, min_size=min_face_size)
    if not faces:
        return FaceDetectionResult(False, default_focal, (), 0)

    focal = focal_from_faces(faces, img_w=img.width, img_h=img.height)
    return FaceDetectionResult(True, focal, ("person", "face"), len(faces))
