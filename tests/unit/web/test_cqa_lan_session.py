"""CQA AC-01/02 · LAN home must not leak token; bootstrap exchanges session."""

from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock

import pytest

from travelogue.web.studio_auth import (
    STUDIO_TOKEN_COOKIE,
    new_studio_token,
    studio_request_authorized,
)
from travelogue.web.studio_handlers import static_handlers as sh


class _WFile(BytesIO):
    def write(self, b: bytes) -> int:  # type: ignore[override]
        return super().write(b)


def _handler(
    *,
    allow_lan: bool,
    token: str | None,
    path: str = "/",
    cookie: str | None = None,
) -> MagicMock:
    handler = MagicMock()
    handler.path = path
    handler.studio_allow_lan = allow_lan
    handler.studio_token = token
    handler.studio_host = "0.0.0.0" if allow_lan else "127.0.0.1"
    headers: dict[str, str] = {}
    if cookie:
        headers["Cookie"] = cookie
    handler.headers = headers
    handler.request_headers = headers
    handler.wfile = _WFile()
    handler._headers_out: list[tuple[str, str]] = []

    def send_response(code: int) -> None:
        handler._status = code

    def send_header(k: str, v: str) -> None:
        handler._headers_out.append((k, v))

    def end_headers() -> None:
        pass

    handler.send_response.side_effect = send_response
    handler.send_header.side_effect = send_header
    handler.end_headers.side_effect = end_headers
    return handler


def test_lan_unauthenticated_home_has_no_token(monkeypatch: pytest.MonkeyPatch) -> None:
    token = new_studio_token()
    handler = _handler(allow_lan=True, token=token, path="/")
    monkeypatch.setattr(
        sh.gate,
        "read_or_assign_bucket",
        lambda _h: (0, False),
    )
    sh._serve_studio_home_html(
        handler, "studio-home-v2.html", bucket=0, is_new=False, homepage_variant="v2"
    )
    assert handler._status == 401
    body = handler.wfile.getvalue().decode("utf-8")
    assert token not in body
    # No Set-Cookie with the raw management token
    cookie_vals = [v for k, v in handler._headers_out if k.lower() == "set-cookie"]
    assert not any(token in v for v in cookie_vals)


def test_lan_bootstrap_query_sets_httponly_and_redirects() -> None:
    token = new_studio_token()
    handler = _handler(
        allow_lan=True,
        token=token,
        path=f"/?studio_token={token}",
    )
    sh._serve_studio_home_html(
        handler, "studio-home-v2.html", bucket=0, is_new=False, homepage_variant="v2"
    )
    assert handler._status == 302
    headers = {k.lower(): v for k, v in handler._headers_out}
    assert headers.get("location") == "/"
    cookie = headers.get("set-cookie", "")
    assert STUDIO_TOKEN_COOKIE in cookie
    assert token in cookie
    assert "HttpOnly" in cookie
    assert "Secure" not in cookie  # plain HTTP fixture


def test_lan_cookie_session_serves_home_without_embedded_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    token = new_studio_token()
    handler = _handler(
        allow_lan=True,
        token=token,
        path="/",
        cookie=f"{STUDIO_TOKEN_COOKIE}={token}",
    )
    # Avoid depending on real template mutations beyond placeholders
    monkeypatch.setattr(
        sh.gate,
        "inject_home_placeholders",
        lambda html, h, bucket, homepage_variant=None: html.replace(
            "__STUDIO_TOKEN__", getattr(h, "studio_token", None) or ""
        ),
    )
    # Point template read to a tiny stub
    stub = tmp_path / "studio-home-v2.html"
    stub.write_text(
        "<html><head><meta name=\"studio-token\" content=\"__STUDIO_TOKEN__\" /></head>"
        "<body>ok</body></html>",
        encoding="utf-8",
    )
    monkeypatch.setattr(sh, "STUDIO_TEMPLATE_DIR", tmp_path)

    sh._serve_studio_home_html(
        handler, "studio-home-v2.html", bucket=0, is_new=False, homepage_variant="v2"
    )
    assert handler._status == 200
    body = handler.wfile.getvalue().decode("utf-8")
    assert token not in body
    cookie_vals = [v for k, v in handler._headers_out if k.lower() == "set-cookie"]
    assert any("HttpOnly" in v and token in v for v in cookie_vals)


def test_lan_query_token_does_not_authorize_api() -> None:
    """AC-02 · URL token is bootstrap-only; APIs need cookie/header session."""
    token = new_studio_token()
    headers = {}
    assert (
        studio_request_authorized(
            host="192.168.1.10",
            token=token,
            headers=headers,
            allow_lan=True,
            query=f"studio_token={token}",
        )
        is False
    )
    assert (
        studio_request_authorized(
            host="192.168.1.10",
            token=token,
            headers={"Cookie": f"{STUDIO_TOKEN_COOKIE}={token}"},
            allow_lan=True,
            query="",
        )
        is True
    )
    assert (
        studio_request_authorized(
            host="192.168.1.10",
            token=token,
            headers={"X-Studio-Token": token},
            allow_lan=True,
            query="",
        )
        is True
    )


def test_lan_without_session_denied() -> None:
    token = new_studio_token()
    assert (
        studio_request_authorized(
            host="192.168.1.10",
            token=token,
            headers={},
            allow_lan=True,
            query="",
        )
        is False
    )
