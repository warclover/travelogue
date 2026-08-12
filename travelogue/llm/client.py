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
    dashscope_model_candidates,
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


def _is_model_quota_error(exc: LlmError) -> bool:
    """Free-tier / quota errors that warrant trying the next DashScope model."""
    detail = f"{exc.message or ''} {exc}".lower()
    return any(
        k in detail
        for k in (
            "freetier",
            "free tier",
            "free_tier",
            "allocationquota",
            "quota",
            "insufficient",
            "arrearage",
            "额度",
            "余额",
        )
    )


def _chat_completion_single(
    messages: list[dict[str, Any]],
    *,
    use_model: str,
    temperature: float,
    runtime: LlmRuntime,
    json_mode: bool,
    shared_backoff: bool,
    max_attempts: int | None,
) -> str:
    from travelogue.llm.shared_backoff import get_shared_backoff

    url = f"{runtime.base_url}/chat/completions"
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
            "Authorization": f"Bearer {runtime.api_key}",
        },
        method="POST",
    )

    attempts = _MAX_ATTEMPTS if max_attempts is None else max(1, int(max_attempts))
    backoff = get_shared_backoff() if shared_backoff else None
    last_http: urllib.error.HTTPError | None = None
    for attempt in range(attempts):
        if backoff is not None:
            backoff.wait_turn()
        try:
            data = _post_chat(req, timeout_sec=runtime.timeout_sec)
            return _extract_content(data)
        except urllib.error.HTTPError as exc:
            last_http = exc
            if not _http_error_retryable(exc) or attempt >= attempts - 1:
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
            if _url_error_retryable(exc) and attempt < attempts - 1:
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


def chat_completion(
    messages: list[dict[str, Any]],
    *,
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    runtime: LlmRuntime | None = None,
    json_mode: bool = True,
    shared_backoff: bool = False,
    max_attempts: int | None = None,
    model_failover: bool = True,
) -> str:
    """Call OpenAI-compatible /chat/completions and return assistant content.

    When ``shared_backoff`` is true, wait on the process-wide provider gate and
    advance it on 429/502/503 (Pipeline Throughput · narrate concurrency).

    For DashScope, ``model_failover`` tries free-tier-friendly models then
    qwen-plus/turbo/max when the current model hits FreeTierOnly / quota.
    """
    rt = runtime or resolve_llm_runtime(provider)
    use_model = model or rt.model
    candidates = (
        dashscope_model_candidates(use_model)
        if model_failover and rt.provider == "dashscope"
        else [use_model]
    )
    last_err: LlmError | None = None
    for cand in candidates:
        try:
            return _chat_completion_single(
                messages,
                use_model=cand,
                temperature=temperature,
                runtime=rt,
                json_mode=json_mode,
                shared_backoff=shared_backoff,
                max_attempts=max_attempts,
            )
        except LlmError as exc:
            last_err = exc
            if not model_failover or not _is_model_quota_error(exc):
                raise
            continue
    assert last_err is not None
    raise last_err


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
        model_failover=False,
    )


_PING_TIMEOUT_SEC = 20
_PING_MAX_ATTEMPTS = 2


def llm_ping(
    *,
    provider: str | None = None,
    secrets: object | None = None,
    cfg: object | None = None,
    runtime: LlmRuntime | None = None,
) -> str:
    """Minimal chat to verify credentials and connectivity.

    Pass request-local ``secrets`` / ``cfg`` / ``runtime`` to avoid process-global
    credential injection (CQA D-CQA-02). Uses a short timeout; retries without
    ``response_format`` when the model rejects JSON mode.

    DashScope：按免费额度友好模型 → qwen-plus/turbo/max 级联探测，
    返回串中的 model 为实际打通的模型。
    """
    from dataclasses import replace

    rt = runtime or resolve_llm_runtime(provider, cfg=cfg, secrets=secrets)
    rt = replace(rt, timeout_sec=min(int(rt.timeout_sec), _PING_TIMEOUT_SEC))
    messages = [
        {"role": "system", "content": "Reply with JSON only."},
        {"role": "user", "content": '{"ok": true}'},
    ]
    candidates = (
        dashscope_model_candidates(rt.model)
        if rt.provider == "dashscope"
        else [rt.model]
    )
    last_err: LlmError | None = None
    used_model = rt.model

    for cand in candidates:
        cand_rt = replace(rt, model=cand)

        def _once(*, json_mode: bool, _rt: LlmRuntime = cand_rt) -> str:
            return chat_completion(
                messages,
                provider=provider,
                temperature=0,
                runtime=_rt,
                json_mode=json_mode,
                max_attempts=_PING_MAX_ATTEMPTS,
                model_failover=False,
            )

        try:
            try:
                content = _once(json_mode=True)
            except LlmError as exc:
                if exc.code in ("E_LLM_HTTP", "E_LLM_RESPONSE", "E_LLM_MODEL"):
                    if _is_model_quota_error(exc):
                        raise
                    content = _once(json_mode=False)
                else:
                    raise
            try:
                data = parse_json_content(content)
                if data.get("ok") is not True:
                    raise LlmError("E_LLM_PING", f"unexpected ping payload: {data!r}")
            except LlmError:
                if not str(content or "").strip():
                    raise
            used_model = cand
            return f"{rt.provider}/{used_model} @ {rt.base_url}"
        except LlmError as exc:
            last_err = exc
            if rt.provider == "dashscope" and _is_model_quota_error(exc):
                continue
            raise

    assert last_err is not None
    raise last_err
