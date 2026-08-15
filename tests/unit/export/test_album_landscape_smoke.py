"""ALS optional Playwright smoke · skip when Chromium is unavailable."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def _have_playwright() -> bool:
    try:
        import playwright  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _have_playwright(), reason="Playwright 未安装")
def test_album_landscape_smoke_index_html(tmp_path: Path) -> None:
    from PIL import Image

    from travelogue.export.album_landscape import OUTPUT_H, OUTPUT_W, export_album_landscape
    from travelogue.export.longshot import LongshotExportError
    from tests.unit.export.test_album_landscape import FIXTURE_HTML, _seed_screens_trip

    trip_dir = _seed_screens_trip(tmp_path / "trips", "als-smoke", FIXTURE_HTML)
    try:
        result = export_album_landscape(trip_dir, trip_id="als-smoke")
    except LongshotExportError as exc:
        if exc.code == "E_LNG_PLAYWRIGHT":
            pytest.skip("Chromium 不可用")
        raise
    assert result.page_count and result.page_count > 0
    for item in result.outputs:
        img = Image.open(item.path)
        assert img.size[0] / img.size[1] == pytest.approx(16 / 9, rel=0.01)
        assert img.size == (OUTPUT_W, OUTPUT_H)
        assert "-landscape-" in item.path.name
