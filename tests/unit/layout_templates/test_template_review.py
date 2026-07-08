"""Template human review workflow (REL-04)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.templating.review import (
    approve_review,
    get_review_status,
    require_review_approved_for_ga,
    submit_for_review,
)


def test_review_workflow_ga_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "template_admin_state.json"
    state.write_text(
        json.dumps({"revision": 1, "templates": {}, "audit": [], "runtime": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr("travelogue.templating.admin_store._STATE_PATH", state)
    monkeypatch.setattr("travelogue.domain.template_admin_state._ADMIN_STATE_PATH", state)

    with pytest.raises(ValueError, match="E_TEMPLATE_REVIEW_REQUIRED"):
        require_review_approved_for_ga("visual-journal")

    submit_for_review("visual-journal", operator="op")
    assert get_review_status("visual-journal")["status"] == "pending"

    approve_review("visual-journal", reviewer="lead", note="ok")
    assert get_review_status("visual-journal")["status"] == "approved"
    require_review_approved_for_ga("visual-journal")
