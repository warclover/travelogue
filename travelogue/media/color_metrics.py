"""Color metrics for layout spread scoring (Phase 3b)."""

from __future__ import annotations

import math

from PIL import Image


def _iter_rgb_pixels(img: Image.Image):
    rgb = img.convert("RGB")
    if hasattr(rgb, "get_flattened_data"):
        data = rgb.get_flattened_data()
        if data:
            sample = data[0]
            if isinstance(sample, tuple) and len(sample) >= 3:
                for px in data:
                    yield px[0], px[1], px[2]
                return
            for i in range(0, len(data) - 2, 3):
                yield data[i], data[i + 1], data[i + 2]
            return
    yield from rgb.getdata()


def mean_luma(img: Image.Image) -> float:
    """Relative luminance in [0, 1] (sRGB)."""
    thumb = img.convert("RGB").resize((32, 32))
    pixels = list(_iter_rgb_pixels(thumb))
    if not pixels:
        return 0.5
    total = sum(0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in pixels)
    return min(1.0, max(0.0, total / len(pixels) / 255.0))


def dominant_tone_hex(img: Image.Image) -> str:
    """Average RGB of a small thumbnail as #rrggbb."""
    thumb = img.convert("RGB").resize((16, 16))
    pixels = list(_iter_rgb_pixels(thumb))
    n = max(len(pixels), 1)
    rs = gs = bs = 0
    for r, g, b in pixels:
        rs += r
        gs += g
        bs += b
    return f"#{rs // n:02x}{gs // n:02x}{bs // n:02x}"


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.strip().lstrip("#")
    if len(h) != 6:
        return 0.5, 0.5, 0.5
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return r, g, b


def _rgb_to_lab(r: float, g: float, b: float) -> tuple[float, float, float]:
    """sRGB → CIE Lab (D65)."""
    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    rl, gl, bl = lin(r), lin(g), lin(b)
    x = rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375
    y = rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750
    z = rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else (7.787 * t + 16 / 116)

    xn, yn, zn = 0.95047, 1.0, 1.08883
    fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b_val = 200 * (fy - fz)
    return L, a, b_val


def delta_e_cie76(hex_a: str, hex_b: str) -> float:
    la = _rgb_to_lab(*_hex_to_rgb(hex_a))
    lb = _rgb_to_lab(*_hex_to_rgb(hex_b))
    return math.sqrt((la[0] - lb[0]) ** 2 + (la[1] - lb[1]) ** 2 + (la[2] - lb[2]) ** 2)


def triangular_score(value: float, *, low: float, peak: float, high: float) -> float:
    """PRD tone window: peak at `peak`, zero outside [low, high]."""
    if value <= low or value >= high:
        return 0.0
    if value <= peak:
        return (value - low) / (peak - low)
    return (high - value) / (high - peak)


def dominant_tone_chroma_score(hex_color: str | None) -> float:
    """0–1 preference for cover saturation (P5-C2)."""
    if not hex_color or not str(hex_color).strip().startswith("#"):
        return 0.5
    L, a, b = _rgb_to_lab(*_hex_to_rgb(str(hex_color)))
    chroma = math.sqrt(a * a + b * b)
    return triangular_score(chroma, low=8, peak=35, high=85)


def color_richness_multiplier(
    *,
    hex_color: str | None,
    mean_luma: float | None = None,
) -> float:
    """P6-C2 · penalize flat gray/dark covers while rewarding chroma."""
    chroma = dominant_tone_chroma_score(hex_color)
    luma = 0.5 if mean_luma is None else float(mean_luma)
    luma_factor = triangular_score(luma, low=0.18, peak=0.55, high=0.9)
    dull_penalty = 0.84 + 0.16 * chroma if luma < 0.32 else 1.0
    return (0.86 + 0.22 * chroma) * (0.88 + 0.12 * luma_factor) * dull_penalty
