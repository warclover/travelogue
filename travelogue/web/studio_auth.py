"""Studio bind/auth helpers (Phase 2 hardening)."""

from __future__ import annotations

import secrets
import sys
from http.cookies import SimpleCookie
from urllib.parse import parse_qs

from travelogue.util.net import LOOPBACK_HOSTS, is_loopback_host

STUDIO_TOKEN_COOKIE = "studio-token"
STUDIO_TOKEN_QUERY_KEYS = ("studio_token", "t")

__all__ = [
    "LOOPBACK_HOSTS",
    "STUDIO_TOKEN_COOKIE",
    "STUDIO_TOKEN_QUERY_KEYS",
    "is_loopback_host",
    "ensure_studio_bind_allowed",
    "new_studio_token",
    "extract_studio_token",
    "studio_request_authorized",
    "studio_post_authorized",
]


def ensure_studio_bind_allowed(host: str, *, allow_lan: bool = False) -> None:
    if is_loopback_host(host) or allow_lan:
        return
    print(
        f"Studio refuses to bind to {host!r} without --allow-lan. "
        "Use 127.0.0.1 (default) for local-only access.",
        file=sys.stderr,
    )
    raise SystemExit(1)


def new_studio_token() -> str:
    return secrets.token_urlsafe(32)


def extract_studio_token(headers, *, query: str = "") -> str:
    """Resolve token from header, then cookie, then query string."""
    supplied = headers.get("X-Studio-Token") or headers.get("x-studio-token") or ""
    if supplied:
        return str(supplied)

    cookie_header = headers.get("Cookie") or headers.get("cookie") or ""
    if cookie_header:
        jar = SimpleCookie()
        try:
            jar.load(cookie_header)
        except Exception:
            jar = SimpleCookie()
        morsel = jar.get(STUDIO_TOKEN_COOKIE)
        if morsel is not None and morsel.value:
            return str(morsel.value)

    if query:
        qs = parse_qs(query, keep_blank_values=False)
        for key in STUDIO_TOKEN_QUERY_KEYS:
            values = qs.get(key) or []
            if values and values[0]:
                return str(values[0])
    return ""


def studio_request_authorized(
    *,
    host: str,
    token: str | None,
    headers,
    allow_lan: bool,
    query: str = "",
) -> bool:
    if is_loopback_host(host) and not allow_lan:
        return True
    if not token:
        return False
    supplied = extract_studio_token(headers, query=query)
    if not supplied:
        return False
    return secrets.compare_digest(supplied, token)


def studio_post_authorized(
    *,
    host: str,
    token: str | None,
    headers,
    allow_lan: bool,
) -> bool:
    return studio_request_authorized(
        host=host,
        token=token,
        headers=headers,
        allow_lan=allow_lan,
    )
