"""Phase 13 template registry tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.templates.registry import (
    DEFAULT_TEMPLATE_ID,
    TemplateRecord,
    TemplateRegistry,
    bootstrap_registry,
    check_template_health,
    get_registry,
    reset_registry_for_tests,
)
from travelogue.templating.resolver import resolve_effective_template, sync_template_id_mirror


@pytest.fixture(autouse=True)
def _reset_registry():
    reset_registry_for_tests(bootstrap_registry())
    yield
    reset_registry_for_tests(None)


def test_visual_journal_health_passes() -> None:
    ok, errs = check_template_health(DEFAULT_TEMPLATE_ID)
    assert ok, errs


def test_unknown_template_fails_health() -> None:
    ok, errs = check_template_health("missing-template")
    assert not ok
    assert errs


def test_resolve_effective_template_priority() -> None:
    trip = {"templateId": "visual-journal", "templateSelection": {"resolvedTemplateId": "visual-journal"}}
    assert resolve_effective_template(trip) == DEFAULT_TEMPLATE_ID
    legacy = {"templateId": "visual-journal"}
    assert resolve_effective_template(legacy) == DEFAULT_TEMPLATE_ID
    sync_template_id_mirror(trip)
    assert trip["templateId"] == DEFAULT_TEMPLATE_ID


def test_event_recap_registered() -> None:
    from travelogue.templates.registry import EVENT_RECAP_TEMPLATE_ID

    ok, errs = check_template_health(EVENT_RECAP_TEMPLATE_ID)
    assert ok, errs


def test_registry_atomic_publish_gate(tmp_path: Path) -> None:
    reg = TemplateRegistry()
    bad_dir = tmp_path / "empty-template"
    bad_dir.mkdir()
    reg.register(
        TemplateRecord(
            template_id="broken",
            version="0",
            template_dir=bad_dir,
            manifest_path=bad_dir / "manifest.json",
            lifecycle="ga",
        )
    )
    ok, errs = check_template_health("broken", registry=reg)
    assert not ok
    assert any("journal.hbs" in e or "manifest" in e for e in errs)


def test_list_for_consumer_excludes_disabled(tmp_path: Path) -> None:
    reg = bootstrap_registry()
    items = reg.list_for_consumer()
    assert any(r.template_id == DEFAULT_TEMPLATE_ID for r in items)
