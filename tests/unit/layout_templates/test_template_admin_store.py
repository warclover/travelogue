"""Phase 13 template admin store tests."""

from __future__ import annotations

import pytest

from travelogue.templating.admin_store import (
    AdminRevisionConflict,
    get_store_revision,
    update_template_lifecycle,
)
from travelogue.templating.lifecycle import LifecycleTransitionError


@pytest.fixture(autouse=True)
def _isolate_state(tmp_path, monkeypatch):
    path = tmp_path / "template_admin_state.json"
    monkeypatch.setattr("travelogue.templating.admin_store._STATE_PATH", path)
    monkeypatch.setattr("travelogue.domain.template_admin_state._ADMIN_STATE_PATH", path)
    monkeypatch.setattr("travelogue.domain.template_admin_state._RUNTIME_CACHE", None)
    yield


def test_lifecycle_update_increments_revision() -> None:
    assert get_store_revision() == 0
    out = update_template_lifecycle(
        "visual-journal",
        "beta",
        current="ga",
        expected_revision=0,
        confirm_high_risk=True,
    )
    assert out["revision"] == 1
    assert get_store_revision() == 1


def test_revision_conflict() -> None:
    update_template_lifecycle(
        "visual-journal",
        "beta",
        current="ga",
        expected_revision=0,
        confirm_high_risk=True,
    )
    with pytest.raises(AdminRevisionConflict):
        update_template_lifecycle(
            "visual-journal",
            "ga",
            current="beta",
            expected_revision=0,
            confirm_high_risk=True,
        )


def test_high_risk_requires_confirm() -> None:
    update_template_lifecycle(
        "visual-journal",
        "beta",
        current="ga",
        expected_revision=0,
        confirm_high_risk=True,
    )
    with pytest.raises(ValueError, match="E_TEMPLATE_CONFIRM_REQUIRED"):
        update_template_lifecycle(
            "visual-journal",
            "disabled",
            current="beta",
            expected_revision=1,
            confirm_high_risk=False,
        )


def test_invalid_transition() -> None:
    with pytest.raises(LifecycleTransitionError):
        update_template_lifecycle(
            "visual-journal",
            "experimental",
            current="ga",
            expected_revision=0,
            confirm_high_risk=True,
        )
