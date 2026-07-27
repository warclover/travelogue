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
    faces: tuple[tuple[int, int, int, int], ...] = ()
    faces_norm: tuple[dict[str, float], ...] = ()
    protect_box: dict[str, float] | None = None


def _opencv_available() -> bool:
    try:
        import cv2

        return hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data")
    except ImportError:
        return False


_cascade_classifier = None
_profile_classifier = None
_cascade_lock = threading.Lock()

# Protect-box expansion relative to each face (hair / shoulders / half-body).
_PROTECT_PAD_TOP = 0.35
_PROTECT_PAD_BOTTOM = 1.6
_PROTECT_PAD_X = 0.25
_NMS_IOU = 0.35


def _get_cascade_classifier():
    """P7-B1 · lazy singleton Haar cascade (frontal)."""
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


def _get_profile_classifier():
    """Lazy singleton profile-face Haar cascade."""
    global _profile_classifier
    with _cascade_lock:
        if _profile_classifier is not None:
            return _profile_classifier
        import cv2

        cascade_path = cv2.data.haarcascades + "haarcascade_profileface.xml"
        classifier = cv2.CascadeClassifier(cascade_path)
        if classifier.empty():
            return None
        _profile_classifier = classifier
        return _profile_classifier


def reset_cascade_classifier() -> None:
    """Clear cached classifiers (tests)."""
    global _cascade_classifier, _profile_classifier
    _cascade_classifier = None
    _profile_classifier = None


def _downscale_for_detect(img: Image.Image, max_edge: int) -> tuple[Image.Image, float]:
    """P7-B4 · optional downscale before Haar detect; returns (work image, scale to original)."""
    if max_edge <= 0:
        return img, 1.0
    w, h = img.size
    long_edge = max(w, h)
    if long_edge <= max_edge:
        return img, 1.0
    scale = max_edge / long_edge
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return img.resize(new_size, Image.Resampling.BILINEAR), scale


def _box_iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x0 = max(ax, bx)
    y0 = max(ay, by)
    x1 = min(ax + aw, bx + bw)
    y1 = min(ay + ah, by + bh)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    inter = (x1 - x0) * (y1 - y0)
    union = aw * ah + bw * bh - inter
    if union <= 0:
        return 0.0
    return inter / union


def _nms_merge(
    boxes: list[tuple[int, int, int, int]],
    *,
    iou_thresh: float = _NMS_IOU,
) -> list[tuple[int, int, int, int]]:
    if not boxes:
        return []
    ordered = sorted(boxes, key=lambda b: b[2] * b[3], reverse=True)
    kept: list[tuple[int, int, int, int]] = []
    for box in ordered:
        if any(_box_iou(box, k) >= iou_thresh for k in kept):
            continue
        kept.append(box)
    return kept


def _detect_with_classifier(
    gray,
    classifier,
    *,
    min_size: int,
    flip_x: bool = False,
) -> list[tuple[int, int, int, int]]:
    import cv2

    work = gray
    if flip_x:
        work = cv2.flip(gray, 1)
    raw = classifier.detectMultiScale(
        work,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(min_size, min_size),
    )
    if len(raw) == 0:
        return []
    h, w = gray.shape[:2]
    out: list[tuple[int, int, int, int]] = []
    for x, y, bw, bh in raw:
        if flip_x:
            x = w - int(x) - int(bw)
        out.append((int(x), int(y), int(bw), int(bh)))
    return out


def detect_faces_in_image(
    img: Image.Image,
    *,
    min_size: int = 48,
    max_edge: int = 0,
) -> list[tuple[int, int, int, int]]:
    """
    Return face boxes (x, y, w, h) in pixel coords.
    Empty when OpenCV is not installed or no faces found.

    Runs frontal + profile (both mirrors) Haar cascades and NMS-merges.
    """
    if not _opencv_available():
        return []
    import cv2
    import numpy as np

    work, scale = _downscale_for_detect(img, max_edge)
    rgb = work.convert("RGB")
    arr = np.array(rgb)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    scaled_min = max(1, int(min_size * scale)) if scale < 1.0 else min_size

    boxes: list[tuple[int, int, int, int]] = []
    frontal = _get_cascade_classifier()
    if frontal is not None:
        boxes.extend(
            _detect_with_classifier(gray, frontal, min_size=scaled_min, flip_x=False)
        )
    profile = _get_profile_classifier()
    if profile is not None:
        boxes.extend(
            _detect_with_classifier(gray, profile, min_size=scaled_min, flip_x=False)
        )
        boxes.extend(
            _detect_with_classifier(gray, profile, min_size=scaled_min, flip_x=True)
        )

    boxes = _nms_merge(boxes)
    if not boxes:
        return []
    if scale >= 1.0:
        return boxes
    inv = 1.0 / scale
    return [
        (int(x * inv), int(y * inv), int(w * inv), int(h * inv))
        for x, y, w, h in boxes
    ]


