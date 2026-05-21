"""Pipeline status gates for CLI and orchestrator."""

from __future__ import annotations

from typing import Literal

Stage = Literal["ingest", "curate", "layout", "narrate", "render", "export", "lock_structure", "lock_copy"]
Until = Literal["ingest", "structure", "layout", "copy", "rendered", "exported"]

STATUS_ORDER = (
    "draft_ingest",
    "ingest_ready",
    "structure_draft",
    "structure_locked",
    "copy_draft",
    "copy_locked",
    "rendered",
    "exported",
)

STAGE_MIN_STATUS: dict[Stage, str] = {
    "ingest": "draft_ingest",
    "curate": "ingest_ready",
    "layout": "structure_draft",
    "narrate": "structure_locked",
    "render": "copy_locked",
    "export": "rendered",
    "lock_structure": "structure_draft",
    "lock_copy": "copy_draft",
}


class PipelineError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def trip_status(trip: dict) -> str:
    return (trip.get("pipeline") or {}).get("status", "draft_ingest")


def assert_stage_allowed(trip: dict, stage: Stage) -> None:
    status = trip_status(trip)
    locks = (trip.get("pipeline") or {}).get("locks") or {}
    if stage == "narrate" and status == "structure_draft" and not locks.get("structure"):
        raise PipelineError(
            "E_PIPELINE_ORDER",
            "narrate requires structure_locked (run lock structure first)",
        )
    if stage == "render" and status == "copy_draft" and not locks.get("copy"):
        raise PipelineError(
            "E_PIPELINE_ORDER",
            "render requires copy_locked (run lock copy first)",
        )
    min_status = STAGE_MIN_STATUS.get(stage)
    if not min_status:
        return
    if STATUS_ORDER.index(status) < STATUS_ORDER.index(min_status):
        raise PipelineError(
            "E_PIPELINE_ORDER",
            f"cannot run {stage} when pipeline.status={status} (need>={min_status})",
        )


def set_layout_status(trip: dict, layout_status: str) -> None:
    pipe = trip.setdefault("pipeline", {})
    pipe["layoutStatus"] = layout_status
