"""Optional callbacks for Studio pipeline progress (shared with run_trip)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

StageProgressCallback = Callable[[str, int, str | None], None]


@dataclass
class StudioHooks:
    """Studio-specific stage notifications; wired into orchestrator when provided."""

    on_stage: StageProgressCallback | None = None

    def report(self, stage: str, index: int, hint: str | None = None) -> None:
        if self.on_stage is not None:
            self.on_stage(stage, index, hint)
