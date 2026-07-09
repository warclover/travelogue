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


def test_cluster_process_pending_no_op_when_empty(tmp_path: Path) -> None:
    trip_dir = tmp_path / "p0"
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text(
        json.dumps(
            {
                "tripId": "p0",
                "pipeline": {
                    "status": "structure_locked",
                    "pendingAssets": [],
                    "locks": {"structure": True, "copy": False},
                },
                "assets": [],
                "chapters": [],
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(
        app, ["cluster", "process-pending", str(trip_dir / "trip.json")]
    )
    assert result.exit_code == 0, result.stdout
    assert "no pending assets" in result.stdout.lower()


def test_cluster_process_pending_drains_list_without_run(tmp_path: Path) -> None:
    trip_dir = tmp_path / "p1"
    trip_dir.mkdir()
    pending = ["a-001", "a-002", "a-003"]
    (trip_dir / "trip.json").write_text(
        json.dumps(
            {
                "tripId": "p1",
                "pipeline": {
                    "status": "structure_locked",
                    "pendingAssets": pending,
                    "locks": {"structure": True, "copy": False},
                },
                "assets": [],
                "chapters": [],
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()
    # --no-run skips scene clustering so this test does not depend on torch/open_clip.
    result = runner.invoke(
        app,
        [
            "cluster",
            "process-pending",
            str(trip_dir / "trip.json"),
            "--no-run",
            "--clear",
        ],
    )
    assert result.exit_code == 0, result.stdout
    body = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    pipe = body["pipeline"]
    assert pipe["pendingAssets"] == [], "pendingAssets must be empty after --clear"
    assert pipe["status"] == "structure_locked", "status must not change"
    assert pipe["locks"] == {"structure": True, "copy": False}
    assert "pending=3" in result.stdout
    assert "cleared=3" in result.stdout
    assert "cluster_mode=skipped" in result.stdout


def test_cluster_process_pending_keep_preserves_list(tmp_path: Path) -> None:
    trip_dir = tmp_path / "p2"
    trip_dir.mkdir()
    pending = ["x-001", "x-002"]
    (trip_dir / "trip.json").write_text(
        json.dumps(
            {
                "tripId": "p2",
                "pipeline": {
                    "status": "structure_locked",
                    "pendingAssets": pending,
                    "locks": {"structure": True, "copy": False},
                },
                "assets": [],
                "chapters": [],
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "cluster",
            "process-pending",
            str(trip_dir / "trip.json"),
            "--no-run",
            "--keep",
        ],
    )
    assert result.exit_code == 0, result.stdout
    body = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    assert body["pipeline"]["pendingAssets"] == pending, "--keep must preserve the list"
    assert "cleared=0" in result.stdout
