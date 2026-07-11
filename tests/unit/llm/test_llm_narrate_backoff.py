"""Shared provider backoff unit tests (AC-PT-09 direction)."""

from __future__ import annotations

import time
import urllib.error
from io import BytesIO

import pytest

from travelogue.llm.client import chat_completion
from travelogue.llm.errors import LlmError
from travelogue.llm.shared_backoff import (
    SharedProviderBackoff,
    get_shared_backoff,
    reset_shared_backoff,
)


def test_shared_backoff_note_and_wait() -> None:
    gate = SharedProviderBackoff(base_sec=0.05)
    assert gate.backoff_count == 0
    gate.note_rate_limit(retry_after_sec=0.08, attempt=0)
    assert gate.backoff_count == 1
    t0 = time.monotonic()
    gate.wait_turn()
    assert time.monotonic() - t0 >= 0.05


def test_reset_shared_backoff() -> None:
    reset_shared_backoff()
    get_shared_backoff().note_rate_limit(retry_after_sec=0.01)
    assert get_shared_backoff().backoff_count >= 1
    reset_shared_backoff()
    assert get_shared_backoff().backoff_count == 0


def test_chat_completion_429_updates_shared_backoff(monkeypatch) -> None:
    reset_shared_backoff()
    calls = {"n": 0}

    class _FakeHTTPError(urllib.error.HTTPError):
        def __init__(self) -> None:
            super().__init__(
                "http://example.test",
                429,
                "Too Many Requests",
                hdrs={"Retry-After": "0.05"},  # type: ignore[arg-type]
                fp=BytesIO(b'{"error":"rate"}'),
            )

    def fake_post(req, *, timeout_sec: int):
        calls["n"] += 1
        if calls["n"] == 1:
            raise _FakeHTTPError()
        return {"choices": [{"message": {"content": '{"ok": true}'}}]}

    monkeypatch.setattr("travelogue.llm.client._post_chat", fake_post)
    monkeypatch.setattr(
        "travelogue.llm.client.resolve_llm_runtime",
        lambda provider=None, cfg=None: type(
            "RT",
            (),
            {
                "provider": "deepseek",
                "model": "m",
                "api_key": "k",
                "base_url": "http://example.test/v1",
                "timeout_sec": 5,
            },
        )(),
    )
    content = chat_completion(
        [{"role": "user", "content": "hi"}],
        shared_backoff=True,
    )
    assert "ok" in content
    assert get_shared_backoff().backoff_count >= 1
    assert calls["n"] == 2
    reset_shared_backoff()


def test_chat_completion_non_retryable_does_not_loop(monkeypatch) -> None:
    reset_shared_backoff()

    class _FakeHTTPError(urllib.error.HTTPError):
        def __init__(self) -> None:
            super().__init__(
                "http://example.test",
                400,
                "Bad Request",
                hdrs={},  # type: ignore[arg-type]
                fp=BytesIO(b"bad"),
            )

    def fake_post(req, *, timeout_sec: int):
        raise _FakeHTTPError()

    monkeypatch.setattr("travelogue.llm.client._post_chat", fake_post)
    monkeypatch.setattr(
        "travelogue.llm.client.resolve_llm_runtime",
        lambda provider=None, cfg=None: type(
            "RT",
            (),
            {
                "provider": "deepseek",
                "model": "m",
                "api_key": "k",
                "base_url": "http://example.test/v1",
                "timeout_sec": 5,
            },
        )(),
    )
    with pytest.raises(LlmError, match="HTTP 400"):
        chat_completion([{"role": "user", "content": "hi"}], shared_backoff=True)
    assert get_shared_backoff().backoff_count == 0
    reset_shared_backoff()
