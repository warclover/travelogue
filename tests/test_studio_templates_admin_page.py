"""GET /templates-admin serves governance console HTML."""

from __future__ import annotations

from travelogue.paths import STUDIO_TEMPLATE_DIR
from travelogue.web.studio_handlers.paths import TEMPLATES_ADMIN_UI_PATH
from travelogue.web.studio_routes import StudioMixin


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


def test_templates_admin_ui_route() -> None:
    probe = _GetProbe()
    assert probe.studio_dispatch_GET(TEMPLATES_ADMIN_UI_PATH) is True
    assert probe.status_code == 200
    html = probe.body.decode("utf-8")
    assert "模板治理控制台" in html
    assert "布局模板（LTE · internal）" in html
    assert (STUDIO_TEMPLATE_DIR / "templates-admin.html").is_file()
