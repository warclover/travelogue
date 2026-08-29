"""Offline Share-Face copy backfill (C1/C2 tail).

Same migrate as preview open (`migrate_share_face_purity_on_open`): stub leads
and non-date chapter titles. Writes ``trip.json`` so old shelf books do not
wait for someone to open preview.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from travelogue.domain.share_face_purity import migrate_share_face_purity_on_open
from travelogue.runtime import app_context_for_trip_json
from travelogue.services.trip import TripService, mark_render_bundle_current


def iter_trip_jsons(
    trips_dir: Path,
    *,
    only: set[str] | None = None,
) -> list[Path]:
    """Trip folders under ``trips_dir`` that have ``trip.json``.

    Skips ``.`` / ``_`` prefixes (internal dogfood dirs).
    """
    root = Path(trips_dir)
    if not root.is_dir():
        return []
    out: list[Path] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith((".", "_")):
            continue
        if only and child.name not in only:
            continue
        trip_json = child / "trip.json"
        if trip_json.is_file():
            out.append(trip_json)
    return out


def backfill_trip(
    trip_json: Path,
    *,
    rerender: bool = True,
    dry_run: bool = False,
    trip_service: TripService | None = None,
) -> dict[str, Any]:
    """Migrate one trip and persist when copy changed.

    Returns ``{tripId, changed, chapters, rerendered, error}``.
    ``chapters`` lists migrate hits (title paths and/or chapter ids).
    """
    trip_json = Path(trip_json).resolve()
    trip_id = trip_json.parent.name
    empty = {
        "tripId": trip_id,
        "changed": False,
        "chapters": [],
        "rerendered": [],
        "error": None,
    }
    try:
        svc = trip_service or app_context_for_trip_json(trip_json).trip_service()
        trip = svc.load(trip_json)
        probe = migrate_share_face_purity_on_open(deepcopy(trip))
        chapter_hits = list(probe.get("chapters") or [])
        empty["chapters"] = chapter_hits
        if not probe.get("changed"):
            return empty
        empty["changed"] = True
        if dry_run:
            return empty

        chapter_copy_changed = bool(chapter_hits)

        def _mutate(disk: dict) -> bool:
            migrate_share_face_purity_on_open(disk)
            if not chapter_copy_changed:
                mark_render_bundle_current(disk)
            return True

        svc.update(
            trip_json,
            _mutate,
            touch_updated=False,
            bump_revision=True,
        )
        if rerender and chapter_copy_changed:
            from travelogue.web.rerender import rerender_draft_trip

            try:
                empty["rerendered"] = list(rerender_draft_trip(trip_json) or [])
            except Exception as exc:
                empty["error"] = f"rerender {type(exc).__name__}: {exc}"
        return empty
    except Exception as exc:
        empty["error"] = f"{type(exc).__name__}: {exc}"
        return empty


def backfill_trips_dir(
    trips_dir: Path,
    *,
    rerender: bool = True,
    dry_run: bool = False,
    only: set[str] | None = None,
    trip_service: TripService | None = None,
) -> list[dict[str, Any]]:
    """Backfill every eligible trip under ``trips_dir``."""
    rows: list[dict[str, Any]] = []
    for trip_json in iter_trip_jsons(trips_dir, only=only):
        rows.append(
            backfill_trip(
                trip_json,
                rerender=rerender,
                dry_run=dry_run,
                trip_service=trip_service,
            )
        )
    return rows
