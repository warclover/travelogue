"""Unit tests for Studio config/static handlers."""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import patch

import pytest

from travelogue.web.studio_handlers.config_handlers import handle_config, handle_pick_folder
from travelogue.web.studio_handlers.static_handlers import (
    handle_home,
    handle_home_root,
    handle_studio_asset,
)
from travelogue.web.studio_handlers.paths import STUDIO_ASSET_PREFIX
from tests.studio_test_helpers import MockStudioHandler

pytestmark = pytest.mark.unit


class MockStaticHandler:
    """Minimal handler stub for static asset/home handlers."""

    def __init__(
        self,
        *,
        studio_token: str = "test-token",
        studio_host: str = "127.0.0.1",
        request_headers: dict[str, str] | None = None,
    ) -> None:
        self.studio_token = studio_token
        self.studio_host = studio_host
        self.request_headers = request_headers or {}
        self.status: int | None = None
        self.headers: dict[str, str] = {}
        self.body = io.BytesIO()
        self.error_code: int | None = None
        self.path = "/"

    def send_response(self, code: int) -> None:
        self.status = code

    def send_header(self, key: str, value: str) -> None:
        self.headers[key] = value

    def end_headers(self) -> None:
        pass

    def send_error(self, code: int, *_args, **_kwargs) -> None:
        self.error_code = code

    @property
    def wfile(self) -> io.BytesIO:
        return self.body


