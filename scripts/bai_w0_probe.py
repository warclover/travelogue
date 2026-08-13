"""BAI W0 live probe: copy models, non-stream thinking, OCR contract, t2i protocol.

Never prints API keys. HTTP bodies are truncated and sk- prefixes stripped.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from io import BytesIO
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from travelogue.cover_engine.title_art.ocr_verify import _image_to_data_url  # noqa: E402
from travelogue.cover_engine.title_art.route_c import (  # noqa: E402
    DEFAULT_MODEL as WANX_DEFAULT,
    _SUBMIT_URL,
    _TASK_URL_TMPL,
)
from travelogue.env import load_dotenv_files  # noqa: E402
from travelogue.llm.client import (  # noqa: E402
    chat_completion,
    parse_json_content,
    resolve_llm_runtime,
    vision_chat_completion,
)
from travelogue.llm.errors import LlmError  # noqa: E402
from travelogue.llm.user_settings import (  # noqa: E402
    inject_secrets_into_environ,
    read_user_llm_secrets,
)

CHAT_URL_SUFFIX = "/chat/completions"
SECRET_RE = re.compile(r"sk-[A-Za-z0-9]+", re.I)

COPY_MODELS = (
    "qwen3.7-flash",
    "deepseek-v4-flash-0731",
    "deepseek-v4-pro",
)
THINKING_MODELS = ("deepseek-v4-pro", "deepseek-v4-flash-0731")
OCR_MODELS = ("qwen3.5-ocr", "qwen3.7-flash", "qwen-vl-plus")
T2I_MODELS = (
    WANX_DEFAULT,
    "wan2.7-image-pro",
    "qwen-image-3.0-pro",
    "wan2.2-t2i-plus",
)

NARRATE_SYSTEM = (
    "你是旅行视觉游记的文案编辑。只输出合法 JSON，不写 HTML。"
    "中文短句，禁止套话。"
)
NARRATE_USER = json.dumps(
    {
        "task": "fill magazine copy",
        "brief": {
            "place": "京都",
            "moment": "雨停后的清水寺石阶",
            "limits": {"hook": 24, "lead": 48},
        },
        "outputSchema": {"meta": {"hook": "string"}, "chapter": {"lead": "string"}},
    },
    ensure_ascii=False,
)
GLYPH_TITLE = "拾光"


def _scrub(text: str, *, limit: int = 400) -> str:
    cleaned = SECRET_RE.sub("sk-***", text or "")
    return cleaned[:limit]


def _result(**kwargs: Any) -> dict[str, Any]:
    return kwargs


def _http_post(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return {"ok": True, "http": resp.status, "body": json.loads(raw)}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "http": exc.code,
            "error": _scrub(detail),
        }
    except Exception as exc:  # noqa: BLE001 — probe must keep going
        return {"ok": False, "http": None, "error": _scrub(str(exc))}


def _http_get(url: str, headers: dict[str, str], timeout: int) -> dict[str, Any]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"ok": True, "http": resp.status, "body": json.loads(resp.read().decode("utf-8"))}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return {"ok": False, "http": exc.code, "error": _scrub(detail)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "http": None, "error": _scrub(str(exc))}


def probe_copy_ping(runtime, model: str) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        content = chat_completion(
            [{"role": "user", "content": "Reply with the JSON {\"ok\":true} and nothing else."}],
            runtime=runtime,
            model=model,
            temperature=0.0,
            json_mode=True,
            model_failover=False,
            max_attempts=1,
        )
        parsed = parse_json_content(content)
        return _result(
            case="copy_ping",
            model=model,
            ok=True,
            parsed_ok=bool(parsed.get("ok") is True or parsed),
            latency_ms=int((time.perf_counter() - t0) * 1000),
            thinking=False,
        )
    except LlmError as exc:
        return _result(
            case="copy_ping",
            model=model,
            ok=False,
            error_code=exc.code,
            error=_scrub(str(exc)),
            latency_ms=int((time.perf_counter() - t0) * 1000),
            thinking=False,
        )


def probe_copy_narrate(runtime, model: str) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        content = chat_completion(
            [
                {"role": "system", "content": NARRATE_SYSTEM},
                {"role": "user", "content": NARRATE_USER},
            ],
            runtime=runtime,
            model=model,
            temperature=0.4,
            json_mode=True,
            model_failover=False,
            max_attempts=1,
        )
        parsed = parse_json_content(content)
        hook = str(((parsed.get("meta") or {}).get("hook")) or "")
        lead = str(((parsed.get("chapter") or {}).get("lead")) or "")
        return _result(
            case="copy_narrate",
            model=model,
            ok=True,
            json_ok=True,
            has_hook=bool(hook.strip()),
            has_lead=bool(lead.strip()),
            latency_ms=int((time.perf_counter() - t0) * 1000),
            thinking=False,
        )
    except LlmError as exc:
        return _result(
            case="copy_narrate",
            model=model,
            ok=False,
            json_ok=False,
            error_code=exc.code,
            error=_scrub(str(exc)),
            latency_ms=int((time.perf_counter() - t0) * 1000),
            thinking=False,
        )


def probe_thinking_nonstream(runtime, model: str) -> dict[str, Any]:
    """Non-stream + enable_thinking + magazine JSON (D-BAI-14)."""
    url = f"{runtime.base_url}{CHAT_URL_SUFFIX}"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": NARRATE_SYSTEM},
            {"role": "user", "content": NARRATE_USER},
        ],
        "temperature": 0.4,
        "stream": False,
        "enable_thinking": True,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {runtime.api_key}",
    }
    t0 = time.perf_counter()
    resp = _http_post(url, payload, headers, timeout=90)
    latency = int((time.perf_counter() - t0) * 1000)
    if not resp.get("ok"):
        err = str(resp.get("error") or "")
        needs_stream = any(k in err.lower() for k in ("stream", "streaming", "enable_thinking"))
        return _result(
            case="thinking_nonstream",
            model=model,
            ok=False,
            http=resp.get("http"),
            needs_stream=needs_stream,
            error=err,
            latency_ms=latency,
            thinking=True,
        )
    body = resp.get("body") or {}
    message = ((body.get("choices") or [{}])[0].get("message") or {})
    content = str(message.get("content") or "")
    reasoning = message.get("reasoning_content") or body.get("reasoning_content")
    json_ok = False
    parse_error = None
    try:
        parsed = parse_json_content(content)
        json_ok = isinstance(parsed, dict) and bool(parsed)
    except LlmError as exc:
        parse_error = f"{exc.code}: {_scrub(str(exc), limit=200)}"
    return _result(
        case="thinking_nonstream",
        model=model,
        ok=json_ok,
        http=resp.get("http"),
        json_ok=json_ok,
        has_reasoning=bool(reasoning),
        parse_error=parse_error,
        latency_ms=latency,
        thinking=True,
    )


def _glyph_image(text: str = GLYPH_TITLE) -> Image.Image:
    img = Image.new("RGB", (512, 256), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("msyh.ttc", 96)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (512 - (bbox[2] - bbox[0])) // 2
    y = (256 - (bbox[3] - bbox[1])) // 2
    draw.text((x, y), text, fill="black", font=font)
    return img


def probe_ocr(runtime, model: str, img: Image.Image) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        data_url = _image_to_data_url(img)
        content = vision_chat_completion(
            [
                {
                    "role": "system",
                    "content": (
                        "你是严格的书法文字校验器。只输出 JSON："
                        '{"recognized": "画面中的汉字", "match": true 或 false}。'
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"期望文字：{GLYPH_TITLE}"},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            provider="dashscope",
            model=model,
            runtime=runtime,
            temperature=0.0,
        )
        parsed = parse_json_content(content)
        recognized = "".join(str(parsed.get("recognized") or "").split())
        matched = recognized == GLYPH_TITLE
        return _result(
            case="ocr_image_url",
            model=model,
            ok=True,
            contract_ok=True,
            json_ok=True,
            recognized=recognized,
            match=bool(matched),
            latency_ms=int((time.perf_counter() - t0) * 1000),
        )
    except LlmError as exc:
        return _result(
            case="ocr_image_url",
            model=model,
            ok=False,
            contract_ok=False,
            error_code=exc.code,
            error=_scrub(str(exc)),
            latency_ms=int((time.perf_counter() - t0) * 1000),
        )


def probe_t2i_protocol(api_key: str, model: str, *, poll: bool) -> dict[str, Any]:
    """Submit on the current wanx async URL; poll only if a task_id comes back."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json; charset=utf-8",
        "X-DashScope-Async": "enable",
    }
    payload = {
        "model": model,
        "input": {
            "prompt": f"纯白背景，黑色书法大字「{GLYPH_TITLE}」，无印章无水印",
            "negative_prompt": "彩色, 风景, 照片, 水印",
        },
        "parameters": {"size": "1024*1024", "n": 1},
    }
    t0 = time.perf_counter()
    submitted = _http_post(_SUBMIT_URL, payload, headers, timeout=20)
    if not submitted.get("ok"):
        err = str(submitted.get("error") or "")
        isomorphic = False
        return _result(
            case="t2i_protocol",
            model=model,
            ok=False,
            isomorphic_with_route_c=isomorphic,
            http=submitted.get("http"),
            error=err,
            latency_ms=int((time.perf_counter() - t0) * 1000),
            submit_url=_SUBMIT_URL,
        )
    body = submitted.get("body") or {}
    task_id = str((body.get("output") or {}).get("task_id") or "").strip()
    if not task_id:
        return _result(
            case="t2i_protocol",
            model=model,
            ok=False,
            isomorphic_with_route_c=False,
            http=submitted.get("http"),
            error=_scrub(json.dumps(body, ensure_ascii=False)),
            latency_ms=int((time.perf_counter() - t0) * 1000),
            submit_url=_SUBMIT_URL,
        )
    out: dict[str, Any] = _result(
        case="t2i_protocol",
        model=model,
        ok=True,
        isomorphic_with_route_c=True,
        http=submitted.get("http"),
        task_id_present=True,
        latency_ms=int((time.perf_counter() - t0) * 1000),
        submit_url=_SUBMIT_URL,
    )
    if not poll:
        return out
    poll_headers = {"Authorization": f"Bearer {api_key}"}
    status = "PENDING"
    message = ""
    for _ in range(30):
        time.sleep(2.0)
        polled = _http_get(_TASK_URL_TMPL.format(task_id=task_id), poll_headers, timeout=20)
        if not polled.get("ok"):
            out.update(poll_ok=False, poll_error=polled.get("error"), task_status=status)
            return out
        payload_p = polled.get("body") or {}
        output = payload_p.get("output") or {}
        status = str(output.get("task_status") or "")
        if status == "SUCCEEDED":
            results = output.get("results") or []
            url = ""
            if results and isinstance(results[0], dict):
                url = str(results[0].get("url") or "")
            out.update(
                poll_ok=True,
                task_status=status,
                has_image_url=bool(url),
                latency_ms=int((time.perf_counter() - t0) * 1000),
            )
            return out
        if status == "FAILED":
            message = str(output.get("message") or output.get("code") or "")
            out.update(
                ok=False,
                poll_ok=False,
                task_status=status,
                error=_scrub(message),
                latency_ms=int((time.perf_counter() - t0) * 1000),
            )
            return out
    out.update(
        ok=False,
        poll_ok=False,
        task_status=status,
        error="poll timeout",
        latency_ms=int((time.perf_counter() - t0) * 1000),
    )
    return out


