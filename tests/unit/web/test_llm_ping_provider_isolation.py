"""llm/settings · BAI W1a：Studio 只接受 dashscope；DeepSeek-only 不驱动连接。"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from travelogue.config import reset_config_cache
from travelogue.llm.user_settings import (
    UserLlmSecrets,
    clear_user_llm_secrets,
    read_user_llm_secrets,
    write_user_llm_config_overlay,
    write_user_llm_secrets,
)
from travelogue.util.llm_presets import PROVIDER_PRESETS
from travelogue.web.studio_handlers import llm_settings_handlers as h


@pytest.fixture()
def user_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("TRAVELOGUE_USER_DATA", str(tmp_path))
    # 连接 API 已不要求开闸；仍开 dark 以免与其它门控夹杂
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

    def _fake_ping(
        *,
        provider: str | None = None,
        secrets=None,
        cfg=None,
        runtime=None,
    ) -> str:
        from travelogue.llm.client import resolve_llm_runtime

        rt = runtime or resolve_llm_runtime(provider, cfg=cfg, secrets=secrets)
        seen["provider"] = rt.provider
        seen["model"] = rt.model
        seen["base_url"] = rt.base_url
        seen["api_key"] = rt.api_key
        return f"{rt.provider}/{rt.model} @ {rt.base_url}"

    monkeypatch.setattr("travelogue.llm.client.llm_ping", _fake_ping)

    handler = _handler(
        {"provider": "dashscope", "apiKey": "sk-dash-new-key-xxxxxxxxxxxx"}
    )
    h.handle_llm_ping(handler)

    assert handler._captured["status"] == 200
    assert handler._captured["body"]["message"] == "已连接通义百炼"
    assert "已自动改用" not in handler._captured["body"]["message"]
    assert seen["provider"] == "dashscope"
    assert seen["model"] == "qwen3.7-flash"
    assert seen["base_url"] == PROVIDER_PRESETS["dashscope"]["base_url"].rstrip("/")
    assert seen["api_key"] == "sk-dash-new-key-xxxxxxxxxxxx"
    # DeepSeek-only 磁盘 Key 仍在（本次 ping 不 persist）
    disk = json.loads((user_data / "secrets.json").read_text(encoding="utf-8"))
    assert disk["provider"] == "deepseek"
    assert disk["api_key"] == "sk-deepseek-old"


def test_save_dashscope_writes_qwen_not_deepseek(
    user_data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    handler = _handler(
        {
            "provider": "dashscope",
            "apiKey": "sk-dash-save-key-xxxxxxxxxxxx",
            "baseUrl": PROVIDER_PRESETS["deepseek"]["base_url"],
            "model": "deepseek-chat",
        }
    )
    h.handle_llm_settings(handler)
    assert handler._captured["status"] == 200
    overlay = (user_data / "config.user.yaml").read_text(encoding="utf-8")
    assert "provider: dashscope" in overlay
    assert "qwen3.7-flash" in overlay
    assert "deepseek-chat" not in overlay
    assert "api.deepseek.com" not in overlay


def test_post_provider_deepseek_rejected_ac_bai_15(user_data: Path) -> None:
    """AC-BAI-15：POST provider=deepseek 不得写成官方 DeepSeek 活跃连接。"""
    write_user_llm_secrets(
        UserLlmSecrets(
            provider="deepseek",
            api_key="sk-deepseek-keep-xxxxxxxxxxxx",
            last_ping_ok=True,
        )
    )
    handler = _handler(
        {
            "provider": "deepseek",
            "apiKey": "sk-https-only-xxxxxxxxxxxx",
            "baseUrl": "http://example.com/v1",
        }
    )
    h.handle_llm_settings(handler)
    assert handler._captured["status"] == 400
    assert handler._captured["body"]["error"] == "E_LLM_PROVIDER"
    assert "请改用通义百炼" in handler._captured["body"]["message"]
    disk = json.loads((user_data / "secrets.json").read_text(encoding="utf-8"))
    assert disk["provider"] == "deepseek"
    assert disk["api_key"] == "sk-deepseek-keep-xxxxxxxxxxxx"


def test_save_forces_region_cn(user_data: Path) -> None:
    """AC-BAI-17：保存后 region 为 cn。"""
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
    assert body.get("region") == "cn"
    assert body.get("readiness") == "已保存未验证"
    overlay = (user_data / "config.user.yaml").read_text(encoding="utf-8")
    assert "dashscope-intl.aliyuncs.com" not in overlay


def test_ping_ignores_client_intl_region(
    user_data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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

    def _fake_ping(
        *,
        provider: str | None = None,
        secrets=None,
        cfg=None,
        runtime=None,
    ) -> str:
        from travelogue.llm.client import resolve_llm_runtime

        rt = runtime or resolve_llm_runtime(provider, cfg=cfg, secrets=secrets)
        seen["base_url"] = rt.base_url
        return f"{rt.provider}/{rt.model} @ {rt.base_url}"

    monkeypatch.setattr("travelogue.llm.client.llm_ping", _fake_ping)
    handler = _handler({"provider": "dashscope", "region": "intl", "persist": False})
    h.handle_llm_ping(handler)
    assert handler._captured["status"] == 200
    assert seen["base_url"] == DASHSCOPE_REGION_BASE_URLS["cn"].rstrip("/")
    sec = read_user_llm_secrets()
    assert sec.region == "cn"
    assert sec.last_ping_ok is None


def test_ping_persist_updates_last_ping_ok_dashscope(
    user_data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_user_llm_secrets(
        UserLlmSecrets(
            provider="dashscope",
            api_key="sk-dash-persist-xxxxxxxxxxxx",
            last_ping_ok=None,
        )
    )
    monkeypatch.setattr(
        "travelogue.llm.client.llm_ping",
        lambda **_k: "dashscope/qwen3.7-flash @ https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    handler = _handler({"provider": "dashscope", "persist": True})
    h.handle_llm_ping(handler)
    assert handler._captured["status"] == 200
    assert handler._captured["body"]["message"] == "已连接通义百炼"
    assert read_user_llm_secrets().last_ping_ok is True
    assert read_user_llm_secrets().provider == "dashscope"


def test_ping_deepseek_rejected_does_not_persist(user_data: Path) -> None:
    write_user_llm_secrets(
        UserLlmSecrets(
            provider="deepseek",
            api_key="sk-deepseek-persist-xxxxxx",
            last_ping_ok=None,
        )
    )
    handler = _handler({"provider": "deepseek", "persist": True})
    h.handle_llm_ping(handler)
    assert handler._captured["status"] == 400
    assert handler._captured["body"]["error"] == "E_LLM_PROVIDER"
    assert read_user_llm_secrets().last_ping_ok is None
    assert read_user_llm_secrets().provider == "deepseek"


def test_save_ignores_client_model(user_data: Path) -> None:
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
    assert "model" not in handler._captured["body"]
    overlay = (user_data / "config.user.yaml").read_text(encoding="utf-8")
    assert "qwen-turbo" not in overlay
    assert "qwen3.7-flash" in overlay


def test_deepseek_only_not_studio_ready_ac_bai_04(user_data: Path) -> None:
    """AC-BAI-04：仅官方 DeepSeek 旧 secrets → Studio 未连接；磁盘 Key 仍在。"""
    write_user_llm_secrets(
        UserLlmSecrets(
            provider="deepseek",
            api_key="sk-deepseek-legacy-xxxxxx",
            last_ping_ok=True,
        )
    )
    reset_config_cache()
    body = h._status_body()
    assert body["configured"] is False
    assert body["llmAvailable"] is False
    assert body["connectionOk"] is False
    assert body["copyReady"] is False
    assert body["hasDashscope"] is False
    assert body["legacyKeyOnDisk"] is True
    assert "hasDeepseek" not in body
    assert body["readiness"] == "未配置"
    assert body["maskedKey"] is None
    disk = json.loads((user_data / "secrets.json").read_text(encoding="utf-8"))
    assert disk["provider"] == "deepseek"
    assert disk["api_key"] == "sk-deepseek-legacy-xxxxxx"
