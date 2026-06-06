"""P1 error-path tests: corrupt trip.json, upload path traversal, LLM URL retry."""

from __future__ import annotations

import io
import json
import urllib.error
from unittest.mock import patch

import pytest

from travelogue.llm.client import LlmRuntime, _url_error_code, chat_completion
from travelogue.llm.errors import LlmError
from travelogue.services.trip import TripNotFoundError, TripService
from travelogue.services.validate import load_json
from travelogue.web.studio_uploads import save_upload_files


def test_load_json_rejects_invalid_json(tmp_path) -> None:
    path = tmp_path / "trip.json"
    path.write_text("{not-valid-json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        load_json(path)


def test_trip_service_load_invalid_json(tmp_path) -> None:
    path = tmp_path / "trip.json"
    path.write_text('{"tripId": ', encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        TripService().load(path)


def test_trip_service_load_missing_file(tmp_path) -> None:
    with pytest.raises(TripNotFoundError):
        TripService().load(tmp_path / "missing.json")


def test_save_upload_files_strips_path_traversal(tmp_path) -> None:
    upload_dir = tmp_path / "job-1"
    upload_dir.mkdir()
    saved = save_upload_files(
        upload_dir,
        [
            ("../../etc/passwd", b"x"),
            ("photos/ok.jpg", b"ok"),
        ],
    )
    assert saved == 1
    assert (upload_dir / "photos" / "ok.jpg").is_file()
    assert not (tmp_path / "etc").exists()


def test_url_error_code_timeout_vs_refused() -> None:
    timeout_exc = urllib.error.URLError(TimeoutError("timed out"))
    assert _url_error_code(timeout_exc) == "E_LLM_TIMEOUT"
    refused_exc = urllib.error.URLError(ConnectionRefusedError(111, "refused"))
    assert _url_error_code(refused_exc) == "E_LLM_CONNECT"


def test_chat_completion_retries_transient_url_error() -> None:
    rt = LlmRuntime(
        provider="deepseek",
        model="deepseek-chat",
        api_key="test-key",
        base_url="https://example.invalid/v1",
        timeout_sec=5,
    )
    ok_body = json.dumps(
        {"choices": [{"message": {"content": '{"ok": true}'}}]}
    ).encode("utf-8")
    calls: list[int] = []

    def fake_urlopen(req, timeout=0):
        calls.append(1)
        if len(calls) < 2:
            raise urllib.error.URLError(TimeoutError("timed out"))
        return io.BytesIO(ok_body)

    with patch("travelogue.llm.client.urllib.request.urlopen", fake_urlopen):
        with patch("travelogue.llm.client.time.sleep"):
            out = chat_completion([{"role": "user", "content": "hi"}], runtime=rt)
    assert out == '{"ok": true}'
    assert len(calls) == 2


def test_chat_completion_no_retry_on_connection_refused() -> None:
    rt = LlmRuntime(
        provider="deepseek",
        model="deepseek-chat",
        api_key="test-key",
        base_url="https://example.invalid/v1",
        timeout_sec=5,
    )

    def fake_urlopen(req, timeout=0):
        raise urllib.error.URLError(ConnectionRefusedError(111, "refused"))

    with patch("travelogue.llm.client.urllib.request.urlopen", fake_urlopen):
        with pytest.raises(LlmError, match="E_LLM_CONNECT"):
            chat_completion([{"role": "user", "content": "hi"}], runtime=rt)
