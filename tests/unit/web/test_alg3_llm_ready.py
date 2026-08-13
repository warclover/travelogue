"""ALG-V3 W0 · probe_llm_ready read-only contract (AC-07 / AC-06)."""

from __future__ import annotations

import os

import pytest

from travelogue.config import AppConfig
from travelogue.config._common import capability_allows
from travelogue.config.misc import LlmConfig
from travelogue.llm.ready import (
    probe_llm_ready,
    resolve_llm_ready_summary,
    studio_llm_status,
)
from travelogue.llm.user_settings import UserLlmSecrets


def test_capability_allows_truth_table() -> None:
    assert capability_allows("auto", ready=False) == (False, None)
    assert capability_allows("auto", ready=True) == (True, None)
    assert capability_allows("true", ready=False) == (False, "llm_no_key")
    assert capability_allows("true", ready=True) == (True, None)
    assert capability_allows("false", ready=True) == (False, None)
    assert capability_allows(True, ready=False) == (False, "llm_no_key")


def test_probe_llm_ready_does_not_mutate_environ(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "travelogue.llm.user_settings.read_user_llm_secrets",
        lambda: UserLlmSecrets(
            provider="deepseek", api_key="sk-test", last_ping_ok=True
        ),
    )
    injected = {"called": False}

    def _inject(_secrets: UserLlmSecrets) -> None:
        injected["called"] = True
        os.environ["DEEPSEEK_API_KEY"] = "should-not-happen"

    monkeypatch.setattr(
        "travelogue.llm.user_settings.inject_secrets_into_environ",
        _inject,
    )
    before = dict(os.environ)
    cfg = AppConfig(llm=LlmConfig(provider="deepseek", capability="auto"))
    ready = probe_llm_ready(cfg=cfg)
    after = dict(os.environ)
    assert injected["called"] is False
    assert before == after
    assert ready is True


def test_probe_llm_ready_false_until_ping_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "travelogue.llm.user_settings.read_user_llm_secrets",
        lambda: UserLlmSecrets(
            provider="deepseek", api_key="sk-test", last_ping_ok=None
        ),
    )
    cfg = AppConfig(llm=LlmConfig(provider="deepseek", capability="auto"))
    assert probe_llm_ready(cfg=cfg) is False


def test_probe_llm_ready_false_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "travelogue.llm.user_settings.read_user_llm_secrets",
        lambda: UserLlmSecrets(),
    )
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    cfg = AppConfig(llm=LlmConfig(provider="deepseek", capability="auto"))
    assert probe_llm_ready(cfg=cfg) is False


def test_resolve_llm_ready_summary_auto_no_key_no_degrade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "travelogue.llm.ready.probe_llm_ready",
        lambda *, cfg=None: False,
    )
    cfg = AppConfig(llm=LlmConfig(provider="stub", capability="auto"))
    summary = resolve_llm_ready_summary(cfg=cfg)
    assert summary["ready"] is False
    assert summary["capability"] == "auto"
    assert summary["mayCall"] is False
    assert summary["usedOnImport"] is False
    assert "degradeReason" not in summary


def test_resolve_llm_ready_summary_true_no_key_writes_llm_no_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "travelogue.llm.ready.probe_llm_ready",
        lambda *, cfg=None: False,
    )
    cfg = AppConfig(llm=LlmConfig(provider="stub", capability="true"))
    summary = resolve_llm_ready_summary(cfg=cfg)
    assert summary["ready"] is False
    assert summary["degradeReason"] == "llm_no_key"


def test_studio_llm_status_does_not_inject_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "travelogue.llm.user_settings.read_user_llm_secrets",
        lambda: UserLlmSecrets(
            provider="deepseek", api_key="sk-test", last_ping_ok=True
        ),
    )
    calls = {"n": 0}

    def _inject(_secrets: UserLlmSecrets) -> None:
        calls["n"] += 1

    monkeypatch.setattr(
        "travelogue.llm.user_settings.inject_secrets_into_environ",
        _inject,
    )
    cfg = AppConfig(llm=LlmConfig(provider="deepseek"))
    status = studio_llm_status(cfg=cfg)
    assert calls["n"] == 0
    assert status["llmAvailable"] is True


def test_studio_llm_status_unavailable_without_ping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "travelogue.llm.user_settings.read_user_llm_secrets",
        lambda: UserLlmSecrets(
            provider="deepseek", api_key="sk-test", last_ping_ok=False
        ),
    )
    cfg = AppConfig(llm=LlmConfig(provider="deepseek"))
    status = studio_llm_status(cfg=cfg)
    assert status["llmAvailable"] is False
