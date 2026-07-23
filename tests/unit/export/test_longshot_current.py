"""QFX · longshot-current.json 读写合同（AC-25 最小）。"""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.export.longshot import (
    LONGSHOT_CURRENT_NAME,
    maybe_write_longshot_current_after_upload,
    read_longshot_current,
    write_longshot_current,
)


def test_write_read_longshot_current_roundtrip(tmp_path: Path) -> None:
    trip_dir = tmp_path / "t1"
    trip_dir.mkdir()
    (trip_dir / "京都-长图.png").write_bytes(b"png")
    path = write_longshot_current(
        trip_dir,
        batch_id="job-1",
        kind="whole",
        files=["京都-长图.png"],
    )
    assert path.name == LONGSHOT_CURRENT_NAME
    cur = read_longshot_current(trip_dir)
    assert cur is not None
    assert cur["batchId"] == "job-1"
    assert cur["kind"] == "whole"
    assert cur["files"] == ["京都-长图.png"]
    assert cur["schemaVersion"] == 1
    assert cur["createdAt"]


def test_read_longshot_current_rejects_orphan_files(tmp_path: Path) -> None:
    trip_dir = tmp_path / "t2"
    trip_dir.mkdir()
    (trip_dir / LONGSHOT_CURRENT_NAME).write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "batchId": "x",
                "createdAt": "2026-07-23T00:00:00Z",
                "kind": "whole",
                "files": ["missing-长图.png"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert read_longshot_current(trip_dir) is None


def test_maybe_write_after_upload_waits_for_full_segment_batch(tmp_path: Path) -> None:
    trip_dir = tmp_path / "t3"
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text(
        json.dumps({"meta": {"title": "分段册"}}, ensure_ascii=False),
        encoding="utf-8",
    )
    (trip_dir / "分段册-长图-01.png").write_bytes(b"1")
    assert (
        maybe_write_longshot_current_after_upload(
            trip_dir,
            rel="分段册-长图-01.png",
            segment_index=1,
            segment_total=2,
            fmt="png",
            batch_id="batch-seg",
        )
        is None
    )
    assert not (trip_dir / LONGSHOT_CURRENT_NAME).exists()
    (trip_dir / "分段册-长图-02.png").write_bytes(b"2")
    path = maybe_write_longshot_current_after_upload(
        trip_dir,
        rel="分段册-长图-02.png",
        segment_index=2,
        segment_total=2,
        fmt="png",
        batch_id="batch-seg",
    )
    assert path is not None
    cur = read_longshot_current(trip_dir)
    assert cur is not None
    assert cur["kind"] == "segmented"
    assert cur["files"] == ["分段册-长图-01.png", "分段册-长图-02.png"]
