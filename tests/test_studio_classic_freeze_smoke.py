"""Classic freeze emergency homepage smoke (GET /classic · M21-e2)."""

from __future__ import annotations

import urllib.request
from pathlib import Path

import pytest

from tests.test_studio_server import _free_port, _start_studio_server

pytestmark = [pytest.mark.e2e, pytest.mark.legacy_homepage]


@pytest.mark.e2e
def test_classic_freeze_page_markers(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/classic", timeout=10) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
        assert "Classic 首页（Deprecated）" in html
        assert 'id="classic-album-path"' in html
        assert "/__studio/legacy-freeze/studio.classic.js" in html
        assert "studio-home-v2.css" not in html
    finally:
        server.shutdown()
        server.server_close()
