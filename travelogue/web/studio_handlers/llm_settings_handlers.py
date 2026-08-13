"""Studio LLM settings API (Desktop LLM Setup V1 · W1a · WEA W1)."""

from __future__ import annotations

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
    preset_base_url,
    validate_custom_base_url,
)
from travelogue.web.studio_errors import user_message
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from travelogue.web.studio_narrate import studio_llm_status

_STUDIO_PROVIDER = "dashscope"

COPY_BAI_04 = "已连接通义百炼"
COPY_BAI_09 = "通义百炼额度不足。请到控制台关闭「仅使用免费额度」或充值后再试。"
COPY_BAI_10 = "请改用通义百炼 API Key。杂志文案和封面字体都在这一把 Key 上。"

# 配置面可行动文案（BAI W1a · 用户面不提 DeepSeek / 国际站 / 模型 id）
_SETTINGS_MESSAGES: dict[str, str] = {
    "E_LLM_AUTH": "Key 无效或已失效。请回控制台重新创建并粘贴。",
    "E_LLM_ENDPOINT": "无法连接通义百炼。请检查网络后重试。",
    "E_LLM_MODEL": "连接测试失败，请检查 Key 或网络后重试。",
    "E_LLM_QUOTA": COPY_BAI_09,
    "E_LLM_QUOTA_FREE_TIER": COPY_BAI_09,
    "E_LLM_RATE": "服务商繁忙，请稍后重试。",
    "E_LLM_TIMEOUT": "无法连接服务商。请检查网络后重试。",
    "E_LLM_NETWORK": "无法连接服务商。请检查网络后重试。",
    "E_LLM_CONNECT": "无法连接服务商。请检查网络后重试。",
    "E_LLM_BASE_URL": "无法连接通义百炼。请检查网络后重试。",
    "E_LLM_PING": "连接测试失败，请检查 Key 或网络后重试。",
    "E_LLM_PROVIDER": COPY_BAI_10,
}

_QUOTA_MARKERS = (
    "quota",
    "balance",
    "insufficient",
    "arrearage",
    "额度",
    "余额",
    "freetier",
    "free tier",
    "free_tier",
    "allocationquota",
)


def _settings_message(code: str, fallback: str = "") -> str:
    if code in _SETTINGS_MESSAGES:
        return _SETTINGS_MESSAGES[code]
    return user_message(code, fallback)


def _classify_ping_error(exc: LlmError) -> str:
    """Map LlmError → settings-facing code (AUTH / ENDPOINT / TIMEOUT / …).

    DashScope「FreeTierOnly」常以 HTTP 403 返回，须在 AUTH 之前识别为配额，
    避免误提示「Key 无效」。
    """
    code = exc.code or "E_LLM_PING"
    detail = f"{exc.message or ''} {exc}".lower()
    if code in ("E_LLM_TIMEOUT", "E_LLM_NETWORK", "E_LLM_CONNECT"):
        return "E_LLM_TIMEOUT" if code == "E_LLM_TIMEOUT" else "E_LLM_NETWORK"
    if code == "E_LLM_AUTH":
        return "E_LLM_AUTH"
    if code == "E_LLM_HTTP":
        m = re.search(r"http\s+(\d{3})", detail)
        status = int(m.group(1)) if m else 0
        # 配额 / 免费额度（含 403 FreeTierOnly）优先于笼统 AUTH
        if any(k in detail for k in _QUOTA_MARKERS):
            if any(
                k in detail
                for k in ("freetier", "free tier", "free_tier", "allocationquota.freetier")
            ):
                return "E_LLM_QUOTA_FREE_TIER"
            return "E_LLM_QUOTA"
        if status == 401:
            return "E_LLM_AUTH"
        if status == 403:
            return "E_LLM_AUTH"
        if status == 429:
            return "E_LLM_RATE"
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


def _with_ping(
    secrets: UserLlmSecrets, ok: bool, *, model: str | None = None
) -> UserLlmSecrets:
    return UserLlmSecrets(
        provider=secrets.provider,
        api_key=secrets.api_key,
        model=model if model is not None else secrets.model,
        base_url=secrets.base_url,
        region=secrets.region,
        last_ping_ok=ok,
        last_image_ok=secrets.last_image_ok,
    )


def _status_body(*, cfg: Any = None) -> dict[str, Any]:
    # 不注入进程环境：Ready 走 request-local secrets（与 ping 隔离一致）
    app_cfg = cfg if cfg is not None else get_config(reload=True)
    status = studio_llm_status(cfg=app_cfg, inject_environ=False)
    secrets = read_user_llm_secrets()
    studio_on = secrets.studio_configured
    ready = readiness_state(secrets)
    available = bool(status.get("llmAvailable"))
    connection_ok = bool(status.get("connectionOk"))
    # L1 = 百炼已配置且 ping 成功（DeepSeek-only 仍为 L0）
    tier = "L1" if studio_on and secrets.last_ping_ok is True else "L0"
    return {
        "ok": True,
        **status,
        "tier": tier,
        "llmTier": tier,
        "configured": studio_on,
        "readiness": ready,
        "maskedKey": mask_api_key(secrets.api_key) if studio_on else None,
        "lastPingOk": secrets.last_ping_ok if studio_on else None,
        "connectionOk": connection_ok,
        "copyReady": connection_ok,
        "imageReady": bool(status.get("imageReady")),
        "hasDashscope": studio_on,
        "legacyKeyOnDisk": bool(secrets.configured and not studio_on),
        "region": "cn" if studio_on else None,
        "userDataDir": str(user_data_dir(ensure=False)),
        "tripsDir": str(getattr(app_cfg, "trips_dir", "") or ""),
        "capabilities": {
            "import": True,
            "layout": True,
            "stubNarrate": True,
            "llmNarrate": available,
            "longshot": True,
        },
    }


