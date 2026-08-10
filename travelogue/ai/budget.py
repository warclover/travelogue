"""Trip-level LLM/VLM call budget · D-ACP-04 / D-ACP-18.

Counts calls only. Rate-limit backoff stays in ``travelogue.llm.shared_backoff``.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

from travelogue.config import AppConfig, get_config
from travelogue.llm.shared_backoff import get_shared_backoff


@dataclass
class TripLlmBudget:
    """Per-trip call counter. Thread-safe for concurrent narrate workers."""

    max_calls: int
    trip_id: str = ""
    _used: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @classmethod
    def from_config(
        cls,
        *,
        trip_id: str = "",
        cfg: AppConfig | None = None,
    ) -> TripLlmBudget:
        app_cfg = cfg or get_config()
        acp = getattr(app_cfg, "ai_capability", None)
        max_calls = int(getattr(acp, "max_calls_per_trip", 12) or 12) if acp else 12
        return cls(max_calls=max(0, max_calls), trip_id=trip_id)

    @property
    def used(self) -> int:
        with self._lock:
            return self._used

    @property
    def remaining(self) -> int:
        with self._lock:
            return max(0, self.max_calls - self._used)

    def try_consume(self, agent: str = "") -> bool:
        """Reserve one call slot. False → caller must fallback (D-ACP-04).

        Also waits on shared provider backoff before returning True (D-ACP-18).
        """
        del agent  # reserved for future per-agent sub-caps
        with self._lock:
            if self._used >= self.max_calls:
                return False
            self._used += 1
        get_shared_backoff().wait_turn()
        return True

    def force_count(self, n: int = 1) -> None:
        """Record calls that already happened outside try_consume (legacy paths)."""
        with self._lock:
            self._used += max(0, int(n))


# Weak trip_id → budget registry for Studio multi-call sessions within one process.
_BUDGETS: dict[str, TripLlmBudget] = {}
_BUDGETS_LOCK = threading.Lock()


def budget_for_trip(
    trip_id: str,
    *,
    cfg: AppConfig | None = None,
    reset: bool = False,
) -> TripLlmBudget:
    """Get or create a process-local budget keyed by trip id."""
    key = str(trip_id or "") or "__anon__"
    with _BUDGETS_LOCK:
        if reset or key not in _BUDGETS:
            _BUDGETS[key] = TripLlmBudget.from_config(trip_id=key, cfg=cfg)
        return _BUDGETS[key]


def clear_budgets() -> None:
    """Test helper."""
    with _BUDGETS_LOCK:
        _BUDGETS.clear()
