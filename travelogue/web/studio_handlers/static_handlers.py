"""Studio static assets and home page."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Literal
from urllib.parse import unquote

from travelogue.paths import STUDIO_TEMPLATE_DIR
from travelogue.render.bundle_serve import parse_bundle_request, resolve_bundle_file
from travelogue.web.studio_handlers.paths import HOME_V2_PATH, STUDIO_ASSET_PREFIX
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol


def _request_header(handler: StudioHandlerProtocol, key: str) -> str | None:
    req = getattr(handler, "request_headers", None)
    if isinstance(req, dict):
        return req.get(key)
    return handler.headers.get(key)


def _serve_studio_home_html(
    handler: StudioHandlerProtocol,
    template_name: str,
    *,
    bucket: int,
    is_new: bool,
) -> None:
    from travelogue.web import studio_homepage_gate as gate

    html_path = STUDIO_TEMPLATE_DIR / template_name
    html = html_path.read_text(encoding="utf-8")
    html = gate.inject_home_placeholders(html, handler, bucket)
    data = html.encode("utf-8")
    handler.send_response(200)
    if is_new:
        gate.set_bucket_cookie(handler, bucket)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Cache-Control", "no-cache")
    handler.end_headers()
    handler.wfile.write(data)


def _serve_studio_home(handler: StudioHandlerProtocol, template_name: str) -> None:
    from travelogue.web import studio_homepage_gate as gate

    bucket, is_new = gate.read_or_assign_bucket(handler)
    _serve_studio_home_html(handler, template_name, bucket=bucket, is_new=is_new)


def send_redirect(handler: StudioHandlerProtocol, location: str, code: int = 302) -> None:
    handler.send_response(code)
    handler.send_header("Location", location)
    handler.end_headers()


def handle_home_root(handler: StudioHandlerProtocol) -> bool:
    """GET / · homepage v2 门控（FEATURE-FLAG §3 / M20-j）。返回 True 若已处理。"""
    from travelogue.web import studio_homepage_gate as gate

    mode = gate.resolve_mode()
    config = gate.load_config_dict(handler)
    percent = gate.resolve_percent(config)
    query = gate.parse_request_query(handler.path)
    bucket, is_new = gate.read_or_assign_bucket(handler)
    allow_override = gate.allow_variant_override(handler.studio_host)
    variant: Literal["v2", "v3"] = gate.decide_root_variant(
        mode=mode,
        percent=percent,
        bucket=bucket,
        query=query,
        allow_override=allow_override,
    )

    if gate.should_redirect_root_to_v2(mode=mode, variant=variant):
        handler.send_response(302)
        if is_new:
            gate.set_bucket_cookie(handler, bucket)
        handler.send_header("Location", HOME_V2_PATH)
        handler.end_headers()
        return True

    template = "studio-home-v2.html" if variant == "v2" else "legacy-freeze/studio.classic.html"
    _serve_studio_home_html(handler, template, bucket=bucket, is_new=is_new)
    return True


def handle_templates_admin_page(handler: StudioHandlerProtocol) -> None:
    """GET /templates-admin — Phase 13 治理控制台（静态页 + Admin API）。"""
    html_path = STUDIO_TEMPLATE_DIR / "templates-admin.html"
    if not html_path.is_file():
        handler.send_error(404)
        return
    html = html_path.read_text(encoding="utf-8")
    if handler.studio_token:
        meta = f'<meta name="studio-token" content="{handler.studio_token}" />'
        if "<meta name=\"studio-token\"" not in html:
            html = html.replace("<head>", "<head>\n  " + meta, 1)
    if handler.studio_allow_lan:
        html = html.replace("<body>", '<body data-admin-config-role-only="1">', 1)
    data = html.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Cache-Control", "no-cache")
    handler.end_headers()
    handler.wfile.write(data)


def handle_lse_flags_admin_page(handler: StudioHandlerProtocol) -> None:
    """GET /lse-flags-admin — LSE 能力开关页（静态页 + Capabilities API）。"""
    html_path = STUDIO_TEMPLATE_DIR / "lse-flags-admin.html"
    if not html_path.is_file():
        handler.send_error(404)
        return
    html = html_path.read_text(encoding="utf-8")
    if handler.studio_token:
        meta = f'<meta name="studio-token" content="{handler.studio_token}" />'
        if "<meta name=\"studio-token\"" not in html:
            html = html.replace("<head>", "<head>\n  " + meta, 1)
    if handler.studio_allow_lan:
        html = html.replace("<body>", '<body data-admin-config-role-only="1">', 1)
    data = html.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Cache-Control", "no-cache")
    handler.end_headers()
    handler.wfile.write(data)


def handle_home(handler: StudioHandlerProtocol) -> None:
    """Serve v3 (image-first) homepage — frozen, GET /classic."""
    _serve_studio_home(handler, "legacy-freeze/studio.classic.html")


def handle_home_v2(handler: StudioHandlerProtocol) -> None:
    """Serve v2 (output-first Bento) homepage — GET /v2 (parallel dev route)."""
    _serve_studio_home(handler, "studio-home-v2.html")


def _asset_etag(asset: Path) -> str:
    st = asset.stat()
    return f'W/"{st.st_mtime_ns}-{st.st_size}"'


def _asset_cache_control(handler: StudioHandlerProtocol, rel: str) -> str:
    from travelogue.web import studio_homepage_gate as gate

    host = getattr(handler, "studio_host", "127.0.0.1") or "127.0.0.1"
    if gate.is_loopback_host(host):
        return "no-cache"
    rel_lower = rel.lower()
    if rel_lower.endswith((".webp", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff2")):
        return "public, max-age=604800, immutable"
    if rel_lower.endswith("manifest.json"):
        return "public, max-age=300"
    return "public, max-age=3600"


def handle_bundle_asset(handler: StudioHandlerProtocol, path: str) -> bool:
    parsed = parse_bundle_request(path)
    if parsed is None:
        handler.send_error(404)
        return True
    template_id, rel = parsed
    asset = resolve_bundle_file(template_id, rel)
    if asset is None:
        handler.send_error(404)
        return True

    etag = _asset_etag(asset)
    inm = _request_header(handler, "If-None-Match")
    if inm and inm.strip() == etag:
        handler.send_response(304)
        handler.send_header("ETag", etag)
        handler.send_header("Cache-Control", _asset_cache_control(handler, rel))
        handler.end_headers()
        return True

    ctype = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
    data = asset.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("ETag", etag)
    handler.send_header("Cache-Control", _asset_cache_control(handler, rel))
    handler.end_headers()
    handler.wfile.write(data)
    return True


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

    etag = _asset_etag(asset)
    inm = _request_header(handler, "If-None-Match")
    if inm and inm.strip() == etag:
        handler.send_response(304)
        handler.send_header("ETag", etag)
        handler.send_header("Cache-Control", _asset_cache_control(handler, rel))
        handler.end_headers()
        return True

    ctype = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
    data = asset.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("ETag", etag)
    handler.send_header("Cache-Control", _asset_cache_control(handler, rel))
    handler.end_headers()
    handler.wfile.write(data)
    return True
