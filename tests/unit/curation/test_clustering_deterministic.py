"""AC-P3-C08 · clustering output deterministic on same fixture."""



from __future__ import annotations
from tests._repo_root import repo_root

import hashlib
import json
from pathlib import Path

from travelogue.config import AppConfig, ClusteringConfig
from travelogue.curation.clustering import run_clustering_layer

ROOT = repo_root(__file__)
FIXTURE = ROOT / "tests" / "fixtures" / "clustering" / "synthetic-gps" / "assets-manifest.json"


def _cluster_hash(trip: dict) -> str:
    blob = json.dumps(trip.get("curation", {}).get("clustering", {}), sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def test_clustering_double_run_same_hash(tmp_path) -> None:
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assets = raw["assets"]
    cfg = AppConfig(clustering=ClusteringConfig(enabled="true"))

    trip_a = {"assets": [dict(a) for a in assets], "curation": {}}
    trip_b = {"assets": [dict(a) for a in assets], "curation": {}}
    run_clustering_layer(trip_a, trip_dir=tmp_path / "a", cfg=cfg)
    run_clustering_layer(trip_b, trip_dir=tmp_path / "b", cfg=cfg)
    assert _cluster_hash(trip_a) == _cluster_hash(trip_b)