def main() -> int:
    load_dotenv_files()
    secrets = read_user_llm_secrets()
    if not secrets.studio_configured:
        print("NO_STUDIO_KEY")
        print("provider", secrets.provider)
        print("has_key", bool(secrets.api_key))
        return 2
    inject_secrets_into_environ(secrets)
    runtime = resolve_llm_runtime("dashscope", secrets=secrets)
    rows: list[dict[str, Any]] = []

    print("=== W0 copy ping (no thinking) ===")
    for model in COPY_MODELS:
        row = probe_copy_ping(runtime, model)
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))

    print("=== W0 copy narrate JSON ===")
    for model in COPY_MODELS:
        if any(r.get("case") == "copy_ping" and r.get("model") == model and r.get("ok") for r in rows):
            row = probe_copy_narrate(runtime, model)
            rows.append(row)
            print(json.dumps(row, ensure_ascii=False))

    print("=== W0 thinking non-stream ===")
    for model in THINKING_MODELS:
        ping_ok = any(
            r.get("case") == "copy_ping" and r.get("model") == model and r.get("ok") for r in rows
        )
        if not ping_ok:
            rows.append(
                _result(
                    case="thinking_nonstream",
                    model=model,
                    ok=False,
                    skipped=True,
                    reason="ping failed",
                )
            )
            print(json.dumps(rows[-1], ensure_ascii=False))
            continue
        row = probe_thinking_nonstream(runtime, model)
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))

    print("=== W0 OCR image_url ===")
    glyph = _glyph_image()
    for model in OCR_MODELS:
        row = probe_ocr(runtime, model, glyph)
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))

    print("=== W0 t2i protocol (route_c async URL) ===")
    api_key = runtime.api_key
    for model in T2I_MODELS:
        # Baseline + isomorphic candidates: poll. Unknown models: submit is enough if they 4xx.
        row = probe_t2i_protocol(api_key, model, poll=True)
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))

    summary = {
        "provider": secrets.provider,
        "region": secrets.region,
        "base_url": runtime.base_url,
        "studio_configured": True,
        "rows": rows,
    }
    print("=== SUMMARY ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
