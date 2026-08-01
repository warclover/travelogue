"""SFI D-SFI-07 · longshot on-disk names use display title (supersede FTUE D-FTUE-05)."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.export.longshot import (
    _longshot_file_stem,
    cleanup_legacy_longshot_outputs,
    default_longshot_output_name,
)


def test_longshot_file_stem_uses_display_title(tmp_path: Path) -> None:
    trip_dir = tmp_path / "demo-album"
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text(
        json.dumps(
            {
                "meta": {
                    # Ban-list title so resolve_display_title falls through to displayTitle.
                    "title": "示例游记",
                    "displayTitle": "京都雨季漫游",
                    "dateStart": "2024-05-27",
                    "dateEnd": "2024-05-29",
                },
                "tripId": "demo-album",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert _longshot_file_stem(trip_dir) == "京都雨季漫游"


def test_default_longshot_output_name_uses_chinese_display(tmp_path: Path) -> None:
    trip_dir = tmp_path / "demo-album"
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text(
        json.dumps(
            {
                "meta": {
                    "title": "示例游记",
                    "displayTitle": "京都雨季漫游",
                    "dateStart": "2024-05-27",
                    "dateEnd": "2024-05-29",
                },
                "tripId": "demo-album",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert default_longshot_output_name(trip_dir) == "京都雨季漫游-长图.png"
    assert (
        default_longshot_output_name(trip_dir, segment_index=1, segment_total=3)
        == "京都雨季漫游-长图-01.png"
    )
    name = default_longshot_output_name(trip_dir, segment_index=2, segment_total=3)
    assert "示例" not in name
    assert name.startswith("京都雨季漫游-长图-")


def test_cleanup_legacy_trip_id_outputs(tmp_path: Path) -> None:
    trip_dir = tmp_path / "demo-album"
    trip_dir.mkdir()
    legacy = trip_dir / "demo-album.png"
    legacy.write_bytes(b"x")
    keep_name = "京都雨季漫游-长图.png"
    (trip_dir / keep_name).write_bytes(b"y")
    removed = cleanup_legacy_longshot_outputs(trip_dir, keep={keep_name})
    assert "demo-album.png" in removed
    assert not legacy.exists()
    assert (trip_dir / keep_name).is_file()
