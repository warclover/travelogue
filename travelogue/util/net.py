"""Network / host helpers (M-B1 · util layer)."""

from __future__ import annotations

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def is_loopback_host(host: str) -> bool:
    host = (host or "").strip().lower()
    if host in LOOPBACK_HOSTS:
        return True
    if host.startswith("127."):
        return True
    return host == "::1"
