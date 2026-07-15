"""NR-P2-02 · non-studio serve matches MVP behavior."""

from __future__ import annotations

import threading
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib import error, request

import pytest

from tests.integration.studio.test_studio_server import _distinct_album, _free_port
from travelogue.web.serve import TripPreviewHandler
from travelogue.web.studio_pipeline import run_studio_pipeline


def _start_mvp_server(trip_dir: Path, port: int) -> ThreadingHTTPServer:
    handler = partial(
        TripPreviewHandler,
        directory=str(trip_dir),
        trip_json=trip_dir / "trip.json",
        studio_mode=False,
    )
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_non_studio_serve_no_preview_toolbar(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    result = run_studio_pipeline(
        album,
        trips_dir=trips_dir,
        title="MVP",
        place="测试",
        dedupe=False,
    )
    trip_dir = trips_dir / result.trip_id
    port = _free_port()
    server = _start_mvp_server(trip_dir, port)
    base = f"http://127.0.0.1:{port}"

    try:
        with request.urlopen(f"{base}/index.html", timeout=10) as resp:
            html = resp.read().decode("utf-8")
        assert "preview-toolbar.js" not in html
        assert 'data-preview-toolbar="on"' not in html

        with pytest.raises(error.HTTPError) as exc:
            request.urlopen(f"{base}/__travelogue/trips", timeout=5)
        assert exc.value.code == 404
    finally:
        server.shutdown()
        server.server_close()


def test_studio_config_stub_llm_unavailable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from travelogue.config import AppConfig
    from travelogue.llm.user_settings import UserLlmSecrets

    monkeypatch.setattr(
        "travelogue.llm.user_settings.read_user_llm_secrets",
        lambda: UserLlmSecrets(),
    )

    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    cfg = AppConfig()
    cfg.llm.provider = "stub"
    handler = partial(
        TripPreviewHandler,
        directory=str(trips_dir),
        trip_json=trips_dir / ".placeholder" / "trip.json",
        studio_mode=True,
        trips_dir=trips_dir,
        studio_host="127.0.0.1",
        studio_port=port,
        app_config=cfg,
    )
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        with request.urlopen(f"http://127.0.0.1:{port}/__travelogue/config", timeout=5) as resp:
            body = __import__("json").loads(resp.read().decode("utf-8"))
        assert body.get("ok") is True
        assert body.get("llmAvailable") is False
        assert body.get("llmProvider") == "stub"
        assert body.get("clustering", {}).get("enabled") == "auto"
        assert body.get("vision", {}).get("enabled") == "false"
    finally:
        server.shutdown()
        server.server_close()
