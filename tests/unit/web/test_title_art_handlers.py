"""Studio · title-art 一次性生成 handler
(PRD-COVER-CALLIGRAPHY-TITLE-V1 §8 · D-CAL-14/16/21)。
"""

from __future__ import annotations

import pytest

from travelogue.cover_engine.title_art.models import TitleArtResult


class _H:
    def __init__(self, body: dict | None = None) -> None:
        self.status: int | None = None
        self.resp_body: dict | None = None
        self._body = body or {}

    def _read_json_body(self):
        return self._body

    def _json_response(self, status, body):
        self.status = status
        self.resp_body = body


class _Cfg:
    class _TitleArt:
        def __init__(self, enabled: bool, route_c_enabled: bool) -> None:
            self.enabled = enabled
            self.route_c_enabled = route_c_enabled
            self.model_name = "wanx2.1-t2i-plus"
            self.prompt_version = "v2"
            self.route_c_max_attempts = 2
            self.ocr_verify = True

    def __init__(self, route_c_enabled: bool = False) -> None:
        self.title_art = _Cfg._TitleArt(True, route_c_enabled)


def _mount(monkeypatch: pytest.MonkeyPatch, tmp_path, *, route_c_enabled: bool = False):
    from travelogue.web.studio_handlers import title_art_handlers as mod

    trip_dir = tmp_path / "demo-title-art"
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text("{}", encoding="utf-8")

    class _Svc:
        def update(self, _path, mutator, **_kwargs):
            return mutator({"meta": {}})

    class _Ctx:
        cfg = _Cfg(route_c_enabled=route_c_enabled)

        def trip_service(self):
            return _Svc()

    monkeypatch.setattr(mod, "load_trip_or_404", lambda *_a, **_k: (trip_dir, {}))
    monkeypatch.setattr(mod, "studio_ctx", lambda *_a, **_k: _Ctx())
    monkeypatch.setattr(mod, "_rerender", lambda *_a, **_k: True)
    return mod


def test_route_c_request_ignored_when_server_gate_off(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """OQ-CAL-06 · routeC:true 请求必须与服务端总闸相与，总闸关时静默走路线 B。"""
    mod = _mount(monkeypatch, tmp_path, route_c_enabled=False)
    captured: dict = {}

    def _fake_resolve(_trip, *, route_c_enabled, **_kwargs):
        captured["route_c_enabled"] = route_c_enabled
        return TitleArtResult(enabled=True)

    monkeypatch.setattr(mod, "resolve_title_art", _fake_resolve)
    h = _H({"routeC": True, "force": True})
    mod.handle_post_resolve_title_art(h, "demo-title-art")
    assert captured["route_c_enabled"] is False
    assert h.status == 200
    assert h.resp_body["ok"] is True
    assert h.resp_body["routeCRequested"] is True
    assert h.resp_body["routeCAllowedByConfig"] is False


def test_route_c_request_honored_when_server_gate_on(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    mod = _mount(monkeypatch, tmp_path, route_c_enabled=True)
    captured: dict = {}

    def _fake_resolve(_trip, *, route_c_enabled, **_kwargs):
        captured["route_c_enabled"] = route_c_enabled
        return TitleArtResult(enabled=True, engine="diffusion-fixed-prompt-v1")

    monkeypatch.setattr(mod, "resolve_title_art", _fake_resolve)
    h = _H({"routeC": True})
    mod.handle_post_resolve_title_art(h, "demo-title-art")
    assert captured["route_c_enabled"] is True
    assert h.resp_body["engine"] == "diffusion-fixed-prompt-v1"


def test_resolve_none_reports_disabled_without_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """fail-open（非白名单/空标题/字形不覆盖）时 resolve_title_art 返回 None，
    handler 须 200 + enabled:false，不能报错。"""
    mod = _mount(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "resolve_title_art", lambda *_a, **_k: None)
    h = _H({})
    mod.handle_post_resolve_title_art(h, "demo-title-art")
    assert h.status == 200
    assert h.resp_body == {
        "ok": True,
        "enabled": False,
        "routeCRequested": False,
        "routeCAllowedByConfig": False,
    }


def test_unexpected_exception_fails_open_not_500(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """D-CAL-16 · 未知异常也要 fail-open，不能把 500 展示给用户。"""
    mod = _mount(monkeypatch, tmp_path)

    def _boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(mod, "resolve_title_art", _boom)
    h = _H({})
    mod.handle_post_resolve_title_art(h, "demo-title-art")
    assert h.status == 200
    assert h.resp_body["ok"] is True
    assert h.resp_body["enabled"] is False


def test_force_defaults_true_for_one_shot_button(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    mod = _mount(monkeypatch, tmp_path)
    captured: dict = {}

    def _fake_resolve(_trip, *, force, **_kwargs):
        captured["force"] = force
        return TitleArtResult(enabled=True)

    monkeypatch.setattr(mod, "resolve_title_art", _fake_resolve)
    h = _H({})
    mod.handle_post_resolve_title_art(h, "demo-title-art")
    assert captured["force"] is True


def test_rerender_failure_returns_500(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    mod = _mount(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "resolve_title_art", lambda *_a, **_k: TitleArtResult(enabled=True))
    monkeypatch.setattr(mod, "_rerender", lambda *_a, **_k: False)
    h = _H({})
    mod.handle_post_resolve_title_art(h, "demo-title-art")
    assert h.status == 500


def test_resolve_runs_outside_cas_mutator(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """付费/耗时 resolve 必须在 TripService.update mutator 之外执行。"""
    mod = _mount(monkeypatch, tmp_path)
    order: list[str] = []

    def _fake_resolve(_trip, **_kwargs):
        order.append("resolve")
        return TitleArtResult(enabled=True, engine="clean-pipeline-v1", asset_path="x.png")

    class _Svc:
        def update(self, _path, mutator, **_kwargs):
            order.append("update")
            return mutator({"meta": {}})

    class _Ctx:
        cfg = _Cfg(route_c_enabled=False)

        def trip_service(self):
            return _Svc()

    monkeypatch.setattr(mod, "resolve_title_art", _fake_resolve)
    monkeypatch.setattr(mod, "studio_ctx", lambda *_a, **_k: _Ctx())
    h = _H({})
    mod.handle_post_resolve_title_art(h, "demo-title-art")
    assert order == ["resolve", "update"]
    assert h.status == 200
    assert h.resp_body["enabled"] is True
