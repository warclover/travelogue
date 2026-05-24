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
