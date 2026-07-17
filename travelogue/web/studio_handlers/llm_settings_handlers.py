"""Studio LLM settings API (Desktop LLM Setup V1 · W1a · WEA W1)."""

from __future__ import annotations

import os
import re
from dataclasses import replace
from typing import Any

from travelogue.config import get_config, reset_config_cache
from travelogue.llm.errors import LlmError
from travelogue.llm.user_settings import (
    UserLlmSecrets,
    clear_user_llm_secrets,
    inject_secrets_into_environ,
    mask_api_key,
    read_user_llm_secrets,
    readiness_state,
    user_data_dir,
    write_user_llm_config_overlay,
    write_user_llm_secrets,
)
from travelogue.util.llm_presets import (
    PROVIDER_PRESETS,
    coerce_base_url_for_provider,
    coerce_model_for_provider,
    normalize_llm_region,
    preset_base_url,
    validate_custom_base_url,
)
from travelogue.web.studio_errors import user_message
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from travelogue.web.studio_narrate import studio_llm_status

_ALLOWED = frozenset({"deepseek", "dashscope"})

# 配置面可行动文案（PRD §4.7 · 与导入路径 E_LLM_AUTH 长句区分）
_SETTINGS_MESSAGES: dict[str, str] = {
    "E_LLM_AUTH": "Key 无效或已失效。请回控制台重新创建并粘贴。",
    "E_LLM_ENDPOINT": "当前地域与 Key 不匹配。请改选中国站/国际站，或检查自定义 API 地址。",
    "E_LLM_MODEL": "模型不可用。请改选列表中的模型，或在高级中填写控制台可见的模型名。",
    "E_LLM_QUOTA": "服务商返回余额或配额不足。请到控制台充值或检查限流。",
    "E_LLM_RATE": "服务商繁忙，请稍后重试。",
    "E_LLM_TIMEOUT": "无法连接服务商。请检查网络后重试。",
    "E_LLM_NETWORK": "无法连接服务商。请检查网络后重试。",
    "E_LLM_CONNECT": "无法连接服务商。请检查网络后重试。",
    "E_LLM_BASE_URL": "自定义 API 地址仅支持 https。",
    "E_LLM_PING": "连接测试失败，请检查 Key、地域或网络后重试。",
}


def _settings_message(code: str, fallback: str = "") -> str:
    if code in _SETTINGS_MESSAGES:
        return _SETTINGS_MESSAGES[code]
    return user_message(code, fallback)


def _classify_ping_error(exc: LlmError) -> str:
    """Map LlmError → settings-facing code (AUTH / ENDPOINT / TIMEOUT / …)."""
    code = exc.code or "E_LLM_PING"
    detail = f"{exc.message or ''} {exc}".lower()
    if code in ("E_LLM_TIMEOUT", "E_LLM_NETWORK", "E_LLM_CONNECT"):
        return "E_LLM_TIMEOUT" if code == "E_LLM_TIMEOUT" else "E_LLM_NETWORK"
    if code == "E_LLM_AUTH":
        return "E_LLM_AUTH"
    if code == "E_LLM_HTTP":
        m = re.search(r"http\s+(\d{3})", detail)
        status = int(m.group(1)) if m else 0
        if status in (401, 403):
            return "E_LLM_AUTH"
        if status == 429:
            return "E_LLM_RATE"
        if any(k in detail for k in ("quota", "balance", "insufficient", "arrearage", "额度", "余额")):
            return "E_LLM_QUOTA"
        if any(k in detail for k in ("model", "not exist", "not found", "does not exist", "无效的模型")):
            return "E_LLM_MODEL"
        if status in (404, 422) or any(
            k in detail for k in ("endpoint", "invalidurl", "accessdenied", "region", "地域")
        ):
            return "E_LLM_ENDPOINT"
        return "E_LLM_PING"
    if code.startswith("E_LLM_"):
        return code
    return "E_LLM_PING"


def _with_ping(secrets: UserLlmSecrets, ok: bool) -> UserLlmSecrets:
    return UserLlmSecrets(
        provider=secrets.provider,
        api_key=secrets.api_key,
        model=secrets.model,
        base_url=secrets.base_url,
        region=secrets.region,
        last_ping_ok=ok,
    )


