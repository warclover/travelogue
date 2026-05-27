"""Validate Studio tripId path segments."""

from __future__ import annotations

import re

_TRIP_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")


def is_valid_studio_trip_id(trip_id: str) -> bool:
    trip_id = (trip_id or "").strip()
    if not trip_id or trip_id in {".", ".."}:
        return False
    return bool(_TRIP_ID_RE.match(trip_id))
