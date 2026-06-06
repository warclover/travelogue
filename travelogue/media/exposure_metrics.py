"""Exposure / tonal + lighting metrics for the aesthetic layer (PA-T02 / PA-T03).

All functions are pure, deterministic and PIL-only (optional numpy is *not*
required). They operate on a small grayscale thumbnail so they share the same
"single decode" budget as :mod:`travelogue.media.color_metrics`. Every output is
normalised to ``[0, 1]`` so the aesthetic synthesiser can blend them directly.
"""

from __future__ import annotations

from PIL import Image, ImageFilter


def _gray_values(gray: Image.Image) -> list[int]:
    """Pixel buffer for an ``L`` image, preferring the non-deprecated accessor."""
    if hasattr(gray, "get_flattened_data"):
        data = gray.get_flattened_data()
        if data:
            sample = data[0]
            if isinstance(sample, (tuple, list)):
                return [int(px[0]) for px in data]
            return [int(v) for v in data]
    return [int(v) for v in gray.getdata()]


def _luma_thumb(img: Image.Image, px: int) -> list[float]:
    """Return a deterministic ``px*px`` grayscale buffer in ``[0, 1]``."""
    px = max(2, int(px))
    gray = img.convert("L").resize((px, px))
    return [v / 255.0 for v in _gray_values(gray)]


def _percentile(sorted_vals: list[float], q: float) -> float:
    """Nearest-rank percentile (deterministic, no numpy)."""
    if not sorted_vals:
        return 0.0
    if q <= 0:
        return sorted_vals[0]
    if q >= 1:
        return sorted_vals[-1]
    idx = int(round(q * (len(sorted_vals) - 1)))
    return sorted_vals[idx]


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


def histogram_stats(
    img: Image.Image,
    *,
    thumb_px: int = 32,
    mean_luma: float | None = None,
    clip_high: float = 0.95,
    clip_low: float = 0.05,
) -> dict[str, float]:
    """Tonal distribution of *img* (PA-T02).

    Returns ``dynamicRange`` (P95-P5 luma spread), ``clipHighRatio`` /
    ``clipLowRatio`` (blown / crushed pixel fraction) and ``midtoneCenter``
    (``1 - |mean - 0.5|*2`` — how centred the average tone is). When
    *mean_luma* is supplied (e.g. ``quality.meanLuma``) it is reused so the
    midtone score stays consistent with the rest of the pipeline.
    """
    luma = _luma_thumb(img, thumb_px)
    n = len(luma)
    if n == 0:
        return {
            "dynamicRange": 0.0,
            "clipHighRatio": 0.0,
            "clipLowRatio": 0.0,
            "midtoneCenter": 1.0,
        }
    clip_high_ratio = sum(1 for v in luma if v > clip_high) / n
    clip_low_ratio = sum(1 for v in luma if v < clip_low) / n
    ordered = sorted(luma)
    dynamic_range = _percentile(ordered, 0.95) - _percentile(ordered, 0.05)
    mean = sum(luma) / n if mean_luma is None else float(mean_luma)
    midtone_center = 1.0 - abs(mean - 0.5) * 2.0
    return {
        "dynamicRange": round(_clamp01(dynamic_range), 4),
        "clipHighRatio": round(_clamp01(clip_high_ratio), 4),
        "clipLowRatio": round(_clamp01(clip_low_ratio), 4),
        "midtoneCenter": round(_clamp01(midtone_center), 4),
    }


