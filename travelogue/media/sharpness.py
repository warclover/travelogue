"""Sharpness heuristic for ingest dedupe and quality metadata."""

from __future__ import annotations

from typing import TypedDict

from PIL import Image, ImageFilter, ImageStat


class SharpnessRoi(TypedDict, total=False):
    x: float
    y: float
    w: float
    h: float


def _downscale_gray(img: Image.Image, *, max_edge: int) -> Image.Image:
    gray = img.convert("L")
    w, h = gray.size
    long_edge = max(w, h)
    if long_edge > max_edge:
        scale = max_edge / long_edge
        gray = gray.resize(
            (max(1, int(w * scale)), max(1, int(h * scale))),
            Image.Resampling.LANCZOS,
        )
    return gray


def _crop_roi(gray: Image.Image, roi: SharpnessRoi | None) -> Image.Image:
    if not roi:
        w, h = gray.size
        margin_w = int(w * 0.2)
        margin_h = int(h * 0.2)
        return gray.crop((margin_w, margin_h, w - margin_w, h - margin_h))
    w, h = gray.size
    x = max(0, min(w - 1, int(float(roi.get("x", 0)) * w)))
    y = max(0, min(h - 1, int(float(roi.get("y", 0)) * h)))
    rw = max(1, int(float(roi.get("w", 1)) * w))
    rh = max(1, int(float(roi.get("h", 1)) * h))
    return gray.crop((x, y, min(w, x + rw), min(h, y + rh)))


def _laplacian_variance_pil(gray: Image.Image) -> float:
    kernel = ImageFilter.Kernel(
        (3, 3),
        [0, 1, 0, 1, -4, 1, 0, 1, 0],
        scale=1,
    )
    lap = gray.filter(kernel)
    return float(ImageStat.Stat(lap).var[0])


def _laplacian_variance(gray: Image.Image) -> float:
    try:
        import cv2
        import numpy as np

        arr = np.asarray(gray, dtype=np.uint8)
        lap = cv2.Laplacian(arr, cv2.CV_64F)
        return float(lap.var())
    except Exception:
        return _laplacian_variance_pil(gray)


def sharpness_score(img: Image.Image, *, max_edge: int = 512) -> float:
    """
    Variance of edge filter on a downscaled grayscale image.

    Higher values usually mean sharper focus; used to pick the best frame in a burst.
    """
    gray = _downscale_gray(img, max_edge=max_edge)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    return float(ImageStat.Stat(edges).var[0])


def sharpness_score_v2(
    img: Image.Image,
    *,
    max_edge: int = 512,
    roi: SharpnessRoi | None = None,
) -> float:
    """Laplacian variance on ROI (salient box > center crop 60%)."""
    gray = _downscale_gray(img, max_edge=max_edge)
    roi_gray = _crop_roi(gray, roi)
    lap = _laplacian_variance(roi_gray)
    if lap > 1e-6:
        return lap
    # Low-texture (sky/wall/solid): Laplacian≈0 — fall back to v1 edge variance on same ROI
    edges = roi_gray.filter(ImageFilter.FIND_EDGES)
    return float(ImageStat.Stat(edges).var[0])
