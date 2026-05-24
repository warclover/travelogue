"""OpenAI-compatible chat completions (DeepSeek, DashScope)."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from travelogue.llm.errors import LlmError
from travelogue.llm.presets import PROVIDER_PRESETS
class LlmRuntime:
    provider: str
    model: str
    api_key: str
    base_url: str
    timeout_sec: int


def resolve_llm_runtime(provider: str | None = None, *, cfg: object | None = None) -> LlmRuntime:
    """Resolve provider, model, API key, and base URL for a chat call."""
    from travelogue.config import get_config

    llm = cfg or get_config().llm
    prov = (provider or llm.provider or "stub").strip().lower()
    if prov == "stub":
        raise LlmError("E_LLM_STUB", "LLM provider is stub; set llm.provider in config.yaml")

    preset = PROVIDER_PRESETS.get(prov)
    if preset is None:
        raise LlmError("E_LLM_PROVIDER", f"unknown provider {prov!r}; use deepseek | dashscope | stub")

    api_key_env = llm.api_key_env or preset["api_key_env"]
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
    try:
        with urllib.request.urlopen(req, timeout=rt.timeout_sec) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        raise LlmError("E_LLM_HTTP", f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LlmError("E_LLM_TIMEOUT", str(exc.reason)) from exc
    except TimeoutError as exc:
        raise LlmError("E_LLM_TIMEOUT", "request timed out") from exc

    try:
        return str(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise LlmError("E_LLM_RESPONSE", f"unexpected response shape: {data!r}") from exc


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
