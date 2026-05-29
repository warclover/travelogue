"""Generate P5-H2 sample longshot thumb crops from sample-longshot.jpg."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "templates" / "studio" / "assets" / "sample-longshot.jpg"
OUT = ROOT / "templates" / "studio" / "assets" / "sample-longshots"

KEYS = ("kyoto", "iceland", "linzhi")
# Vertical slices (fraction of height) for visual variety on empty-state cards.
SLICES = (0.0, 0.28, 0.56)


def main() -> int:
    if not SRC.is_file():
        print(f"missing source: {SRC}", flush=True)
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    im = Image.open(SRC).convert("RGB")
    width, height = im.size
    thumb_h = min(int(width * 4.4 / 3), height)
    for key, start_frac in zip(KEYS, SLICES, strict=True):
        y0 = int(height * start_frac)
        y1 = min(y0 + thumb_h, height)
        if y1 - y0 < thumb_h // 2:
            y0 = max(0, height - thumb_h)
            y1 = height
        crop = im.crop((0, y0, width, y1))
        target_w = 420
        target_h = max(1, int(target_w * crop.height / crop.width))
        crop = crop.resize((target_w, target_h), Image.Resampling.LANCZOS)
        dest = OUT / f"{key}-thumb.jpg"
        crop.save(dest, quality=88, optimize=True)
        print(f"wrote {dest.relative_to(ROOT)} ({target_w}x{target_h})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
