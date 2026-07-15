"""Studio LLM settings API (Desktop LLM Setup V1 · W1a)."""

from __future__ import annotations

import os
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
from travelogue.util.llm_presets import PROVIDER_PRESETS
from travelogue.web.studio_errors import client_error_payload, user_message
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol
from travelogue.web.studio_narrate import studio_llm_status

_ALLOWED = frozenset({"deepseek", "dashscope"})


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
    return {
        "ok": True,
        **status,
        "tier": tier,
        "llmTier": tier,
        "configured": secrets.configured,
        "readiness": ready,
        "maskedKey": mask_api_key(secrets.api_key),
        "lastPingOk": secrets.last_ping_ok,
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
    if not api_key:
        handler._json_response(
            400,
            {
                "ok": False,
                "error": "E_LLM_AUTH",
                "message": user_message("E_LLM_AUTH"),
            },
        )
        return

    secrets = UserLlmSecrets(
        provider=provider,
        api_key=api_key,
        model=model_s or None,
        base_url=base_s or None,
        last_ping_ok=None,
    )
    try:
        write_user_llm_secrets(secrets)
        write_user_llm_config_overlay(provider=provider, model=model_s, base_url=base_s)
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
                "message": user_message("E_LLM_AUTH"),
            },
        )
        return

    os.environ[env_name] = key_to_use
    base_cfg = get_config(reload=True)
    model_override = payload.get("model") or secrets.model or base_cfg.llm.model
    base_override = (
        payload.get("baseUrl")
        or payload.get("base_url")
        or secrets.base_url
        or base_cfg.llm.base_url
    )
    llm = replace(
        base_cfg.llm,
        provider=prov,
        model=str(model_override or ""),
        api_key_env=env_name,
        base_url=str(base_override).strip() if base_override else None,
    )
    cfg = replace(base_cfg, llm=llm)

    try:
        with config_override(cfg):
            msg = llm_ping(provider=prov)
        if secrets.configured and secrets.provider == prov and (
            not api_key or api_key == secrets.api_key
        ):
            write_user_llm_secrets(
                UserLlmSecrets(
                    provider=secrets.provider,
                    api_key=secrets.api_key,
                    model=secrets.model,
                    base_url=secrets.base_url,
                    last_ping_ok=True,
                )
            )
        handler._json_response(200, {"ok": True, "message": msg, **_status_body(cfg=cfg)})
    except LlmError as exc:
        if secrets.configured and secrets.provider == prov and (
            not api_key or api_key == secrets.api_key
        ):
            write_user_llm_secrets(
                UserLlmSecrets(
                    provider=secrets.provider,
                    api_key=secrets.api_key,
                    model=secrets.model,
                    base_url=secrets.base_url,
                    last_ping_ok=False,
                )
            )
        body = client_error_payload(exc)
        body["ok"] = False
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
