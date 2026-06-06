"""Shared helpers for Studio handler and HTTP integration tests."""

from __future__ import annotations

import io
import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib import error, request

from PIL import Image

from travelogue.config import get_config
from travelogue.runtime import AppContext


def make_test_album(base: Path, n: int = 6, *, name: str = "album") -> Path:
    """Create a small JPEG album under ``base`` (shared by pipeline fixtures)."""
    album = base / name
    album.mkdir(parents=True, exist_ok=True)
    stamp = time.time() - n * 10
    for i in range(n):
        path = album / f"p{i:02d}.jpg"
        Image.new("RGB", (2400, 3200), (30 + i * 17, 50 + i * 11, 70 + i * 13)).save(
            path, quality=95
        )
        ts = stamp + i * 10
        os.utime(path, (ts, ts))
    return album


@dataclass(frozen=True)
class IngestedTripWorkspace:
    trips_dir: Path
    trip_id: str
    trip_dir: Path
    trip_json: Path


class MockStudioHandler:
    """Minimal handler stub for direct studio_handlers unit tests."""

    def __init__(
        self,
        trips_dir: Path,
        *,
        json_body: dict | None = None,
        headers: dict[str, str] | None = None,
        body: bytes = b"",
        studio_host: str = "127.0.0.1",
        studio_allow_lan: bool = False,
        path: str = "/",
    ) -> None:
        self.trips_dir = trips_dir.resolve()
        self.trips_dir.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.trip_json_path: Path | None = None
        self.studio_host = studio_host
        self.studio_port = 8766
        self.studio_allow_lan = studio_allow_lan
        self.studio_config_path: Path | None = None
        self.app_config = get_config()
        self.headers = dict(headers or {})
        self.rfile = io.BytesIO(body)
        self._json_body = dict(json_body or {})
        self.response: tuple[int, dict] | None = None
        self.command = "GET"
        self.client_address: tuple[str, int] = ("127.0.0.1", 0)

    def _json_response(self, status: int, body: dict) -> None:
        self.response = (status, body)

    def _read_json_body(self) -> dict | None:
        if not self._json_body:
            return None
        return dict(self._json_body)


def studio_handler_ctx(handler: MockStudioHandler) -> AppContext:
    return AppContext(cfg=handler.app_config, trips_root=handler.trips_dir)


def wait_for_job(
    fetch: Callable[[], dict],
    *,
    timeout_sec: float = 120,
    poll_sec: float = 0.05,
    terminal: frozenset[str] = frozenset({"succeeded", "failed", "cancelled"}),
) -> dict:
    """Poll job status until terminal state or timeout."""
    deadline = time.time() + timeout_sec
    last: dict = {}
    while time.time() < deadline:
        last = fetch()
        if last.get("status") in terminal:
            return last
        time.sleep(poll_sec)
    return last


def post_json(url: str, payload: dict, *, timeout: float = 30) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body) if body else {}


def get_json(url: str, *, timeout: float = 30) -> tuple[int, dict]:
    with request.urlopen(url, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return resp.status, json.loads(body) if body else {}
