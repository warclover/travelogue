"""ACP LLM call helpers · hard timeout (D-ACP-13)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Any

from travelogue.ai.gate import timeout_sec
from travelogue.config import AppConfig, get_config
from travelogue.llm.client import chat_completion
from travelogue.llm.errors import LlmError


def chat_with_timeout(
    messages: Sequence[dict[str, str]],
    *,
    cfg: AppConfig | None = None,
    chat_fn: Callable[[list[dict[str, str]]], str] | None = None,
    timeout: float | None = None,
) -> str:
    """Run chat with ACP ``timeout_sec`` hard limit; raises ``LlmError`` on timeout."""
    app_cfg = cfg or get_config()
    limit = float(timeout if timeout is not None else timeout_sec(cfg=app_cfg))
    payload = list(messages)

    def _invoke() -> str:
        if chat_fn is not None:
            return chat_fn(payload)
        return chat_completion(payload)

    if limit <= 0:
        return _invoke()
    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_invoke)
        try:
            return fut.result(timeout=limit)
        except FuturesTimeout as exc:
            fut.cancel()
            raise LlmError("E_ACP_TIMEOUT", f"LLM call exceeded {limit}s") from exc


def vision_or_chat_safe(
    invoke: Callable[[], Any],
    *,
    cfg: AppConfig | None = None,
    timeout: float | None = None,
) -> Any:
    """Generic hard-timeout wrapper for any blocking LLM/VLM invoke."""
    app_cfg = cfg or get_config()
    limit = float(timeout if timeout is not None else timeout_sec(cfg=app_cfg))
    if limit <= 0:
        return invoke()
    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(invoke)
        try:
            return fut.result(timeout=limit)
        except FuturesTimeout as exc:
            fut.cancel()
            raise LlmError("E_ACP_TIMEOUT", f"LLM call exceeded {limit}s") from exc
