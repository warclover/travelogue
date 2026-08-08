"""Route C · fixed-prompt layered diffusion (PRD §5.5 · D-CAL-14~19).

调用 DashScope 通义万相文生图 API（异步提交 + 轮询），产出"白底黑字"原图，
交由调用方 OCR 回读校验 + 抠字重上色。任何一步失败都抛出
:class:`RouteCFailure`，绝不返回半成品——调用方（engine.py）捕获后必须走
D-CAL-16 分层 fallback 到路线 B，本模块自身不做兜底。

2026-08-07 API 验证记录（用户已提供 key 现场实测，见 chat/PRD 附录）：
``wanx2.1-t2i-turbo`` 对"拾光"二字出现"光"字形笔画错误；
``wanx2.1-t2i-plus`` 实测字形正确 —— 因此默认模型选用 plus，turbo 仅作为
显式指定时的备选（成本/速度更优但字形风险更高，不作为默认）。
"""

from __future__ import annotations

import io
import json
import logging
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from PIL import Image

from travelogue.cover_engine.title_art.style_registry import (
    CalligraphyStyle,
    get_style,
    render_prompt,
)

_log = logging.getLogger(__name__)

_SUBMIT_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
_TASK_URL_TMPL = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"

#: D-CAL-18 · 2026-08-07 实测 plus 字形正确率优于 turbo，定为默认模型。
DEFAULT_MODEL = "wanx2.1-t2i-plus"

_POLL_INTERVAL_SEC = 2.0
_POLL_MAX_ATTEMPTS = 30
_REQUEST_TIMEOUT_SEC = 20
_API_KEY_ENV = "DASHSCOPE_API_KEY"


class RouteCFailure(RuntimeError):
    """任一门槛失败（提交/轮询/超时/审核/OCR 不通过）→ 调用方须 fallback（D-CAL-16）。"""

    def __init__(self, reason: str, *, detail: str = ""):
        message = f"{reason}: {detail}" if detail else reason
        super().__init__(message)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class RouteCRawResult:
    image: Image.Image  # 白底黑字原图（未抠字未上色）
    style: CalligraphyStyle
    model: str
    actual_prompt: str


def _api_key() -> str:
    key = os.environ.get(_API_KEY_ENV, "").strip()
    if not key:
        raise RouteCFailure("E_CAL_C_NOKEY", detail=f"{_API_KEY_ENV} not set")
    return key


def _submit_task(prompt: str, negative_prompt: str, *, model: str, size: str = "1024*1024") -> str:
    body = {
        "model": model,
        "input": {"prompt": prompt, "negative_prompt": negative_prompt},
        "parameters": {"size": size, "n": 1},
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        _SUBMIT_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json; charset=utf-8",
            "X-DashScope-Async": "enable",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT_SEC) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RouteCFailure("E_CAL_C_SUBMIT_HTTP", detail=detail) from exc
    except urllib.error.URLError as exc:
        raise RouteCFailure("E_CAL_C_SUBMIT_NETWORK", detail=str(exc.reason)) from exc
    task_id = str((payload.get("output") or {}).get("task_id") or "").strip()
    if not task_id:
        raise RouteCFailure(
            "E_CAL_C_SUBMIT_NO_TASK", detail=json.dumps(payload, ensure_ascii=False)[:300]
        )
    return task_id


def _poll_task(task_id: str) -> dict:
    req = urllib.request.Request(
        _TASK_URL_TMPL.format(task_id=task_id),
        headers={"Authorization": f"Bearer {_api_key()}"},
        method="GET",
    )
    for _attempt in range(_POLL_MAX_ATTEMPTS):
        time.sleep(_POLL_INTERVAL_SEC)
        try:
            with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT_SEC) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise RouteCFailure("E_CAL_C_POLL_NETWORK", detail=str(exc)) from exc
        status = str((payload.get("output") or {}).get("task_status") or "")
        if status == "SUCCEEDED":
            return payload
        if status == "FAILED":
            raise RouteCFailure(
                "E_CAL_C_TASK_FAILED",
                detail=str((payload.get("output") or {}).get("message") or ""),
            )
    raise RouteCFailure("E_CAL_C_TIMEOUT", detail=f"task {task_id} exceeded poll budget")


def _download_image(url: str) -> Image.Image:
    try:
        with urllib.request.urlopen(url, timeout=_REQUEST_TIMEOUT_SEC) as resp:
            raw = resp.read()
    except urllib.error.URLError as exc:
        raise RouteCFailure("E_CAL_C_DOWNLOAD", detail=str(exc)) from exc
    return Image.open(io.BytesIO(raw)).convert("RGBA")


def generate_raw(
    style_id: str,
    *,
    title: str,
    subtitle: str | None = None,
    model: str | None = None,
    prompt_version: str = "v2",
) -> RouteCRawResult:
    """提交 + 轮询通义万相；返回未抠字/未上色的原图。

    失败即抛 :class:`RouteCFailure`；调用方必须 fallback（D-CAL-16）。
    """
    style = get_style(style_id, prompt_version=prompt_version)
    if style is None:
        raise RouteCFailure(
            "E_CAL_C_UNKNOWN_STYLE",
            detail=f"{style_id}@{prompt_version}",
        )
    prompt = render_prompt(style, title=title, subtitle=subtitle)
    use_model = model or DEFAULT_MODEL
    task_id = _submit_task(prompt, style.negative_prompt, model=use_model)
    payload = _poll_task(task_id)
    results = (payload.get("output") or {}).get("results") or []
    if not results:
        raise RouteCFailure("E_CAL_C_NO_RESULT")
    url = str(results[0].get("url") or "")
    actual_prompt = str(results[0].get("actual_prompt") or prompt)
    if not url:
        raise RouteCFailure("E_CAL_C_NO_URL")
    image = _download_image(url)
    return RouteCRawResult(image=image, style=style, model=use_model, actual_prompt=actual_prompt)
