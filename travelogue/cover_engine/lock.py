"""Bookends lock sync helpers (ADR-017 · D3 / PRD §5.3)."""

from __future__ import annotations

from travelogue.cover_engine.types import BookendsLockState


def _curation(trip: dict) -> dict:
    curation = trip.get("curation")
    if not isinstance(curation, dict):
        curation = {}
        trip["curation"] = curation
    return curation


def read_lock_state(trip: dict) -> BookendsLockState:
    """Prefer bookendsLock; legacy coverJointLocked backfills opening only."""
    curation = trip.get("curation") if isinstance(trip.get("curation"), dict) else {}
    raw = curation.get("bookendsLock")
    opening: bool | None = None
    closing = False
    if isinstance(raw, dict):
        if "opening" in raw:
            opening = bool(raw.get("opening"))
        if "closing" in raw:
            closing = bool(raw.get("closing"))
    if opening is None:
        opening = bool(curation.get("coverJointLocked"))
    return BookendsLockState(opening=bool(opening), closing=bool(closing))


def write_lock_state(
    trip: dict,
    *,
    opening: bool | None = None,
    closing: bool | None = None,
) -> BookendsLockState:
    """Write bookendsLock and keep coverJointLocked / bookendsLocked in sync."""
    curation = _curation(trip)
    current = read_lock_state(trip)
    next_opening = current.opening if opening is None else bool(opening)
    next_closing = current.closing if closing is None else bool(closing)
    state = BookendsLockState(opening=next_opening, closing=next_closing)
    curation["bookendsLock"] = {"opening": state.opening, "closing": state.closing}
    curation["coverJointLocked"] = state.opening
    curation["bookendsLocked"] = state.all_locked
    return state


def sync_lock_mirrors(trip: dict) -> BookendsLockState:
    """Normalize mirrors from current truth (bookendsLock preferred, else joint)."""
    state = read_lock_state(trip)
    return write_lock_state(trip, opening=state.opening, closing=state.closing)


def is_opening_locked(trip: dict) -> bool:
    return read_lock_state(trip).opening


def is_closing_locked(trip: dict) -> bool:
    return read_lock_state(trip).closing


def set_opening_locked(trip: dict, locked: bool = True) -> BookendsLockState:
    return write_lock_state(trip, opening=bool(locked))


def set_closing_locked(trip: dict, locked: bool = True) -> BookendsLockState:
    return write_lock_state(trip, closing=bool(locked))
