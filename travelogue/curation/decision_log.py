"""Audit trail for layout search decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class LayoutDecisionLog:
    chapter_id: str | None = None
    started_at: str = field(default_factory=_utc_now_iso)
    events: list[dict[str, Any]] = field(default_factory=list)

    def add(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        self.events.append(
            {
                "type": event_type,
                "at": _utc_now_iso(),
                **(payload or {}),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "chapterId": self.chapter_id,
            "startedAt": self.started_at,
            "events": self.events,
        }