def _union_pixel_box(
    faces: list[tuple[int, int, int, int]],
) -> tuple[int, int, int, int] | None:
    if not faces:
        return None
    x0 = min(x for x, _, _, _ in faces)
    y0 = min(y for _, y, _, _ in faces)
    x1 = max(x + w for x, _, w, _ in faces)
    y1 = max(y + h for _, y, _, h in faces)
    return (x0, y0, x1 - x0, y1 - y0)


def focal_from_faces(
    faces: list[tuple[int, int, int, int]],
    *,
    img_w: int,
    img_h: int,
    default: tuple[float, float] = (0.5, 0.45),
) -> tuple[float, float]:
    """Center of face-union box, normalized 0..1 (group-shot aware)."""
    if not faces or img_w <= 0 or img_h <= 0:
        return default
    union = _union_pixel_box(faces)
    if union is None:
        return default
    x, y, w, h = union
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


def faces_norm_from_faces(
    faces: list[tuple[int, int, int, int]],
    *,
    img_w: int,
    img_h: int,
) -> tuple[dict[str, float], ...]:
    """All face boxes as normalized {x,y,w,h}."""
    if not faces or img_w <= 0 or img_h <= 0:
        return ()
    out: list[dict[str, float]] = []
    for x, y, w, h in faces:
        out.append(
            {
                "x": round(min(1.0, max(0.0, x / img_w)), 4),
                "y": round(min(1.0, max(0.0, y / img_h)), 4),
                "w": round(min(1.0, max(0.0, w / img_w)), 4),
                "h": round(min(1.0, max(0.0, h / img_h)), 4),
            }
        )
    return tuple(out)


def protect_box_from_faces(
    faces: list[tuple[int, int, int, int]],
    *,
    img_w: int,
    img_h: int,
    pad_top: float = _PROTECT_PAD_TOP,
    pad_bottom: float = _PROTECT_PAD_BOTTOM,
    pad_x: float = _PROTECT_PAD_X,
) -> dict[str, float] | None:
    """Union of expanded face boxes (hair + shoulders), normalized."""
    if not faces or img_w <= 0 or img_h <= 0:
        return None
    x0 = img_w
    y0 = img_h
    x1 = 0
    y1 = 0
    for x, y, w, h in faces:
        px = pad_x * w
        py_top = pad_top * h
        py_bot = pad_bottom * h
        left = x - px
        top = y - py_top
        right = x + w + px
        bottom = y + h + py_bot
        x0 = min(x0, left)
        y0 = min(y0, top)
        x1 = max(x1, right)
        y1 = max(y1, bottom)
    x0 = max(0.0, min(float(img_w), x0))
    y0 = max(0.0, min(float(img_h), y0))
    x1 = max(0.0, min(float(img_w), x1))
    y1 = max(0.0, min(float(img_h), y1))
    if x1 <= x0 or y1 <= y0:
        return None
    return {
        "x": round(x0 / img_w, 4),
        "y": round(y0 / img_h, 4),
        "w": round((x1 - x0) / img_w, 4),
        "h": round((y1 - y0) / img_h, 4),
    }


def analyze_subject(
    img: Image.Image,
    *,
    min_face_size: int = 48,
    face_detect_max_edge: int = 0,
    enabled: bool = True,
) -> FaceDetectionResult:
    """Run face detection; safe no-op when disabled or OpenCV missing."""
    default_focal = (0.5, 0.45)
    if not enabled:
        return FaceDetectionResult(False, default_focal, (), 0, None, (), (), None)

    faces = detect_faces_in_image(
        img,
        min_size=min_face_size,
        max_edge=face_detect_max_edge,
    )
    if not faces:
        return FaceDetectionResult(False, default_focal, (), 0, None, (), (), None)

    focal = focal_from_faces(faces, img_w=img.width, img_h=img.height)
    salient = salient_box_from_faces(faces, img_w=img.width, img_h=img.height)
    faces_norm = faces_norm_from_faces(faces, img_w=img.width, img_h=img.height)
    protect = protect_box_from_faces(faces, img_w=img.width, img_h=img.height)
    face_tuple = tuple((int(x), int(y), int(w), int(h)) for x, y, w, h in faces)
    return FaceDetectionResult(
        True,
        focal,
        ("person", "face"),
        len(faces),
        salient,
        face_tuple,
        faces_norm,
        protect,
    )
