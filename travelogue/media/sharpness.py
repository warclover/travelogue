"""Sharpness heuristic for ingest dedupe and quality metadata."""

from __future__ import annotations

from PIL import Image, ImageFilter, ImageStat


def sharpness_score(img: Image.Image, *, max_edge: int = 512) -> float:
    """
    Variance of edge filter on a downscaled grayscale image.

    Higher values usually mean sharper focus; used to pick the best frame in a burst.
    """
    gray = img.convert("L")
    w, h = gray.size
    long_edge = max(w, h)
    if long_edge > max_edge:
        scale = max_edge / long_edge
        gray = gray.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    return float(ImageStat.Stat(edges).var[0])
