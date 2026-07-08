"""Optional callbacks for Studio pipeline progress (shared with run_trip)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

StageProgressCallback = Callable[[str, int, str | None], None]
TimingCallback = Callable[[dict[str, float]], None]


@dataclass
class StudioHooks:
    """Studio-specific stage notifications; wired into orchestrator when provided."""

    on_stage: StageProgressCallback | None = None
    on_timing: TimingCallback | None = None

    def report(self, stage: str, index: int, hint: str | None = None) -> None:
        if self.on_stage is not None:
            self.on_stage(stage, index, hint)

    def report_timing(self, timings: dict[str, float]) -> None:
        if self.on_timing is not None:
            self.on_timing(dict(timings))
