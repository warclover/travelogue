"""LLM provider defaults (layer-0 · no upward imports)."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "dashscope": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        # 默认优先仍有新人免费额度的轻量模型；耗尽后由 client 级联到付费兜底
        "default_model": "qwen3.7-flash",
        "api_key_env": "DASHSCOPE_API_KEY",
    },
}

# 通义百炼 · 中国站 / 国际站（D-WEA-04）
DASHSCOPE_REGION_BASE_URLS: dict[str, str] = {
    "cn": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "intl": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
}

# 文本写作级联：免费额度友好模型 → 付费兜底（qwen-plus/turbo/max）
# 不含 OCR / 纯视觉专用模型。
DASHSCOPE_MODEL_CASCADE: tuple[str, ...] = (
    "qwen3.7-flash",
    "qwen3.7-plus",
    "qwen3.8-max",
    "qwen3.7-max",
    "qwen3.6-plus",
    "qwen-plus",
    "qwen-turbo",
    "qwen-max",
)


def dashscope_model_candidates(selected: str | None = None) -> list[str]:
    """Ordered models to try: selected first (if any), then free-tier cascade, then paid."""
    out: list[str] = []
    seen: set[str] = set()
    for name in (selected, *DASHSCOPE_MODEL_CASCADE):
        m = (name or "").strip()
        if not m or m in seen:
            continue
        seen.add(m)
        out.append(m)
    return out or ["qwen-plus"]


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
    """Pick model for provider; drop another provider's sticky models."""
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
    # 切到 DeepSeek 时丢掉整条通义级联；切到通义时丢掉 deepseek-* 族
    if provider != "dashscope":
        foreign.update(DASHSCOPE_MODEL_CASCADE)
    elif raw.lower().startswith("deepseek"):
        return default
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


def _hostname_is_blocked(host: str) -> bool:
    """Block localhost / link-local / private / cloud metadata hosts (SSRF).

    Hostname literals only — no DNS resolve (save/ping must not depend on network).
    """
    h = (host or "").strip().lower().rstrip(".")
    if not h:
        return True
    if h in {"localhost", "metadata.google.internal", "metadata"}:
        return True
    if h.endswith(".localhost") or h.endswith(".local"):
        return True
    try:
        ip = ipaddress.ip_address(h)
    except ValueError:
        return False
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
        or str(ip) == "169.254.169.254"
    )


def validate_custom_base_url(base_url: str | None) -> str | None:
    """Return cleaned custom URL, None if empty.

    Raises ValueError('E_LLM_BASE_URL') if not https or host looks like SSRF target.
    """
    raw = (base_url or "").strip()
    if not raw:
        return None
    if not raw.lower().startswith("https://"):
        raise ValueError("E_LLM_BASE_URL")
    cleaned = raw.rstrip("/")
    parsed = urlparse(cleaned if "://" in cleaned else f"https://{cleaned}")
    host = parsed.hostname or ""
    if _hostname_is_blocked(host):
        raise ValueError("E_LLM_BASE_URL")
    return cleaned


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
