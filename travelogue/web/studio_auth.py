"""Studio bind/auth helpers (Phase 2 hardening)."""

from __future__ import annotations

import secrets
import sys

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def is_loopback_host(host: str) -> bool:
    host = (host or "").strip().lower()
    if host in LOOPBACK_HOSTS:
        return True
    if host.startswith("127."):
        return True
    return host == "::1"


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


def studio_post_authorized(
    *,
    host: str,
    token: str | None,
    headers,
    allow_lan: bool,
) -> bool:
    if is_loopback_host(host) and not allow_lan:
        return True
    if not token:
        return False
    supplied = headers.get("X-Studio-Token") or headers.get("x-studio-token") or ""
    return secrets.compare_digest(supplied, token)
