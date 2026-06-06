"""Admin high-risk / rollback metrics (REL-07/08)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.templates.registry import get_registry
from travelogue.templating.admin_store import apply_rollback, update_template_lifecycle


def test_rollback_records_metric(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "state.json"
    monkeypatch.setattr("travelogue.templating.admin_store._STATE_PATH", state)
    mp = tmp_path / "m.jsonl"
    monkeypatch.setattr("travelogue.templating.metrics.metrics_path", lambda: mp)

    apply_rollback("L1", confirm_high_risk=True, operator="test")
    rows = [json.loads(line) for line in mp.read_text(encoding="utf-8").splitlines()]
    assert any(r.get("name") == "template.admin.rollback_count" for r in rows)


def test_high_risk_lifecycle_records_metric(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "state.json"
    state.write_text(
        json.dumps({"revision": 1, "templates": {}, "audit": [], "runtime": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr("travelogue.templating.admin_store._STATE_PATH", state)
    mp = tmp_path / "m.jsonl"
    monkeypatch.setattr("travelogue.templating.metrics.metrics_path", lambda: mp)

    rec = get_registry().get("event-recap")
    update_template_lifecycle(
        "event-recap",
        "disabled",
        current=rec.lifecycle,
        expected_revision=1,
        confirm_high_risk=True,
        operator="test",
    )
    rows = [json.loads(line) for line in mp.read_text(encoding="utf-8").splitlines()]
    assert any(r.get("name") == "template.admin.high_risk_action_count" for r in rows)
