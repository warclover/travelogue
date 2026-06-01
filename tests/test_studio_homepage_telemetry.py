"""P9-P1-05 · Studio homepage funnel telemetry."""

from __future__ import annotations

import json

import pytest

from travelogue.web.studio_handlers.telemetry_handlers import handle_studio_event
from travelogue.web.studio_homepage_telemetry import (
    ALLOWED_STUDIO_HOMEPAGE_EVENTS,
    append_studio_homepage_event,
    studio_homepage_events_path,
)
from tests.studio_test_helpers import MockStudioHandler

pytestmark = pytest.mark.unit


def test_append_studio_homepage_event_writes_jsonl(tmp_path, monkeypatch) -> None:
    path = tmp_path / "studio-homepage-events.jsonl"
    monkeypatch.setattr(
        "travelogue.web.studio_homepage_telemetry.studio_homepage_events_path",
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


def test_handle_studio_event_accepts_allowed_event(tmp_path, monkeypatch) -> None:
    events_path = tmp_path / "events.jsonl"
    monkeypatch.setattr(
        "travelogue.web.studio_homepage_telemetry.studio_homepage_events_path",
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
        "travelogue.web.studio_homepage_telemetry.studio_homepage_events_path",
        lambda: path,
    )
    huge = {"payload": "x" * 5000}
    append_studio_homepage_event("js_error", huge)
    record = json.loads(path.read_text(encoding="utf-8").strip())
    assert record["meta"].get("_truncated") is True
    assert len(json.dumps(record["meta"], ensure_ascii=False).encode("utf-8")) <= 4096
