"""Create empty trip workspaces."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from travelogue.services.trip import TripService


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def create_trip(
    trip_id: str,
    trips_dir: Path,
    *,
    title: str = "待命名旅程",
    place: str = "旅途",
    export_layout: str = "auto",
) -> Path:
    trip_dir = trips_dir / trip_id
    if trip_dir.exists() and any(trip_dir.iterdir()):
        raise FileExistsError(f"E_TRIP_EXISTS trip directory not empty: {trip_dir}")

    for sub in ("source", "assets", "runs"):
        (trip_dir / sub).mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    trip = {
        "version": "0.2",
        "tripId": trip_id,
        "templateId": "visual-journal",
        "exportLayout": export_layout,
        "meta": {
            "title": title[:20],
            "subtitle": "",
            "hook": "",
            "dateStart": today,
            "dateEnd": today,
            "places": [place],
            "tone": "relaxed",
        },
        "coverAssetId": "",
        "assets": [],
        "chapters": [],
        "epilogue": "",
        "privacy": {"level": "private", "stripExifOnExport": True, "confirmedAt": None},
        "pipeline": {
            "status": "draft_ingest",
            "layoutStatus": "pending",
            "locks": {"structure": False, "copy": False},
            "pendingAssets": [],
            "runs": [],
        },
        "createdAt": _utc_now_iso(),
        "updatedAt": _utc_now_iso(),
    }

    trip_json = trip_dir / "trip.json"
    TripService(root=trips_dir.parent).save(trip, trip_json)
    return trip_json
