"""Studio static assets and home page."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from urllib.parse import unquote

from travelogue.paths import STUDIO_TEMPLATE_DIR
from travelogue.web.studio_handlers.paths import STUDIO_ASSET_PREFIX


def _serve_studio_home(handler: StudioHandlerProtocol, template_name: str) -> None:
    from travelogue.web import studio_homepage_gate as gate

    bucket, is_new = gate.read_or_assign_bucket(handler)
    html_path = STUDIO_TEMPLATE_DIR / template_name
    html = html_path.read_text(encoding="utf-8")
    html = gate.inject_home_placeholders(html, handler, bucket)
    data = html.encode("utf-8")
    handler.send_response(200)
    if is_new:
        gate.set_bucket_cookie(handler, bucket)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def send_redirect(handler: StudioHandlerProtocol, location: str, code: int = 302) -> None:
    handler.send_response(code)
    handler.send_header("Location", location)
    handler.end_headers()


def handle_home(handler: StudioHandlerProtocol) -> None:
    """Serve v3 (image-first) homepage — frozen, GET /classic."""
    _serve_studio_home(handler, "studio.html")


def handle_home_v2(handler: StudioHandlerProtocol) -> None:
    """Serve v2 (output-first Bento) homepage — GET /v2 (parallel dev route)."""
    _serve_studio_home(handler, "studio-home-v2.html")


def handle_studio_asset(handler: StudioHandlerProtocol, path: str) -> bool:
    rel = unquote(path[len(STUDIO_ASSET_PREFIX) :].lstrip("/"))
    asset = (STUDIO_TEMPLATE_DIR / rel).resolve()
    try:
        asset.relative_to(STUDIO_TEMPLATE_DIR.resolve())
    except ValueError:
        handler.send_error(404)
        return True
    if not asset.is_file():
        handler.send_error(404)
        return True
    ctype = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
    data = asset.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)
    return True
