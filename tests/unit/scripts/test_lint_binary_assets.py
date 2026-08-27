"""B-04 binary asset signature helper."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lint_binary_assets import classify_bytes, expected_kind, scan

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
