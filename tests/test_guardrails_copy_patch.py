"""AC-P13-12: inline copy guardrails block locked scopes."""

from __future__ import annotations

import pytest

from travelogue.web.copy_patch import CopyPatchError, apply_copy_patches


def test_guardrails_allows_editable_meta_hook() -> None:
    trip = {
        "templateId": "visual-journal",
        "templateSelection": {"resolvedTemplateId": "visual-journal"},
        "meta": {},
    }
    updated = apply_copy_patches(trip, [{"path": "meta.hook", "value": "停顿一下"}])
    assert "meta.hook" in updated
    assert trip["meta"]["hook"] == "停顿一下"


def test_guardrails_blocks_non_editable_scope() -> None:
    trip = {
        "templateId": "visual-journal",
        "templateSelection": {"resolvedTemplateId": "visual-journal"},
    }
    with pytest.raises(CopyPatchError) as exc:
        apply_copy_patches(trip, [{"path": "chapters.c1.screens", "value": "x"}])
    assert exc.value.code == "E_TEMPLATE_GUARDRAIL"
