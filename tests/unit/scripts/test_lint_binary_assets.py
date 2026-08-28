"""B-04 binary asset signature helper."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lint_binary_assets import (
    classify_bytes,
    expected_kind,
    issue_rel_key,
    partition_issues,
    scan,
)

pytestmark = pytest.mark.unit


def test_classify_known_signatures() -> None:
    assert classify_bytes(b"\x89PNG\r\n\x1a\nxxxx") == "png"
    assert classify_bytes(b"\xff\xd8\xff\xe0xxxx") == "jpeg"
    assert classify_bytes(b"RIFF\x00\x00\x00\x00WEBP") == "webp"
    assert classify_bytes(b"not-an-image") is None


def test_scan_reports_extension_mismatch(tmp_path: Path) -> None:
    jpeg = tmp_path / "shot.png"
    jpeg.write_bytes(b"\xff\xd8\xff\xe0xxxx")
    issues = scan([jpeg])
    assert issues
    assert "jpeg" in issues[0]
    assert expected_kind(".png") == "png"


def test_abandoned_paths_are_partitioned(tmp_path: Path) -> None:
    bad = tmp_path / "docs" / "old.png"
    bad.parent.mkdir()
    bad.write_bytes(b"not-an-image")
    fresh = tmp_path / "docs" / "new.png"
    fresh.write_bytes(b"also-bad")
    issues = scan([bad, fresh])
    signed, new = partition_issues(
        issues,
        root=tmp_path,
        abandoned={"docs/old.png"},
    )
    assert len(signed) == 1
    assert len(new) == 1
    assert issue_rel_key(new[0], root=tmp_path) == "docs/new.png"
