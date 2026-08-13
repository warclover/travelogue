"""Provider-scoped model / base_url · DeepSeek ↔ 通义不得串配置。"""

from __future__ import annotations

from dataclasses import replace

import pytest

from travelogue.config import get_config, reset_config_cache
from travelogue.config.runtime import config_override
from travelogue.llm.client import resolve_llm_runtime
from travelogue.llm.user_settings import UserLlmSecrets
from travelogue.util.llm_presets import (
    DASHSCOPE_REGION_BASE_URLS,
    PROVIDER_PRESETS,
    coerce_base_url_for_provider,
    coerce_model_for_provider,
    preset_base_url,
    resolve_base_url_for_provider,
    validate_custom_base_url,
)


def test_validate_custom_base_url_https_public_only() -> None:
    assert validate_custom_base_url(None) is None
    assert validate_custom_base_url("") is None
    assert (
        validate_custom_base_url("https://api.example.com/v1")
        == "https://api.example.com/v1"
    )
    with pytest.raises(ValueError, match="E_LLM_BASE_URL"):
        validate_custom_base_url("http://api.example.com/v1")
    with pytest.raises(ValueError, match="E_LLM_BASE_URL"):
        validate_custom_base_url("https://127.0.0.1/v1")
    with pytest.raises(ValueError, match="E_LLM_BASE_URL"):
        validate_custom_base_url("https://localhost/v1")
    with pytest.raises(ValueError, match="E_LLM_BASE_URL"):
        validate_custom_base_url("https://10.0.0.8/v1")
    with pytest.raises(ValueError, match="E_LLM_BASE_URL"):
        validate_custom_base_url("https://169.254.169.254/latest")


def test_coerce_drops_foreign_default_model() -> None:
    assert coerce_model_for_provider("dashscope", "deepseek-chat") == "qwen3.7-flash"
    assert coerce_model_for_provider("deepseek", "qwen-plus") == "deepseek-chat"
    assert coerce_model_for_provider("deepseek", "qwen3.7-flash") == "deepseek-chat"
    assert coerce_model_for_provider("dashscope", None) == "qwen3.7-flash"
    assert coerce_model_for_provider("dashscope", "qwen-turbo") == "qwen-turbo"


def test_dashscope_model_candidates_prefer_free_then_paid() -> None:
    from travelogue.util.llm_presets import dashscope_model_candidates

    chain = dashscope_model_candidates(None)
    assert chain[0] == "qwen3.7-flash"
    assert "qwen-plus" in chain
    assert chain.index("qwen3.7-flash") < chain.index("qwen-plus")
    selected_first = dashscope_model_candidates("qwen-max")
    assert selected_first[0] == "qwen-max"
    assert "qwen3.7-flash" in selected_first


def test_coerce_drops_foreign_default_base_url() -> None:
    ds = PROVIDER_PRESETS["deepseek"]["base_url"]
    dash = PROVIDER_PRESETS["dashscope"]["base_url"]
    assert coerce_base_url_for_provider("dashscope", ds) is None
    assert coerce_base_url_for_provider("deepseek", dash) is None
    assert coerce_base_url_for_provider("dashscope", dash + "/") is None  # own default → use preset
    # 国际站亦属通义 preset，交给 region 解析，不作为「自定义」残留
    assert (
        coerce_base_url_for_provider(
            "dashscope", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
        is None
    )
    assert coerce_base_url_for_provider("deepseek", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1") is None


def test_resolve_runtime_ignores_sticky_deepseek_when_dashscope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-dash-test-key")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr(
        "travelogue.llm.user_settings.read_user_llm_secrets",
        lambda: UserLlmSecrets(),
    )
    monkeypatch.setattr(
        "travelogue.llm.user_settings.inject_secrets_into_environ",
        lambda *_a, **_k: None,
    )
    reset_config_cache()
    base = get_config()
    sticky = replace(
        base,
        llm=replace(
            base.llm,
            provider="deepseek",
            model="deepseek-chat",
            base_url=PROVIDER_PRESETS["deepseek"]["base_url"],
            api_key_env="DEEPSEEK_API_KEY",
        ),
    )
    with config_override(sticky):
        # Explicit provider=dashscope must not inherit DeepSeek endpoint/model
        rt = resolve_llm_runtime("dashscope")
    assert rt.provider == "dashscope"
    assert rt.model == "qwen3.7-flash"
    assert rt.base_url == PROVIDER_PRESETS["dashscope"]["base_url"].rstrip("/")


def test_resolve_runtime_coerces_mismatched_cfg_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """config 已标 dashscope，但 model/URL 仍是 DeepSeek 残留。"""
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-dash-test-key")
    monkeypatch.setattr(
        "travelogue.llm.user_settings.read_user_llm_secrets",
        lambda: UserLlmSecrets(provider="dashscope", api_key="sk-dash-test-key"),
    )
    monkeypatch.setattr(
        "travelogue.llm.user_settings.inject_secrets_into_environ",
        lambda *_a, **_k: None,
    )
    reset_config_cache()
    base = get_config()
    contaminated = replace(
        base,
        llm=replace(
            base.llm,
            provider="dashscope",
            model="deepseek-chat",
            base_url=PROVIDER_PRESETS["deepseek"]["base_url"],
            api_key_env="DASHSCOPE_API_KEY",
        ),
    )
    with config_override(contaminated):
        rt = resolve_llm_runtime("dashscope")
    assert rt.model == "qwen3.7-flash"
    assert rt.base_url == PROVIDER_PRESETS["dashscope"]["base_url"].rstrip("/")


def test_preset_base_url_dashscope_region() -> None:
    assert preset_base_url("dashscope", "cn") == DASHSCOPE_REGION_BASE_URLS["cn"].rstrip("/")
    assert preset_base_url("dashscope", "intl") == DASHSCOPE_REGION_BASE_URLS["intl"].rstrip("/")
    assert resolve_base_url_for_provider("dashscope", None, "intl") == DASHSCOPE_REGION_BASE_URLS[
        "intl"
    ].rstrip("/")


def test_resolve_runtime_uses_secrets_region_intl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-dash-test-key")
    monkeypatch.setattr(
        "travelogue.llm.user_settings.read_user_llm_secrets",
        lambda: UserLlmSecrets(
            provider="dashscope",
            api_key="sk-dash-test-key",
            region="intl",
        ),
    )
    monkeypatch.setattr(
        "travelogue.llm.user_settings.inject_secrets_into_environ",
        lambda *_a, **_k: None,
    )
    reset_config_cache()
    base = get_config()
    cfg = replace(
        base,
        llm=replace(
            base.llm,
            provider="dashscope",
            model="qwen-plus",
            base_url=None,
            api_key_env="DASHSCOPE_API_KEY",
        ),
    )
    with config_override(cfg):
        rt = resolve_llm_runtime("dashscope")
    assert rt.base_url == DASHSCOPE_REGION_BASE_URLS["intl"].rstrip("/")
