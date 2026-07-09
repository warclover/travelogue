"""Studio bind/auth helpers (Phase 2 hardening)."""

from __future__ import annotations

import secrets
import sys

from travelogue.util.net import LOOPBACK_HOSTS, is_loopback_host

__all__ = ["LOOPBACK_HOSTS", "is_loopback_host", "ensure_studio_bind_allowed", "new_studio_token", "studio_post_authorized"]


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
