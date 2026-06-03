"""Studio POST/PATCH dispatch for template admin CRUD routes."""

from __future__ import annotations

from travelogue.web.studio_handlers.paths import (
    TEMPLATES_ADMIN_DELETE_PATH,
    TEMPLATES_ADMIN_REGISTER_PATH,
    match_template_admin_metadata,
)
from travelogue.web.studio_routes import StudioMixin


class _PostProbe(StudioMixin):
    studio_mode = True
    studio_token = "t"
    studio_host = "127.0.0.1"
    studio_port = 8766
    studio_allow_lan = False
    calls: list[str]

    def __init__(self) -> None:
        self.calls = []

    def _studio_require_post_auth(self) -> bool:
        return True

    def _json_response(self, code: int, payload: dict) -> None:
        pass


def test_studio_dispatch_post_template_admin_register(monkeypatch) -> None:
    probe = _PostProbe()
    monkeypatch.setattr(
        "travelogue.web.studio_handlers.template_admin_handlers.handle_templates_admin_register",
        lambda h: probe.calls.append("register"),
    )
    assert probe.studio_dispatch_POST(TEMPLATES_ADMIN_REGISTER_PATH) is True
    assert probe.calls == ["register"]


def test_studio_dispatch_post_template_admin_delete(monkeypatch) -> None:
    probe = _PostProbe()
    monkeypatch.setattr(
        "travelogue.web.studio_handlers.template_admin_handlers.handle_templates_admin_delete",
        lambda h: probe.calls.append("delete"),
    )
    assert probe.studio_dispatch_POST(TEMPLATES_ADMIN_DELETE_PATH) is True
    assert probe.calls == ["delete"]


def test_match_template_admin_metadata() -> None:
    assert match_template_admin_metadata("/__travelogue/templates/admin/visual-journal/metadata") == "visual-journal"
    assert match_template_admin_metadata("/__travelogue/templates/admin/visual-journal") is None
