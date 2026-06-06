"""Studio Chrome allowlist injection (M8b)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.test_studio_server import _distinct_album, _free_port, _get_json, _start_studio_server
from travelogue.web.studio_chrome import inject_studio_chrome, should_inject_studio_chrome
from travelogue.web.studio_jobs import reset_job_store
from travelogue.web.studio_pipeline import run_studio_pipeline


def test_should_inject_allowlist() -> None:
    assert should_inject_studio_chrome("index.html")
    assert should_inject_studio_chrome("index-mobile.html")
    assert should_inject_studio_chrome("index-longshot.html")
    assert not should_inject_studio_chrome("longshot.css")


def test_share_query_still_injects_minimal_chrome() -> None:
    assert should_inject_studio_chrome("index.html", "share=1")
    assert should_inject_studio_chrome("index.html", "mode=share&foo=1")
    assert should_inject_studio_chrome("index.html", "focus=longshot")


def test_inject_studio_chrome_share_mode() -> None:
    html = "<html><body><main>hi</main></body></html>"
    out = inject_studio_chrome(html, share_mode=True)
    assert 'data-preview-share="on"' in out
    assert 'data-preview-toolbar="on"' not in out
    assert "/__studio/preview-toolbar.js" in out


def test_inject_studio_chrome_adds_script() -> None:
    html = "<html><body><main>hi</main></body></html>"
    out = inject_studio_chrome(html)
    assert 'data-preview-toolbar="on"' in out
    assert "/__studio/preview-toolbar.js" in out
    assert "/__studio/preview-toolbar.css" in out
    assert "/__studio/studio-modal.js" in out
    assert 'type="module" src="/__studio/preview-toolbar.js"' in out
    assert "/__studio/studio-api.js" not in out


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


@pytest.mark.e2e
def test_studio_home_html(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        import urllib.request

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10) as resp:
            html = resp.read().decode("utf-8")
        assert "Travelogue Studio" in html
        assert 'data-homepage-variant="v2"' in html
        assert "/__studio/homepage-v2/bootstrap.js" in html
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_chrome_on_index_and_longshot(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()

    result = run_studio_pipeline(
        album,
        trips_dir=trips_dir,
        title="测试",
        place="测试",
        dedupe=False,
    )

    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"

    try:
        import urllib.request

        with urllib.request.urlopen(f"{base}/{result.trip_id}/index.html", timeout=10) as resp:
            index_html = resp.read().decode("utf-8")
        with urllib.request.urlopen(
            f"{base}/{result.trip_id}/index-longshot.html", timeout=10
        ) as resp:
            longshot_html = resp.read().decode("utf-8")

        assert "preview-toolbar.js" in index_html
        assert 'type="module" src="/__studio/preview-toolbar.js"' in index_html
        assert "studio-api.js" not in index_html
        assert 'data-preview-toolbar="on"' in index_html
        assert "preview-toolbar.js" in longshot_html
        assert 'data-preview-toolbar="on"' in longshot_html
        assert 'data-block="surface-nav"' in longshot_html
        assert "← 返回卷轴" in longshot_html

        with urllib.request.urlopen(
            f"{base}/{result.trip_id}/index.html?share=1", timeout=10
        ) as resp:
            share_html = resp.read().decode("utf-8")
        assert "preview-toolbar.js" in share_html
        assert 'data-preview-share="on"' in share_html
        assert 'data-preview-toolbar="on"' not in share_html
        assert "footer-cta__studio-home" in share_html
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_trips_list(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    run_studio_pipeline(album, trips_dir=trips_dir, dedupe=False)

    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        status, body = _get_json(f"http://127.0.0.1:{port}/__travelogue/trips")
        assert status == 200
        assert body.get("trips")
        assert body.get("total") is not None
        assert body["trips"][0].get("tripId")
        assert body["trips"][0].get("previewUrl", "").endswith("/index.html")
    finally:
        server.shutdown()
        server.server_close()
