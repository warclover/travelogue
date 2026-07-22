"""llm/ping · 切换到通义时不得沿用 DeepSeek 的 model/base_url。"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from travelogue.config import get_config, reset_config_cache
from travelogue.llm.user_settings import (
    UserLlmSecrets,
    clear_user_llm_secrets,
    write_user_llm_config_overlay,
    write_user_llm_secrets,
)
from travelogue.util.llm_presets import PROVIDER_PRESETS
from travelogue.web.studio_handlers import llm_settings_handlers as h


@pytest.fixture()
def user_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("TRAVELOGUE_USER_DATA", str(tmp_path))
    # NAS · dark ON：本模块测写作引擎写/ping；默认面会 403
    monkeypatch.setenv("TRAVELOGUE_AI_SURFACE", "1")
    clear_user_llm_secrets()
    reset_config_cache()
    return tmp_path


def _handler(payload: dict) -> MagicMock:
    handler = MagicMock()
    handler.command = "POST"
    handler._read_json_body.return_value = payload
    captured: dict = {}

    def _json(status: int, body: dict) -> None:
        captured["status"] = status
        captured["body"] = body

    handler._json_response.side_effect = _json
    handler._captured = captured
    return handler


def test_ping_dashscope_ignores_sticky_deepseek_config(
    user_data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 先前 DeepSeek 配置残留在 overlay
    write_user_llm_config_overlay(
        provider="deepseek",
        model="deepseek-chat",
        base_url=PROVIDER_PRESETS["deepseek"]["base_url"],
    )
    write_user_llm_secrets(
        UserLlmSecrets(
            provider="deepseek",
            api_key="sk-deepseek-old",
            model="deepseek-chat",
            base_url=PROVIDER_PRESETS["deepseek"]["base_url"],
            last_ping_ok=True,
        )
    )
    reset_config_cache()

    seen: dict = {}

    def _fake_ping(*, provider: str | None = None) -> str:
        from travelogue.llm.client import resolve_llm_runtime

        rt = resolve_llm_runtime(provider)
        seen["provider"] = rt.provider
        seen["model"] = rt.model
        seen["base_url"] = rt.base_url
        return f"{rt.provider}/{rt.model} @ {rt.base_url}"

    # handle_llm_ping 在函数内 from travelogue.llm.client import llm_ping
    monkeypatch.setattr("travelogue.llm.client.llm_ping", _fake_ping)

    handler = _handler(
        {"provider": "dashscope", "apiKey": "sk-dash-new-key-xxxxxxxxxxxx"}
    )
    h.handle_llm_ping(handler)

    assert handler._captured["status"] == 200
    assert seen["provider"] == "dashscope"
    assert seen["model"] == "qwen-plus"
    assert seen["base_url"] == PROVIDER_PRESETS["dashscope"]["base_url"].rstrip("/")


def test_save_dashscope_writes_qwen_not_deepseek(
    user_data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    handler = _handler(
        {
            "provider": "dashscope",
            "apiKey": "sk-dash-save-key-xxxxxxxxxxxx",
            # 客户端误带 DeepSeek 地址时也应被丢掉
            "baseUrl": PROVIDER_PRESETS["deepseek"]["base_url"],
            "model": "deepseek-chat",
        }
    )
    h.handle_llm_settings(handler)
    assert handler._captured["status"] == 200
    overlay = (user_data / "config.user.yaml").read_text(encoding="utf-8")
    assert "provider: dashscope" in overlay
    assert "qwen-plus" in overlay
    assert "deepseek-chat" not in overlay
    assert "api.deepseek.com" not in overlay


def test_save_rejects_http_base_url(user_data: Path) -> None:
    handler = _handler(
        {
            "provider": "deepseek",
            "apiKey": "sk-https-only-xxxxxxxxxxxx",
            "baseUrl": "http://example.com/v1",
        }
    )
    h.handle_llm_settings(handler)
    assert handler._captured["status"] == 400
    assert handler._captured["body"]["error"] == "E_LLM_BASE_URL"


def test_save_dashscope_region_intl(user_data: Path) -> None:
    handler = _handler(
        {
            "provider": "dashscope",
            "apiKey": "sk-dash-intl-xxxxxxxxxxxx",
            "region": "intl",
        }
    )
    h.handle_llm_settings(handler)
    assert handler._captured["status"] == 200
    body = handler._captured["body"]
    assert body.get("region") == "intl"
    assert body.get("readiness") == "已保存未验证"
    overlay = (user_data / "config.user.yaml").read_text(encoding="utf-8")
    assert "dashscope-intl.aliyuncs.com" in overlay


def test_ping_respects_region_intl(
    user_data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from travelogue.llm.user_settings import read_user_llm_secrets
    from travelogue.util.llm_presets import DASHSCOPE_REGION_BASE_URLS

    write_user_llm_secrets(
        UserLlmSecrets(
            provider="dashscope",
            api_key="sk-dash-intl-ping-xxxxxxxx",
            region="cn",
            last_ping_ok=None,
        )
    )
    seen: dict = {}

    def _fake_ping(*, provider: str | None = None) -> str:
        from travelogue.llm.client import resolve_llm_runtime

        rt = resolve_llm_runtime(provider)
        seen["base_url"] = rt.base_url
        return f"{rt.provider}/{rt.model} @ {rt.base_url}"

    monkeypatch.setattr("travelogue.llm.client.llm_ping", _fake_ping)
    # 仅测试：不 persist，不得改写 region / last_ping_ok
    handler = _handler({"provider": "dashscope", "region": "intl", "persist": False})
    h.handle_llm_ping(handler)
    assert handler._captured["status"] == 200
    assert seen["base_url"] == DASHSCOPE_REGION_BASE_URLS["intl"].rstrip("/")
    sec = read_user_llm_secrets()
    assert sec.region == "cn"
    assert sec.last_ping_ok is None


def test_ping_persist_updates_last_ping_ok(
    user_data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from travelogue.llm.user_settings import read_user_llm_secrets

    write_user_llm_secrets(
        UserLlmSecrets(
            provider="deepseek",
            api_key="sk-deepseek-persist-xxxxxx",
            last_ping_ok=None,
        )
    )
    monkeypatch.setattr(
        "travelogue.llm.client.llm_ping",
        lambda **_k: "deepseek/deepseek-chat @ https://api.deepseek.com/v1",
    )
    handler = _handler({"provider": "deepseek", "persist": True})
    h.handle_llm_ping(handler)
    assert handler._captured["status"] == 200
    assert read_user_llm_secrets().last_ping_ok is True


def test_save_model_qwen_turbo(user_data: Path) -> None:
    handler = _handler(
        {
            "provider": "dashscope",
            "apiKey": "sk-dash-model-xxxxxxxxxxxx",
            "model": "qwen-turbo",
            "region": "cn",
        }
    )
    h.handle_llm_settings(handler)
    assert handler._captured["status"] == 200
    assert handler._captured["body"].get("model") == "qwen-turbo"
    overlay = (user_data / "config.user.yaml").read_text(encoding="utf-8")
    assert "qwen-turbo" in overlay
