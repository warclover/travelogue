"""OpenAI-compatible chat completions (DeepSeek, DashScope)."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from travelogue.llm.errors import LlmError
from travelogue.llm.presets import PROVIDER_PRESETS
from travelogue.util.llm_presets import (
    coerce_model_for_provider,
    resolve_base_url_for_provider,
)

_RETRYABLE_HTTP = frozenset({429, 502, 503})
_RETRYABLE_URL_CODES = frozenset({"E_LLM_TIMEOUT", "E_LLM_NETWORK"})
_MAX_ATTEMPTS = 3
_RETRY_BASE_SEC = 1.0


@dataclass(frozen=True)
class LlmRuntime:
    provider: str
    model: str
    api_key: str
    base_url: str
    timeout_sec: int


def resolve_llm_runtime(
    provider: str | None = None,
    *,
    cfg: object | None = None,
    secrets: object | None = None,
) -> LlmRuntime:
    """Resolve provider, model, API key, and base URL for a chat call.

    When ``secrets`` is provided (request-local ``UserLlmSecrets``), credentials
    and endpoint are taken from that object — no ``os.environ`` mutation and no
    global ``read_user_llm_secrets`` monkey-patch (CQA D-CQA-02).
    """
    from travelogue.config import AppConfig, get_config

    if isinstance(cfg, AppConfig):
        llm = cfg.llm
    else:
        llm = cfg or get_config().llm
    prov = (provider or llm.provider or "stub").strip().lower()
    if prov == "stub":
        raise LlmError("E_LLM_STUB", "LLM provider is stub; set llm.provider in config.yaml")

    preset = PROVIDER_PRESETS.get(prov)
    if preset is None:
        raise LlmError("E_LLM_PROVIDER", f"unknown provider {prov!r}; use deepseek | dashscope | stub")

    api_key_env = (
        preset["api_key_env"]
        if provider and prov != (llm.provider or "").strip().lower()
        else (llm.api_key_env or preset["api_key_env"])
    )

    # Request-local secrets path (Studio ping / concurrent-safe).
    if secrets is not None:
        sec_provider = (getattr(secrets, "provider", None) or "").strip().lower()
        if sec_provider and sec_provider != prov:
            raise LlmError(
                "E_LLM_PROVIDER",
                f"secrets provider {sec_provider!r} does not match {prov!r}",
            )
        api_key = str(getattr(secrets, "api_key", None) or "").strip()
        if not api_key:
            raise LlmError("E_LLM_AUTH", f"missing API key for provider {prov}")
        llm_base = getattr(llm, "base_url", None)
        model = coerce_model_for_provider(prov, getattr(secrets, "model", None))
        base = resolve_base_url_for_provider(
            prov,
            getattr(secrets, "base_url", None) or llm_base,
            getattr(secrets, "region", None),
        )
        return LlmRuntime(
            provider=prov,
            model=model,
            api_key=api_key,
            base_url=base,
            timeout_sec=int(llm.timeout_sec),
        )

    api_key = os.environ.get(api_key_env, "").strip()
    if not api_key:
        # Desktop LLM Setup V1: fall back to user_data secrets (MF-DLLM-03).
        try:
            from travelogue.llm.user_settings import (
                inject_secrets_into_environ,
                read_user_llm_secrets,
            )

            disk_secrets = read_user_llm_secrets()
            inject_secrets_into_environ(disk_secrets)
            api_key = os.environ.get(api_key_env, "").strip()
            if not api_key and disk_secrets.api_key and disk_secrets.provider == prov:
                api_key = disk_secrets.api_key.strip()
        except Exception:
            pass
    if not api_key:
        raise LlmError("E_LLM_AUTH", f"missing API key env {api_key_env}")

    # Provider-scoped defaults: do not keep DeepSeek model/URL when using dashscope
    # (common after switching 服务商 while config.user.yaml still has leftovers).
    cfg_provider = (llm.provider or "").strip().lower()
    provider_switched = bool(provider and prov != cfg_provider)
    llm_base = getattr(llm, "base_url", None)
    if provider_switched:
        model = coerce_model_for_provider(prov, None)
        # Keep explicit endpoint from ping/settings cfg (may be region preset URL)
        base = resolve_base_url_for_provider(prov, llm_base, None)
    else:
        model = coerce_model_for_provider(prov, getattr(llm, "model", None))
        base = resolve_base_url_for_provider(prov, llm_base, None)
    try:
        from travelogue.llm.user_settings import read_user_llm_secrets

        disk_secrets = read_user_llm_secrets()
        if disk_secrets.provider == prov:
            if disk_secrets.model:
                model = coerce_model_for_provider(prov, disk_secrets.model)
            # secrets.base_url 自定义优先；否则按 region / cfg 解析
            base = resolve_base_url_for_provider(
                prov,
                disk_secrets.base_url if disk_secrets.base_url else llm_base,
                disk_secrets.region,
            )
    except Exception:
        pass
    return LlmRuntime(
        provider=prov,
        model=model,
        api_key=api_key,
        base_url=base,
        timeout_sec=int(llm.timeout_sec),
    )


def parse_json_content(raw: str) -> dict[str, Any]:
    """Parse LLM JSON output; tolerate optional markdown fences."""
    text = (raw or "").strip()
    if not text:
        raise LlmError("E_NARRATE_PARSE", "empty LLM response")
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LlmError("E_NARRATE_PARSE", f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise LlmError("E_NARRATE_PARSE", "LLM JSON root must be an object")
    return data


def _url_error_code(exc: urllib.error.URLError) -> str:
    reason = exc.reason
    if isinstance(reason, TimeoutError):
        return "E_LLM_TIMEOUT"
    if isinstance(reason, ConnectionRefusedError):
        return "E_LLM_CONNECT"
    if isinstance(reason, OSError) and reason.errno is not None:
        return "E_LLM_NETWORK"
    msg = str(reason or exc).lower()
    if "timed out" in msg or "timeout" in msg:
        return "E_LLM_TIMEOUT"
    return "E_LLM_NETWORK"


def _http_error_retryable(exc: urllib.error.HTTPError) -> bool:
    return exc.code in _RETRYABLE_HTTP


def _url_error_retryable(exc: urllib.error.URLError) -> bool:
    return _url_error_code(exc) in _RETRYABLE_URL_CODES


def _post_chat(req: urllib.request.Request, *, timeout_sec: int) -> dict[str, Any]:
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _extract_content(data: dict[str, Any]) -> str:
    try:
        return str(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise LlmError("E_LLM_RESPONSE", f"unexpected response shape: {data!r}") from exc


def chat_completion(
    messages: list[dict[str, Any]],
    *,
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    runtime: LlmRuntime | None = None,
    json_mode: bool = True,
    shared_backoff: bool = False,
) -> str:
    """Call OpenAI-compatible /chat/completions and return assistant content.

    When ``shared_backoff`` is true, wait on the process-wide provider gate and
    advance it on 429/502/503 (Pipeline Throughput · narrate concurrency).
    """
    from travelogue.llm.shared_backoff import get_shared_backoff

    rt = runtime or resolve_llm_runtime(provider)
    use_model = model or rt.model
    url = f"{rt.base_url}/chat/completions"
    payload: dict[str, Any] = {
        "model": use_model,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {rt.api_key}",
        },
        method="POST",
    )

    backoff = get_shared_backoff() if shared_backoff else None
    last_http: urllib.error.HTTPError | None = None
    for attempt in range(_MAX_ATTEMPTS):
        if backoff is not None:
            backoff.wait_turn()
        try:
            data = _post_chat(req, timeout_sec=rt.timeout_sec)
            return _extract_content(data)
        except urllib.error.HTTPError as exc:
            last_http = exc
            if not _http_error_retryable(exc) or attempt >= _MAX_ATTEMPTS - 1:
                detail = exc.read().decode("utf-8", errors="replace")[:400]
                raise LlmError("E_LLM_HTTP", f"HTTP {exc.code}: {detail}") from exc
            retry_after = None
            raw_ra = exc.headers.get("Retry-After") if exc.headers else None
            if raw_ra:
                try:
                    retry_after = float(raw_ra)
                except ValueError:
                    retry_after = None
            if backoff is not None:
                backoff.note_rate_limit(retry_after_sec=retry_after, attempt=attempt)
            else:
                time.sleep(_RETRY_BASE_SEC * (2**attempt))
        except urllib.error.URLError as exc:
            if _url_error_retryable(exc) and attempt < _MAX_ATTEMPTS - 1:
                if backoff is not None:
                    backoff.note_rate_limit(attempt=attempt)
                else:
                    time.sleep(_RETRY_BASE_SEC * (2**attempt))
                continue
            code = _url_error_code(exc)
            raise LlmError(code, str(exc.reason)) from exc
        except TimeoutError as exc:
            raise LlmError("E_LLM_TIMEOUT", "request timed out") from exc

    if last_http is None:
        raise LlmError("E_LLM_HTTP", "no HTTP response after retries")
    detail = last_http.read().decode("utf-8", errors="replace")[:400]
    raise LlmError("E_LLM_HTTP", f"HTTP {last_http.code}: {detail}") from last_http


def vision_chat_completion(
    messages: list[dict[str, Any]],
    *,
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.0,
    runtime: LlmRuntime | None = None,
    json_mode: bool = True,
) -> str:
    """Multimodal chat (text + image_url blocks in message content)."""
    return chat_completion(
        messages,
        provider=provider,
        model=model,
        temperature=temperature,
        runtime=runtime,
        json_mode=json_mode,
    )


def llm_ping(
    *,
    provider: str | None = None,
    secrets: object | None = None,
    cfg: object | None = None,
    runtime: LlmRuntime | None = None,
) -> str:
    """Minimal chat to verify credentials and connectivity.

    Pass request-local ``secrets`` / ``cfg`` / ``runtime`` to avoid process-global
    credential injection (CQA D-CQA-02).
    """
    rt = runtime or resolve_llm_runtime(provider, cfg=cfg, secrets=secrets)
    content = chat_completion(
        [
            {"role": "system", "content": "Reply with JSON only."},
            {"role": "user", "content": '{"ok": true}'},
        ],
        provider=provider,
        temperature=0,
        runtime=rt,
    )
    data = parse_json_content(content)
    if data.get("ok") is not True:
        raise LlmError("E_LLM_PING", f"unexpected ping payload: {data!r}")
    return f"{rt.provider}/{rt.model} @ {rt.base_url}"
