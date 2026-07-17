"""LLM provider defaults (layer-0 · no upward imports)."""

from __future__ import annotations

PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "dashscope": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
        "api_key_env": "DASHSCOPE_API_KEY",
    },
}


def coerce_model_for_provider(provider: str, model: str | None) -> str:
    """Pick model for provider; drop another provider's default model if sticky."""
    preset = PROVIDER_PRESETS.get(provider) or {}
    default = str(preset.get("default_model") or "").strip() or "deepseek-chat"
    raw = (model or "").strip()
    if not raw:
        return default
    foreign = {
        str(p.get("default_model") or "").strip()
        for name, p in PROVIDER_PRESETS.items()
        if name != provider and p.get("default_model")
    }
    if raw in foreign:
        return default
    return raw


def coerce_base_url_for_provider(provider: str, base_url: str | None) -> str | None:
    """Return custom base_url, or None to use the provider preset.

    Strips another provider's default endpoint so switching DeepSeek ↔ 通义
    does not keep calling the wrong host. Own default URL also collapses to None.
    """
    preset = PROVIDER_PRESETS.get(provider) or {}
    raw = (base_url or "").strip().rstrip("/")
    if not raw:
        return None
    own = str(preset.get("base_url") or "").strip().rstrip("/")
    if own and raw == own:
        return None
    foreign = {
        str(p.get("base_url") or "").strip().rstrip("/")
        for name, p in PROVIDER_PRESETS.items()
        if name != provider and p.get("base_url")
    }
    if raw in foreign:
        return None
    return raw
