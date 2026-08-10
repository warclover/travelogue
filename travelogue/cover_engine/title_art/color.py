"""Automatic color contrast (PRD §6.1 · D-CAL-13/17). Shared by Route B and Route C.

用户口径（2026-08-07）：需要有足够对比度，默认白色兜底。
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image

WHITE: tuple[int, int, int] = (255, 255, 255)
DARK: tuple[int, int, int] = (26, 26, 26)  # #1a1a1a
DEFAULT_SEAL: tuple[int, int, int] = (176, 58, 46)  # #B03A2E

#: WCAG 风格对比度比值。Kickoff 时先写入占位值（SHD-CAL-02），W2 用 14 条
#: 真实 trip 封面照片测试集实测 4 款白名单风格候选矩形，观测 ratio 区间
#: 4.27~19.80（band-cut/veil-footer 走真实照片 ROI 采样；contact-stamp/
#: folio-overlap 因 assume_dark_veil/assume_paper_bg 走固定背景估计，见
#: whitelist.py），均有充足冗余（AC-CAL-04 钉定，见验收记录
#: cover-calligraphy-title-v1-ac04-05-06-13-2026-08-08.md）——3.0 予以确认
#: 定稿，不再是占位值。
MIN_CONTRAST_RATIO = 3.0


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    def chan(c: int) -> float:
        v = c / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def contrast_ratio(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    l1 = _relative_luminance(fg) + 0.05
    l2 = _relative_luminance(bg) + 0.05
    return max(l1, l2) / min(l1, l2)


def roi_average_color(img: Image.Image, box: tuple[int, int, int, int]) -> tuple[int, int, int]:
    """box = (x, y, w, h) 像素坐标；越界裁剪；空框回落中性灰。"""
    x, y, w, h = box
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(img.width, x + w), min(img.height, y + h)
    if x1 <= x0 or y1 <= y0:
        return (128, 128, 128)
    crop = img.convert("RGB").crop((x0, y0, x1, y1))
    small = crop.resize((1, 1), Image.Resampling.BOX)
    px = small.getpixel((0, 0))
    return (int(px[0]), int(px[1]), int(px[2]))


@dataclass(frozen=True)
class ContrastPick:
    color_hex: str
    color_rgb: tuple[int, int, int]
    ratio: float
    ok: bool  # 达标（≥ MIN_CONTRAST_RATIO）


def pick_readable_color(bg_rgb: tuple[int, int, int]) -> ContrastPick:
    """白/深二选一 + 达标判定；仍不达标时默认回落白色（用户口径 (3)）。"""
    white_ratio = contrast_ratio(WHITE, bg_rgb)
    dark_ratio = contrast_ratio(DARK, bg_rgb)
    if white_ratio >= dark_ratio:
        best_rgb, best_ratio = WHITE, white_ratio
    else:
        best_rgb, best_ratio = DARK, dark_ratio
    ok = best_ratio >= MIN_CONTRAST_RATIO
    if not ok:
        best_rgb, best_ratio = WHITE, white_ratio
        ok = white_ratio >= MIN_CONTRAST_RATIO
    hex_ = "#{:02x}{:02x}{:02x}".format(*best_rgb)
    return ContrastPick(color_hex=hex_, color_rgb=best_rgb, ratio=round(best_ratio, 3), ok=ok)


def recolor_ink_on_white(
    img: Image.Image,
    target_rgb: tuple[int, int, int],
    *,
    threshold: int = 235,
) -> Image.Image:
    """路线 C 后处理（D-CAL-17）：白底黑字稿 → 透明背景 + 指定墨色。

    亮度 ≥ threshold 视为纸面背景（透明）；越暗则 alpha 越高，保留笔锋的
    浓淡/飞白层次，只替换色值本身，不破坏笔触纹理。
    """
    gray = img.convert("L")

    def _alpha_lut(lum: int) -> int:
        if lum >= threshold:
            return 0
        return min(255, int(round(255 * (threshold - lum) / threshold)))

    alpha = gray.point(_alpha_lut)
    solid = Image.new("RGB", gray.size, target_rgb)
    r, g, b = solid.split()
    return Image.merge("RGBA", (r, g, b, alpha))


def image_to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
