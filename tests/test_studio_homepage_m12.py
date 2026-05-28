"""Studio M12 homepage HTML / trips API smoke tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.web.studio_jobs import reset_job_store
from travelogue.web.studio_pipeline import run_studio_pipeline
from travelogue.web.studio_trips import list_studio_trips, studio_trips_total
from tests.test_studio_server import _distinct_album, _free_port, _get_json, _start_studio_server


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


M12_HOME_MARKERS = (
    "选择照片文件夹",
    "让每一段旅程",
    "studio-hero-magazine",
    "studio-gallery-carousel",
    "studio-import-error",
    "studio-toast.js",
    "studio-modal.js",
    "studio-gallery.js",
    "不知道选哪个文件夹",
    "每个文件夹会生成一篇",
    "demo-album/demo-01.jpg",
)


def test_studio_homepage_m12_html(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        import urllib.request

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10) as resp:
            html = resp.read().decode("utf-8")
        for marker in M12_HOME_MARKERS:
            assert marker in html, marker
    finally:
        server.shutdown()
        server.server_close()


def test_studio_homepage_m12_css() -> None:
    css_path = Path(__file__).resolve().parents[1] / "templates" / "studio" / "studio.css"
    css = css_path.read_text(encoding="utf-8")
    assert "sample-longshot.jpg" in css


def test_studio_homepage_js_strings() -> None:
    js_path = Path(__file__).resolve().parents[1] / "templates" / "studio" / "studio.js"
    js = js_path.read_text(encoding="utf-8")
    assert "浏览器上传" in js
    assert "\ufffd" not in js
    assert "Cancel: confirm first" in js
    assert "options.highlight" in js
    assert "tripsListLimit" in js
    assert "check();" in js


def test_studio_trips_api_limit_and_total(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    run_studio_pipeline(album, trips_dir=trips_dir, title="Limit test", dedupe=False)

    assert studio_trips_total(trips_dir) == 1
    assert len(list_studio_trips(trips_dir, limit=1)) == 1

    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        status, body = _get_json(f"http://127.0.0.1:{port}/__travelogue/trips?limit=1")
        assert status == 200
        assert body.get("total") == 1
        assert len(body.get("trips") or []) == 1
    finally:
        server.shutdown()
        server.server_close()
