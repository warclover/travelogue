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


def resolve_llm_runtime(provider: str | None = None, *, cfg: object | None = None) -> LlmRuntime:
    """Resolve provider, model, API key, and base URL for a chat call."""
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
    api_key = os.environ.get(api_key_env, "").strip()
    if not api_key:
        raise LlmError("E_LLM_AUTH", f"missing API key env {api_key_env}")

    model = (llm.model or preset["default_model"]).strip()
    base = (llm.base_url or preset["base_url"]).rstrip("/")
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
    messages: list[dict[str, str]],
    *,
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    runtime: LlmRuntime | None = None,
) -> str:
    """Call OpenAI-compatible /chat/completions and return assistant content."""
    rt = runtime or resolve_llm_runtime(provider)
    use_model = model or rt.model
    url = f"{rt.base_url}/chat/completions"
    payload = {
        "model": use_model,
        "messages": messages,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
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

    last_http: urllib.error.HTTPError | None = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            data = _post_chat(req, timeout_sec=rt.timeout_sec)
            return _extract_content(data)
        except urllib.error.HTTPError as exc:
            last_http = exc
            if not _http_error_retryable(exc) or attempt >= _MAX_ATTEMPTS - 1:
                detail = exc.read().decode("utf-8", errors="replace")[:400]
                raise LlmError("E_LLM_HTTP", f"HTTP {exc.code}: {detail}") from exc
            time.sleep(_RETRY_BASE_SEC * (2**attempt))
        except urllib.error.URLError as exc:
            if _url_error_retryable(exc) and attempt < _MAX_ATTEMPTS - 1:
                time.sleep(_RETRY_BASE_SEC * (2**attempt))
                continue
            code = _url_error_code(exc)
            raise LlmError(code, str(exc.reason)) from exc
        except TimeoutError as exc:
            raise LlmError("E_LLM_TIMEOUT", "request timed out") from exc

    assert last_http is not None
    detail = last_http.read().decode("utf-8", errors="replace")[:400]
    raise LlmError("E_LLM_HTTP", f"HTTP {last_http.code}: {detail}") from last_http


def llm_ping(*, provider: str | None = None) -> str:
    """Minimal chat to verify credentials and connectivity."""
    content = chat_completion(
        [
            {"role": "system", "content": "Reply with JSON only."},
            {"role": "user", "content": '{"ok": true}'},
        ],
        provider=provider,
        temperature=0,
    )
    data = parse_json_content(content)
    if data.get("ok") is not True:
        raise LlmError("E_LLM_PING", f"unexpected ping payload: {data!r}")
    rt = resolve_llm_runtime(provider)
    return f"{rt.provider}/{rt.model} @ {rt.base_url}"
