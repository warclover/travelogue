"""Tests for D-INS-10 version mapping."""

from __future__ import annotations

from scripts.gen_studio_version_info import parse_marketing_version, render_version_info


def test_parse_beta_version() -> None:
    marketing, fv = parse_marketing_version("0.2.0-beta.1\n")
    assert marketing == "0.2.0-beta.1"
    assert fv == (0, 2, 0, 1)


def test_render_contains_file_version() -> None:
    text = render_version_info("0.2.0-beta.1", (0, 2, 0, 1))
    assert "filevers=(0, 2, 0, 1)" in text
    assert "FileVersion', '0.2.0.1'" in text
    assert "ProductVersion', '0.2.0-beta.1'" in text
