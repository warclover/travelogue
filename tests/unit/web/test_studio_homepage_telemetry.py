"""P9-P1-05 · Studio homepage funnel telemetry."""

from __future__ import annotations

import json

import pytest

from tests.studio_test_helpers import MockStudioHandler
from travelogue.web.studio_handlers.telemetry_handlers import handle_studio_event
from travelogue.web.studio_homepage_telemetry import (
    ALLOWED_STUDIO_HOMEPAGE_EVENTS,
    append_studio_homepage_event,
    studio_homepage_events_path,
)

pytestmark = pytest.mark.unit


def test_append_studio_homepage_event_writes_jsonl(tmp_path, monkeypatch) -> None:
    path = tmp_path / "studio-homepage-events.jsonl"
    monkeypatch.setattr(
        "travelogue.domain.studio_events.studio_homepage_events_path",
        lambda: path,
    )
    append_studio_homepage_event("open_sheet", {"state": "IdleEmpty"})
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["event"] == "open_sheet"
    assert record["meta"] == {"state": "IdleEmpty"}
    assert "ts" in record


def test_append_rejects_unknown_event() -> None:
    with pytest.raises(ValueError, match="unknown"):
        append_studio_homepage_event("not_real")


def test_ai_surface_gate_meta_exactly_enabled_bool(tmp_path, monkeypatch) -> None:
    """AC-QFX-10 · meta 恰好 {enabled: bool}。"""
    path = tmp_path / "studio-homepage-events.jsonl"
    monkeypatch.setattr(
        "travelogue.domain.studio_events.studio_homepage_events_path",
        lambda: path,
    )
    append_studio_homepage_event("ai_surface_gate", {"enabled": False})
    with pytest.raises(ValueError, match="exactly"):
        append_studio_homepage_event(
            "ai_surface_gate", {"enabled": True, "extra": 1}
        )
    with pytest.raises(ValueError, match="bool"):
        append_studio_homepage_event("ai_surface_gate", {"enabled": "yes"})


def test_longshot2_telemetry_events_allowed(tmp_path, monkeypatch) -> None:
    """DOC-LNG2-01 · PRD-LONGSHOT-2.0 §12 events are registered."""
    path = tmp_path / "studio-homepage-events.jsonl"
    monkeypatch.setattr(
        "travelogue.domain.studio_events.studio_homepage_events_path",
        lambda: path,
    )
    for ev in (
        "longshot_export_start",
        "longshot_export_success",
        "longshot_export_fail",
        "longshot_platform_change",
    ):
        assert ev in ALLOWED_STUDIO_HOMEPAGE_EVENTS
        append_studio_homepage_event(ev, {"platform": "xiaohongshu"})
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 4


def test_ftue_telemetry_events_allowed(tmp_path, monkeypatch) -> None:
    """PRD-FTUE §7 · funnel events registered on both sides."""
    path = tmp_path / "studio-homepage-events.jsonl"
    monkeypatch.setattr(
        "travelogue.domain.studio_events.studio_homepage_events_path",
        lambda: path,
    )
    for ev in (
        "ftue_demo_album_click",
        "ftue_demo_album_success",
        "ftue_reveal_folder",
        "longshot_success_share_hint_shown",
        "help_funnel_reveal_folder",
    ):
        assert ev in ALLOWED_STUDIO_HOMEPAGE_EVENTS
        append_studio_homepage_event(ev, {"source": "unit"})
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 5


def test_handle_studio_event_accepts_allowed_event(tmp_path, monkeypatch) -> None:
    events_path = tmp_path / "events.jsonl"
    monkeypatch.setattr(
        "travelogue.domain.studio_events.studio_homepage_events_path",
        lambda: events_path,
    )
    handler = MockStudioHandler(tmp_path / "trips")
    handler.command = "POST"
    handler._json_body = {"event": "demo_try", "meta": {"via": "secondary"}}
    handle_studio_event(handler)
    assert handler.response == (200, {"ok": True})


def test_handle_studio_event_rejects_invalid_event(tmp_path) -> None:
    handler = MockStudioHandler(tmp_path / "trips")
    handler.command = "POST"
    handler._json_body = {"event": "bad_event"}
    handle_studio_event(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 400
    assert body.get("allowed") == sorted(ALLOWED_STUDIO_HOMEPAGE_EVENTS)


def test_studio_homepage_events_default_path_under_travelogue() -> None:
    assert studio_homepage_events_path().name == "studio-homepage-events.jsonl"
    assert ".travelogue" in str(studio_homepage_events_path())


def test_append_trims_oversized_meta(tmp_path, monkeypatch) -> None:
    path = tmp_path / "studio-homepage-events.jsonl"
    monkeypatch.setattr(
        "travelogue.domain.studio_events.studio_homepage_events_path",
        lambda: path,
    )
    huge = {"payload": "x" * 5000}
    append_studio_homepage_event("js_error", huge)
    record = json.loads(path.read_text(encoding="utf-8").strip())
    assert record["meta"].get("_truncated") is True
    assert len(json.dumps(record["meta"], ensure_ascii=False).encode("utf-8")) <= 4096
