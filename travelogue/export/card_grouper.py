"""CardGrouper — sequential slot-count chunking + orientation-role matching.

PRD-EXPORT-CARD-COMPOSE-V1 §4 (v0.2 simplification): xiaohongshu / poster_bric /
album_spread do **not** require shot-grouping / scene-cluster boundary
awareness. The only hard requirement (AC-ECC-04) is that each slot receives a
photo whose native orientation matches the slot's *actual shape*
(``role == "landscape"``, or a ``main`` slot whose ``display_aspect`` is
landscape-shaped, e.g. ``card-5-hero-mid-landscape``); other ``main`` slots
(portrait/near-square shaped) accept either.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from travelogue.export.card_templates import (
    AVAILABLE_SLOT_COUNTS,
    CARD_TEMPLATES,
    CardSlot,
    CardTemplate,
    pick_template_for_count,
)
from travelogue.media.image_ops import peek_image_meta

Orientation = str  # "landscape" | "portrait"


@dataclass(frozen=True)
class CardPlan:
    template: CardTemplate
    photos: tuple[Path, ...]  # ordered to match template.slots


def _photo_orientation(path: Path) -> Orientation:
    try:
        meta = peek_image_meta(path)
        return "landscape" if meta.width > meta.height * 1.05 else "portrait"
    except Exception:
        return "portrait"


def plan_slot_counts(total_photos: int, *, target_per_card: int | None = None) -> list[int]:
    """Chunk ``total_photos`` using the template library's available slot
    counts (currently ``{1,2,4,6,7,8,9,16}``); ``1`` always exists so this
    always terminates and consumes every photo exactly once.

    Default mode: greedy largest-fits-first (PRD §5.1 — no longer follows the
    old slice-count formula).

    ``target_per_card``: optional advisory hint (e.g. derived from a user's
    manual "自定义张数" / Studio ``slideCount`` request, or
    ``platform_profiles.resolve_xhs_slide_count``'s auto band) — when given,
    repeats the *nearest available* slot count per card instead of always
    maximizing card size, so the resulting page count stays close to what the
    user asked for. The template library still has final say on exact slot
    counts; this never invents an unsupported count.
    """
    remaining = max(0, int(total_photos))
    counts = AVAILABLE_SLOT_COUNTS
    plan: list[int] = []
    if target_per_card and target_per_card > 0:
        nearest = min(counts, key=lambda c: abs(c - target_per_card))
        while remaining > nearest:
            plan.append(nearest)
            remaining -= nearest
    while remaining > 0:
        choice = next((c for c in counts if c <= remaining), min(counts))
        plan.append(choice)
        remaining -= choice
    return plan


#: display_aspect above this reads as a landscape-shaped cell — used to route
#: ``main`` slots by their *actual* geometry rather than blindly by role.
#: card-4-square-top-triband's main (1.125, the one crop-required slot) stays
#: below this line on purpose: it's near-square, not landscape-shaped, and
#: always needs a real crop regardless of which pool it draws from.
_LANDSCAPE_SHAPED_ASPECT_MIN = 1.3


def _slot_is_landscape_shaped(slot: CardSlot) -> bool:
    """Whether a slot should draw from the landscape photo pool.

    ``role == "landscape"`` slots always do. ``main`` slots are declared
    "accept either" orientation, but several v0.5.0 templates
    (card-3/5/7/9-*) give ``main`` a genuinely landscape-shaped cell
    (``display_aspect=1.5``) — those must pull from the landscape pool too,
    or they starve real landscape slots of supply while forcing a portrait
    photo into a 1.5-aspect cell (severe crop). Portrait/near-square
    ``main`` cells (0.75 / 1.125) are unaffected — they keep drawing from
    the portrait pool as before.
    """
    return slot.role == "landscape" or slot.display_aspect > _LANDSCAPE_SHAPED_ASPECT_MIN


def assign_photos_to_slots(photos: list[Path], template: CardTemplate) -> list[Path]:
    """Reorder ``photos`` to match ``template.slots``, matching each photo's
    native orientation to its slot's *actual shape* (landscape-shaped cells,
    including a landscape-shaped ``main``, draw from the landscape pool;
    everything else — portrait/near-square, including a portrait-shaped
    ``main`` — draws from the portrait pool). Within each pool, a ``main``
    slot gets first pick (best/first photo lands there).

    Best-effort: if supply doesn't exactly match demand (e.g. all-portrait
    trip feeding a template with landscape slots), leftovers are filled in
    original relative order rather than left blank.
    """
    if len(photos) != template.slot_count:
        raise ValueError(
            f"assign_photos_to_slots: template {template.id} expects "
            f"{template.slot_count} photos, got {len(photos)}"
        )
    landscape_slot_idx = [
        i for i, s in enumerate(template.slots) if _slot_is_landscape_shaped(s)
    ]
    other_slot_idx = [
        i for i, s in enumerate(template.slots) if not _slot_is_landscape_shaped(s)
    ]
    # `main` slots get first pick within whichever pool they draw from
    # (best/first photo lands there).
    landscape_slot_idx.sort(key=lambda i: 0 if template.slots[i].role == "main" else 1)
    other_slot_idx.sort(key=lambda i: 0 if template.slots[i].role == "main" else 1)

    landscape_photos = [p for p in photos if _photo_orientation(p) == "landscape"]
    other_photos = [p for p in photos if _photo_orientation(p) != "landscape"]

    result: list[Path | None] = [None] * template.slot_count
    li = 0
    for idx in landscape_slot_idx:
        if li < len(landscape_photos):
            result[idx] = landscape_photos[li]
            li += 1
        elif other_photos:
            result[idx] = other_photos.pop(0)
    leftover_landscape = landscape_photos[li:]
    fill_pool = other_photos + leftover_landscape
    fi = 0
    for idx in other_slot_idx:
        if fi < len(fill_pool):
            result[idx] = fill_pool[fi]
            fi += 1

    # Safety net — should never trigger given len(photos) == slot_count exactly.
    used_ids = {id(p) for p in result if p is not None}
    spare = [p for p in photos if id(p) not in used_ids]
    for i, v in enumerate(result):
        if v is None and spare:
            result[i] = spare.pop(0)
    return result  # type: ignore[return-value]


def plan_cards(photos: list[Path], *, target_per_card: int | None = None) -> list[CardPlan]:
    """Chunk ``photos`` (in order) into cards per §4: slot-count chunking
    (greedy by default, or hinted by ``target_per_card``) + round-robin
    template pick (OQ-ECC-04 default) + orientation role matching. Returns
    ``[]`` for an empty input (callers should validate minimum kept-photo
    count before calling, per platform's own N floor)."""
    if not photos:
        return []
    counts = plan_slot_counts(len(photos), target_per_card=target_per_card)
    plans: list[CardPlan] = []
    cursor = 0
    for card_index, n in enumerate(counts):
        chunk = photos[cursor : cursor + n]
        cursor += n
        template = pick_template_for_count(n, card_index=card_index)
        ordered = assign_photos_to_slots(chunk, template)
        plans.append(CardPlan(template=template, photos=tuple(ordered)))
    return plans


def plan_poster_card(ranked_photos: list[Path]) -> CardPlan:
    """Pick a single poster Card from a *cover_score_v2-ranked* (best-first)
    photo pool, per PRD §5.2 priority: prefer richer "hero" templates (no/low
    crop loss) when enough highly-ranked photos exist; fall back to the
    crop-required 4-slot template, then the single full-frame template.
    Never selects the no-main-slot templates (bookend/brick/triband/grid).

    Caller must have already validated ``len(ranked_photos) >= 1``.
    """
    if not ranked_photos:
        raise ValueError("plan_poster_card: ranked_photos must not be empty")
    pool_size = len(ranked_photos)
    if pool_size >= 6:
        # Alternate hero-tl/hero-br for visual variety across trips; both are
        # equal-priority per §5.2 (mirror layouts, same crop-loss profile).
        template_id = "card-6-hero-br-stack" if pool_size % 2 else "card-6-hero-tl-stack"
    elif pool_size >= 4:
        template_id = "card-4-square-top-triband"
    else:
        template_id = "card-1-full-frame"
    template = CARD_TEMPLATES[template_id]
    chosen = ranked_photos[: template.slot_count]
    ordered = assign_photos_to_slots(chosen, template)
    return CardPlan(template=template, photos=tuple(ordered))
