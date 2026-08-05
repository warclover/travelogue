"""Unit tests · card_templates registry (PRD-EXPORT-CARD-COMPOSE-V1 §6)."""

from __future__ import annotations

import pytest

from travelogue.export.card_templates import (
    AVAILABLE_SLOT_COUNTS,
    CARD_TEMPLATES,
    POSTER_TEMPLATE_PRIORITY,
    pick_template_for_count,
    templates_by_slot_count,
)

pytestmark = pytest.mark.unit


def test_nine_templates_registered() -> None:
    assert len(CARD_TEMPLATES) == 9


def test_slot_counts_distribution() -> None:
    counts = sorted(t.slot_count for t in CARD_TEMPLATES.values())
    assert counts == [1, 4, 6, 6, 6, 6, 7, 7, 9]


def test_available_slot_counts_desc() -> None:
    assert AVAILABLE_SLOT_COUNTS == (9, 7, 6, 4, 1)


def test_every_slot_within_3x3_grid() -> None:
    for template in CARD_TEMPLATES.values():
        for slot in template.slots:
            assert 0 <= slot.row < 3
            assert 0 <= slot.col < 3
            assert slot.row + slot.row_span <= 3, template.id
            assert slot.col + slot.col_span <= 3, template.id


def test_only_card4_has_crop_required_slot() -> None:
    crop_required = [
        t.id
        for t in CARD_TEMPLATES.values()
        if any(1.0 < s.display_aspect < 1.3 for s in t.slots)
    ]
    assert crop_required == ["card-4-square-top-triband"]


def test_main_slot_templates_match_poster_priority() -> None:
    main_slot_ids = {t.id for t in CARD_TEMPLATES.values() if t.has_main_slot}
    assert main_slot_ids == set(POSTER_TEMPLATE_PRIORITY)


def test_templates_by_slot_count_deterministic_order() -> None:
    six = templates_by_slot_count(6)
    assert [t.id for t in six] == sorted(t.id for t in six)
    assert len(six) == 4


def test_pick_template_for_count_round_robins() -> None:
    picks = [pick_template_for_count(6, card_index=i).id for i in range(4)]
    assert len(set(picks)) == 4  # all 4 six-slot templates visited once
    assert pick_template_for_count(6, card_index=4).id == picks[0]


def test_pick_template_for_count_single_candidate() -> None:
    assert pick_template_for_count(1, card_index=0).id == "card-1-full-frame"
    assert pick_template_for_count(1, card_index=7).id == "card-1-full-frame"
    assert pick_template_for_count(9, card_index=3).id == "card-9-grid-equal"


def test_pick_template_for_count_unknown_raises() -> None:
    with pytest.raises(ValueError):
        pick_template_for_count(2)
