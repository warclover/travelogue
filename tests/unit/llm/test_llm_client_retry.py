"""LLM client retry and URL error classification (offline)."""

from __future__ import annotations

import io
import json
import urllib.error
from unittest.mock import patch

import pytest

from travelogue.llm.client import LlmRuntime, _url_error_code, chat_completion, llm_ping
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


def test_chat_completion_dashscope_failsover_on_freetier() -> None:
    rt = LlmRuntime(
        provider="dashscope",
        model="qwen3.7-flash",
        api_key="test-key",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout_sec=10,
    )
    seen: list[str] = []

    def fake_urlopen(req, timeout=0):
        body = json.loads(req.data.decode("utf-8"))
        seen.append(body["model"])
        if body["model"] == "qwen3.7-flash":
            raise urllib.error.HTTPError(
                req.full_url,
                403,
                "forbidden",
                hdrs=None,
                fp=io.BytesIO(
                    b'{"error":{"code":"AllocationQuota.FreeTierOnly",'
                    b'"message":"Free quota exhausted"}}'
                ),
            )
        ok = json.dumps(
            {"choices": [{"message": {"content": '{"ok": true}'}}]}
        ).encode("utf-8")
        return io.BytesIO(ok)

    with patch("travelogue.llm.client.urllib.request.urlopen", fake_urlopen):
        out = chat_completion(
            [{"role": "user", "content": "hi"}],
            runtime=rt,
            json_mode=False,
        )
    assert out == '{"ok": true}'
    assert seen[0] == "qwen3.7-flash"
    assert "deepseek-v4-pro" in seen or "qwen3.7-plus" in seen or "qwen-plus" in seen


def test_chat_completion_v4_sends_nonstream_thinking() -> None:
    rt = LlmRuntime(
        provider="dashscope",
        model="deepseek-v4-pro",
        api_key="test-key",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout_sec=10,
    )
    payloads: list[dict] = []

    def fake_urlopen(req, timeout=0):
        payloads.append(json.loads(req.data.decode("utf-8")))
        ok = json.dumps(
            {"choices": [{"message": {"content": '{"ok": true}'}}]}
        ).encode("utf-8")
        return io.BytesIO(ok)

    with patch("travelogue.llm.client.urllib.request.urlopen", fake_urlopen):
        chat_completion(
            [{"role": "user", "content": "hi"}],
            runtime=rt,
            model="deepseek-v4-pro",
            model_failover=False,
            json_mode=True,
        )
    assert payloads[0]["model"] == "deepseek-v4-pro"
    assert payloads[0]["enable_thinking"] is True
    assert payloads[0]["stream"] is False


def test_llm_ping_dashscope_skips_pro_and_thinking() -> None:
    rt = LlmRuntime(
        provider="dashscope",
        model="deepseek-v4-pro",
        api_key="test-key",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout_sec=120,
    )
    payloads: list[dict] = []

    def fake_urlopen(req, timeout=0):
        payloads.append(json.loads(req.data.decode("utf-8")))
        ok = json.dumps(
            {"choices": [{"message": {"content": '{"ok": true}'}}]}
        ).encode("utf-8")
        return io.BytesIO(ok)

    with patch("travelogue.llm.client.urllib.request.urlopen", fake_urlopen):
        msg = llm_ping(runtime=rt)
    assert "dashscope/qwen3.7-flash" in msg
    assert payloads[0]["model"] == "qwen3.7-flash"
    assert "enable_thinking" not in payloads[0]


def test_llm_ping_uses_short_timeout_and_json_fallback() -> None:
    rt = LlmRuntime(
        provider="deepseek",
        model="deepseek-chat",
        api_key="test-key",
        base_url="https://example.invalid/v1",
        timeout_sec=120,
    )
    seen_timeouts: list[int] = []
    modes: list[bool] = []

    def fake_urlopen(req, timeout=0):
        seen_timeouts.append(int(timeout))
        body = req.data.decode("utf-8") if req.data else ""
        modes.append("response_format" in body)
        if "response_format" in body:
            raise urllib.error.HTTPError(
                req.full_url,
                400,
                "bad",
                hdrs=None,
                fp=io.BytesIO(b"json mode unsupported"),
            )
        ok = json.dumps(
            {"choices": [{"message": {"content": '{"ok": true}'}}]}
        ).encode("utf-8")
        return io.BytesIO(ok)

    with patch("travelogue.llm.client.urllib.request.urlopen", fake_urlopen):
        msg = llm_ping(runtime=rt)
    assert "deepseek/deepseek-chat" in msg
    assert modes == [True, False]
    assert all(t <= 20 for t in seen_timeouts)
