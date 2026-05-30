"""Typing protocol for Studio HTTP handler (BaseHTTPRequestHandler + StudioMixin)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from travelogue.config import AppConfig


class StudioHandlerProtocol(Protocol):
    command: str
    path: str
    headers: Any
    wfile: Any
    studio_mode: bool
    studio_token: str | None
    studio_host: str
    studio_port: int
    studio_allow_lan: bool
    studio_config_path: Path | None
    trips_dir: Path | None
    trip_json_path: Path | None
    app_config: AppConfig | None

    def send_response(self, code: int, message: str | None = None) -> None: ...
    def send_header(self, keyword: str, value: str) -> None: ...
    def end_headers(self) -> None: ...
    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None: ...

    def _read_json_body(self) -> dict[str, Any] | None: ...
    def _json_response(self, code: int, payload: dict[str, Any]) -> None: ...
