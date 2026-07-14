"""Studio process lifecycle hooks (shutdown signal for desktop exit)."""

from __future__ import annotations

import threading
from http.server import ThreadingHTTPServer
from typing import Any

_lock = threading.Lock()
_shutdown_event: threading.Event | None = None
_active_server: ThreadingHTTPServer | None = None


def register_studio_server(server: ThreadingHTTPServer, event: threading.Event) -> None:
    global _shutdown_event, _active_server
    with _lock:
        _active_server = server
        _shutdown_event = event


def clear_studio_server(server: ThreadingHTTPServer | None = None) -> None:
    global _shutdown_event, _active_server
    with _lock:
        if server is not None and _active_server is not server:
            return
        _active_server = None
        _shutdown_event = None


def request_studio_shutdown() -> bool:
    """Ask the running Studio HTTP server to stop. Returns False if none registered."""
    with _lock:
        event = _shutdown_event
        server = _active_server
    if event is None or server is None:
        return False
    event.set()

    def _shutdown() -> None:
        try:
            server.shutdown()
        except Exception:
            pass

    threading.Thread(target=_shutdown, daemon=True, name="studio-shutdown").start()
    return True


def studio_shutdown_requested() -> bool:
    with _lock:
        return bool(_shutdown_event and _shutdown_event.is_set())


def bind_studio_server(
    host: str,
    port: int,
    handler: Any,
    *,
    max_tries: int = 8,
) -> tuple[ThreadingHTTPServer, int]:
    """Bind Studio server; try next ports when the preferred one is busy."""
    last_err: OSError | None = None
    for offset in range(max(1, max_tries)):
        candidate = port + offset
        try:
            server = ThreadingHTTPServer((host, candidate), handler)
            return server, candidate
        except OSError as exc:
            last_err = exc
            continue
    assert last_err is not None
    raise last_err
