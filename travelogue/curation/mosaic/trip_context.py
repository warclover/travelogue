"""Per-curate mosaic trip id for template rollout cohort (R-P19-105)."""

from __future__ import annotations

from contextvars import ContextVar

_mosaic_trip_id_var: ContextVar[str | None] = ContextVar("mosaic_trip_id", default=None)


def mosaic_trip_id() -> str | None:
    tid = _mosaic_trip_id_var.get()
    return str(tid).strip() if tid else None


def set_mosaic_trip_id(trip_id: str | None) -> None:
    if trip_id is not None and str(trip_id).strip():
        _mosaic_trip_id_var.set(str(trip_id).strip())
    else:
        _mosaic_trip_id_var.set(None)
