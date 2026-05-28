"""AL-P3-02/03 · trip.schema.json accepts Phase 3 clustering fields."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.config import AppConfig, ClusteringConfig
from travelogue.curation.clustering import run_clustering_layer
from travelogue.services.validate import validate_trip

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FIXTURE = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
SYNTHETIC = ROOT / "tests" / "fixtures" / "clustering" / "synthetic-gps" / "assets-manifest.json"


def _schema_errors(trip: dict) -> list[str]:
    return [e for e in validate_trip(trip, level="schema") if not e.startswith("WARN:")]


def test_schema_accepts_clustering_metadata(tmp_path: Path) -> None:
    trip = json.loads(SCHEMA_FIXTURE.read_text(encoding="utf-8"))
    for i, asset in enumerate(trip.get("assets") or []):
        if asset.get("type") != "image":
            continue
        asset["geo"] = {"lat": 35.0 + (i % 5) * 0.05, "lon": 139.0 + (i % 3) * 0.05}
        asset["takenAt"] = asset.get("takenAt") or "2025-04-02T10:00:00Z"
    cfg = AppConfig(clustering=ClusteringConfig(enabled="true"))
    run_clustering_layer(trip, trip_dir=tmp_path / "trip", cfg=cfg)
    clustering = trip.get("curation", {}).get("clustering") or {}
    assert clustering.get("segmentMode") in ("geo_event", "date_fallback")
    assert not _schema_errors(trip), _schema_errors(trip)


def test_event_id_matches_segment_asset_ids(tmp_path: Path) -> None:
    raw = json.loads(SYNTHETIC.read_text(encoding="utf-8"))
    trip = {
        "version": "0.2",
        "tripId": "schema-join",
        "templateId": "visual-journal",
        "exportLayout": "auto",
        "meta": {
            "title": "join",
            "dateStart": "2025-04-01",
            "dateEnd": "2025-04-10",
            "places": ["测试"],
            "tone": "relaxed",
        },
        "coverAssetId": raw["assets"][0]["id"],
        "assets": [dict(a) for a in raw["assets"]],
        "chapters": [],
        "privacy": {"mode": "private"},
        "pipeline": {"status": "structure_draft"},
        "createdAt": "2025-04-01T00:00:00Z",
        "updatedAt": "2025-04-01T00:00:00Z",
        "curation": {},
    }
    run_clustering_layer(trip, trip_dir=tmp_path / "join", cfg=AppConfig(clustering=ClusteringConfig(enabled="true")))
    segments = (trip.get("curation") or {}).get("clustering", {}).get("segments") or []
    if not segments:
        return
    seg_ids = {s["id"]: set(s.get("assetIds") or []) for s in segments}
    for asset in trip.get("assets") or []:
        eid = asset.get("eventId")
        if not eid:
            continue
        assert asset["id"] in seg_ids.get(eid, set())
