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


def test_guardrails_allows_meta_cover_opening_style() -> None:
    trip = {
        "templateId": "visual-journal",
        "templateSelection": {"resolvedTemplateId": "visual-journal"},
        "meta": {},
    }
    updated = apply_copy_patches(
        trip,
        [{"path": "meta.coverOpeningStyle", "value": "split-mat"}],
    )
    assert "meta.coverOpeningStyle" in updated
    assert trip["meta"]["coverOpeningStyle"] == "split-mat"


def test_guardrails_allows_screen_copy_kicker() -> None:
    trip = {
        "templateId": "visual-journal",
        "templateSelection": {"resolvedTemplateId": "visual-journal"},
        "chapters": [
            {
                "id": "ch-01",
                "screens": [
                    {
                        "screenId": "ch01-s4mix",
                        "patternId": "screen-editorial-4mix",
                        "slots": [{"assetId": "a1", "slot": 0}],
                    }
                ],
            }
        ],
    }
    updated = apply_copy_patches(
        trip,
        [{"path": "chapters.ch-01.screens.ch01-s4mix.copy.kicker", "value": "地点"}],
    )
    assert updated == ["chapters.ch-01.screens.ch01-s4mix.copy.kicker"]


def test_guardrails_blocks_non_editable_scope() -> None:
    trip = {
        "templateId": "visual-journal",
        "templateSelection": {"resolvedTemplateId": "visual-journal"},
    }
    with pytest.raises(CopyPatchError) as exc:
        apply_copy_patches(trip, [{"path": "chapters.c1.screens", "value": "x"}])
    assert exc.value.code == "E_TEMPLATE_GUARDRAIL"
