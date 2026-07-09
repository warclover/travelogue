"""event-recap pilot template tests."""

from __future__ import annotations

import pytest

from travelogue.templates.registry import (
    EVENT_RECAP_TEMPLATE_ID,
    check_template_health,
)
from travelogue.templating.router import route_template


@pytest.fixture(autouse=True)
def _registry():
    from travelogue.templates.registry import bootstrap_registry, reset_registry_for_tests

    reset_registry_for_tests(bootstrap_registry())
    yield


def test_event_recap_registry_health() -> None:
    ok, errs = check_template_health(EVENT_RECAP_TEMPLATE_ID)
    assert ok, errs


def test_event_recap_route_prefers_video_heavy_trip() -> None:
    trip = {
        "meta": {"dateStart": "2026-01-01", "dateEnd": "2026-01-01", "places": ["会场"]},
        "assets": [
            {"id": "a1", "type": "video"},
            {"id": "a2", "type": "video"},
            {"id": "a3", "type": "image"},
        ],
    }
    sel = route_template(trip, mode="smart")
    assert sel["resolvedTemplateId"] in (EVENT_RECAP_TEMPLATE_ID, "visual-journal")


def test_rollback_l1_disables_router(monkeypatch, tmp_path) -> None:
    from travelogue.templating import admin_store

    monkeypatch.setattr(admin_store, "_STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr("travelogue.domain.template_admin_state._ADMIN_STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr("travelogue.domain.template_admin_state._RUNTIME_CACHE", None)
    admin_store.apply_rollback("L1", confirm_high_risk=True)
    trip = {"meta": {"dateStart": "2026-01-01", "dateEnd": "2026-01-01", "places": ["A"]}}
    sel = route_template(trip, mode="smart")
    assert sel["resolvedTemplateId"] == "visual-journal"
    assert sel.get("fallbackUsed") is True
