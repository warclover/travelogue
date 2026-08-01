"""M3 · run_curate(scope=tier) preserves chapter structure."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.unit.media.test_user_tier import _dual_album, _write_photo
from travelogue.curation.curate import CurateError, run_curate
from travelogue.domain.pipeline_view import lock_structure
from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip import TripService
from travelogue.services.trip_factory import create_trip

pytestmark = pytest.mark.integration


def _chapter_fingerprint(trip: dict) -> list[tuple[str, tuple[str, ...]]]:
    from travelogue.layout_contract.chapter_items import (
        collect_screen_asset_ids,
        item_asset_ids,
    )

    out: list[tuple[str, tuple[str, ...]]] = []
    for ch in trip.get("chapters") or []:
        aids = collect_screen_asset_ids(ch)
        if not aids:
            seen: set[str] = set()
            flat: list[str] = []
            for it in ch.get("items") or []:
                for a in item_asset_ids(it) or (
                    [str(it["assetId"])] if it.get("assetId") else []
                ):
                    if a and a not in seen:
                        seen.add(a)
                        flat.append(a)
            aids = flat
        out.append((str(ch.get("id") or ""), tuple(aids)))
    return out


def test_tier_scope_preserves_chapter_ids_and_pipeline_lock(tmp_path: Path) -> None:
    album = _dual_album(tmp_path, featured_n=2, material_n=6)
    trips = tmp_path / "trips"
    trip_json = create_trip("tier-scope-01", trips, title="tier", export_layout="web")
    trip_dir = trips / "tier-scope-01"
    trip = TripService().load(trip_json)
    ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=False, generate_crops=False)
    run_curate(
        trip,
        export_layout="web",
        layout_engine="screens",
        apply_layout=True,
        trip_dir=trip_dir,
    )
    lock_structure(trip)
    TripService().save(trip, trip_json)
    trip = TripService().load(trip_json)

    before = _chapter_fingerprint(trip)
    assert before
    assert (trip.get("pipeline") or {}).get("status") == "structure_locked"

    run_curate(
        trip,
        export_layout="web",
        layout_engine="screens",
        apply_layout=True,
        trip_dir=trip_dir,
        scope="tier",
        cover_force=True,
    )
    after = _chapter_fingerprint(trip)
    assert [c[0] for c in after] == [c[0] for c in before]
    assert [set(c[1]) for c in after] == [set(c[1]) for c in before]
    assert (trip.get("pipeline") or {}).get("status") == "structure_locked"
    assert (trip.get("pipeline") or {}).get("locks", {}).get("structure") is True


def test_tier_scope_requires_existing_chapters(tmp_path: Path) -> None:
    root = tmp_path / "flat"
    root.mkdir()
    for i in range(8):
        _write_photo(root / f"p-{i:02d}.jpg", idx=i)
    trips = tmp_path / "trips"
    trip_json = create_trip("tier-empty", trips, title="empty", export_layout="web")
    trip_dir = trips / "tier-empty"
    trip = TripService().load(trip_json)
    ingest_into_trip(trip, trip_dir, from_dir=root, dedupe=False, generate_crops=False)
    trip["chapters"] = []
    with pytest.raises(CurateError) as exc:
        run_curate(trip, export_layout="web", apply_layout=False, trip_dir=trip_dir, scope="tier")
    assert exc.value.code == "E_CURATE_NO_STRUCTURE"