def lighting_stats(
    img: Image.Image,
    *,
    thumb_px: int = 32,
    gradient_norm: float = 0.12,
    contrast_norm: float = 0.30,
) -> dict[str, float]:
    """Directional-light proxy for *img* (PA-T03).

    ``lumaGradient`` is the mean absolute luminance step between neighbouring
    cells (a stand-in for directional light strength); ``contrast`` is the luma
    standard deviation. Both are normalised so flat / even light scores low and
    images with directional light or tonal layering score high.
    """
    px = max(2, int(thumb_px))
    luma = _luma_thumb(img, px)
    n = len(luma)
    if n == 0:
        return {"lumaGradient": 0.0, "contrast": 0.0}

    grid = [luma[r * px : (r + 1) * px] for r in range(px)]
    diffs: list[float] = []
    for r in range(px):
        for c in range(px):
            if c + 1 < px:
                diffs.append(abs(grid[r][c] - grid[r][c + 1]))
            if r + 1 < px:
                diffs.append(abs(grid[r][c] - grid[r + 1][c]))
    raw_gradient = sum(diffs) / len(diffs) if diffs else 0.0

    mean = sum(luma) / n
    variance = sum((v - mean) ** 2 for v in luma) / n
    std = variance ** 0.5

    return {
        "lumaGradient": round(_clamp01(raw_gradient / gradient_norm), 4),
        "contrast": round(_clamp01(std / contrast_norm), 4),
    }


def quadrant_balance(img: Image.Image, *, thumb_px: int = 32) -> float:
    """Left/right + top/bottom luminance symmetry in ``[0, 1]`` (composition).

    A perfectly balanced frame scores ``1.0``; strong one-sided weighting
    scores lower. Used as the ``balance`` term of the composition dimension.
    """
    px = max(2, int(thumb_px))
    luma = _luma_thumb(img, px)
    if not luma:
        return 0.5
    grid = [luma[r * px : (r + 1) * px] for r in range(px)]
    half = px // 2
    left = [grid[r][c] for r in range(px) for c in range(half)]
    right = [grid[r][c] for r in range(px) for c in range(px - half, px)]
    top = [grid[r][c] for r in range(half) for c in range(px)]
    bottom = [grid[r][c] for r in range(px - half, px) for c in range(px)]

    def _mean(vals: list[float]) -> float:
        return sum(vals) / len(vals) if vals else 0.0

    lr = abs(_mean(left) - _mean(right))
    tb = abs(_mean(top) - _mean(bottom))
    return round(_clamp01(1.0 - (lr + tb) / 0.5), 4)


def subject_contrast_score(
    img: Image.Image,
    box: dict | None,
    *,
    thumb_px: int = 64,
) -> float | None:
    """Edge-energy contrast between the subject box and its surroundings.

    Returns ``None`` when *box* is missing/degenerate so the caller can apply a
    confidence discount instead of inventing a value. Higher means the subject
    is markedly sharper than the background (good subject separation).
    """
    if not isinstance(box, dict):
        return None
    try:
        bx = float(box.get("x", 0.0))
        by = float(box.get("y", 0.0))
        bw = float(box.get("w", 0.0))
        bh = float(box.get("h", 0.0))
    except (TypeError, ValueError):
        return None
    if bw <= 0.02 or bh <= 0.02:
        return None

    px = max(8, int(thumb_px))
    gray = img.convert("L").resize((px, px))
    edges = gray.filter(ImageFilter.FIND_EDGES)
    data = _gray_values(edges)

    x0 = max(0, min(px - 1, int(round(bx * px))))
    y0 = max(0, min(px - 1, int(round(by * px))))
    x1 = max(x0 + 1, min(px, int(round((bx + bw) * px))))
    y1 = max(y0 + 1, min(px, int(round((by + bh) * px))))

    inside: list[int] = []
    outside: list[int] = []
    for r in range(px):
        row = data[r * px : (r + 1) * px]
        in_y = y0 <= r < y1
        for c in range(px):
            if in_y and x0 <= c < x1:
                inside.append(row[c])
            else:
                outside.append(row[c])
    if not inside or not outside:
        return None

    def _energy(vals: list[int]) -> float:
        m = sum(vals) / len(vals)
        return sum((v - m) ** 2 for v in vals) / len(vals)

    e_in = _energy(inside)
    e_out = _energy(outside)
    denom = e_in + e_out
    if denom <= 0:
        return 0.5
    return round(_clamp01(e_in / denom), 4)
