"""FTUE D-FTUE-05 · longshot on-disk names use tripId, not Chinese title."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.export.longshot import (
    _longshot_file_stem,
    default_longshot_output_name,
)


def test_longshot_file_stem_uses_trip_dir_name() -> None:
    trip_dir = Path("C:/tmp/trips/demo-album")
    assert _longshot_file_stem(trip_dir) == "demo-album"


def test_default_longshot_output_name_ignores_chinese_title(tmp_path: Path) -> None:
    trip_dir = tmp_path / "demo-album"
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text(
        json.dumps(
            {"meta": {"title": "示例京都"}, "tripId": "demo-album"},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert default_longshot_output_name(trip_dir) == "demo-album.png"
    assert (
        default_longshot_output_name(
            trip_dir, segment_index=1, segment_total=3
        )
        == "demo-album-ch01.png"
    )
    # Must not embed mojibake / Chinese title in basename
    name = default_longshot_output_name(trip_dir, segment_index=2, segment_total=3)
    assert "示例" not in name
    assert "京都" not in name
    assert name.startswith("demo-album-")
