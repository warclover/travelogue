"""Compose a vertical longshot roll from the trip's own photos."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TRIP = Path(r"c:\Users\xiafe\Projects\travelogue\trips\demo-e52494839a\assets")
OUT = Path(__file__).resolve().parent / "lanka-longshot.png"
WIDTH = 780
ASSETS = [
    "asset-006-w1600.webp",
    "asset-001-w1600.webp",
    "asset-002-w1600.webp",
    "asset-003-w1600.webp",
]


def _title_bar(width: int) -> Image.Image:
    bar = Image.new("RGB", (width, 188), (8, 8, 8))
    draw = ImageDraw.Draw(bar)
    try:
        font_sm = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 22)
        font_lg = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 40)
    except OSError:
        font_sm = font_lg = ImageFont.load_default()
    draw.text((36, 44), "2018.07.22 – 08.18 · 28 天", fill=(140, 136, 128), font=font_sm)
    draw.text((36, 88), "斯里兰卡风光精选", fill=(236, 232, 224), font=font_lg)
    return bar


def _fit_width(path: Path, width: int) -> Image.Image:
    im = Image.open(path).convert("RGB")
    h = max(1, round(im.size[1] * width / im.size[0]))
    return im.resize((width, h), Image.Resampling.LANCZOS)


def main() -> None:
    slices = [_title_bar(WIDTH)]
    for name in ASSETS:
        src = TRIP / name
        if not src.exists():
            raise SystemExit(f"missing {src}")
        slices.append(_fit_width(src, WIDTH))
        print(name, slices[-1].size)

    gap = 6
    height = sum(im.size[1] for im in slices) + gap * (len(slices) - 1)
    roll = Image.new("RGB", (WIDTH, height), (8, 8, 8))
    y = 0
    for i, im in enumerate(slices):
        roll.paste(im, (0, y))
        y += im.size[1] + (gap if i < len(slices) - 1 else 0)
    roll.save(OUT, optimize=True)
    print(f"wrote {OUT.name} {roll.size} ar={WIDTH / height:.3f}")


if __name__ == "__main__":
    main()
