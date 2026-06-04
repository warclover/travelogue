"""Lightweight face crop embeddings for cohort matching (vision optional)."""

from __future__ import annotations

import numpy as np
from PIL import Image

_EMBED_SIZE = 64


def l2_normalize(vec: np.ndarray) -> np.ndarray:
    v = np.asarray(vec, dtype=np.float64).reshape(-1)
    n = float(np.linalg.norm(v))
    if n <= 1e-12:
        return v
    return v / n


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    va = l2_normalize(a)
    vb = l2_normalize(b)
    return float(np.clip(np.dot(va, vb), -1.0, 1.0))


def face_crop_embedding(
    img: Image.Image,
    box: tuple[int, int, int, int],
    *,
    pad_ratio: float = 0.12,
) -> np.ndarray | None:
    """Deterministic v1 embedding: resized RGB patch, flattened + L2 norm."""
    x, y, w, h = box
    if w <= 0 or h <= 0:
        return None
    iw, ih = img.size
    pad_x = int(w * pad_ratio)
    pad_y = int(h * pad_ratio)
    x0 = max(0, x - pad_x)
    y0 = max(0, y - pad_y)
    x1 = min(iw, x + w + pad_x)
    y1 = min(ih, y + h + pad_y)
    if x1 <= x0 or y1 <= y0:
        return None
    crop = img.crop((x0, y0, x1, y1)).convert("RGB")
    crop = crop.resize((_EMBED_SIZE, _EMBED_SIZE), Image.Resampling.BILINEAR)
    arr = np.asarray(crop, dtype=np.float64) / 255.0
    return l2_normalize(arr.reshape(-1))


def mean_embedding(vectors: list[np.ndarray]) -> np.ndarray | None:
    if not vectors:
        return None
    stack = np.stack([l2_normalize(v) for v in vectors], axis=0)
    return l2_normalize(stack.mean(axis=0))
