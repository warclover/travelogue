"""Export trip HTML to PDF via Playwright (PRD-EXPERIENCE P5)."""

from __future__ import annotations

import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from travelogue.errors import PlainCodeError


class PdfExportError(PlainCodeError):
    def __init__(self, message: str, *, code: str = "E_PDF_EXPORT") -> None:
        super().__init__(message, code=code)


def _start_static_server(directory: Path, host: str, port: int) -> ThreadingHTTPServer:
    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(  # noqa: E731
        *args, directory=str(directory), **kwargs
    )
    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def export_trip_pdf(
    trip_dir: Path,
    *,
    index: str = "index.html",
    output: Path | None = None,
    host: str = "127.0.0.1",
    port: int = 0,
    width_px: int = 1200,
    timeout_ms: int = 120_000,
) -> Path:
    """
    Render index.html to a single-page PDF (full scroll height).
    Requires playwright + chromium: pip install 'travelogue[playwright]' && playwright install chromium
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise PdfExportError(
            "playwright not installed — run: pip install 'travelogue[playwright]' "
            "&& playwright install chromium"
        ) from exc

    trip_dir = trip_dir.resolve()
    index_path = trip_dir / index
    if not index_path.is_file():
        raise PdfExportError(f"{index} not found in {trip_dir}")

    title = "travelogue"
    trip_json = trip_dir / "trip.json"
    if trip_json.is_file():
        import json

        meta = (json.loads(trip_json.read_text(encoding="utf-8")).get("meta") or {})
        title = str(meta.get("title") or title).strip() or title

    from travelogue.export.longshot import EXPORT_OUTPUT_DIRNAME

    out_path = output or trip_dir / EXPORT_OUTPUT_DIRNAME / f"{title}-print.pdf"
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    server = _start_static_server(trip_dir, host, port or 0)
    bound_port = server.server_address[1]
    url = f"http://{host}:{bound_port}/{index}"

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width_px, "height": 900})
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            page.wait_for_load_state("domcontentloaded")
            height = page.evaluate(
                "() => Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)"
            )
            height = max(int(height), 900)
            page.pdf(
                path=str(out_path),
                print_background=True,
                width=f"{width_px}px",
                height=f"{height}px",
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    if not out_path.is_file() or out_path.stat().st_size == 0:
        raise PdfExportError(f"PDF export failed: {out_path}")
    return out_path
