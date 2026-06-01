"""Studio homepage gate · security / holdback integrity (P1 review fixes)."""

from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

import pytest

from travelogue.web.studio_homepage_gate import (
    decide_root_variant,
    inject_home_placeholders,
    set_bucket_cookie,
    sign_bucket_value,
    stable_bucket,
)
from tests.test_studio_server import _free_port, _start_studio_server

pytestmark = pytest.mark.e2e


class _Hdr:
    def __init__(
        self,
        *,
        token: str = "gate-test-secret",
        host: str = "127.0.0.1",
        ua: str = "Mozilla/Test",
    ) -> None:
        self.studio_token = token
        self.studio_host = host
        self.headers = {"User-Agent": ua}


def test_inject_home_placeholders_escapes_token() -> None:
    h = _Hdr(token='"><script>alert(1)</script>')
    html = inject_home_placeholders(
        '<meta content="__STUDIO_TOKEN__" data-bucket-id="__STUDIO_BUCKET_ID__" '
        'data-studio-dev="__STUDIO_DEV__">',
        h,
        7,
    )
    assert "__STUDIO_" not in html
    assert 'data-bucket-id="7"' in html
    assert 'data-studio-dev="1"' in html
    assert "<script>" not in html


def test_inject_home_no_dev_on_lan_host() -> None:
    h = _Hdr(host="192.168.1.10")
    html = inject_home_placeholders('data-studio-dev="__STUDIO_DEV__"', h, 1)
    assert 'data-studio-dev=""' in html


def test_decide_on_mode_blocks_v3_override_when_not_allowed() -> None:
    assert (
        decide_root_variant(
            mode="on",
            percent=100,
            bucket=99,
            query={"homepageVariant": ["v3"]},
            allow_override=False,
        )
        == "v2"
    )


@pytest.mark.e2e
def test_studio_home_gate_on_ignores_homepage_variant_v3(tmp_path: Path, monkeypatch) -> None:
    """P1 · mode=on 时 ?homepageVariant=v3 不可绕过（非 loopback studio_host）。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "on")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port, studio_host="10.0.0.5")
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/?homepageVariant=v3",
            timeout=10,
        ) as resp:
            html = resp.read().decode("utf-8")
        assert 'data-homepage-variant="v2"' in html
        assert "studio-home-v2.css" in html
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_home_gate_tampered_cookie_reassigned(tmp_path: Path, monkeypatch) -> None:
    """P1 · 伪造未签名 hp_bucket → 服务端按 UA 重新分桶并 Set-Cookie。"""
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "auto")
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", "10")
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    ua = "M20jTest/5"
    expected = stable_bucket(ua)
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/",
            method="GET",
            headers={
                "User-Agent": ua,
                "Cookie": "travelogue.studio.hp_bucket=99",
            },
        )

        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ARG002
                return None

        opener = urllib.request.build_opener(_NoRedirect)
        try:
            opener.open(req, timeout=10)
            pytest.fail("expected redirect for treatment bucket")
        except urllib.error.HTTPError as exc:
            assert exc.code == 302
            cookie = exc.headers.get("Set-Cookie") or ""
            assert "travelogue.studio.hp_bucket=" in cookie
            assert str(expected) in cookie
            assert "." in cookie.split("hp_bucket=")[1]
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.e2e
def test_studio_home_injects_data_bucket_id(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/v2", timeout=10) as resp:
            html = resp.read().decode("utf-8")
        assert 'data-bucket-id="' in html
        assert "__STUDIO_BUCKET_ID__" not in html
        assert 'data-studio-dev="1"' in html
    finally:
        server.shutdown()
        server.server_close()


def test_set_bucket_cookie_secure_on_https() -> None:
    class _Hdr:
        studio_token = "secret"
        headers = {"X-Forwarded-Proto": "https"}
        sent: list[tuple[str, str]] = []

        def send_header(self, key: str, value: str) -> None:
            self.sent.append((key, value))

    h = _Hdr()
    set_bucket_cookie(h, 42)
    cookie = next(v for k, v in h.sent if k == "Set-Cookie")
    assert "; Secure" in cookie
    assert "42." in cookie


@pytest.mark.e2e
def test_studio_home_gate_lan_dev_flag_empty(tmp_path: Path) -> None:
    """LAN studio_host 时 HTML 不注入 data-studio-dev=1（harness 不可用）。"""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port, studio_host="10.0.0.5")
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/v2", timeout=10) as resp:
            html = resp.read().decode("utf-8")
        assert 'data-studio-dev=""' in html
    finally:
        server.shutdown()
        server.server_close()
