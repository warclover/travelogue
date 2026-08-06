"""Unit tests · card_grouper (PRD-EXPORT-CARD-COMPOSE-V1 §4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from travelogue.export.card_grouper import (
    _slot_is_landscape_shaped,
    assign_photos_to_slots,
    count_orientation_mismatches,
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
    # v0.5.0: AVAILABLE_SLOT_COUNTS gained {3,5,10,12,13} from the 2026-08-05
    # user-mockup template batch, so several of these now resolve to a
    # single exact-fit card instead of a multi-card split.
    assert plan_slot_counts(0) == []
    assert plan_slot_counts(1) == [1]
    assert plan_slot_counts(9) == [9]
    assert plan_slot_counts(13) == [13]  # was [9, 4] pre-v0.5.0
    assert plan_slot_counts(15) == [13, 2]  # was [9, 6] pre-v0.5.0
    assert plan_slot_counts(10) == [10]  # was [9, 1] pre-v0.5.0


def test_plan_slot_counts_small_prefers_largest_exact_fit() -> None:
    # card-2-stack-equal (v0.4.0) and card-3-mini-triband (v0.5.0) are each
    # now the largest-fits-first exact match for n=2/3.
    assert plan_slot_counts(2) == [2]
    assert plan_slot_counts(3) == [3]  # was [2, 1] pre-v0.5.0


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


@pytest.mark.parametrize(
    "template_id",
    [
        "card-3-mini-triband",
        "card-5-hero-mid-landscape",
        "card-7-triband-hero-mid",
        "card-9-hero-mid-triband",
    ],
)
def test_assign_photos_to_slots_landscape_shaped_main_prefers_landscape_photo(
    tmp_path: Path, template_id: str
) -> None:
    """Regression (2026-08-05, post-wechat_official user report): these 4
    v0.5.0 templates give ``main`` a landscape-shaped cell (display_aspect
    1.5), not the portrait/near-square shape the original 9 templates use.
    A landscape-shaped ``main`` must draw from the landscape photo pool —
    otherwise it starves the template's real landscape slots and a portrait
    photo gets force-cropped into a 1.5-aspect cell."""
    template = CARD_TEMPLATES[template_id]
    n = template.slot_count
    landscape_shaped = sum(
        1 for s in template.slots if s.role == "landscape" or s.display_aspect > 1.3
    )
    assert landscape_shaped >= 1  # sanity: every one of these has >=1 such slot
    # Supply exactly as many landscape photos as there are landscape-shaped
    # slots, and fill the rest with portrait — enough supply that nothing
    # should need to "borrow" across pools.
    landscapes = [_landscape(tmp_path / f"l{i}.jpg") for i in range(landscape_shaped)]
    portraits = [_portrait(tmp_path / f"p{i}.jpg") for i in range(n - landscape_shaped)]
    ordered = assign_photos_to_slots(landscapes + portraits, template)
    for path, slot in zip(ordered, template.slots, strict=True):
        is_landscape_shaped = slot.role == "landscape" or slot.display_aspect > 1.3
        if is_landscape_shaped:
            assert "l" in path.stem, (
                f"{template_id}: {slot.role} slot (display_aspect="
                f"{slot.display_aspect}) got a portrait photo despite full "
                "landscape supply"
            )
        else:
            assert "p" in path.stem


def test_plan_cards_covers_all_photos(tmp_path: Path) -> None:
    photos = [_portrait(tmp_path / f"p{i}.jpg") for i in range(20)]
    plans = plan_cards(photos)
    total = sum(len(p.photos) for p in plans)
    assert total == 20
    all_photos = [p for plan in plans for p in plan.photos]
    assert set(all_photos) == set(photos)


def test_plan_cards_all_portrait_matches_pre_fix_chunking(tmp_path: Path) -> None:
    """The 2026-08-05 supply-aware rewrite must not change behavior for the
    common all-portrait case: with zero landscape supply, every 0%-landscape
    template ties on "proportional fit", so the largest-count tie-break
    should still land on the exact same chunk sequence the old pure
    greedy-largest-first chunker produced (card-16-grid-equal x1 +
    card-4-square-top-triband x1, same as ``plan_slot_counts(20)``)."""
    photos = [_portrait(tmp_path / f"p{i}.jpg") for i in range(20)]
    plans = plan_cards(photos)
    assert [p.template.id for p in plans] == [
        "card-16-grid-equal",
        "card-4-square-top-triband",
    ]


def _mixed(tmp_path: Path, n_landscape: int, n_portrait: int) -> list[Path]:
    photos = [_landscape(tmp_path / f"l{i}.jpg") for i in range(n_landscape)]
    photos += [_portrait(tmp_path / f"p{i}.jpg") for i in range(n_portrait)]
    return photos


@pytest.mark.parametrize(
    ("n_landscape", "n_portrait"),
    [
        (31, 41),  # real-trip mix that exposed the bug (2026-08-05)
        (4, 4),  # test_export_xiaohongshu_collage_pages fixture ratio
        (7, 6),  # test_export_xiaohongshu_covers_every_photo fixture ratio
        (6, 6),  # test_export_album_spread_geometry fixture ratio
        (2, 70),  # landscape-scarce trip
        (70, 2),  # landscape-abundant trip
    ],
)
def test_plan_cards_avoids_avoidable_orientation_mismatches(
    tmp_path: Path, n_landscape: int, n_portrait: int
) -> None:
    """Regression (2026-08-05, user report: "还有部分模板会错误装配横版或竖版
    照片，导致人物被裁"). Root cause: ``plan_cards`` picked each card's
    template purely by count (greedy-largest-first + round-robin), blind to
    how much landscape/portrait supply the trip's photos actually had. Some
    templates are 100% one orientation (``card-2-stack-equal``,
    ``card-5-hero-mid-landscape``, ``card-8-grid-equal``) or 0% landscape
    (``card-16-grid-equal`` + 6 others), so greedy-largest-first heavily
    over-used the 0%-landscape ``card-16-grid-equal`` (the single largest
    count) while starving every other card of landscape capacity — forcing
    dozens of landscape photos into portrait-shaped cells (or vice versa).

    A card is only allowed to have a wrong-orientation slot when the
    *global* supply genuinely can't do better — i.e. total mismatches must
    not exceed ``abs(n_landscape - total_landscape_shaped_slots)`` (the
    structural, unavoidable shortfall from the chosen template mix)."""
    photos = _mixed(tmp_path, n_landscape, n_portrait)
    plans = plan_cards(photos)
    total = sum(len(p.photos) for p in plans)
    assert total == n_landscape + n_portrait
    all_photos = [p for plan in plans for p in plan.photos]
    assert set(all_photos) == set(photos)

    total_landscape_shaped_slots = 0
    mismatches = 0
    for plan in plans:
        for photo, slot in zip(plan.photos, plan.template.slots, strict=True):
            want_landscape = _slot_is_landscape_shaped(slot)
            got_landscape = "l" in photo.stem and "p" not in photo.stem
            if want_landscape:
                total_landscape_shaped_slots += 1
            if want_landscape != got_landscape:
                mismatches += 1

    structural_shortfall = abs(n_landscape - total_landscape_shaped_slots)
    assert mismatches <= structural_shortfall, (
        f"n_landscape={n_landscape} n_portrait={n_portrait}: {mismatches} "
        f"mismatches exceed the {structural_shortfall} structurally "
        "unavoidable given the chosen template mix's landscape-shaped-slot "
        f"total ({total_landscape_shaped_slots})"
    )


def test_plan_cards_never_picks_card16_when_landscape_supply_is_meaningful(
    tmp_path: Path,
) -> None:
    """``card-16-grid-equal`` has zero landscape-shaped slots — it's the
    template that hoarded portrait-friendly capacity in the pre-fix bug.
    With a healthy (~40%) landscape supply, it must not be the first pick."""
    photos = _mixed(tmp_path, 31, 41)
    plans = plan_cards(photos)
    assert plans[0].template.id != "card-16-grid-equal"


@pytest.mark.parametrize(
    ("n_landscape", "n_portrait", "target_per_card"),
    [
        (20, 27, 6),  # demo-1547c68851 repro ratio (2026-08-06 user report)
        (20, 27, 5),  # target itself equals the all-landscape template's size
        (2, 45, 6),  # landscape-scarce, same target as above
    ],
)
def test_plan_cards_manual_target_per_card_still_avoids_avoidable_mismatches(
    tmp_path: Path, n_landscape: int, n_portrait: int, target_per_card: int
) -> None:
    """Regression (2026-08-06, user report: 自定义张数=8 张即 target_per_card=6
    时，``card-5-hero-mid-landscape`` 的横版槙位被塞进竖版照片). Root cause:
    manual mode used to walk a *fixed* chunk-size sequence
    (``plan_slot_counts``' repeat-nearest-count contract) and pick a
    template only *within* that exact size — so a trailing 5-photo chunk
    had no choice but the one 100%-landscape template that size offers,
    however little landscape supply actually remained. ``target_per_card``
    is now a **soft** bias on the same joint size+template selection auto
    mode uses (2026-08-06 "soft-target" decision): AC-ECC-04 orientation
    correctness always outranks hitting the requested size exactly, so the
    resulting page count may drift from a literal reading of
    ``target_per_card`` — that's intentional, not a regression."""
    photos = _mixed(tmp_path, n_landscape, n_portrait)
    plans = plan_cards(photos, target_per_card=target_per_card)
    total = sum(len(p.photos) for p in plans)
    assert total == n_landscape + n_portrait
    assert set(p for plan in plans for p in plan.photos) == set(photos)

    total_landscape_shaped_slots = sum(
        1 for plan in plans for slot in plan.template.slots if _slot_is_landscape_shaped(slot)
    )
    structural_shortfall = abs(n_landscape - total_landscape_shaped_slots)
    mismatches = count_orientation_mismatches(plans)
    assert mismatches <= structural_shortfall, (
        f"target_per_card={target_per_card} n_landscape={n_landscape} "
        f"n_portrait={n_portrait}: {mismatches} mismatches exceed the "
        f"{structural_shortfall} structurally unavoidable given the chosen "
        f"template mix's landscape-shaped-slot total ({total_landscape_shaped_slots})"
    )


def test_count_orientation_mismatches_matches_manual_computation(tmp_path: Path) -> None:
    """Sanity check for the helper itself (used by ``export_collage_pack``'s
    post-hoc "被迫裁切" hint, 2026-08-06): must agree with the same per-slot
    orientation comparison the regression tests above compute inline."""
    photos = _mixed(tmp_path, 31, 41)
    plans = plan_cards(photos)
    expected = sum(
        1
        for plan in plans
        for photo, slot in zip(plan.photos, plan.template.slots, strict=True)
        if _slot_is_landscape_shaped(slot) != ("l" in photo.stem and "p" not in photo.stem)
    )
    assert count_orientation_mismatches(plans) == expected


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
