"""Studio static assets and home page."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from travelogue.paths import STUDIO_TEMPLATE_DIR
from travelogue.web.studio_handlers.paths import STUDIO_ASSET_PREFIX


def handle_home(handler: Any) -> None:
    html_path = STUDIO_TEMPLATE_DIR / "studio.html"
    html = html_path.read_text(encoding="utf-8")
    token = handler.studio_token or ""
    html = html.replace("__STUDIO_TOKEN__", token)
    data = html.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def handle_studio_asset(handler: Any, path: str) -> bool:
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
