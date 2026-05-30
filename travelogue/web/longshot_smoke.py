"""Playwright smoke test for index-longshot.html capture readiness."""

from __future__ import annotations

import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from travelogue.render.engine import LONGSHOT_INDEX_NAME


class LongshotSmokeError(Exception):
    def __init__(self, message: str, *, code: str = "E_LONGSHOT_SMOKE") -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def _start_static_server(directory: Path, host: str, port: int) -> ThreadingHTTPServer:
    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(  # noqa: E731
        *args, directory=str(directory), **kwargs
    )
    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _ignorable_console_error(text: str) -> bool:
    t = text.lower()
    if "favicon" in t:
        return True
    if "416" in t or "range not satisfiable" in t:
        return True
    return False


def run_longshot_smoke(
    trip_dir: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 0,
    index: str = LONGSHOT_INDEX_NAME,
    capture_first_chapter: bool = True,
    timeout_ms: int = 180_000,
) -> dict:
    """
    Load longshot HTML over http://, verify DOM + TravelogueLongshot API.
    Optionally capture chapter 1 at 1× and assert non-empty PNG.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise LongshotSmokeError(
            "playwright not installed — run: pip install 'travelogue[playwright]' "
            "&& playwright install chromium"
        ) from exc

    trip_dir = trip_dir.resolve()
    index_path = trip_dir / index
    if not index_path.is_file():
        raise LongshotSmokeError(f"{index} not found in {trip_dir}")

    server = _start_static_server(trip_dir, host, port or 0)
    bound_port = server.server_address[1]
    base = f"http://{host}:{bound_port}"
    url = f"{base}/{index}"
    console_errors: list[str] = []
    result: dict = {"url": url, "console_errors": console_errors}

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 428, "height": 844})
            page.on(
                "console",
                lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
            )
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            page.wait_for_function(
                "() => window.TravelogueLongshot && document.documentElement.dataset.longshot === 'on'",
                timeout=30_000,
            )

            chapter_count = page.locator("[data-chapter-id]").count()
            card_count = page.locator('[data-block="media-card"]').count()
            result["chapter_count"] = chapter_count
            result["media_card_count"] = card_count

            if chapter_count < 1:
                raise LongshotSmokeError("no [data-chapter-id] sections found")
            if card_count < 1:
                raise LongshotSmokeError("no media-card blocks found")

            dims = page.evaluate("() => window.TravelogueLongshot.captureDimensions()")
            result["capture_dimensions"] = dims

            if capture_first_chapter and card_count <= 25:
                blob_size = page.evaluate(
                    """async () => {
                      const main = document.querySelector('main');
                      const chapters = Array.from(main.querySelectorAll('section.chapter'));
                      const cover = main.querySelector('.cover-hero');
                      const pageEl = main.querySelector('.page');
                      const hook = pageEl && pageEl.querySelector('.hook-line');
                      const epilogue = pageEl && pageEl.querySelector('.epilogue');
                      const tripMeta = pageEl && pageEl.querySelector('.trip-meta');
                      function stash(el, show) {
                        if (!el) return;
                        el.hidden = !show;
                        el.style.display = show ? '' : 'none';
                      }
                      chapters.forEach((ch, i) => stash(ch, i === 0));
                      stash(cover, true);
                      stash(hook, true);
                      stash(tripMeta, true);
                      stash(epilogue, false);
                      const out = await window.TravelogueLongshot.captureMainToBlob({
                        scale: 1,
                        format: 'png',
                        quietProgress: true,
                      });
                      return out.blob.size;
                    }"""
                )
                result["first_chapter_blob_bytes"] = blob_size
                if not blob_size or blob_size < 1024:
                    raise LongshotSmokeError(f"capture blob too small: {blob_size} bytes")
            elif capture_first_chapter:
                result["first_chapter_blob_bytes"] = None
                result["capture_skipped"] = "too many images for smoke capture"

            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    hard_errors = [e for e in console_errors if not _ignorable_console_error(e)]
    if hard_errors:
        raise LongshotSmokeError("browser console errors: " + "; ".join(hard_errors[:3]))

    return result
