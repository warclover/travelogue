"""P14 admin CRUD: register / metadata / logical delete."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.templating.template_admin_crud import (
    count_trips_referencing_template,
    register_template_from_disk,
    update_template_metadata,
)


def test_count_trips_referencing_template(tmp_path: Path) -> None:
    trips = tmp_path / "trips"
    (trips / "t1").mkdir(parents=True)
    (trips / "t1" / "trip.json").write_text(
        json.dumps({"templateSelection": {"resolvedTemplateId": "event-recap"}}),
        encoding="utf-8",
    )
    assert count_trips_referencing_template(trips, "event-recap") == 1
    assert count_trips_referencing_template(trips, "visual-journal") == 0


def test_register_event_recap_from_disk() -> None:
    out = register_template_from_disk("event-recap", operator="test")
    assert out["templateId"] == "event-recap"
    assert out["healthy"] is True


def test_update_template_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "template_admin_state.json"
    state.write_text(
        json.dumps({"revision": 1, "templates": {}, "audit": [], "runtime": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr("travelogue.templating.admin_store._STATE_PATH", state)
    out = update_template_metadata(
        "visual-journal",
        {"displayName": "视觉游记", "category": "travel"},
        operator="test",
    )
    assert out["revision"] == 2
    assert out["metadata"]["displayName"] == "视觉游记"


def test_logical_delete_requires_confirm(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="E_TEMPLATE_CONFIRM_REQUIRED"):
        from travelogue.templating.template_admin_crud import logical_delete_template

        logical_delete_template("event-recap", trips_root=tmp_path, confirm_high_risk=False)
