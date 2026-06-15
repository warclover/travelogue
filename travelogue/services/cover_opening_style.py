"""Web cover opening style assignment and resolution (Cover Styles V5)."""

from __future__ import annotations

import hashlib

COVER_OPENING_STYLES: tuple[str, ...] = ("card-br", "split-mat", "magazine-head")
_DEFAULT_STYLE = "card-br"


def assign_cover_opening_style(trip_id: str) -> str:
    """Deterministic 1:1:1 style from tripId (create-time only)."""
    digest = hashlib.sha256(trip_id.encode("utf-8")).hexdigest()
    index = int(digest[:8], 16) % len(COVER_OPENING_STYLES)
    return COVER_OPENING_STYLES[index]


def resolve_cover_opening_style(trip: dict) -> str:
    """Read trip meta; fall back to card-br for missing or invalid values."""
    raw = str((trip.get("meta") or {}).get("coverOpeningStyle") or "").strip()
    if raw in COVER_OPENING_STYLES:
        return raw
    return _DEFAULT_STYLE
