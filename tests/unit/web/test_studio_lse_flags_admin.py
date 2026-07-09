"""Studio LSE capability flags admin page and API."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
import yaml

from tests.studio_test_helpers import MockStudioHandler
from travelogue.config import load_config
from travelogue.config.loader import patch_config_file
from travelogue.layout_engine.capabilities import (
    capability_flags_snapshot,
    effective_capabilities,
)
from travelogue.layout_engine.registry import get_strategy_pack
from travelogue.paths import STUDIO_TEMPLATE_DIR
from travelogue.web.studio_handlers import layout_strategy_handlers
from travelogue.web.studio_handlers.layout_strategy_handlers import (
    handle_lse_capabilities_get,
    handle_lse_capabilities_patch,
)
from travelogue.web.studio_handlers.paths import LSE_CAPS_API_PATH, LSE_FLAGS_UI_PATH
from travelogue.web.studio_handlers.static_handlers import handle_lse_flags_admin_page
from travelogue.web.studio_routes import StudioMixin

pytestmark = pytest.mark.unit


class _GetProbe(StudioMixin):
    studio_mode = True
    status_code = 0
    body = b""

    def send_response(self, code: int, message: str | None = None) -> None:
        self.status_code = code

    def send_header(self, key: str, value: str) -> None:
        pass

    def end_headers(self) -> None:
        pass

    @property
    def wfile(self):
        return self

    def write(self, data: bytes) -> int:
        self.body += data
        return len(data)


class _DispatchProbe(StudioMixin):
    studio_mode = True
    studio_token = "t"
    studio_host = "127.0.0.1"
    studio_port = 8766
    studio_allow_lan = False
    calls: list[str]

    def __init__(self) -> None:
        self.calls = []

    def _json_response(self, code: int, payload: dict) -> None:
        pass

    def _studio_require_post_auth(self) -> bool:
        return True


def _auth_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "travelogue.web.studio_handlers.layout_strategy_handlers._lse_caps_gate",
        lambda *a, **k: True,
    )


def _handler(
    tmp_path: Path,
    *,
    json_body: dict | None = None,
    headers: dict[str, str] | None = None,
    studio_host: str = "127.0.0.1",
    command: str = "GET",
) -> MockStudioHandler:
    handler = MockStudioHandler(
        tmp_path / "trips",
        json_body=json_body,
        headers=headers or {"X-Template-Role": "template_admin"},
        studio_host=studio_host,
    )
    handler.studio_token = ""
    handler.command = command
    return handler


def test_lse_flags_admin_ui_route() -> None:
    probe = _GetProbe()
    assert probe.studio_dispatch_GET(LSE_FLAGS_UI_PATH) is True
    assert probe.status_code == 200
    html = probe.body.decode("utf-8")
    assert "智能排版能力开关" in html
    assert "warn-box" in html
    assert "rollout-allow" in html
    assert "paceProfile" not in html
    assert (STUDIO_TEMPLATE_DIR / "lse-flags-admin.html").is_file()


def test_handle_lse_flags_admin_page() -> None:
    probe = _GetProbe()
    handle_lse_flags_admin_page(probe)
    assert probe.status_code == 200
    assert "LSE Capabilities" in probe.body.decode("utf-8")


def test_studio_dispatch_get_lse_capabilities(monkeypatch: pytest.MonkeyPatch) -> None:
    probe = _DispatchProbe()
    monkeypatch.setattr(
        "travelogue.web.studio_handlers.layout_strategy_handlers.handle_lse_capabilities_get",
        lambda h: probe.calls.append("get"),
    )
    assert probe.studio_dispatch_GET(LSE_CAPS_API_PATH) is True
    assert probe.calls == ["get"]


def test_studio_dispatch_patch_lse_capabilities(monkeypatch: pytest.MonkeyPatch) -> None:
    probe = _DispatchProbe()
    monkeypatch.setattr(
        "travelogue.web.studio_handlers.layout_strategy_handlers.handle_lse_capabilities_patch",
        lambda h: probe.calls.append("patch"),
    )
    assert probe.studio_dispatch_PATCH(LSE_CAPS_API_PATH) is True
    assert probe.calls == ["patch"]


def test_patch_lse_capabilities_config(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("layout: {}\n", encoding="utf-8")
    patch_config_file(
        cfg_path,
        {
            "layout": {
                "strategy_engine": {
                    "enabled": True,
                    "capabilities": {
                        "saliency_scoring": True,
                        "tone_harmony": False,
                        "beat_profile": "classic_magazine",
                    },
                }
            }
        },
    )
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    se = raw["layout"]["strategy_engine"]
    assert se["enabled"] is True
    assert se["capabilities"]["saliency_scoring"] is True
    assert se["capabilities"]["beat_profile"] == "classic_magazine"


def test_patch_lse_beat_profile_rejects_invalid(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("layout: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="beat_profile"):
        patch_config_file(
            cfg_path,
            {
                "layout": {
                    "strategy_engine": {
                        "capabilities": {"beat_profile": "not_a_profile"},
                    }
                }
            },
        )


def test_handle_lse_capabilities_get_and_patch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _auth_ok(monkeypatch)
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        yaml.safe_dump({"layout": {"strategy_engine": {"enabled": False, "capabilities": {}}}}),
        encoding="utf-8",
    )
    handler = MockStudioHandler(
        tmp_path / "trips",
        headers={"X-Template-Role": "template_admin"},
    )
    handler.studio_config_path = cfg_path

    handle_lse_capabilities_get(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 200
    assert body["ok"] is True
    assert body["engineEnabled"] is False
    assert "saliencyScoring" in body["capabilities"]
    assert "paceProfile" not in body["capabilities"]
    assert "rollout" in body

    handler.command = "PATCH"
    handler._json_body = {
        "engineEnabled": True,
        "capabilities": {
            "saliencyScoring": True,
            "beatProfile": "dense_mid",
        },
    }
    handle_lse_capabilities_patch(handler)
    assert handler.response is not None
    patch_status, patch_body = handler.response
    assert patch_status == 200
    assert patch_body["engineEnabled"] is True
    assert patch_body["capabilities"]["saliencyScoring"]["effective"] is True
    assert patch_body["capabilities"]["beatProfile"]["effective"] == "dense_mid"

    reloaded = load_config(cfg_path)
    assert reloaded.layout.strategy_engine.enabled is True
    assert reloaded.layout.strategy_engine.capabilities.saliency_scoring is True
    assert reloaded.layout.strategy_engine.capabilities.beat_profile == "dense_mid"


def test_handle_lse_capabilities_patch_invalid_beat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _auth_ok(monkeypatch)
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("layout: {}\n", encoding="utf-8")
    handler = MockStudioHandler(
        tmp_path / "trips",
        json_body={"capabilities": {"beatProfile": "invalid"}},
        headers={"X-Template-Role": "template_admin"},
    )
    handler.command = "PATCH"
    handler.studio_config_path = cfg_path
    handle_lse_capabilities_patch(handler)
    assert handler.response is not None
    assert handler.response[0] == 400


def test_handle_lse_capabilities_get_rejects_non_internal(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("layout: {}\n", encoding="utf-8")
    handler = _handler(tmp_path, studio_host="203.0.113.1")
    handler.studio_config_path = cfg_path
    handle_lse_capabilities_get(handler)
    assert handler.response is not None
    assert handler.response[0] == 403
    assert handler.response[1]["error"] == "E_LSE_INTERNAL_ONLY"


def test_handle_lse_capabilities_patch_rejects_viewer_role(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("layout: {}\n", encoding="utf-8")
    handler = _handler(
        tmp_path,
        json_body={"engineEnabled": True},
        headers={"X-Template-Role": "viewer"},
        command="PATCH",
    )
    handler.studio_config_path = cfg_path
    handle_lse_capabilities_patch(handler)
    assert handler.response is not None
    assert handler.response[0] == 403
    assert handler.response[1]["error"] == "E_TEMPLATE_PERMISSION_DENIED"


def test_handle_lse_capabilities_get_matches_effective_capabilities(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _auth_ok(monkeypatch)
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        yaml.safe_dump(
            {
                "layout": {
                    "strategy_engine": {
                        "enabled": False,
                        "capabilities": {"saliency_scoring": True},
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    handler = _handler(tmp_path)
    handler.studio_config_path = cfg_path
    handle_lse_capabilities_get(handler)
    assert handler.response is not None
    _, body = handler.response
    cfg = load_config(cfg_path)
    pack = get_strategy_pack(cfg.layout.strategy_engine.default_strategy_id)
    effective = effective_capabilities(cfg, pack)
    assert body["capabilities"]["saliencyScoring"]["effective"] == effective.saliency_scoring
    assert body["capabilities"]["saliencyScoring"]["fromConfig"] is True
    assert "allowlistTripIds" in body["rollout"]
    assert "blocklistTripIds" in body["rollout"]


def test_handle_lse_capabilities_patch_updates_capability_flags_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _auth_ok(monkeypatch)
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        yaml.safe_dump({"layout": {"strategy_engine": {"enabled": False, "capabilities": {}}}}),
        encoding="utf-8",
    )
    handler = _handler(
        tmp_path,
        json_body={
            "engineEnabled": True,
            "capabilities": {"saliencyScoring": True, "beatProfile": "classic_magazine"},
        },
        command="PATCH",
    )
    handler.studio_config_path = cfg_path
    handle_lse_capabilities_patch(handler)
    assert handler.response is not None
    assert handler.response[0] == 200

    cfg = load_config(cfg_path)
    pack = get_strategy_pack(cfg.layout.strategy_engine.default_strategy_id)
    snap = capability_flags_snapshot(cfg, pack)
    assert snap["saliencyScoring"] is True
    assert snap["beatProfile"] == "classic_magazine"
    assert snap["hungarianAssignment"] is False


def test_handle_lse_capabilities_patch_writes_audit_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _auth_ok(monkeypatch)
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("layout: {}\n", encoding="utf-8")
    handler = _handler(
        tmp_path,
        json_body={"engineEnabled": True},
        headers={"X-Template-Role": "template_admin"},
        command="PATCH",
    )
    handler.studio_config_path = cfg_path
    caplog.set_level(logging.INFO, logger=layout_strategy_handlers.__name__)
    handle_lse_capabilities_patch(handler)
    assert handler.response is not None
    assert handler.response[0] == 200
    assert any("[lse-flags-admin]" in rec.message for rec in caplog.records)


def test_ac6_warn_condition_engine_off_capability_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-6: API state that should show frontend warn banner (engine off, cap effective)."""
    _auth_ok(monkeypatch)
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        yaml.safe_dump(
            {
                "layout": {
                    "strategy_engine": {
                        "enabled": False,
                        "capabilities": {"saliency_scoring": True},
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    handler = _handler(tmp_path)
    handler.studio_config_path = cfg_path
    handle_lse_capabilities_get(handler)
    assert handler.response is not None
    _, body = handler.response
    assert body["engineEnabled"] is False
    assert body["capabilities"]["saliencyScoring"]["effective"] is True
    should_warn = (not body["engineEnabled"]) and (
        body["capabilities"]["saliencyScoring"]["effective"]
        or body["capabilities"]["beatProfile"]["effective"] != "flat"
    )
    assert should_warn is True
