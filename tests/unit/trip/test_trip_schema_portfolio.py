"""PFO · studio.portfolio.photosFolder must pass trip.schema.json."""

from __future__ import annotations

import json

from tests._repo_root import repo_root
from travelogue.services.validate import validate_trip

ROOT = repo_root(__file__)
SCHEMA_FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"


def _schema_errors(trip: dict) -> list[str]:
    return [e for e in validate_trip(trip, level="schema") if not e.startswith("WARN:")]


def test_schema_accepts_portfolio_photos_folder() -> None:
    trip = json.loads(SCHEMA_FIXTURE.read_text(encoding="utf-8"))
    trip.setdefault("studio", {})
    trip["studio"]["edition"] = "portfolio"
    trip["studio"]["portfolio"] = {
        "seriesId": "magazine-12-standard",
        "pageCount": 12,
        "pageCountSource": "auto",
        "density": "standard",
        "photosPlaced": 20,
        "photosKept": 28,
        "photosFolder": 31,
        "overflow": {"count": 8, "resolution": "placement_gap"},
        "match": {"folderCount": 31},
    }
    errs = _schema_errors(trip)
    assert not any("photosFolder" in e for e in errs), errs
