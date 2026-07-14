"""Bookends Engine · B1 lock sync (ADR-017 · D3)."""

from __future__ import annotations

from travelogue.cover_engine.lock import (
    is_opening_locked,
    read_lock_state,
    set_opening_locked,
    sync_lock_mirrors,
    write_lock_state,
)
from travelogue.cover_engine.joint import apply_joint_pick, pick_cover_style_and_asset


def _trip(*, joint: bool | None = None, bookends: dict | None = None) -> dict:
    curation: dict = {}
    if joint is not None:
        curation["coverJointLocked"] = joint
    if bookends is not None:
        curation["bookendsLock"] = bookends
    return {
        "tripId": "lock-demo",
        "exportLayout": "auto",
        "meta": {"coverOpeningStyle": "veil-footer"},
        "assets": [
            {
                "id": "a1",
                "type": "image",
                "width": 1600,
                "height": 1200,
                "focalPoint": {"x": 0.5, "y": 0.3},
                "userTier": "featured",
                "sharpness": 0.8,
                "aesthetic": {"overall": 0.7},
            }
        ],
        "coverAssetId": "a1",
        "curation": curation,
        "chapters": [],
    }


def test_legacy_cover_joint_locked_backfills_opening() -> None:
    trip = _trip(joint=True)
    state = read_lock_state(trip)
    assert state.opening is True
    assert state.closing is False
    assert state.all_locked is False


def test_write_lock_syncs_three_fields() -> None:
    trip = _trip()
    write_lock_state(trip, opening=True, closing=False)
    curation = trip["curation"]
    assert curation["bookendsLock"] == {"opening": True, "closing": False}
    assert curation["coverJointLocked"] is True
    assert curation["bookendsLocked"] is False

    write_lock_state(trip, closing=True)
    assert curation["bookendsLock"] == {"opening": True, "closing": True}
    assert curation["bookendsLocked"] is True
    assert curation["coverJointLocked"] is True


def test_sync_lock_mirrors_from_legacy_joint() -> None:
    trip = _trip(joint=True)
    sync_lock_mirrors(trip)
    assert trip["curation"]["bookendsLock"]["opening"] is True
    assert trip["curation"]["coverJointLocked"] is True
    assert trip["curation"]["bookendsLocked"] is False


def test_bookends_lock_preferred_over_joint_mismatch() -> None:
    trip = _trip(joint=False, bookends={"opening": True, "closing": False})
    assert is_opening_locked(trip) is True
    assert read_lock_state(trip).opening is True


def test_apply_joint_pick_sets_bookends_opening_lock() -> None:
    trip = _trip()
    explain = pick_cover_style_and_asset(trip, layout="web", k=3)
    apply_joint_pick(trip, explain, lock=True, layout="web")
    assert trip["curation"]["coverJointLocked"] is True
    assert trip["curation"]["bookendsLock"]["opening"] is True
    assert trip["curation"]["bookendsLocked"] is False


def test_set_opening_locked_helper() -> None:
    trip = _trip()
    set_opening_locked(trip, True)
    assert is_opening_locked(trip) is True
    set_opening_locked(trip, False)
    assert is_opening_locked(trip) is False
    assert trip["curation"]["coverJointLocked"] is False
