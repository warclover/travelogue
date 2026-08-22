"""Pick Sri Lanka trip photos + composed screens for the marketing hi-fi."""
from __future__ import annotations

import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
TRIP = ROOT / "trips" / "demo-e52494839a"
OUT = Path(__file__).resolve().parent
BASE = "http://127.0.0.1:8766/demo-e52494839a"

PHOTOS = {
    "lanka-hero.webp": TRIP / "assets" / "asset-095-w2400.webp",
    "lanka-church.webp": TRIP / "assets" / "asset-006-w1600.webp",
    "lanka-coast.webp": TRIP / "assets" / "asset-088-w1600.webp",
    "lanka-cove.webp": TRIP / "assets" / "asset-094-w1600.webp",
    "lanka-lamps.webp": TRIP / "assets" / "asset-054-w1600.webp",
    "lanka-sunset.webp": TRIP / "assets" / "asset-102-w1600.webp",
    "lanka-dusk.webp": TRIP / "assets" / "asset-104-w1600.webp",
    "lanka-longshot.jpg": TRIP / "preview.jpg",
}

HIDE_CHROME = """
.preview-toolbar, .screenplay-toolbar, .preview-drawer-root,
.preview-task-dock, .preview-sheet-root, #preview-toolbar-toast,
.chapter-header, #preview-help-longshot-tip, .preview-help-longshot-tip,
#preview-toolbar-cover-footnote, .preview-toolbar__cover-footnote {
  display: none !important;
}
"""

SCREENS = [
    ("lanka-plate.png", "1"),
    ("lanka-grid-4.png", "2"),
    ("lanka-landscape.png", "3"),
    ("lanka-portrait-3.png", "16"),
    ("lanka-grid-6.png", "39"),
    ("lanka-1p2l.png", "72"),
]


def copy_photos() -> None:
    for dest, src in PHOTOS.items():
        if not src.exists():
            raise SystemExit(f"missing {src}")
        target = OUT / dest
        shutil.copy2(src, target)
        print(f"copy {src.name} -> {dest} ({target.stat().st_size})")


def capture_screens() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
        )
        page.goto(f"{BASE}/index.html", wait_until="networkidle")
        page.add_style_tag(content=HIDE_CHROME)
        page.evaluate(
            """() => {
              document.querySelectorAll(
                '#preview-help-longshot-tip, .preview-help-longshot-tip, #preview-toolbar-cover-footnote'
              ).forEach((el) => el.remove());
            }"""
        )
        page.wait_for_timeout(600)

        cover = page.locator(".cover-opening").first
        cover.screenshot(path=str(OUT / "lanka-cover.png"), animations="disabled")
        print("shot lanka-cover.png")

        for name, index in SCREENS:
            el = page.locator(f'.layout-screen[data-screen-index="{index}"]').first
            el.scroll_into_view_if_needed()
            page.wait_for_timeout(250)
            el.screenshot(path=str(OUT / name), animations="disabled")
            print(f"shot {name} screen {index}")

        browser.close()


if __name__ == "__main__":
    copy_photos()
    capture_screens()
