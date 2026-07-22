"""NAS · BE-NAS-01/02/03 unit gates."""

from __future__ import annotations

import os

import pytest

from travelogue.web.ai_surface import (
    ENV_AI_SURFACE,
    ai_surface_disabled_body,
    resolve_ai_surface_enabled,
)


def test_resolve_ai_surface_default_false(monkeypatch):
    monkeypatch.delenv(ENV_AI_SURFACE, raising=False)
    assert resolve_ai_surface_enabled(None) is False


def test_resolve_ai_surface_env_on(monkeypatch):
    monkeypatch.setenv(ENV_AI_SURFACE, "1")
    assert resolve_ai_surface_enabled(None) is True


@pytest.mark.parametrize("raw", ["true", "on", "yes", "TRUE"])
def test_resolve_ai_surface_env_truthy(monkeypatch, raw):
    monkeypatch.setenv(ENV_AI_SURFACE, raw)
    assert resolve_ai_surface_enabled(None) is True


def test_resolve_ai_surface_config_flag(monkeypatch):
    monkeypatch.delenv(ENV_AI_SURFACE, raising=False)

    class _Studio:
        ai_surface_enabled = True

    class _Cfg:
        studio = _Studio()

    assert resolve_ai_surface_enabled(_Cfg()) is True


def test_ai_surface_disabled_body_code():
    body = ai_surface_disabled_body()
    assert body["ok"] is False
    assert body["error"] == "E_AI_SURFACE_DISABLED"
    assert "不可用" in body["message"]
    assert "写作引擎" not in body["message"]
    assert "AI 文案" not in body["message"]


def test_user_message_registered():
    from travelogue.web.studio_errors import user_message

    assert user_message("E_AI_SURFACE_DISABLED") == "当前版本不可用"
