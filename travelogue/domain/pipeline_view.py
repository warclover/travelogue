"""Pipeline status view helpers (M-C4 · trip dict mutations)."""

from __future__ import annotations

from typing import Literal

from travelogue.errors import CodeError

Stage = Literal["ingest", "clustering", "curate", "layout", "narrate", "render", "export", "lock_structure", "lock_copy"]
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
    "clustering": "ingest_ready",
    "curate": "ingest_ready",
    "layout": "structure_draft",
    "narrate": "structure_locked",
    "render": "copy_locked",
    "export": "rendered",
    "lock_structure": "structure_draft",
    "lock_copy": "copy_draft",
}


class PipelineError(CodeError):
    pass


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


def pipeline_dict(trip: dict) -> dict:
    return trip.setdefault("pipeline", {})


def set_pipeline_status(trip: dict, status: str) -> None:
    pipeline_dict(trip)["status"] = status


def set_pipeline_lock(trip: dict, name: str, value: bool) -> None:
    pipeline_dict(trip).setdefault("locks", {})[name] = value


def replace_pipeline_locks(trip: dict, locks: dict) -> None:
    """Replace the whole locks map (e.g. restore after tier-only curate)."""
    pipeline_dict(trip)["locks"] = dict(locks)


def append_pipeline_run(trip: dict, run: dict) -> None:
    pipeline_dict(trip).setdefault("runs", []).append(run)


def set_pipeline_timings(trip: dict, timings: dict[str, float]) -> None:
    pipeline_dict(trip)["timings"] = dict(timings)


def absorb_pipeline_timing_keys(trip: dict, timings: dict[str, float]) -> None:
    """Copy keys from ``trip.pipeline.timings`` into *timings* when absent.

    Stages such as ingest may write PT telemetry (``ingestWorkers`` …) onto the
    trip before the orchestrator flushes its local timings dict. Without this
    merge, ``set_pipeline_timings`` would wipe those keys (PRD-PIPELINE-PERF-V1
    · P-PPF-01 / MF-07).
    """
    existing = pipeline_dict(trip).get("timings") or {}
    if not isinstance(existing, dict):
        return
    for key, value in existing.items():
        if key in timings:
            continue
        try:
            timings[key] = float(value)
        except (TypeError, ValueError):
            continue


def clear_pending_assets(trip: dict) -> None:
    pipeline_dict(trip)["pendingAssets"] = []


def lock_structure(trip: dict) -> None:
    """G1 confirm: structure_draft → structure_locked."""
    set_pipeline_lock(trip, "structure", True)
    set_pipeline_status(trip, "structure_locked")


def lock_copy(trip: dict) -> None:
    """Copy gate: copy_draft → copy_locked."""
    set_pipeline_lock(trip, "copy", True)
    set_pipeline_status(trip, "copy_locked")


def unlock_structure_for_replan(trip: dict) -> None:
    set_pipeline_lock(trip, "structure", False)
    set_pipeline_status(trip, "structure_draft")


def revert_copy_lock_for_edit(trip: dict) -> None:
    """Inline copy edit after copy_locked → copy_draft."""
    if pipeline_dict(trip).get("status") == "copy_locked":
        set_pipeline_status(trip, "copy_draft")
        set_pipeline_lock(trip, "copy", False)