def _status_body(*, cfg: Any = None) -> dict[str, Any]:
    inject_secrets_into_environ()
    app_cfg = cfg if cfg is not None else get_config(reload=True)
    status = studio_llm_status(cfg=app_cfg)
    secrets = read_user_llm_secrets()
    ready = readiness_state(secrets)
    available = bool(status.get("llmAvailable"))
    if secrets.configured and (secrets.last_ping_ok is True or available):
        tier = "L1"
    else:
        tier = "L0"
    region = secrets.region if secrets.provider == "dashscope" else None
    model = secrets.model
    if not model and secrets.provider:
        model = (PROVIDER_PRESETS.get(secrets.provider) or {}).get("default_model")
    return {
        "ok": True,
        **status,
        "tier": tier,
        "llmTier": tier,
        "configured": secrets.configured,
        "readiness": ready,
        "maskedKey": mask_api_key(secrets.api_key),
        "lastPingOk": secrets.last_ping_ok,
        "region": region,
        "model": model,
        "userDataDir": str(user_data_dir(ensure=False)),
        "tripsDir": str(getattr(app_cfg, "trips_dir", "") or ""),
        "capabilities": {
            "import": True,
            "layout": True,
            "stubNarrate": True,
            "llmNarrate": bool(status.get("llmAvailable")),
            "longshot": True,
        },
    }


def handle_llm_status(handler: StudioHandlerProtocol) -> None:
    handler._json_response(200, _status_body())


def handle_llm_settings(handler: StudioHandlerProtocol) -> None:
    if handler.command == "DELETE":
        clear_user_llm_secrets()
        reset_config_cache()
        handler._json_response(200, _status_body())
        return

    if handler.command != "POST":
        handler._json_response(
            405,
            {"ok": False, "error": "E_METHOD", "message": "method not allowed"},
        )
        return

    payload = handler._read_json_body() or {}
    provider = str(payload.get("provider") or "").strip().lower()
    api_key = str(payload.get("apiKey") or payload.get("api_key") or "").strip()
    model = payload.get("model")
    model_s = str(model).strip() if model else None
    base_url = payload.get("baseUrl") or payload.get("base_url")
    base_s = str(base_url).strip() if base_url else None
    region = normalize_llm_region(provider, payload.get("region"))

    if provider not in _ALLOWED:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_LLM_PROVIDER",
                "message": user_message("E_LLM_PROVIDER", "请选择 DeepSeek 或 通义千问"),
            },
        )
        return

    existing = read_user_llm_secrets()
    if not api_key:
        # 允许仅改地域/地址：复用同商已存 Key
        if existing.configured and existing.provider == provider and existing.api_key:
            api_key = existing.api_key
        else:
            handler._json_response(
                400,
                {
                    "ok": False,
                    "error": "E_LLM_AUTH",
                    "message": _settings_message("E_LLM_AUTH"),
                },
            )
            return

    try:
        base_s = validate_custom_base_url(base_s)
    except ValueError:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_LLM_BASE_URL",
                "message": _settings_message("E_LLM_BASE_URL"),
            },
        )
        return

    # 按服务商归一：勿把 DeepSeek 的 model/base_url 写进通义配置（或反之）
    model_s = coerce_model_for_provider(provider, model_s)
    base_s = coerce_base_url_for_provider(provider, base_s)

    secrets = UserLlmSecrets(
        provider=provider,
        api_key=api_key,
        model=model_s or None,
        base_url=base_s or None,
        region=region,
        last_ping_ok=None,
    )
    try:
        write_user_llm_secrets(secrets)
        write_user_llm_config_overlay(
            provider=provider, model=model_s, base_url=base_s, region=region
        )
        inject_secrets_into_environ(secrets)
        reset_config_cache()
    except OSError:
        handler._json_response(
            500,
            {
                "ok": False,
                "error": "E_STUDIO_CONFIG_WRITE",
                "message": user_message("E_STUDIO_CONFIG_WRITE"),
            },
        )
        return

    handler._json_response(200, _status_body())


