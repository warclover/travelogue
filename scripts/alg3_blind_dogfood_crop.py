"""Crop / scroll screenshots for ALG-V3 blind pairs where first viewport is cover-identical."""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path("docs/acceptance-records/attachments/alg3-blind-2026-08-02")
TRIP = Path("trips/demo-3ee2727aea")
BASE = "http://127.0.0.1:8766/demo-3ee2727aea/index.html"


def shot_scrolled(arm: str, out_name: str, *, scroll_y: int = 1400) -> None:
    src = ROOT / f"{arm}-index.html"
    shutil.copy2(src, TRIP / "index.html")
    out = ROOT / out_name
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 1800})
        page.goto(BASE, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(600)
        page.evaluate(f"window.scrollTo(0, {scroll_y})")
        page.wait_for_timeout(500)
        page.screenshot(path=str(out), full_page=False)
        browser.close()
    print(f"wrote {out}")


def crop_full(arm: str, out_name: str, *, y0: int = 1200, height: int = 2400) -> None:
    full = ROOT / f"{arm}-pair1-{'off' if arm.endswith('off') else 'on'}-full.png"
    # naming: w1b-off -> w1b-pair1-off-full.png
    prefix = arm.rsplit("-", 1)[0]
    side = arm.rsplit("-", 1)[1]
    full = ROOT / f"{prefix}-pair1-{side}-full.png"
    im = Image.open(full).convert("RGB")
    y1 = min(im.height, y0 + height)
    crop = im.crop((0, y0, im.width, y1))
    out = ROOT / out_name
    crop.save(out)
    print(f"wrote {out} from {full.name} y={y0}:{y1}")


def side_by_side(left: Path, right: Path, out: Path, labels: tuple[str, str]) -> None:
    a = Image.open(left).convert("RGB")
    b = Image.open(right).convert("RGB")
    h = max(a.height, b.height)
    gap = 24
    canvas = Image.new("RGB", (a.width + b.width + gap, h), (245, 245, 245))
    canvas.paste(a, (0, 0))
    canvas.paste(b, (a.width + gap, 0))
    canvas.save(out)
    print(f"wrote {out} ({labels[0]} | {labels[1]})")


if __name__ == "__main__":
    for arm in ("w1b-off", "w1b-on", "a4-off", "a4-on"):
        shot_scrolled(arm, f"{arm}-body.png", scroll_y=1500)
        crop_full(arm, f"{arm}-crop.png", y0=1100, height=2800)

    side_by_side(
        ROOT / "w1b-off-body.png",
        ROOT / "w1b-on-body.png",
        ROOT / "w1b-pair1-compare.png",
        ("W1b Off", "W1b On"),
    )
    side_by_side(
        ROOT / "a4-off-body.png",
        ROOT / "a4-on-body.png",
        ROOT / "a4-pair1-compare.png",
        ("A4 Off", "A4 On"),
    )
