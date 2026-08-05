"""Unit tests · card_grouper (PRD-EXPORT-CARD-COMPOSE-V1 §4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from travelogue.export.card_grouper import (
    assign_photos_to_slots,
    plan_cards,
    plan_poster_card,
    plan_slot_counts,
)
from travelogue.export.card_templates import CARD_TEMPLATES

pytestmark = pytest.mark.unit


def _landscape(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (1200, 800), (200, 40, 40)).save(path, format="JPEG", quality=90)
    return path


def _portrait(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (800, 1200), (40, 200, 40)).save(path, format="JPEG", quality=90)
    return path


def test_plan_slot_counts_exact_fits() -> None:
    assert plan_slot_counts(0) == []
    assert plan_slot_counts(1) == [1]
    assert plan_slot_counts(9) == [9]
    assert plan_slot_counts(13) == [9, 4]
    assert plan_slot_counts(15) == [9, 6]
    assert plan_slot_counts(10) == [9, 1]


def test_plan_slot_counts_small_all_ones() -> None:
    assert plan_slot_counts(2) == [1, 1]
    assert plan_slot_counts(3) == [1, 1, 1]


def test_plan_slot_counts_consumes_every_photo() -> None:
    for n in range(0, 40):
        counts = plan_slot_counts(n)
        assert sum(counts) == n


def test_assign_photos_to_slots_landscape_role_matching(tmp_path: Path) -> None:
    template = CARD_TEMPLATES["card-6-bookend-rows"]
    photos = []
    for i in range(3):
        photos.append(_landscape(tmp_path / f"l{i}.jpg"))
    for i in range(3):
        photos.append(_portrait(tmp_path / f"p{i}.jpg"))
    ordered = assign_photos_to_slots(photos, template)
    assert len(ordered) == template.slot_count
    for path, slot in zip(ordered, template.slots, strict=True):
        if slot.role == "landscape":
            assert "l" in path.stem
        else:
            assert "p" in path.stem


def test_assign_photos_to_slots_wrong_count_raises(tmp_path: Path) -> None:
    template = CARD_TEMPLATES["card-1-full-frame"]
    with pytest.raises(ValueError):
        assign_photos_to_slots([_landscape(tmp_path / "a.jpg"), _portrait(tmp_path / "b.jpg")], template)


def test_assign_photos_to_slots_borrows_when_no_landscape_supply(tmp_path: Path) -> None:
    """All-portrait pool feeding a template with landscape slots must not drop photos."""
    template = CARD_TEMPLATES["card-6-hero-tl-stack"]  # 1 main + 5 portrait, no landscape slot
    photos = [_portrait(tmp_path / f"p{i}.jpg") for i in range(6)]
    ordered = assign_photos_to_slots(photos, template)
    assert len(ordered) == 6
    assert set(ordered) == set(photos)


def test_plan_cards_covers_all_photos(tmp_path: Path) -> None:
    photos = [_portrait(tmp_path / f"p{i}.jpg") for i in range(20)]
    plans = plan_cards(photos)
    total = sum(len(p.photos) for p in plans)
    assert total == 20
    all_photos = [p for plan in plans for p in plan.photos]
    assert set(all_photos) == set(photos)


def test_plan_cards_empty() -> None:
    assert plan_cards([]) == []


def test_plan_poster_card_small_pool_uses_full_frame(tmp_path: Path) -> None:
    ranked = [_portrait(tmp_path / f"p{i}.jpg") for i in range(2)]
    plan = plan_poster_card(ranked)
    assert plan.template.id == "card-1-full-frame"
    assert len(plan.photos) == 1
    assert plan.photos[0] == ranked[0]


def test_plan_poster_card_medium_pool_uses_square_top(tmp_path: Path) -> None:
    ranked = [_portrait(tmp_path / f"p{i}.jpg") for i in range(4)]
    plan = plan_poster_card(ranked)
    assert plan.template.id == "card-4-square-top-triband"
    assert len(plan.photos) == 4


def test_plan_poster_card_rich_pool_uses_hero_template(tmp_path: Path) -> None:
    ranked = [_portrait(tmp_path / f"p{i}.jpg") for i in range(8)]
    plan = plan_poster_card(ranked)
    assert plan.template.id in {"card-6-hero-tl-stack", "card-6-hero-br-stack"}
    assert plan.template.has_main_slot
    assert len(plan.photos) == 6
    assert set(plan.photos) <= set(ranked[:6])


def test_plan_poster_card_empty_raises() -> None:
    with pytest.raises(ValueError):
        plan_poster_card([])
