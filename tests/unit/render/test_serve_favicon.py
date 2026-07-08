"""Local preview server favicon handling."""

from __future__ import annotations

from travelogue.web.serve import FAVICON_SILENT_PATHS


def test_favicon_paths_include_ico_and_svg() -> None:
    assert "/favicon.ico" in FAVICON_SILENT_PATHS
    assert "/favicon.svg" in FAVICON_SILENT_PATHS
