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


def test_thirteen_templates_registered() -> None:
    assert len(CARD_TEMPLATES) == 13


def test_slot_counts_distribution() -> None:
    counts = sorted(t.slot_count for t in CARD_TEMPLATES.values())
    assert counts == [1, 2, 4, 4, 6, 6, 6, 6, 7, 7, 8, 9, 16]


def test_available_slot_counts_desc() -> None:
    assert AVAILABLE_SLOT_COUNTS == (16, 9, 8, 7, 6, 4, 2, 1)


def test_every_slot_within_its_own_grid() -> None:
    for template in CARD_TEMPLATES.values():
        for slot in template.slots:
            assert 0 <= slot.row < template.grid_rows, template.id
            assert 0 <= slot.col < template.grid_cols, template.id
            assert slot.row + slot.row_span <= template.grid_rows, template.id
            assert slot.col + slot.col_span <= template.grid_cols, template.id


def test_equal_grid_templates_use_own_grid_not_3x3() -> None:
    expected_grids = {
        "card-2-stack-equal": (2, 1),
        "card-4-grid-equal": (2, 2),
        "card-8-grid-equal": (4, 2),
        "card-16-grid-equal": (4, 4),
    }
    for template_id, (rows, cols) in expected_grids.items():
        template = CARD_TEMPLATES[template_id]
        assert (template.grid_rows, template.grid_cols) == (rows, cols)
        assert template.slot_count == rows * cols


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
        pick_template_for_count(3)


def test_pick_template_for_count_new_equal_grid_templates() -> None:
    assert pick_template_for_count(2, card_index=0).id == "card-2-stack-equal"
    assert pick_template_for_count(8, card_index=0).id == "card-8-grid-equal"
    assert pick_template_for_count(16, card_index=0).id == "card-16-grid-equal"


def test_pick_template_for_count_four_round_robins_two_candidates() -> None:
    picks = [pick_template_for_count(4, card_index=i).id for i in range(2)]
    assert set(picks) == {"card-4-grid-equal", "card-4-square-top-triband"}
