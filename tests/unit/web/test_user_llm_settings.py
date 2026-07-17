"""Unit tests · Desktop LLM Setup V1 user_data secrets + status."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.llm.user_settings import (
    UserLlmSecrets,
    clear_user_llm_secrets,
    inject_secrets_into_environ,
    mask_api_key,
    read_user_llm_secrets,
    readiness_state,
    write_user_llm_config_overlay,
    write_user_llm_secrets,
)
from travelogue.web.studio_narrate import studio_llm_status


@pytest.fixture()
def user_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("TRAVELOGUE_USER_DATA", str(tmp_path))
    clear_user_llm_secrets()
    return tmp_path


def test_mask_api_key() -> None:
    assert mask_api_key(None) is None
    assert mask_api_key("short") == "***"
    assert mask_api_key("sk-abcdefghijklmn") == "sk-***klmn"


def test_write_read_clear_secrets(user_data: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_user_llm_secrets(
        UserLlmSecrets(provider="deepseek", api_key="sk-test-key-123456", last_ping_ok=None)
    )
    sec = read_user_llm_secrets()
    assert sec.configured
    assert sec.provider == "deepseek"
    assert readiness_state(sec) == "已保存未验证"
    write_user_llm_secrets(
        UserLlmSecrets(
            provider="deepseek",
            api_key="sk-test-key-123456",
            last_ping_ok=True,
        )
    )
    assert readiness_state() == "已就绪"
    inject_secrets_into_environ()
    assert monkeypatch is not None
    import os

    assert os.environ.get("DEEPSEEK_API_KEY") == "sk-test-key-123456"
    clear_user_llm_secrets()
    assert not read_user_llm_secrets().configured
    assert not (user_data / "secrets.json").exists()


def test_config_overlay_and_status(user_data: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_user_llm_config_overlay(provider="dashscope", model="qwen-plus", base_url=None)
    write_user_llm_secrets(
        UserLlmSecrets(provider="dashscope", api_key="sk-dash-aaaaaaaa", last_ping_ok=True)
    )
    inject_secrets_into_environ()
    status = studio_llm_status()
    assert status["llmProvider"] == "dashscope"
    assert status["llmAvailable"] is True
    overlay = (user_data / "config.user.yaml").read_text(encoding="utf-8")
    assert "provider: dashscope" in overlay
    assert "api_key" not in overlay or "api_key_env" in overlay
    raw = json.loads((user_data / "secrets.json").read_text(encoding="utf-8"))
    assert "api_key" in raw


def test_status_body_exposes_user_and_trips_dirs(user_data: Path) -> None:
    from travelogue.web.studio_handlers.llm_settings_handlers import _status_body

    body = _status_body()
    assert body["ok"] is True
    assert body["userDataDir"]
    assert Path(body["userDataDir"]) == user_data.resolve()
    assert "tripsDir" in body
    assert body["tripsDir"]


def test_region_roundtrip_in_secrets(user_data: Path) -> None:
    write_user_llm_secrets(
        UserLlmSecrets(
            provider="dashscope",
            api_key="sk-dash-region-xxxxxxxxxxxx",
            region="intl",
            last_ping_ok=None,
        )
    )
    sec = read_user_llm_secrets()
    assert sec.region == "intl"
    raw = json.loads((user_data / "secrets.json").read_text(encoding="utf-8"))
    assert raw["region"] == "intl"
    write_user_llm_config_overlay(
        provider="dashscope", model="qwen-plus", base_url=None, region="intl"
    )
    overlay = (user_data / "config.user.yaml").read_text(encoding="utf-8")
    assert "dashscope-intl.aliyuncs.com" in overlay


def test_clear_secrets_drops_injected_env(user_data: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    from travelogue.llm.user_settings import clear_injected_llm_environ

    write_user_llm_secrets(
        UserLlmSecrets(provider="deepseek", api_key="sk-clear-env-12345678", last_ping_ok=True)
    )
    inject_secrets_into_environ()
    assert os.environ.get("DEEPSEEK_API_KEY") == "sk-clear-env-12345678"
    clear_user_llm_secrets()
    assert os.environ.get("DEEPSEEK_API_KEY") is None
    # idempotent
    clear_injected_llm_environ()
    assert os.environ.get("DEEPSEEK_API_KEY") is None
