"""Phase 13 security hardening regression tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.config import AppConfig, TemplateAdminConfig
from travelogue.templating.config_governance import approve_router_change, propose_router_change
from travelogue.templating.roles import require_template_role, resolve_template_role
from travelogue.templating.template_admin_crud import (
    register_template_from_disk,
    validate_template_id,
)


class _Headers(dict):
    def get(self, key, default=None):  # type: ignore[override]
        return super().get(key, default)


def _cfg(**kwargs) -> AppConfig:
    return AppConfig(template_admin=TemplateAdminConfig(**kwargs))


def test_lan_ignores_spoofed_template_admin_header() -> None:
    headers = _Headers({"X-Template-Role": "template_admin"})
    role = resolve_template_role(
        headers,
        host="192.168.1.5",
        allow_lan=True,
        cfg=_cfg(require_role_on_lan=True, lan_role="template_operator"),
        studio_authenticated=True,
    )
    assert role == "template_operator"


def test_lan_without_token_is_viewer() -> None:
    headers = _Headers({"X-Template-Role": "template_admin"})
    role = resolve_template_role(
        headers,
        host="192.168.1.5",
        allow_lan=True,
        cfg=_cfg(require_role_on_lan=True),
        studio_authenticated=False,
    )
    assert role == "viewer"


def test_loopback_requires_token_when_configured() -> None:
    headers = _Headers()
    role = resolve_template_role(
        headers,
        host="127.0.0.1",
        allow_lan=False,
        cfg=_cfg(require_token_on_loopback=True, default_role_loopback="template_admin"),
        studio_authenticated=False,
    )
    assert role == "viewer"
    ok, _, code = require_template_role(
        headers,
        host="127.0.0.1",
        allow_lan=False,
        minimum="template_admin",
        cfg=_cfg(require_token_on_loopback=True),
        studio_authenticated=False,
    )
    assert ok is False
    assert code == "E_TEMPLATE_PERMISSION_DENIED"


def test_validate_template_id_rejects_dotdot() -> None:
    with pytest.raises(ValueError, match="invalid templateId"):
        validate_template_id("..")


def test_register_template_from_disk_rejects_dotdot() -> None:
    with pytest.raises(ValueError, match="invalid templateId"):
        register_template_from_disk("..")


def test_config_approve_rejects_same_operator(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "template_admin_state.json"
    state.write_text(
        json.dumps({"revision": 0, "templates": {}, "audit": [], "runtime": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr("travelogue.templating.admin_store._STATE_PATH", state)
    monkeypatch.setattr("travelogue.domain.template_admin_state._ADMIN_STATE_PATH", state)
    monkeypatch.setattr("travelogue.domain.template_admin_state._RUNTIME_CACHE", None)
    req = propose_router_change({"traffic_percent": 50}, operator="alice", reason="test")
    with pytest.raises(ValueError, match="E_CONFIG_APPROVER_SAME_AS_OPERATOR"):
        approve_router_change(req["id"], approver="alice")
