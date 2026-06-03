"""Studio PATCH dispatch for template admin metadata."""

from __future__ import annotations

from travelogue.web.studio_handlers.paths import match_template_admin_metadata
from travelogue.web.studio_routes import StudioMixin


class _PatchProbe(StudioMixin):
    studio_mode = True
    studio_token = "t"
    studio_host = "127.0.0.1"
    studio_port = 8766
    studio_allow_lan = False

    def __init__(self) -> None:
        self.calls: list[str] = []

    def _studio_require_post_auth(self) -> bool:
        return True

    def _json_response(self, code: int, payload: dict) -> None:
        pass


def test_studio_dispatch_patch_template_metadata(monkeypatch) -> None:
    path = "/__travelogue/templates/admin/visual-journal/metadata"
    assert match_template_admin_metadata(path) == "visual-journal"
    probe = _PatchProbe()
    monkeypatch.setattr(
        "travelogue.web.studio_handlers.template_admin_handlers.handle_templates_admin_metadata",
        lambda h, tid: probe.calls.append(f"metadata:{tid}"),
    )
    assert probe.studio_dispatch_PATCH(path) is True
    assert probe.calls == ["metadata:visual-journal"]
