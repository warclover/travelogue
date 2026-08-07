"""Unit tests · title_art Route C DashScope caller (PRD §5.5.2 · D-CAL-14/16).

网络调用全部 mock（不依赖真实 DASHSCOPE_API_KEY / 网络），验证：
- 缺 key / 未知 styleId / 提交失败 / 轮询超时 / 任务失败 / 无结果
  均抛 :class:`RouteCFailure`（调用方据此走 D-CAL-16 fallback）。
- 成功路径正确解析 task_id → 轮询 SUCCEEDED → 下载图片。
"""

from __future__ import annotations

import io
import json
import urllib.error

import pytest
from PIL import Image

from travelogue.cover_engine.title_art import route_c
from travelogue.cover_engine.title_art.route_c import RouteCFailure, generate_raw

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _dashscope_key(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test-fake-key")
    yield
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    monkeypatch.setattr(route_c.time, "sleep", lambda *_a, **_k: None)


def test_generate_raw_missing_api_key_raises(monkeypatch) -> None:
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    with pytest.raises(RouteCFailure) as exc:
        generate_raw("cascade-seal", title="拾光")
    assert exc.value.reason == "E_CAL_C_NOKEY"


def test_generate_raw_unknown_style_raises() -> None:
    with pytest.raises(RouteCFailure) as exc:
        generate_raw("not-a-real-style", title="拾光")
    assert exc.value.reason == "E_CAL_C_UNKNOWN_STYLE"


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


def _png_bytes(color=(0, 0, 0)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(buf, format="PNG")
    return buf.getvalue()


def test_generate_raw_submit_http_error_raises(monkeypatch) -> None:
    def _boom(*_a, **_k):
        raise urllib.error.HTTPError(
            "http://x", 500, "boom", None, io.BytesIO(b"server error")
        )

    monkeypatch.setattr(route_c.urllib.request, "urlopen", _boom)
    with pytest.raises(RouteCFailure) as exc:
        generate_raw("cascade-seal", title="拾光")
    assert exc.value.reason == "E_CAL_C_SUBMIT_HTTP"


def test_generate_raw_submit_no_task_id_raises(monkeypatch) -> None:
    payload = json.dumps({"output": {}}).encode("utf-8")
    monkeypatch.setattr(
        route_c.urllib.request, "urlopen", lambda *_a, **_k: _FakeResponse(payload)
    )
    with pytest.raises(RouteCFailure) as exc:
        generate_raw("cascade-seal", title="拾光")
    assert exc.value.reason == "E_CAL_C_SUBMIT_NO_TASK"


def test_generate_raw_task_failed_raises(monkeypatch) -> None:
    responses = [
        json.dumps({"output": {"task_id": "t1"}}).encode("utf-8"),
        json.dumps({"output": {"task_status": "FAILED", "message": "内容审核不通过"}}).encode(
            "utf-8"
        ),
    ]
    call_count = {"n": 0}

    def _fake_urlopen(*_a, **_k):
        resp = _FakeResponse(responses[min(call_count["n"], len(responses) - 1)])
        call_count["n"] += 1
        return resp

    monkeypatch.setattr(route_c.urllib.request, "urlopen", _fake_urlopen)
    with pytest.raises(RouteCFailure) as exc:
        generate_raw("cascade-seal", title="拾光")
    assert exc.value.reason == "E_CAL_C_TASK_FAILED"


def test_generate_raw_timeout_after_poll_budget(monkeypatch) -> None:
    submit_payload = json.dumps({"output": {"task_id": "t1"}}).encode("utf-8")
    pending_payload = json.dumps({"output": {"task_status": "PENDING"}}).encode("utf-8")
    call_count = {"n": 0}

    def _fake_urlopen(*_a, **_k):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _FakeResponse(submit_payload)
        return _FakeResponse(pending_payload)

    monkeypatch.setattr(route_c.urllib.request, "urlopen", _fake_urlopen)
    with pytest.raises(RouteCFailure) as exc:
        generate_raw("cascade-seal", title="拾光")
    assert exc.value.reason == "E_CAL_C_TIMEOUT"


def test_generate_raw_success_downloads_image(monkeypatch) -> None:
    submit_payload = json.dumps({"output": {"task_id": "t1"}}).encode("utf-8")
    success_payload = json.dumps(
        {
            "output": {
                "task_status": "SUCCEEDED",
                "results": [
                    {"url": "http://fake/img.png", "actual_prompt": "毛笔字·拾光"}
                ],
            }
        }
    ).encode("utf-8")
    image_bytes = _png_bytes()
    call_count = {"n": 0}

    def _fake_urlopen(req, *_a, **_k):
        call_count["n"] += 1
        url = getattr(req, "full_url", req if isinstance(req, str) else "")
        if call_count["n"] == 1:
            return _FakeResponse(submit_payload)
        if "img.png" in str(url):
            return _FakeResponse(image_bytes)
        return _FakeResponse(success_payload)

    monkeypatch.setattr(route_c.urllib.request, "urlopen", _fake_urlopen)
    result = generate_raw("cascade-seal", title="拾光", model="wanx2.1-t2i-plus")
    assert result.model == "wanx2.1-t2i-plus"
    assert result.style.style_id == "cascade-seal"
    assert result.image.size == (8, 8)
    assert "拾光" in result.actual_prompt
