"""Unified demo build uses official pipeline stages."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from travelogue.demo.build import run_demo_from_album


def _album(tmp_path: Path, n: int = 6) -> Path:
    album = tmp_path / "album"
    album.mkdir()
    for i in range(n):
        Image.new("RGB", (1200, 1600), (30 + i * 17, 50, 70)).save(
            album / f"p{i:02d}.jpg", quality=95
        )
    return album


def test_run_demo_stages(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    result = run_demo_from_album(
        _album(tmp_path),
        trips_dir=trips,
        trip_id="demo-stages",
        title="阶段测试",
        dedupe=False,
    )
    assert result.stages == ["ingest", "curate", "render"]
    assert result.trip_json.is_file()
    assert result.index_html.is_file()
    import json

    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    assert trip["pipeline"]["status"] == "rendered"
