"""collect_asset_paths must not follow path traversal outside trip_root."""

from __future__ import annotations

from pathlib import Path

from travelogue.render.context import collect_asset_paths


def test_collect_asset_paths_skips_parent_traversal(tmp_path: Path) -> None:
    trip_root = tmp_path / "trip"
    assets = trip_root / "assets"
    assets.mkdir(parents=True)
    safe = assets / "ok.jpg"
    safe.write_bytes(b"ok")
    outside = tmp_path / "secret.jpg"
    outside.write_bytes(b"secret")

    trip = {
        "exportLayout": "mobile",
        "assets": [
            {"id": "a1", "displayFile": "assets/ok.jpg"},
            {"id": "a2", "displayFile": "../secret.jpg"},
            {"id": "a3", "displayFile": "/etc/passwd"},
        ],
        "chapters": [],
    }
    paths = collect_asset_paths(trip, trip_root)
    rels = {rel for rel, _ in paths}
    assert "assets/ok.jpg" in rels
    assert "../secret.jpg" not in rels
    assert "/etc/passwd" not in rels
    for _rel, abs_path in paths:
        abs_path.relative_to(trip_root.resolve())


def test_collect_asset_paths_skips_nested_dotdot(tmp_path: Path) -> None:
    trip_root = tmp_path / "trip"
    trip_root.mkdir()
    trip = {
        "exportLayout": "mobile",
        "assets": [{"id": "a1", "displayFile": "assets/../../outside.jpg"}],
        "chapters": [],
    }
    assert collect_asset_paths(trip, trip_root) == []
