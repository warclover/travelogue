"""Offline C1/C2 share-face copy backfill."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.services.share_face_backfill import (
    backfill_trip,
    backfill_trips_dir,
    iter_trip_jsons,
)
from travelogue.services.trip import TripService


def _old_trip() -> dict:
    return {
        "version": "0.2",
        "tripId": "backfill-old",
        "templateId": "visual-journal",
        "exportLayout": "auto",
        "meta": {
            "title": "京都见闻",
            "dateStart": "2026-05-27",
            "dateEnd": "2026-05-27",
            "places": ["京都"],
            "tone": "relaxed",
        },
        "intent": {"title": "京都见闻"},
        "assets": [
            {"id": "a1", "takenAt": "2026-05-27T10:00:00"},
            {"id": "a2", "takenAt": "2026-05-27T15:00:00"},
        ],
        "chapters": [
            {
                "id": "c1",
                "index": 1,
                "title": "5月27日",
                "lead": "",
                "items": [{"type": "media-card", "assetId": "a1"}],
            },
            {
                "id": "c2",
                "index": 2,
                "title": "5月27日 · 下午",
                "lead": "",
                "items": [{"type": "media-card", "assetId": "a2"}],
            },
        ],
        "pipeline": {"status": "draft"},
        "createdAt": "2026-05-27T00:00:00Z",
        "updatedAt": "2026-05-27T00:00:00Z",
    }


def _write_trip(trips_dir: Path, trip_id: str, payload: dict) -> Path:
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True, exist_ok=True)
    path = trip_dir / "trip.json"
    TripService().save(payload, path)
    return path


def test_iter_skips_underscore_dirs(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    _write_trip(trips, "keep-me", _old_trip())
    _write_trip(trips, "_hidden", _old_trip())
    ids = [p.parent.name for p in iter_trip_jsons(trips)]
    assert ids == ["keep-me"]


def test_backfill_trip_writes_stub_leads_and_place_titles(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    path = _write_trip(trips, "backfill-old", _old_trip())
    svc = TripService(root=tmp_path)
    result = backfill_trip(path, rerender=False, trip_service=svc)
    assert result["changed"] is True
    assert result["error"] is None
    trip = json.loads(path.read_text(encoding="utf-8"))
    titles = [ch["title"] for ch in trip["chapters"]]
    leads = [ch["lead"] for ch in trip["chapters"]]
    assert all(lead.strip() for lead in leads)
    assert all("旅行照片" not in lead for lead in leads)
    assert not any(t.startswith("5月27日") and "·" not in t for t in titles)
    assert any("京都" in t for t in titles)

    again = backfill_trip(path, rerender=False, trip_service=svc)
    assert again["changed"] is False


def test_dry_run_does_not_write(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    path = _write_trip(trips, "backfill-old", _old_trip())
    before = path.read_text(encoding="utf-8")
    result = backfill_trip(path, rerender=False, dry_run=True)
    assert result["changed"] is True
    assert path.read_text(encoding="utf-8") == before


def test_backfill_trips_dir_only(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    _write_trip(trips, "one", _old_trip())
    _write_trip(trips, "two", _old_trip())
    rows = backfill_trips_dir(
        trips,
        rerender=False,
        only={"one"},
        trip_service=TripService(root=tmp_path),
    )
    assert [r["tripId"] for r in rows] == ["one"]
    assert rows[0]["changed"] is True
