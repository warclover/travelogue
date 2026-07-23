"""NAS · BE-NAS-01/02/03 unit gates + HTTP 403 / PATCH 锁。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from travelogue.config import get_config, load_config, reset_config_cache
from travelogue.config.loader import patch_config_file
from travelogue.web.ai_surface import (
    ENV_AI_SURFACE,
    ai_surface_disabled_body,
    resolve_ai_surface_enabled,
)
from travelogue.web.studio_handlers import export_handlers, llm_settings_handlers
from travelogue.web.studio_handlers.config_handlers import handle_config


def test_resolve_ai_surface_default_false(monkeypatch):
    monkeypatch.delenv(ENV_AI_SURFACE, raising=False)
    assert resolve_ai_surface_enabled(None) is False
    assert resolve_ai_surface_enabled(get_config()) is False


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


def test_resolve_rejects_magicmock_truthy(monkeypatch):
    """MagicMock.app_config.studio.ai_surface_enabled 不得伪阳。"""
    monkeypatch.delenv(ENV_AI_SURFACE, raising=False)
    assert resolve_ai_surface_enabled(MagicMock()) is False


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


def test_ai_surface_gate_event_allowlisted():
    from travelogue.domain.studio_events import ALLOWED_STUDIO_HOMEPAGE_EVENTS

    assert "ai_surface_gate" in ALLOWED_STUDIO_HOMEPAGE_EVENTS
    analytics = (
        Path(__file__).resolve().parents[3]
        / "templates"
        / "studio"
        / "js"
        / "analytics.js"
    ).read_text(encoding="utf-8")
    assert '"ai_surface_gate"' in analytics


def _mock_handler(payload: dict | None = None, *, command: str = "POST") -> MagicMock:
    handler = MagicMock()
    handler.command = command
    handler._read_json_body.return_value = payload
    handler.app_config = get_config()
    handler.trips_dir = Path(".")
    handler.studio_config_path = None
    handler.client_address = ("127.0.0.1", 0)
    captured: dict = {}

    def _json(status: int, body: dict) -> None:
        captured["status"] = status
        captured["body"] = body

    handler._json_response.side_effect = _json
    handler._captured = captured
    return handler


def test_narrate_403_when_surface_off(monkeypatch, tmp_path: Path):
    import json

    from tests.studio_test_helpers import MockStudioHandler

    monkeypatch.delenv(ENV_AI_SURFACE, raising=False)
    reset_config_cache()
    trips = tmp_path / "trips"
    trip_dir = trips / "t1-gate"
    trip_dir.mkdir(parents=True)
    (trip_dir / "trip.json").write_text(
        json.dumps(
            {
                "id": "t1-gate",
                "pipeline": {"stage": "layout_done"},
                "chapters": [{"id": "c1"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    handler = MockStudioHandler(trips, json_body={"tripId": "t1-gate"})
    handler.command = "POST"
    export_handlers.handle_narrate(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 403
    assert body["error"] == "E_AI_SURFACE_DISABLED"


def test_llm_settings_write_403_when_surface_off(monkeypatch):
    monkeypatch.delenv(ENV_AI_SURFACE, raising=False)
    reset_config_cache()
    handler = _mock_handler(
        {"provider": "deepseek", "apiKey": "sk-test-xxxxxxxxxxxx"}
    )
    llm_settings_handlers.handle_llm_settings(handler)
    assert handler._captured["status"] == 403
    assert handler._captured["body"]["error"] == "E_AI_SURFACE_DISABLED"


def test_llm_settings_delete_403_when_surface_off(monkeypatch):
    monkeypatch.delenv(ENV_AI_SURFACE, raising=False)
    reset_config_cache()
    handler = _mock_handler(None, command="DELETE")
    llm_settings_handlers.handle_llm_settings(handler)
    assert handler._captured["status"] == 403


def test_llm_ping_403_when_surface_off(monkeypatch):
    monkeypatch.delenv(ENV_AI_SURFACE, raising=False)
    reset_config_cache()
    handler = _mock_handler({"provider": "deepseek", "apiKey": "sk-test-xxxxxxxxxxxx"})
    llm_settings_handlers.handle_llm_ping(handler)
    assert handler._captured["status"] == 403
    assert handler._captured["body"]["error"] == "E_AI_SURFACE_DISABLED"


def test_config_exposes_ai_surface_enabled_false(monkeypatch, tmp_path: Path):
    monkeypatch.delenv(ENV_AI_SURFACE, raising=False)
    reset_config_cache()
    handler = _mock_handler(command="GET")
    handler.trips_dir = tmp_path / "trips"
    handler.trips_dir.mkdir()
    handle_config(handler)
    assert handler._captured["status"] == 200
    assert handler._captured["body"].get("aiSurfaceEnabled") is False


def test_llm_status_403_when_surface_off(monkeypatch):
    """AC-NAS-17c / AC-QFX-05/23：off 时早拒，不进 _status_body，零敏感键。"""
    monkeypatch.delenv(ENV_AI_SURFACE, raising=False)
    reset_config_cache()
    handler = _mock_handler(command="GET")
    called = {"status_body": False}

    def _boom(*_a, **_k):
        called["status_body"] = True
        return {"ok": True}

    monkeypatch.setattr(llm_settings_handlers, "_status_body", _boom)
    llm_settings_handlers.handle_llm_status(handler)
    assert handler._captured["status"] == 403
    body = handler._captured["body"]
    assert body["error"] == "E_AI_SURFACE_DISABLED"
    assert called["status_body"] is False
    for key in (
        "maskedKey",
        "userDataDir",
        "tripsDir",
        "llmAvailable",
        "llmProvider",
        "configured",
        "readiness",
        "model",
        "region",
        "lastPingOk",
        "capabilities",
    ):
        assert key not in body, key


def test_config_projection_strips_llm_when_surface_off(monkeypatch, tmp_path: Path):
    """AC-NAS-17d / AC-QFX-27：off 时无 llm* / tripsDir。"""
    monkeypatch.delenv(ENV_AI_SURFACE, raising=False)
    reset_config_cache()
    handler = _mock_handler(command="GET")
    handler.trips_dir = tmp_path / "trips"
    handler.trips_dir.mkdir()
    handle_config(handler)
    body = handler._captured["body"]
    assert handler._captured["status"] == 200
    assert body.get("aiSurfaceEnabled") is False
    assert "llmAvailable" not in body
    assert "llmProvider" not in body
    assert "tripsDir" not in body
    assert "clustering" in body


def test_config_projection_includes_llm_when_surface_on(monkeypatch, tmp_path: Path):
    monkeypatch.setenv(ENV_AI_SURFACE, "1")
    reset_config_cache()
    handler = _mock_handler(command="GET")
    handler.trips_dir = tmp_path / "trips"
    handler.trips_dir.mkdir()
    handle_config(handler)
    body = handler._captured["body"]
    assert handler._captured["status"] == 200
    assert body.get("aiSurfaceEnabled") is True
    assert "llmAvailable" in body
    assert "llmProvider" in body
    assert "tripsDir" in body


def test_patch_cannot_enable_ai_surface(tmp_path: Path, monkeypatch):
    """aiSurfaceEnabled / ai_surface_enabled 不在 PATCH allowlist。"""
    monkeypatch.delenv(ENV_AI_SURFACE, raising=False)
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("studio:\n  g1_confirm_structure: false\n", encoding="utf-8")
    patch_config_file(
        cfg_path,
        {
            "studio": {
                "aiSurfaceEnabled": True,
                "ai_surface_enabled": True,
                "g1ConfirmStructure": True,
            }
        },
    )
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    studio = raw.get("studio") or {}
    assert studio.get("ai_surface_enabled") in (None, False)
    assert studio.get("aiSurfaceEnabled") in (None, False)
    assert studio.get("g1_confirm_structure") is True or studio.get("g1ConfirmStructure") is True
    cfg = load_config(cfg_path)
    assert cfg.studio.ai_surface_enabled is False
    assert resolve_ai_surface_enabled(cfg) is False


def test_ai_surface_js_exports_readonly_only() -> None:
    """AC-QFX-04：源码层不导出写 setter / hydrate 写路径。"""
    src = (
        Path(__file__).resolve().parents[3]
        / "templates"
        / "studio"
        / "js"
        / "ai-surface.js"
    ).read_text(encoding="utf-8")
    assert "export function isAiSurfaceEnabled" in src
    assert "export function ensureAiSurfaceHydrated" in src
    assert "export function setAiSurfaceEnabled" not in src
    assert "export function hydrateAiSurfaceFromConfig" not in src


def test_settings_ai_zone_gated_by_ai_surface_flag() -> None:
    """AC-QFX-04：设置 AI 区可见性只读 isAiSurfaceEnabled，无法经公开 API 翻转。"""
    settings = (
        Path(__file__).resolve().parents[3]
        / "templates"
        / "studio"
        / "homepage-v2"
        / "settings-panel.js"
    ).read_text(encoding="utf-8")
    assert "from \"../js/ai-surface.js\"" in settings or "from '../js/ai-surface.js'" in settings
    assert "isAiSurfaceEnabled" in settings
    assert "setAiSurfaceEnabled" not in settings
    assert "zone.hidden = !on" in settings
    llm = (
        Path(__file__).resolve().parents[3]
        / "templates"
        / "studio"
        / "js"
        / "llm-settings.js"
    ).read_text(encoding="utf-8")
    assert "if (!isAiSurfaceEnabled()) return" in llm
    readiness = (
        Path(__file__).resolve().parents[3]
        / "templates"
        / "studio"
        / "js"
        / "llm-readiness.js"
    )
    assert not readiness.is_file(), "dead llm-readiness.js must stay deleted"