def test_handle_config_get_returns_exposed_config(tmp_path: Path) -> None:
    handler = MockStudioHandler(tmp_path / "trips")
    handler.command = "GET"
    handle_config(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["ok"] is True
    assert "studio" in body
    assert "pipelineEstimates" in body
    assert "capabilities" in body
    assert "pickFolder" in body["capabilities"]


def test_studio_capabilities_win32_loopback() -> None:
    from travelogue.web.studio_handlers.config_handlers import studio_capabilities

    caps = studio_capabilities(client_host="127.0.0.1")
    assert "pickFolder" in caps
    assert caps["pickFolder"] is ( __import__("sys").platform == "win32")
    assert studio_capabilities(client_host="203.0.113.1")["pickFolder"] is False


def test_handle_config_patch_empty_body(tmp_path: Path) -> None:
    handler = MockStudioHandler(tmp_path / "trips", json_body={})
    handler.command = "PATCH"
    handle_config(handler)
    assert handler.response == (400, {"ok": False, "error": "empty body"})


def test_handle_config_patch_invalid_value(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("studio: {}\n", encoding="utf-8")
    handler = MockStudioHandler(tmp_path / "trips", json_body={"bad": object()})
    handler.command = "PATCH"
    handler.studio_config_path = cfg_path
    with patch(
        "travelogue.web.studio_handlers.config_handlers.patch_config_file",
        side_effect=ValueError("invalid patch"),
    ):
        handle_config(handler)
    assert handler.response == (400, {"ok": False, "error": "invalid patch"})


def test_handle_config_patch_write_error(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    handler = MockStudioHandler(tmp_path / "trips", json_body={"studio": {"g1ConfirmStructure": True}})
    handler.command = "PATCH"
    handler.studio_config_path = cfg_path
    with patch(
        "travelogue.web.studio_handlers.config_handlers.patch_config_file",
        side_effect=PermissionError("denied"),
    ):
        handle_config(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 500
    assert body["error"] == "E_STUDIO_CONFIG_WRITE"


def test_handle_config_patch_success(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("studio: {}\n", encoding="utf-8")
    handler = MockStudioHandler(
        tmp_path / "trips",
        json_body={"studio": {"g1ConfirmStructure": True}},
    )
    handler.command = "PATCH"
    handler.studio_config_path = cfg_path
    with patch("travelogue.web.studio_handlers.config_handlers.patch_config_file"):
        handle_config(handler)
    assert handler.response is not None
    assert handler.response[0] == 200
    assert handler.response[1]["ok"] is True


def test_handle_pick_folder_denied_off_loopback(tmp_path: Path) -> None:
    handler = MockStudioHandler(tmp_path / "trips")
    handler.client_address = ("203.0.113.1", 12345)
    handle_pick_folder(handler)
    assert handler.response is not None
    assert handler.response[0] == 403
    assert handler.response[1]["error"] == "E_PICK_FOLDER_DENIED"


def test_handle_pick_folder_unsupported_platform(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import sys

    handler = MockStudioHandler(tmp_path / "trips")
    handler.client_address = ("127.0.0.1", 12345)
    monkeypatch.setattr(sys, "platform", "linux")
    handle_pick_folder(handler)
    assert handler.response is not None
    assert handler.response[0] == 501
    assert handler.response[1]["error"] == "E_PICK_FOLDER_UNSUPPORTED"


def test_handle_pick_folder_cancelled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import sys

    from travelogue.desktop.folder_picker_service import FolderPickResult

    handler = MockStudioHandler(tmp_path / "trips")
    handler.client_address = ("127.0.0.1", 12345)
    monkeypatch.setattr(sys, "platform", "win32")
    with patch(
        "travelogue.desktop.folder_picker_service.request_folder",
        return_value=FolderPickResult(cancelled=True),
    ):
        handle_pick_folder(handler)
    assert handler.response == (200, {"ok": True, "cancelled": True})


def test_handle_home_injects_token() -> None:
    handler = MockStaticHandler(studio_token="abc123")
    handle_home(handler)
    assert handler.status == 200
    html = handler.body.getvalue().decode("utf-8")
    assert "abc123" in html
    assert "__STUDIO_TOKEN__" not in html


def test_handle_studio_asset_serves_existing_file() -> None:
    handler = MockStaticHandler()
    path = f"{STUDIO_ASSET_PREFIX}studio-home-v2.css"
    handled = handle_studio_asset(handler, path)
    assert handled is True
    assert handler.status == 200
    assert handler.headers.get("Content-Type", "").startswith("text/css")
    assert len(handler.body.getvalue()) > 0


def test_handle_studio_asset_rejects_traversal() -> None:
    handler = MockStaticHandler()
    path = f"{STUDIO_ASSET_PREFIX}../studio-home-v2.html"
    handled = handle_studio_asset(handler, path)
    assert handled is True
    assert handler.error_code == 404


def test_handle_studio_asset_missing_file() -> None:
    handler = MockStaticHandler()
    path = f"{STUDIO_ASSET_PREFIX}missing-file-xyz.css"
    handled = handle_studio_asset(handler, path)
    assert handled is True
    assert handler.error_code == 404


def test_handle_studio_asset_cache_headers_loopback() -> None:
    handler = MockStaticHandler(studio_host="127.0.0.1")
    path = f"{STUDIO_ASSET_PREFIX}studio-home-v2.css"
    handled = handle_studio_asset(handler, path)
    assert handled is True
    assert handler.status == 200
    assert handler.headers.get("Cache-Control") == "no-cache"
    assert handler.headers.get("ETag", "").startswith('W/"')


def test_handle_studio_asset_cache_headers_lan() -> None:
    handler = MockStaticHandler(studio_host="192.168.1.5")
    path = f"{STUDIO_ASSET_PREFIX}studio-home-v2.css"
    handled = handle_studio_asset(handler, path)
    assert handled is True
    assert handler.headers.get("Cache-Control") == "public, max-age=3600"


def test_handle_studio_asset_not_modified() -> None:
    handler = MockStaticHandler(studio_host="127.0.0.1")
    path = f"{STUDIO_ASSET_PREFIX}studio-home-v2.css"
    handle_studio_asset(handler, path)
    etag = handler.headers.get("ETag")
    assert etag

    handler2 = MockStaticHandler(
        studio_host="127.0.0.1",
        request_headers={"If-None-Match": etag},
    )
    handled = handle_studio_asset(handler2, path)
    assert handled is True
    assert handler2.status == 304


def test_handle_home_root_delegates_gate(monkeypatch) -> None:
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "off")
    handler = MockStaticHandler()
    handler.path = "/"
    assert handle_home_root(handler) is True
    assert handler.status == 200
    html = handler.body.getvalue().decode("utf-8")
    assert 'data-studio-v="4"' in html