def handle_llm_ping(handler: StudioHandlerProtocol) -> None:
    from travelogue.config.runtime import config_override
    from travelogue.llm.client import llm_ping

    payload = handler._read_json_body() or {}
    provider = str(payload.get("provider") or "").strip().lower() or None
    api_key = str(payload.get("apiKey") or payload.get("api_key") or "").strip() or None

    secrets = read_user_llm_secrets()
    prov = provider or secrets.provider
    if not prov or prov not in _ALLOWED:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_LLM_PROVIDER",
                "message": user_message("E_LLM_PROVIDER", "请先选择服务商"),
            },
        )
        return

    env_name = PROVIDER_PRESETS[prov]["api_key_env"]
    prev = os.environ.get(env_name)
    key_to_use = api_key or secrets.api_key
    if not key_to_use:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_LLM_AUTH",
                "message": _settings_message("E_LLM_AUTH"),
            },
        )
        return

    same_secrets = secrets.provider == prov
    region = normalize_llm_region(
        prov,
        payload.get("region") if payload.get("region") is not None else (secrets.region if same_secrets else None),
    )

    raw_base = (
        payload.get("baseUrl")
        or payload.get("base_url")
        or (secrets.base_url if same_secrets else None)
    )
    try:
        raw_base_s = validate_custom_base_url(str(raw_base).strip() if raw_base else None)
    except ValueError:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_LLM_BASE_URL",
                "message": _settings_message("E_LLM_BASE_URL"),
            },
        )
        return

    os.environ[env_name] = key_to_use
    base_cfg = get_config(reload=True)
    # 仅复用「同一服务商」的 secrets；禁止回落到 base_cfg 里另一家的 model/URL
    raw_model = payload.get("model") or (secrets.model if same_secrets else None)
    model_override = coerce_model_for_provider(
        prov, str(raw_model).strip() if raw_model else None
    )
    base_override = coerce_base_url_for_provider(prov, raw_base_s)
    # 无自定义时按地域解析；写入 cfg 以便 resolve 在 secrets 尚未更新时仍命中正确 host
    effective_base = base_override or preset_base_url(prov, region)
    llm = replace(
        base_cfg.llm,
        provider=prov,
        model=model_override,
        api_key_env=env_name,
        base_url=effective_base,
    )
    cfg = replace(base_cfg, llm=llm)

    # ping 时若带了 region/key，临时对齐 secrets 视图，避免 resolve 仍用旧地域
    ping_secrets = UserLlmSecrets(
        provider=prov,
        api_key=key_to_use,
        model=model_override,
        base_url=base_override,
        region=region,
        last_ping_ok=secrets.last_ping_ok if same_secrets else None,
    )

    def _read_ping_secrets() -> UserLlmSecrets:
        return ping_secrets

    try:
        import travelogue.llm.user_settings as us

        prev_read = us.read_user_llm_secrets
        us.read_user_llm_secrets = _read_ping_secrets  # type: ignore[assignment]
        try:
            with config_override(cfg):
                msg = llm_ping(provider=prov)
        finally:
            us.read_user_llm_secrets = prev_read  # type: ignore[assignment]

        # 成功简句（隐藏完整 URL · FE 亦可再格式化）
        label = "通义千问" if prov == "dashscope" else "DeepSeek"
        user_ok = f"已连通 · {label} · {model_override}"

        if secrets.configured and secrets.provider == prov and (
            not api_key or api_key == secrets.api_key
        ):
            # 合并本次 region/base（仅测试也可能刚改地域）
            stored = UserLlmSecrets(
                provider=secrets.provider,
                api_key=secrets.api_key,
                model=model_override or secrets.model,
                base_url=base_override if base_override is not None else secrets.base_url,
                region=region if prov == "dashscope" else None,
                last_ping_ok=True,
            )
            # 若仅测试且未保存过 region，写回便于下次 status
            if payload.get("region") is not None or base_override is not None:
                write_user_llm_secrets(stored)
                write_user_llm_config_overlay(
                    provider=prov,
                    model=stored.model,
                    base_url=stored.base_url,
                    region=stored.region,
                )
            else:
                write_user_llm_secrets(_with_ping(secrets, True))
        handler._json_response(
            200, {"ok": True, "message": user_ok or msg, **_status_body(cfg=cfg)}
        )
    except LlmError as exc:
        err_code = _classify_ping_error(exc)
        if secrets.configured and secrets.provider == prov and (
            not api_key or api_key == secrets.api_key
        ):
            write_user_llm_secrets(_with_ping(secrets, False))
        body: dict[str, Any] = {
            "ok": False,
            "error": err_code,
            "message": _settings_message(err_code, str(exc)),
        }
        try:
            for k, v in _status_body().items():
                if k != "ok":
                    body[k] = v
        except Exception:
            pass
        handler._json_response(400, body)
    finally:
        if prev is None:
            os.environ.pop(env_name, None)
            inject_secrets_into_environ()
        else:
            os.environ[env_name] = prev
