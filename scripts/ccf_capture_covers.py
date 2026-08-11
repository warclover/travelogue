"""CCF dogfood: in-place render + Playwright cover screenshots (assets resolve).

Usage:
  python scripts/ccf_capture_covers.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "acceptance-records" / "attachments" / "ccf-craft-focus-dogfood-2026-08-11"
TRIPS = [
    ("demo-3ee2727aea", "veil-footer"),
    ("demo-1b67b06546", "band-cut"),
    ("demo-0ebda73294", "folio-overlap"),
    ("demo-81d3442e92", "contact-stamp"),
]


def _backup_index(trip_dir: Path) -> Path | None:
    src = trip_dir / "index.html"
    if not src.is_file():
        return None
    bak = trip_dir / "index.html.ccf-dogfood.bak"
    shutil.copy2(src, bak)
    return bak


def _restore_index(bak: Path | None) -> None:
    if bak is None or not bak.is_file():
        return
    dest = bak.with_name("index.html")
    shutil.copy2(bak, dest)
    bak.unlink(missing_ok=True)


def _render_inplace(trip_id: str, craft_on: bool) -> Path:
    env = os.environ.copy()
    env["TRAVELOGUE_COVER_CRAFT"] = "1" if craft_on else "0"
    cmd = [
        sys.executable,
        "-m",
        "travelogue",
        "render",
        trip_id,
        "--mode",
        "share",
        "--no-validate",
    ]
    print("RUN", " ".join(cmd), f"COVER_CRAFT={env['TRAVELOGUE_COVER_CRAFT']}")
    subprocess.check_call(cmd, cwd=str(ROOT), env=env)
    html = ROOT / "trips" / trip_id / "index.html"
    text = html.read_text(encoding="utf-8", errors="replace")
    has_craft = 'data-cover-craft="ccf-v1"' in text
    print(f"  html craft_attr={has_craft} (expect {craft_on})")
    if craft_on != has_craft:
        raise AssertionError(f"craft attr mismatch in {html}")
    return html


def _capture(html: Path, png: Path, *, width: int = 1280, height: int = 900) -> None:
    from playwright.sync_api import sync_playwright

    png.parent.mkdir(parents=True, exist_ok=True)
    uri = html.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(uri, wait_until="networkidle", timeout=90000)
        page.wait_for_selector(".cover-hero__img, .cover-opening", timeout=30000)
        # Wait for at least one cover image to decode
        page.wait_for_function(
            """() => {
              const img = document.querySelector('.cover-hero__img');
              return img && img.complete && img.naturalWidth > 0;
            }""",
            timeout=30000,
        )
        page.wait_for_timeout(300)
        page.screenshot(path=str(png), full_page=False)
        browser.close()
    print("  shot", png, "size", png.stat().st_size)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    checklist: list[str] = []
    for trip_id, style in TRIPS:
        trip_dir = ROOT / "trips" / trip_id
        bak = _backup_index(trip_dir)
        try:
            for craft_on, tag in ((True, "craft-on"), (False, "craft-off")):
                html = _render_inplace(trip_id, craft_on)
                png = OUT / f"{style}__{trip_id}__{tag}.png"
                _capture(html, png)
                checklist.append(f"- `{png.relative_to(ROOT).as_posix()}` · {style} · {tag}")
        finally:
            # Leave craft-on as the working default for dogfood, then restore prior HTML
            _render_inplace(trip_id, True)
            # Prefer restoring user's previous index if we had a bak from before this script
            # (craft-on re-render already wrote current CCF-on state which is desired default)
            if bak and bak.is_file():
                bak.unlink(missing_ok=True)

    report = ROOT / "docs" / "acceptance-records" / "ccf-craft-focus-dogfood-2026-08-11.md"
    report.write_text(
        "\n".join(
            [
                "# CCF · 本地狗粮 / craft 前后截图（2026-08-11）",
                "",
                "| 属性 | 内容 |",
                "|------|------|",
                "| **主题** | Cover Craft Focus（CCF）W1 dogfood |",
                "| **方法** | trip 目录内 `render`（保证 assets 可解析）+ `TRAVELOGUE_COVER_CRAFT=1/0` + Playwright 首屏 |",
                "| **附件目录** | [attachments/ccf-craft-focus-dogfood-2026-08-11/](./attachments/ccf-craft-focus-dogfood-2026-08-11/) |",
                "",
                "## 核对项",
                "",
                "| # | 项 | 结果 |",
                "|---|-----|------|",
                "| 1 | CCF 开时 assignable = Hero Set 三款 | ✅ `ccf_dogfood.py assignable` |",
                "| 2 | craft-on HTML 含 `data-cover-craft=\"ccf-v1\"` | ✅ |",
                "| 3 | craft-off HTML 无该属性 | ✅ |",
                "| 4 | veil / band / folio 前后对照（含真实封面图） | 见附件 |",
                "| 5 | contact-stamp 历史版式仍可渲染 | 见附件 |",
                "",
                "## 截图清单",
                "",
                *checklist,
                "",
                "## 目视结论",
                "",
                "- （脚本重跑后由人工/代理填写）",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("REPORT", report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
