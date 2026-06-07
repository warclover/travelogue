"""Studio GET dispatch for LSE layout strategy Inspector routes."""

from __future__ import annotations

from travelogue.web.studio_handlers.paths import (
    LAYOUT_STRATEGIES_PATH,
    LAYOUT_STRATEGIES_RUNTIME_APPROVE_PATH,
    LAYOUT_STRATEGIES_SANDBOX_PATH,
    match_layout_strategy_decisions,
    match_layout_strategy_detail,
    match_layout_strategy_rollback,
    match_layout_strategy_runtime,
)
from travelogue.web.studio_routes import StudioMixin


class _Probe(StudioMixin):
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


def test_match_layout_strategy_paths() -> None:
    sid = "lse-default-2026-06"
    assert match_layout_strategy_detail(f"/__travelogue/layout-strategies/{sid}") == sid
    assert (
        match_layout_strategy_decisions(f"/__travelogue/layout-strategies/{sid}/decisions")
        == sid
    )
    assert match_layout_strategy_runtime(f"/__travelogue/layout-strategies/{sid}/runtime") == sid
    assert match_layout_strategy_detail(LAYOUT_STRATEGIES_PATH) is None
    assert match_layout_strategy_detail(LAYOUT_STRATEGIES_RUNTIME_APPROVE_PATH) is None
    assert (
        match_layout_strategy_rollback(
            "/__travelogue/layout-strategies/lse-default-2026-06/rollback"
        )
        == "lse-default-2026-06"
    )


def test_studio_dispatch_get_layout_strategies_list(monkeypatch) -> None:
    probe = _Probe()
    monkeypatch.setattr(
        "travelogue.web.studio_handlers.layout_strategy_handlers.handle_layout_strategies_list",
        lambda h: probe.calls.append("list"),
    )
    assert probe.studio_dispatch_GET(LAYOUT_STRATEGIES_PATH) is True
    assert probe.calls == ["list"]


def test_studio_dispatch_get_layout_strategy_detail(monkeypatch) -> None:
    probe = _Probe()
    captured: list[str] = []

    def _detail(h, sid: str) -> None:
        captured.append(sid)

    monkeypatch.setattr(
        "travelogue.web.studio_handlers.layout_strategy_handlers.handle_layout_strategy_detail",
        _detail,
    )
    path = "/__travelogue/layout-strategies/lse-default-2026-06"
    assert probe.studio_dispatch_GET(path) is True
    assert captured == ["lse-default-2026-06"]


def test_studio_dispatch_get_layout_strategy_decisions(monkeypatch) -> None:
    probe = _Probe()
    captured: list[str] = []

    def _decisions(h, sid: str) -> None:
        captured.append(sid)

    monkeypatch.setattr(
        "travelogue.web.studio_handlers.layout_strategy_handlers.handle_layout_strategy_decisions",
        _decisions,
    )
    path = "/__travelogue/layout-strategies/lse-default-2026-06/decisions?tripId=demo"
    assert probe.studio_dispatch_GET(path) is True
    assert captured == ["lse-default-2026-06"]


def test_studio_dispatch_post_layout_strategy_runtime_propose(monkeypatch) -> None:
    probe = _Probe()
    captured: list[str] = []

    def _propose(h, sid: str) -> None:
        captured.append(sid)

    monkeypatch.setattr(
        "travelogue.web.studio_handlers.layout_strategy_handlers.handle_layout_strategy_runtime_propose",
        _propose,
    )
    path = "/__travelogue/layout-strategies/lse-default-2026-06/runtime"
    assert probe.studio_dispatch_POST(path) is True
    assert captured == ["lse-default-2026-06"]


def test_studio_dispatch_post_layout_strategy_runtime_approve(monkeypatch) -> None:
    probe = _Probe()
    monkeypatch.setattr(
        "travelogue.web.studio_handlers.layout_strategy_handlers.handle_layout_strategy_runtime_approve",
        lambda h: probe.calls.append("approve"),
    )
    assert probe.studio_dispatch_POST(LAYOUT_STRATEGIES_RUNTIME_APPROVE_PATH) is True
    assert probe.calls == ["approve"]


def test_studio_dispatch_post_layout_strategy_sandbox(monkeypatch) -> None:
    probe = _Probe()
    monkeypatch.setattr(
        "travelogue.web.studio_handlers.layout_strategy_handlers.handle_layout_strategy_sandbox",
        lambda h: probe.calls.append("sandbox"),
    )
    assert probe.studio_dispatch_POST(LAYOUT_STRATEGIES_SANDBOX_PATH) is True
    assert probe.calls == ["sandbox"]


def test_studio_dispatch_post_layout_strategy_rollback(monkeypatch) -> None:
    probe = _Probe()
    captured: list[str] = []

    def _rollback(h, sid: str) -> None:
        captured.append(sid)

    monkeypatch.setattr(
        "travelogue.web.studio_handlers.layout_strategy_handlers.handle_layout_strategy_rollback",
        _rollback,
    )
    path = "/__travelogue/layout-strategies/lse-default-2026-06/rollback"
    assert probe.studio_dispatch_POST(path) is True
    assert captured == ["lse-default-2026-06"]
