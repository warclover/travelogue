"""Cross-call shared provider backoff for concurrent narrate (Pipeline Throughput · M2).

Module-level lock + next-allowed monotonic timestamp. 429/502/503 update the
gate; callers wait before the next HTTP attempt. Not a per-request sleep reuse —
one shared clock across ThreadPool workers.
"""

from __future__ import annotations

import threading
import time


class SharedProviderBackoff:
    """Thread-safe gate for provider rate limits."""

    def __init__(self, *, base_sec: float = 1.0) -> None:
        self._lock = threading.Lock()
        self._next_allowed = 0.0
        self._backoff_count = 0
        self._base_sec = float(base_sec)

    @property
    def backoff_count(self) -> int:
        with self._lock:
            return self._backoff_count

    def wait_turn(self) -> None:
        with self._lock:
            now = time.monotonic()
            delay = self._next_allowed - now
        if delay > 0:
            time.sleep(delay)

    def note_rate_limit(self, *, retry_after_sec: float | None = None, attempt: int = 0) -> None:
        """Record a retryable provider limit and push the shared next-allowed time."""
        delay = float(retry_after_sec) if retry_after_sec is not None else self._base_sec * (2 ** max(0, attempt))
        delay = max(0.05, min(delay, 60.0))
        with self._lock:
            self._backoff_count += 1
            self._next_allowed = max(self._next_allowed, time.monotonic() + delay)

    def reset(self) -> None:
        with self._lock:
            self._next_allowed = 0.0
            self._backoff_count = 0


_SHARED = SharedProviderBackoff()


def get_shared_backoff() -> SharedProviderBackoff:
    return _SHARED


def reset_shared_backoff() -> None:
    """Test helper — clear shared gate between cases."""
    _SHARED.reset()
