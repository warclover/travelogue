"""F-CLU-CACHE-04 · ingest writes pendingAssets after structure lock.

Covers:
- post-lock re-ingest preserves ``pipeline.status`` / ``pipeline.locks`` and
  appends only the *new* asset ids to ``pipeline.pendingAssets``
- ``incremental=True`` reflush drains the pending list without unlocking
- pre-lock ingest keeps the legacy behaviour (status → ingest_ready, pending = [])
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip


def _album(root: Path, name: str, *, count: int, seed: int) -> Path:
    album = root / name
    album.mkdir()
    for i in range(count):
        color = (
            (seed + i * 17) % 255,
            (seed + i * 11 + 30) % 255,
            (seed + i * 13 + 60) % 255,
        )
        Image.new("RGB", (1200, 1600), color).save(
            album / f"{name}-{i:02d}.jpg", quality=92
        )
    return album


def _load_trip(trip_json: Path) -> dict:
    return json.loads(trip_json.read_text(encoding="utf-8"))


def _save_trip(trip: dict, trip_json: Path) -> None:
    trip_json.write_text(json.dumps(trip, ensure_ascii=False), encoding="utf-8")


def test_ingest_pre_lock_keeps_legacy_pending_reset(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("pre-lock", trips, title="未锁导入")
    trip_dir = trips / "pre-lock"
    trip = _load_trip(trip_json)
    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=_album(tmp_path, "wave1", count=4, seed=0),
        generate_crops=False,
        dedupe=False,
    )
    pipe = trip["pipeline"]
    assert pipe["status"] == "ingest_ready"
    assert pipe["pendingAssets"] == []
    assert pipe["locks"] == {"structure": False, "copy": False}


def test_ingest_post_lock_appends_new_asset_ids_to_pending(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("post-lock", trips, title="锁后追加")
    trip_dir = trips / "post-lock"
    trip = _load_trip(trip_json)

    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=_album(tmp_path, "wave1", count=4, seed=10),
        generate_crops=False,
        dedupe=False,
    )
    first_ids = sorted(a["id"] for a in trip["assets"])
    # simulate user locking the structure after the first ingest
    trip["pipeline"]["status"] = "structure_locked"
    trip["pipeline"]["locks"] = {"structure": True, "copy": False}
    _save_trip(trip, trip_json)

    # second ingest with new files arriving after the lock
    trip = _load_trip(trip_json)
    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=_album(tmp_path, "wave2", count=2, seed=120),
        generate_crops=False,
        dedupe=False,
    )

    pipe = trip["pipeline"]
    assert pipe["status"] == "structure_locked", "post-lock ingest must NOT downgrade status"
    assert pipe["locks"] == {"structure": True, "copy": False}, "locks must survive ingest"
    pending = list(pipe.get("pendingAssets") or [])
    assert pending, "expected new asset ids to be appended to pendingAssets"
    all_ids = sorted(a["id"] for a in trip["assets"])
    new_ids = sorted(set(all_ids) - set(first_ids))
    assert sorted(pending) == new_ids, (
        f"pendingAssets should match the newly imported ids; "
        f"pending={pending!r} new_ids={new_ids!r}"
    )
    # idempotent merge: a second post-lock pass adds more without clobbering
    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=_album(tmp_path, "wave3", count=1, seed=240),
        generate_crops=False,
        dedupe=False,
    )
    pipe = trip["pipeline"]
    assert pipe["status"] == "structure_locked"
    assert len(pipe["pendingAssets"]) == len(new_ids) + 1
    # all previously pending ids must still be present (no truncation)
    for aid in new_ids:
        assert aid in pipe["pendingAssets"]


def test_ingest_post_lock_incremental_clears_pending(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    trip_json = create_trip("incremental", trips, title="增量回放")
    trip_dir = trips / "incremental"
    trip = _load_trip(trip_json)

    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=_album(tmp_path, "wave1", count=4, seed=20),
        generate_crops=False,
        dedupe=False,
    )
    trip["pipeline"]["status"] = "structure_locked"
    trip["pipeline"]["locks"] = {"structure": True, "copy": False}
    _save_trip(trip, trip_json)

    trip = _load_trip(trip_json)
    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=_album(tmp_path, "wave2", count=2, seed=200),
        generate_crops=False,
        dedupe=False,
    )
    pending_after_lock = list(trip["pipeline"]["pendingAssets"])
    assert pending_after_lock

    # caller drains pending via incremental=True; status stays locked, list emptied
    ingest_into_trip(
        trip,
        trip_dir,
        from_dir=None,
        incremental=True,
        generate_crops=False,
        dedupe=False,
    )
    pipe = trip["pipeline"]
    assert pipe["status"] == "structure_locked", "incremental reflush must preserve lock"
    assert pipe["locks"] == {"structure": True, "copy": False}
    assert pipe["pendingAssets"] == [], "incremental reflush must empty pendingAssets"
