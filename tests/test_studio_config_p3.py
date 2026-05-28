"""Studio config API · Phase 3 M12-7 (UX-P3-03)."""

from __future__ import annotations

import json
import threading
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib import request

import yaml

from travelogue.config import AppConfig
from travelogue.web.serve import TripPreviewHandler
from tests.test_studio_server import _free_port


def _start_studio_with_config(
    trips_dir: Path,
    port: int,
    *,
    config_path: Path,
    app_config: AppConfig | None = None,
) -> ThreadingHTTPServer:
    cfg = app_config or AppConfig()
    handler = partial(
        TripPreviewHandler,
        directory=str(trips_dir),
        trip_json=trips_dir / ".placeholder" / "trip.json",
        studio_mode=True,
        trips_dir=trips_dir,
        studio_host="127.0.0.1",
        studio_port=port,
        app_config=cfg,
        studio_config_path=config_path,
    )
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _patch_json(url: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    with request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode("utf-8")
        return resp.status, json.loads(body) if body else {}


def test_studio_config_get_exposes_clustering(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {"clustering": {"enabled": "auto"}, "vision": {"enabled": "false"}},
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    port = _free_port()
    server = _start_studio_with_config(trips_dir, port, config_path=config_path)
    try:
        with request.urlopen(f"http://127.0.0.1:{port}/__travelogue/config", timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        assert body.get("ok") is True
        assert body.get("clustering", {}).get("enabled") == "auto"
        assert body.get("vision", {}).get("enabled") == "false"
    finally:
        server.shutdown()
        server.server_close()


def test_studio_config_patch_persists_yaml(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    config_path = tmp_path / "config.yaml"
    config_path.write_text("trips_dir: ./trips\n", encoding="utf-8")
    port = _free_port()
    server = _start_studio_with_config(trips_dir, port, config_path=config_path)
    try:
        status, body = _patch_json(
            f"http://127.0.0.1:{port}/__travelogue/config",
            {"clustering": {"enabled": "false"}, "vision": {"enabled": "auto"}},
        )
        assert status == 200
        assert body.get("ok") is True
        assert body.get("clustering", {}).get("enabled") == "false"
        assert body.get("vision", {}).get("enabled") == "auto"

        saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert saved["clustering"]["enabled"] == "false"
        assert saved["vision"]["enabled"] == "auto"
    finally:
        server.shutdown()
        server.server_close()
