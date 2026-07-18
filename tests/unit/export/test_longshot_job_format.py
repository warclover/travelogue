"""Dogfood UX Fixpack M2 · BE-DFX-20 job-level output format."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from travelogue.export.longshot import (
    MAX_WECHAT_BYTES,
    _capture_chapters_job_locked,
    purge_longshot_session_files,
)


def test_job_locked_format_upgrades_whole_batch_to_jpeg(tmp_path: Path) -> None:
    page = MagicMock()
    session_writes: list[Path] = []
    # Chapter 0 fits as PNG; chapter 1 is oversized → whole job becomes JPEG.
    png_ok = b"\x89PNG" + b"a" * 100
    png_big = b"\x89PNG" + b"b" * (MAX_WECHAT_BYTES + 10)
    jpeg_bytes = b"\xff\xd8\xff" + b"j" * 200

    calls: list[tuple[str, int]] = []

    def fake_capture(_page, *, scale, fmt, chapter_index=None):
        calls.append((fmt, int(chapter_index)))
        if fmt == "jpeg":
            return jpeg_bytes, "p0"
        if chapter_index == 1:
            return png_big, "p0"
        return png_ok, "p0"

    with patch("travelogue.export.longshot._capture_bytes", side_effect=fake_capture):
        with patch("travelogue.export.longshot._maybe_watermark", side_effect=lambda data, **k: data):
            job_fmt, job_ext, outputs, _method = _capture_chapters_job_locked(
                page,
                trip_dir=tmp_path,
                title="demo",
                chapter_count=2,
                scale=2,
                fmt="png",
                ext="png",
                watermark=False,
                cancel_check=None,
                progress=None,
                session_writes=session_writes,
            )

    assert job_fmt == "jpeg"
    assert job_ext == "jpg"
    assert len(outputs) == 2
    assert all(p.path.suffix == ".jpg" for p in outputs)
    assert all(p.path.is_file() for p in outputs)
    # No leftover PNGs from the aborted first pass
    assert list(tmp_path.glob("*.png")) == []
    assert ("jpeg", 0) in calls and ("jpeg", 1) in calls


def test_purge_session_files_removes_partials(tmp_path: Path) -> None:
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    a.write_bytes(b"x")
    b.write_bytes(b"y")
    assert purge_longshot_session_files([a, b]) == 2
    assert not a.exists()
    assert not b.exists()