def handle_llm_status(handler: StudioHandlerProtocol) -> None:
    # SAS · D-SAS-07：连接状态可读（关闸亦可预配 Key）；烧模型仍由 narrate 等门控
    handler._json_response(200, _status_body())


def handle_llm_settings(handler: StudioHandlerProtocol) -> None:
    # SAS · D-SAS-07：settings 写/删不要求开闸（AI Sheet allowWhenSurfaceOff）
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
    provider_in = str(payload.get("provider") or "").strip().lower()
    api_key = str(payload.get("apiKey") or payload.get("api_key") or "").strip()

    if provider_in == "deepseek":
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_LLM_PROVIDER",
                "message": COPY_BAI_10,
            },
        )
        return

    if provider_in and provider_in != _STUDIO_PROVIDER:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_LLM_PROVIDER",
                "message": COPY_BAI_10,
            },
        )
        return

    provider = _STUDIO_PROVIDER
    existing = read_user_llm_secrets()
    if not api_key:
        if existing.studio_configured and existing.api_key:
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

    # V1 正式包：忽略客户端模型 / 自定义 URL / 国际站；磁盘旧字段可留
    model_s = existing.model if existing.studio_configured else None
    base_s = existing.base_url if existing.studio_configured else None
    region = "cn"

    secrets = UserLlmSecrets(
        provider=provider,
        api_key=api_key,
        model=model_s or None,
        base_url=base_s or None,
        region=region,
        last_ping_ok=None,
        last_image_ok=None,
    )
    try:
        write_user_llm_secrets(secrets)
        write_user_llm_config_overlay(
            provider=provider, model=None, base_url=None, region=region
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
    from travelogue.llm.client import llm_ping

    # SAS · D-SAS-07：ping 不要求开闸（保存并测试 / 预配 Key）
    payload = handler._read_json_body() or {}
    provider_in = str(payload.get("provider") or "").strip().lower() or None
    api_key = str(payload.get("apiKey") or payload.get("api_key") or "").strip() or None

    if provider_in == "deepseek" or (provider_in and provider_in != _STUDIO_PROVIDER):
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_LLM_PROVIDER",
                "message": COPY_BAI_10,
            },
        )
        return

    prov = _STUDIO_PROVIDER
    secrets = read_user_llm_secrets()
    env_name = PROVIDER_PRESETS[prov]["api_key_env"]
    key_to_use = api_key or (secrets.api_key if secrets.studio_configured else None)
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

    same_secrets = secrets.studio_configured
    # V1 只中国站；磁盘旧 intl/custom 仍可用于请求，但不接受客户端改写
    region = secrets.region if same_secrets and secrets.region else "cn"
    raw_base = secrets.base_url if same_secrets else None
    try:
        raw_base_s = validate_custom_base_url(str(raw_base).strip() if raw_base else None)
    except ValueError:
        raw_base_s = None

    base_cfg = get_config(reload=True)
    # 运行时忽略用户模型字段，走服务端默认（D-BAI-02）
    model_override = coerce_model_for_provider(prov, None)
    base_override = coerce_base_url_for_provider(prov, raw_base_s)
    effective_base = base_override or preset_base_url(prov, region)
    llm = replace(
        base_cfg.llm,
        provider=prov,
        model=model_override,
        api_key_env=env_name,
        base_url=effective_base,
    )
    cfg = replace(base_cfg, llm=llm)

    ping_secrets = UserLlmSecrets(
        provider=prov,
        api_key=key_to_use,
        model=model_override,
        base_url=base_override,
        region=region,
        last_ping_ok=secrets.last_ping_ok if same_secrets else None,
    )

    want_persist = (
        bool(payload.get("persist"))
        and secrets.studio_configured
        and (not api_key or api_key == secrets.api_key)
    )

    try:
        llm_ping(provider=prov, secrets=ping_secrets, cfg=cfg)
        user_ok = COPY_BAI_04

        persisted = False
        if want_persist:
            try:
                # 不把级联后的 model id 写回磁盘（D-BAI-09）
                write_user_llm_secrets(_with_ping(secrets, True, model=secrets.model))
                persisted = True
            except OSError:
                status = _status_body(cfg=cfg)
                handler._json_response(
                    500,
                    {
                        "ok": False,
                        "error": "E_STUDIO_CONFIG_WRITE",
                        "message": "已连通，但未能保存状态。请重试保存。",
                        "pingOk": True,
                        "persisted": False,
                        **{k: v for k, v in status.items() if k != "ok"},
                    },
                )
                return

        status = _status_body(cfg=cfg)
        handler._json_response(
            200,
            {
                "ok": True,
                "message": user_ok,
                "pingOk": True,
                "persisted": persisted,
                **status,
            },
        )
    except LlmError as exc:
        err_code = _classify_ping_error(exc)
        persisted = False
        if want_persist:
            try:
                write_user_llm_secrets(_with_ping(secrets, False))
                persisted = True
            except OSError:
                persisted = False
        body: dict[str, Any] = {
            "ok": False,
            "error": err_code,
            "message": _settings_message(err_code, str(exc)),
            "pingOk": False,
            "persisted": persisted,
        }
        try:
            for k, v in _status_body(cfg=cfg).items():
                if k != "ok":
                    body[k] = v
        except Exception:
            pass
        handler._json_response(400, body)
