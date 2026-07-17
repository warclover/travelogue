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

# 通义百炼 · 中国站 / 国际站（D-WEA-04）
DASHSCOPE_REGION_BASE_URLS: dict[str, str] = {
    "cn": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "intl": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
}


def normalize_llm_region(provider: str | None, region: str | None) -> str | None:
    """Return cn|intl for dashscope; None for other providers."""
    if (provider or "").strip().lower() != "dashscope":
        return None
    r = (region or "cn").strip().lower()
    if r in ("intl", "international", "global", "sg", "singapore"):
        return "intl"
    return "cn"


def preset_base_url(provider: str, region: str | None = None) -> str:
    """Default OpenAI-compatible base URL for provider (+ dashscope region)."""
    prov = (provider or "").strip().lower()
    if prov == "dashscope":
        reg = normalize_llm_region(prov, region) or "cn"
        return DASHSCOPE_REGION_BASE_URLS[reg].rstrip("/")
    preset = PROVIDER_PRESETS.get(prov) or {}
    return str(preset.get("base_url") or "").strip().rstrip("/")


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
    """Return custom base_url, or None to use the provider/region preset.

    Strips another provider's default endpoint and own region presets so
    switching DeepSeek ↔ 通义 (or 中国站 ↔ 国际站) does not stick the wrong host.
    """
    raw = (base_url or "").strip().rstrip("/")
    if not raw:
        return None
    own_bases: set[str] = set()
    if provider == "dashscope":
        own_bases = {u.rstrip("/") for u in DASHSCOPE_REGION_BASE_URLS.values()}
    else:
        own = str((PROVIDER_PRESETS.get(provider) or {}).get("base_url") or "").strip().rstrip("/")
        if own:
            own_bases.add(own)
    if raw in own_bases:
        return None
    foreign = {
        str(p.get("base_url") or "").strip().rstrip("/")
        for name, p in PROVIDER_PRESETS.items()
        if name != provider and p.get("base_url")
    }
    # 通义 intl 对 DeepSeek 也算 foreign
    if provider != "dashscope":
        foreign.update(u.rstrip("/") for u in DASHSCOPE_REGION_BASE_URLS.values())
    if raw in foreign:
        return None
    return raw


def validate_custom_base_url(base_url: str | None) -> str | None:
    """Return cleaned custom URL, None if empty; raise ValueError('E_LLM_BASE_URL') if not https."""
    raw = (base_url or "").strip()
    if not raw:
        return None
    if not raw.lower().startswith("https://"):
        raise ValueError("E_LLM_BASE_URL")
    return raw.rstrip("/")


def detect_dashscope_region(base_url: str | None) -> str | None:
    """If URL is a known DashScope region preset, return cn|intl."""
    raw = (base_url or "").strip().rstrip("/")
    if not raw:
        return None
    for reg, url in DASHSCOPE_REGION_BASE_URLS.items():
        if raw == url.rstrip("/"):
            return reg
    return None


def resolve_base_url_for_provider(
    provider: str,
    base_url: str | None,
    region: str | None = None,
) -> str:
    """Custom URL, else region/preset (coerce may collapse own presets to None)."""
    custom = coerce_base_url_for_provider(provider, base_url)
    if custom:
        return custom.rstrip("/")
    reg = region
    if (provider or "").strip().lower() == "dashscope" and reg is None:
        reg = detect_dashscope_region(base_url)
    return preset_base_url(provider, reg).rstrip("/")
