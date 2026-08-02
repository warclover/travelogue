"""Screenshot ALG-V3 blind dogfood arm HTML via Playwright."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path("docs/acceptance-records/attachments/alg3-blind-2026-08-02")
TRIP = Path("trips/demo-3ee2727aea")
BASE = "http://127.0.0.1:8766/demo-3ee2727aea/index.html"


def shot(arm: str, out_name: str) -> None:
    src = ROOT / f"{arm}-index.html"
    shutil.copy2(src, TRIP / "index.html")
    out = ROOT / out_name
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 1600})
        page.goto(BASE, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(800)
        # First viewport (opening + early screens — where Off/On differ most)
        page.screenshot(path=str(out), full_page=False)
        # Tall strip for scroll context
        page.screenshot(path=str(ROOT / out_name.replace(".png", "-full.png")), full_page=True)
        browser.close()
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    pairs = [
        ("w1b-off", "w1b-pair1-off.png"),
        ("w1b-on", "w1b-pair1-on.png"),
        ("a4-off", "a4-pair1-off.png"),
        ("a4-on", "a4-pair1-on.png"),
    ]
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    for arm, name in pairs:
        if only and arm not in only:
            continue
        shot(arm, name)
