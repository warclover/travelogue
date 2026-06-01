#!/usr/bin/env python3
"""Studio 首页 v2 · 视觉 sign-off 截图采集（P3 · AC-03/08/12/17/18）。

Playwright 按 AC-VERIFICATION 人工项生成 PNG，供设计/QA 归档至
docs/acceptance-records/studio-homepage-v2-visual/。

用法：
    pip install -e ".[dev,playwright]" && playwright install chromium
    python scripts/studio_ac_visual_capture.py
    python scripts/studio_ac_visual_capture.py --out docs/acceptance-records/studio-homepage-v2-visual
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]

# AC ID → (filename, viewport, url_query, wait_selector)
_SCENARIOS: list[tuple[str, str, dict[str, int], str, str]] = [
    (
        "AC-HP2-03",
        "01-demo-same-trip-desktop.png",
        {"width": 1440, "height": 900},
        "dev=1&studioFixture=empty",
        "v2-frame",
    ),
    (
        "AC-HP2-08",
        "02-odd-tail-carousel.png",
        {"width": 1440, "height": 900},
        "dev=1&studioFixture=empty",
        "v2-frame",
    ),
    (
        "AC-HP2-12",
        "03-ipad-landscape-bento.png",
        {"width": 1024, "height": 768},
        "dev=1&studioFixture=empty",
        "v2-frame",
    ),
    (
        "AC-HP2-17",
        "04-importing-cold-static-bg.png",
        {"width": 1440, "height": 900},
        "dev=1&studioState=importing-cold",
        "v2-import-cancel",
    ),
    (
        "AC-HP2-18",
        "05-first-success-shelf-shell.png",
        {"width": 1440, "height": 900},
        "dev=1&studioState=first-success&studioFixture=multi",
        "v2-success-open",
    ),
]

_MANIFEST_PAGES = 5


def _advance_carousel_to_tail(page) -> None:
    """AC-HP2-08 · 连点 next 至末页（与 test_ac_hp2_08 一致）。"""
    page.wait_for_timeout(200)
    nxt = page.locator("#v2-carousel-next")
    for _ in range(_MANIFEST_PAGES + 2):
        if nxt.is_disabled():
            break
        nxt.click()
        page.wait_for_timeout(200)

    last_idx = _MANIFEST_PAGES - 1
    page.wait_for_function(
        """
        (lastIdx) => {
          const dot = document.querySelector('#v2-carousel-dots [aria-current="true"]');
          return dot && Number(dot.dataset.index) === lastIdx;
        }
        """,
        arg=last_idx,
        timeout=20_000,
    )
    page.wait_for_timeout(400)


def _wait_visible(page, el_id: str, timeout: int = 20_000) -> None:
    page.wait_for_function(
        """
        (id) => {
          const el = document.getElementById(id);
          if (!el || el.hidden) return false;
          const cs = getComputedStyle(el);
          return cs.display !== 'none' && cs.visibility !== 'hidden'
            && el.getClientRects().length > 0;
        }
        """,
        arg=el_id,
        timeout=timeout,
    )


def capture_all(*, out_dir: Path, base_url: str | None = None) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit("需要 playwright：pip install -e '.[dev,playwright]'") from exc

    sys.path.insert(0, str(_REPO))
    from tests.test_studio_server import _free_port, _start_studio_server

    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    server = None
    trips_dir = Path(tempfile.mkdtemp(prefix="visual-cap-")) / "trips"
    trips_dir.mkdir(parents=True)

    try:
        if base_url:
            base = base_url.rstrip("/")
        else:
            port = _free_port()
            server = _start_studio_server(trips_dir, port)
            base = f"http://127.0.0.1:{port}"

        with sync_playwright() as p:
            browser = p.chromium.launch()
            for ac_id, filename, viewport, query, wait_id in _SCENARIOS:
                page = browser.new_page(viewport=viewport)
                url = f"{base}/v2?{query}"
                page.goto(url, wait_until="networkidle")
                _wait_visible(page, wait_id)
                if ac_id == "AC-HP2-08":
                    _advance_carousel_to_tail(page)
                page.wait_for_timeout(300)
                path = out_dir / filename
                page.screenshot(path=str(path), full_page=True)
                results.append({"ac": ac_id, "file": str(path), "url": url})
                page.close()
            browser.close()
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()

    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Studio 首页 v2 视觉 sign-off 截图")
    parser.add_argument(
        "--out",
        type=Path,
        default=_REPO / "docs" / "acceptance-records" / "studio-homepage-v2-visual",
        help="PNG 输出目录",
    )
    parser.add_argument(
        "--base",
        default=None,
        help="已运行 Studio 基址（省略则自动 spawn）",
    )
    args = parser.parse_args(argv)

    results = capture_all(out_dir=args.out, base_url=args.base)
    print(f"已采集 {len(results)} 张截图 → {args.out.resolve()}")
    for row in results:
        print(f"  [{row['ac']}] {Path(row['file']).name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
