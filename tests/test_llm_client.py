"""LLM client unit tests (offline)."""

from __future__ import annotations

import pytest

from travelogue.llm.client import resolve_llm_runtime
from travelogue.llm.errors import LlmError


def test_resolve_llm_runtime_stub_raises():
    with pytest.raises(LlmError, match="E_LLM_STUB"):
        resolve_llm_runtime("stub")


def test_resolve_llm_runtime_missing_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(LlmError, match="E_LLM_AUTH"):
        resolve_llm_runtime("deepseek")


def test_llm_runtime_dataclass():
    from travelogue.llm.client import LlmRuntime

    obj = LlmRuntime(
        provider="deepseek",
        model="deepseek-chat",
        api_key="test",
        base_url="https://api.deepseek.com/v1",
        timeout_sec=30,
    )
    assert obj.provider == "deepseek"
    assert obj.model == "deepseek-chat"
