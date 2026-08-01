"""Share-Face Integrity · longshot density (D-SFI-11 / FE-SFI-09)."""

from __future__ import annotations

from typing import Literal

Density = Literal["default", "compact"]


def resolve_longshot_density(trip: dict | None) -> Density:
    export = (trip or {}).get("export") if isinstance(trip, dict) else None
    raw = ""
    if isinstance(export, dict):
        raw = str(export.get("longshotDensity") or "").strip().lower()
    if raw == "compact":
        return "compact"
    return "default"


def is_compact_longshot(trip: dict | None) -> bool:
    return resolve_longshot_density(trip) == "compact"
