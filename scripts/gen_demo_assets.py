#!/usr/bin/env python3
"""Generate demo WebP placeholders for visual-journal golden sample."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "templates" / "visual-journal" / "assets" / "demo"

# name -> (width, height, (color_top, color_bottom))
SPECS: dict[str, tuple[int, int, tuple[tuple[int, int, int], tuple[int, int, int]]]] = {
    "cover": (1200, 2133, ((42, 58, 72), (154, 171, 184))),
    "station": (1600, 1200, ((61, 74, 92), (136, 153, 170))),
    "umbrella": (1600, 1200, ((201, 191, 179), (138, 127, 114))),
    "video-poster": (1600, 900, ((15, 15, 26), (61, 74, 92))),
    "lantern": (1600, 1200, ((26, 16, 8), (201, 161, 39))),
    "scroll-bamboo": (1200, 1600, ((30, 61, 20), (74, 124, 35))),
    "scroll-platform": (1200, 1600, ((61, 74, 92), (154, 171, 184))),
    "scroll-ice": (1200, 1600, ((245, 239, 227), (201, 149, 108))),
    "night-river": (1600, 900, ((6, 10, 18), (74, 106, 138))),
    "night-return": (1600, 1200, ((20, 28, 40), (61, 74, 92))),
    "row-umbrella": (1200, 1600, ((201, 191, 179), (138, 127, 114))),
    "row-shoes": (1200, 1600, ((184, 176, 166), (107, 101, 96))),
    "fallback": (1600, 1200, ((40, 40, 40), (90, 90, 90))),
}


def gradient_image(w: int, h: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (w, y)], fill=color)
    return img


def save_webp(img: Image.Image, path: Path, quality: int = 82) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "WEBP", quality=quality, method=6)


def main() -> None:
    for name, (w, h, colors) in SPECS.items():
        base = gradient_image(w, h, colors[0], colors[1])
        save_webp(base, OUT / f"{name}-w1600.webp")
        small = base.resize((800, int(h * 800 / w)), Image.Resampling.LANCZOS)
        save_webp(small, OUT / f"{name}-w800.webp")
        print("wrote", name)
    print("OK ->", OUT)


if __name__ == "__main__":
    main()
