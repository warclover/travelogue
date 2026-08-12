"""Ping 错误分类：DashScope FreeTierOnly 不得误报 Key 无效。"""

from __future__ import annotations

from travelogue.llm.errors import LlmError
from travelogue.web.studio_handlers.llm_settings_handlers import (
    _classify_ping_error,
    _settings_message,
)


def test_freetier_403_is_quota_not_auth() -> None:
    exc = LlmError(
        "E_LLM_HTTP",
        'HTTP 403: {"error":{"message":"Free quota exhausted. '
        'disable the \\"use free tier only\\" mode",'
        '"code":"AllocationQuota.FreeTierOnly"}}',
    )
    code = _classify_ping_error(exc)
    assert code == "E_LLM_QUOTA_FREE_TIER"
    msg = _settings_message(code)
    assert "免费额度" in msg
    assert "Key 无效" not in msg


def test_plain_403_still_auth() -> None:
    exc = LlmError("E_LLM_HTTP", "HTTP 403: invalid api key")
    assert _classify_ping_error(exc) == "E_LLM_AUTH"


def test_401_is_auth() -> None:
    exc = LlmError("E_LLM_HTTP", "HTTP 401: Unauthorized")
    assert _classify_ping_error(exc) == "E_LLM_AUTH"


def test_quota_keyword_without_status() -> None:
    exc = LlmError("E_LLM_HTTP", "HTTP 400: insufficient balance / 余额不足")
    assert _classify_ping_error(exc) == "E_LLM_QUOTA"
