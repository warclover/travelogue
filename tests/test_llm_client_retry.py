"""LLM client retry and URL error classification (offline)."""

from __future__ import annotations

import io
import json
import urllib.error
from unittest.mock import patch

import pytest

from travelogue.llm.client import LlmRuntime, _url_error_code, chat_completion
from travelogue.llm.errors import LlmError


def test_url_error_code_distinguishes_refused() -> None:
    exc = urllib.error.URLError(ConnectionRefusedError(111, "refused"))
    assert _url_error_code(exc) == "E_LLM_CONNECT"


def test_chat_completion_retries_on_503() -> None:
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
        if len(calls) < 3:
            raise urllib.error.HTTPError(
                req.full_url, 503, "unavailable", hdrs=None, fp=io.BytesIO(b"busy")
            )
        return io.BytesIO(ok_body)

    with patch("travelogue.llm.client.urllib.request.urlopen", fake_urlopen):
        with patch("travelogue.llm.client.time.sleep"):
            out = chat_completion(
                [{"role": "user", "content": "hi"}],
                runtime=rt,
            )
    assert out == '{"ok": true}'
    assert len(calls) == 3


def test_chat_completion_retries_timeout_url_error() -> None:
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
    assert len(calls) == 2
    assert out == '{"ok": true}'


def test_chat_completion_no_retry_on_400() -> None:
    rt = LlmRuntime(
        provider="deepseek",
        model="deepseek-chat",
        api_key="test-key",
        base_url="https://example.invalid/v1",
        timeout_sec=5,
    )

    def fake_urlopen(req, timeout=0):
        raise urllib.error.HTTPError(
            req.full_url, 400, "bad", hdrs=None, fp=io.BytesIO(b"nope")
        )

    with patch("travelogue.llm.client.urllib.request.urlopen", fake_urlopen):
        with pytest.raises(LlmError, match="E_LLM_HTTP"):
            chat_completion([{"role": "user", "content": "hi"}], runtime=rt)
