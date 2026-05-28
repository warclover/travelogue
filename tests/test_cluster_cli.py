"""M14 · cluster cache CLI."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from travelogue.cli import app
from travelogue.vision.cache import CACHE_DIR_NAME, EMBEDDINGS_FILE, save_embedding_cache


def test_cluster_cache_clear(tmp_path: Path) -> None:
    trip_dir = tmp_path / "demo"
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text(
        json.dumps({"tripId": "demo", "assets": [], "chapters": []}),
        encoding="utf-8",
    )
    import numpy as np

    save_embedding_cache(
        trip_dir,
        asset_ids=["a1"],
        vectors=np.array([[1.0, 0.0]], dtype=np.float32),
        source="heuristic",
    )
    cache_file = trip_dir / CACHE_DIR_NAME / EMBEDDINGS_FILE
    assert cache_file.is_file()

    runner = CliRunner()
    result = runner.invoke(app, ["cluster", "cache-clear", str(trip_dir / "trip.json")])
    assert result.exit_code == 0
    assert "cleared" in result.stdout.lower() or "cache" in result.stdout.lower()
    assert not cache_file.is_file()


def test_cluster_pending_assets_empty(tmp_path: Path) -> None:
    trip_dir = tmp_path / "t1"
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text(
        json.dumps(
            {
                "tripId": "t1",
                "pipeline": {"status": "structure_draft", "pendingAssets": []},
                "assets": [],
                "chapters": [],
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(app, ["cluster", "pending-assets", str(trip_dir / "trip.json")])
    assert result.exit_code == 0
    assert "no pending" in result.stdout.lower()
