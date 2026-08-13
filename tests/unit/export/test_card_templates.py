"""Unit tests · card_templates registry (PRD-EXPORT-CARD-COMPOSE-V1 §6)."""

from __future__ import annotations

import pytest

from travelogue.export.card_templates import (
    AVAILABLE_SLOT_COUNTS,
    CARD_TEMPLATES,
    POSTER_TEMPLATE_PRIORITY,
    PROBE_TEMPLATES,
    pick_template_for_count,
    templates_by_slot_count,
)

pytestmark = pytest.mark.unit


def test_twenty_eight_templates_registered() -> None:
    assert len(CARD_TEMPLATES) == 28


def test_probe_templates_empty_and_disjoint() -> None:
    from travelogue.export.card_templates import _ALL_TEMPLATES

    assert PROBE_TEMPLATES == {}
    assert CARD_TEMPLATES.keys().isdisjoint(PROBE_TEMPLATES)
    assert len(_ALL_TEMPLATES) == 28
    assert AVAILABLE_SLOT_COUNTS == (16, 13, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1)


def test_slot_counts_distribution() -> None:
    counts = sorted(t.slot_count for t in CARD_TEMPLATES.values())
    assert counts == [
        1, 2, 3, 4, 4, 5, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 9, 9, 10, 10,
        12, 12, 12, 13, 13, 16,
    ]


def test_available_slot_counts_desc() -> None:
    assert AVAILABLE_SLOT_COUNTS == (16, 13, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1)


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
    assert len(six) == 6


def test_pick_template_for_count_round_robins() -> None:
    picks = [pick_template_for_count(6, card_index=i).id for i in range(6)]
    assert len(set(picks)) == 6  # all 6 six-slot templates visited once
    assert pick_template_for_count(6, card_index=6).id == picks[0]


def test_pick_template_for_count_single_candidate() -> None:
    assert pick_template_for_count(1, card_index=0).id == "card-1-full-frame"
    assert pick_template_for_count(1, card_index=7).id == "card-1-full-frame"


def test_pick_template_for_count_nine_round_robins_two_candidates() -> None:
    # v0.5.0: card-9-hero-mid-triband joined card-9-grid-equal at slot_count=9.
    picks = [pick_template_for_count(9, card_index=i).id for i in range(2)]
    assert set(picks) == {"card-9-grid-equal", "card-9-hero-mid-triband"}
    assert pick_template_for_count(9, card_index=2).id == picks[0]


def test_pick_template_for_count_unknown_raises() -> None:
    with pytest.raises(ValueError):
        pick_template_for_count(11)  # not in AVAILABLE_SLOT_COUNTS


def test_pick_template_for_count_new_equal_grid_templates() -> None:
    assert pick_template_for_count(2, card_index=0).id == "card-2-stack-equal"
    assert pick_template_for_count(8, card_index=0).id == "card-8-grid-equal"
    assert pick_template_for_count(16, card_index=0).id == "card-16-grid-equal"


def test_pick_template_for_count_four_round_robins_two_candidates() -> None:
    picks = [pick_template_for_count(4, card_index=i).id for i in range(2)]
    assert set(picks) == {"card-4-grid-equal", "card-4-square-top-triband"}


# -- v0.5.0 · 15 templates from the 2026-08-05 user-mockup batch ------------

_V050_NEW_TEMPLATE_IDS: tuple[str, ...] = (
    "card-3-mini-triband",
    "card-5-hero-mid-landscape",
    "card-6-pinwheel-diagonal",
    "card-6-sandwich-bands",
    "card-7-hero-top-halves",
    "card-7-triband-hero-mid",
    "card-8-pinwheel-diagonal",
    "card-9-hero-mid-triband",
    "card-10-dual-hero-column",
    "card-10-dual-hero-diagonal",
    "card-12-alt-side-rows",
    "card-12-center-land-rows",
    "card-12-sandwich-bands",
    "card-13-hero-center-stack",
    "card-13-hero-top-stack",
)


def test_v050_new_templates_all_registered() -> None:
    for template_id in _V050_NEW_TEMPLATE_IDS:
        assert template_id in CARD_TEMPLATES


def test_v050_new_templates_grid_fully_covered_no_overlap() -> None:
    """Every cell on each new template's own grid is covered by exactly one
    slot — no gaps, no double-booked cells (hand-derived from user mockups,
    so this is the main safety net against a row/col/span transcription
    error)."""
    for template_id in _V050_NEW_TEMPLATE_IDS:
        template = CARD_TEMPLATES[template_id]
        owner: list[list[int | None]] = [
            [None] * template.grid_cols for _ in range(template.grid_rows)
        ]
        for idx, slot in enumerate(template.slots):
            for r in range(slot.row, slot.row + slot.row_span):
                for c in range(slot.col, slot.col + slot.col_span):
                    assert owner[r][c] is None, (
                        f"{template_id}: cell ({r},{c}) claimed by both "
                        f"slot {owner[r][c]} and slot {idx}"
                    )
                    owner[r][c] = idx
        uncovered = [
            (r, c)
            for r in range(template.grid_rows)
            for c in range(template.grid_cols)
            if owner[r][c] is None
        ]
        assert uncovered == [], f"{template_id}: uncovered cells {uncovered}"


def test_v050_hero_center_vs_top_stack_are_distinct() -> None:
    """User explicitly clarified (annotated-image round) that the 13-slot
    center-hero and top-hero mockups are two different templates, not a
    duplicate — hero row position must differ."""
    center = CARD_TEMPLATES["card-13-hero-center-stack"]
    top = CARD_TEMPLATES["card-13-hero-top-stack"]
    assert center.slot_count == top.slot_count == 13
    center_hero = next(s for s in center.slots if s.row_span > 1)
    top_hero = next(s for s in top.slots if s.row_span > 1)
    assert center_hero.row == 1  # rows 1-2, i.e. vertically centered
    assert top_hero.row == 0  # rows 0-1, i.e. top-anchored
    assert center_hero.row != top_hero.row


def test_v050_new_main_slot_templates_are_crop_free() -> None:
    """The 4 new main-slot templates must not introduce a second
    crop-required slot (display_aspect in the 1.0-1.3 near-square band)."""
    for template_id in (
        "card-3-mini-triband",
        "card-5-hero-mid-landscape",
        "card-7-triband-hero-mid",
        "card-9-hero-mid-triband",
    ):
        template = CARD_TEMPLATES[template_id]
        assert template.has_main_slot
        assert all(not (1.0 < s.display_aspect < 1.3) for s in template.slots)


def test_v050_no_main_slot_templates_have_no_main() -> None:
    no_main_ids = set(_V050_NEW_TEMPLATE_IDS) - {
        "card-3-mini-triband",
        "card-5-hero-mid-landscape",
        "card-7-triband-hero-mid",
        "card-9-hero-mid-triband",
    }
    for template_id in no_main_ids:
        assert not CARD_TEMPLATES[template_id].has_main_slot
