"""CQA AC-03/04 · concurrent ping isolation + persist OSError separation."""

from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from travelogue.config import reset_config_cache
from travelogue.llm.client import resolve_llm_runtime
from travelogue.llm.user_settings import (
    UserLlmSecrets,
    clear_user_llm_secrets,
    read_user_llm_secrets,
    write_user_llm_secrets,
)
from travelogue.web.studio_handlers import llm_settings_handlers as h


@pytest.fixture()
def user_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("TRAVELOGUE_USER_DATA", str(tmp_path))
    monkeypatch.setenv("TRAVELOGUE_AI_SURFACE", "1")
    clear_user_llm_secrets()
    reset_config_cache()
    return tmp_path


def _handler(payload: dict) -> MagicMock:
    handler = MagicMock()
    handler.command = "POST"
    handler._read_json_body.return_value = payload
    captured: dict = {}

    def _json(status: int, body: dict) -> None:
        captured["status"] = status
        captured["body"] = body

    handler._json_response.side_effect = _json
    handler._captured = captured
    return handler


def test_resolve_llm_runtime_request_local_secrets_no_env(
    user_data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-env-should-not-win")
    write_user_llm_secrets(
        UserLlmSecrets(provider="deepseek", api_key="sk-disk-should-not-win")
    )
    rt = resolve_llm_runtime(
        "deepseek",
        secrets=UserLlmSecrets(
            provider="deepseek",
            api_key="sk-request-local-key",
            model="deepseek-chat",
        ),
    )
    assert rt.api_key == "sk-request-local-key"


def test_concurrent_ping_does_not_cross_credentials(
    user_data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[tuple[str, str]] = []
    lock = threading.Lock()
    barrier = threading.Barrier(2)

    def _fake_ping(*, provider=None, secrets=None, cfg=None, runtime=None) -> str:
        rt = runtime or resolve_llm_runtime(provider, cfg=cfg, secrets=secrets)
        barrier.wait(timeout=5)
        with lock:
            seen.append((rt.api_key, rt.base_url.rstrip("/")))
        return f"{rt.provider}/{rt.model} @ {rt.base_url}"

    monkeypatch.setattr("travelogue.llm.client.llm_ping", _fake_ping)

    payloads = [
        {
            "provider": "deepseek",
            "apiKey": "sk-thread-a-xxxxxxxxxxxx",
            "baseUrl": "https://api.deepseek.com/v1",
        },
        {
            "provider": "dashscope",
            "apiKey": "sk-thread-b-xxxxxxxxxxxx",
            "baseUrl": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        },
    ]
    errors: list[BaseException] = []

    def _run(payload: dict) -> None:
        try:
            h.handle_llm_ping(_handler(payload))
        except BaseException as exc:  # noqa: BLE001 — collect for main thread
            errors.append(exc)

    threads = [threading.Thread(target=_run, args=(p,)) for p in payloads]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert not errors
    assert len(seen) == 2
    keys = {row[0] for row in seen}
    assert keys == {"sk-thread-a-xxxxxxxxxxxx", "sk-thread-b-xxxxxxxxxxxx"}
    # No cross: deepseek key must not pair with dashscope host and vice versa
    by_key = {k: u for k, u in seen}
    assert "deepseek.com" in by_key["sk-thread-a-xxxxxxxxxxxx"]
    assert "dashscope" in by_key["sk-thread-b-xxxxxxxxxxxx"]


def test_ping_persist_oserror_keeps_ping_ok(
    user_data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_user_llm_secrets(
        UserLlmSecrets(
            provider="deepseek",
            api_key="sk-deepseek-persist-xxxxxx",
            last_ping_ok=None,
        )
    )
    monkeypatch.setattr(
        "travelogue.llm.client.llm_ping",
        lambda **_k: "deepseek/deepseek-chat @ https://api.deepseek.com/v1",
    )

    def _boom(*_a, **_k):
        raise OSError("simulated lock")

    monkeypatch.setattr(
        "travelogue.web.studio_handlers.llm_settings_handlers.write_user_llm_secrets",
        _boom,
    )
    handler = _handler({"provider": "deepseek", "persist": True})
    h.handle_llm_ping(handler)
    assert handler._captured["status"] == 500
    body = handler._captured["body"]
    assert body["error"] == "E_STUDIO_CONFIG_WRITE"
    assert body["pingOk"] is True
    assert body["persisted"] is False
    # Disk unchanged
    assert read_user_llm_secrets().last_ping_ok is None


def test_no_module_level_secrets_monkey_patch_in_handler_source() -> None:
    import inspect

    src = inspect.getsource(h.handle_llm_ping)
    assert "read_user_llm_secrets =" not in src
    assert "os.environ[" not in src
