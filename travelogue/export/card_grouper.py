"""CardGrouper — supply-aware slot-count/template selection + orientation-role matching.

PRD-EXPORT-CARD-COMPOSE-V1 §4 (v0.2 simplification): xiaohongshu / poster_bric /
album_spread do **not** require shot-grouping / scene-cluster boundary
awareness. The only hard requirement (AC-ECC-04) is that each slot receives a
photo whose native orientation matches the slot's *actual shape*
(``role == "landscape"``, or a ``main`` slot whose ``display_aspect`` is
landscape-shaped, e.g. ``card-5-hero-mid-landscape``); other ``main`` slots
(portrait/near-square shaped) accept either.

2026-08-05 fix (user report, post-wechat_official regression follow-up): a
per-slot classification bug (landscape-shaped ``main`` slots routed to the
wrong pool) was fixed earlier the same day, but a *second*, larger bug
remained: ``plan_cards`` picked each card's template purely by walking
``plan_slot_counts``' pure-count chunks and round-robining
``pick_template_for_count`` — **blind to how much landscape/portrait supply
the trip's photos actually have**. Some templates are 100% one orientation
(``card-2-stack-equal``, ``card-5-hero-mid-landscape``, ``card-8-grid-equal``)
or 0% landscape (``card-16-grid-equal`` and 6 other all-portrait templates),
and greedy-largest-first chunking heavily favors ``card-16-grid-equal``
(the single largest available count) — which has *zero* landscape-shaped
slots. On a real trip with a realistic ~40/60 landscape/portrait mix, this
starved every other card of landscape capacity and forced dozens of
landscape photos into portrait-shaped cells (and vice versa for the rare
all-landscape template), which is exactly the "人物被裁" symptom (a
landscape group photo of people gets center-cropped hard into a 0.75-aspect
cell, or a portrait photo of a person gets stretched/cropped into a
1.5-aspect cell). ``plan_cards`` now tracks the trip's remaining
landscape/portrait supply globally and picks, at each step, the
best-matching (template, and — in auto mode — slot count) so every card's
demand is met by its own supply as much as globally possible, instead of
committing to a template shape the photo pool can't actually fill. See
``_best_matching_template`` / ``_pull_chunk_for_template`` below.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from travelogue.export.card_templates import (
    AVAILABLE_SLOT_COUNTS,
    CARD_TEMPLATES,
    CardSlot,
    CardTemplate,
    templates_by_slot_count,
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


def _landscape_shaped_slot_count(template: CardTemplate) -> int:
    return sum(1 for s in template.slots if _slot_is_landscape_shaped(s))


def _shortfall(
    template: CardTemplate, *, landscape_remaining: int, portrait_remaining: int
) -> int:
    """How many slots ``template`` would be forced to fill with the *wrong*
    orientation given the currently-remaining global supply (0 == fully
    fillable from real supply, no borrowing needed)."""
    landscape_need = _landscape_shaped_slot_count(template)
    portrait_need = template.slot_count - landscape_need
    return max(0, landscape_need - landscape_remaining) + max(
        0, portrait_need - portrait_remaining
    )


#: Tier-2 tolerance (in *slots*, not a ratio) for how far a candidate's
#: landscape-shaped-slot count may sit from the "proportional share" implied
#: by the currently-remaining supply's ratio and still count as "close
#: enough" to prefer a bigger card over a smaller, more exactly-matched one.
#: Calibrated against a real trip (72 photos, 31 landscape/41 portrait,
#: 2026-08-05): with this tolerance the planner lands on the 12-slot
#: templates (deviation ~1.17 slots) instead of fragmenting into ten
#: 7-slot cards chasing a near-zero deviation — trading roughly one
#: borrowed photo per card for meaningfully fewer, bigger pages, while
#: still keeping an all-or-nothing template like ``card-16-grid-equal``
#: (deviation ~6.9 slots here) excluded whenever landscape supply is
#: non-trivial.
_PROPORTION_SLOT_TOLERANCE = 1.5


def _best_matching_template(
    candidates: list[CardTemplate],
    *,
    landscape_remaining: int,
    portrait_remaining: int,
    card_index: int,
) -> CardTemplate:
    """Pick the best template among ``candidates`` given how much
    landscape/portrait supply *actually remains* trip-wide.

    Tier 1 — prefer templates fully fillable without borrowing across pools
    (``shortfall == 0``) over ones that would force a wrong-orientation
    photo into a slot, whenever any borrow-free option exists.
    Tier 2 (within tier 1, or across all candidates when none are
    borrow-free) — among those, keep only the ones whose landscape-shaped
    slot count is within ``_PROPORTION_SLOT_TOLERANCE`` slots of the
    "proportional share" implied by the remaining supply's own ratio. This
    is what stops an all-portrait template (e.g. ``card-16-grid-equal``,
    0% landscape) from winning purely by being the largest available count
    while real landscape photos still need a home elsewhere in the plan —
    see module docstring — without forcing the planner to chase a
    near-perfect ratio match at the cost of many tiny cards.
    Tier 3 — among the surviving "close enough" candidates, prefer the
    larger slot count (fewer total cards; keeps the "greedy largest"
    spirit of §5.1 as the deciding factor once orientation-fit is already
    good, not an override of it).
    Tier 4 — round-robin by ``card_index`` for visual variety (OQ-ECC-04),
    same spirit as the original ``pick_template_for_count``.
    """
    total_remaining = landscape_remaining + portrait_remaining
    target_ratio = (landscape_remaining / total_remaining) if total_remaining > 0 else 0.0

    def proportion_deviation(t: CardTemplate) -> float:
        return abs(_landscape_shaped_slot_count(t) - target_ratio * t.slot_count)

    min_shortfall = min(
        _shortfall(t, landscape_remaining=landscape_remaining, portrait_remaining=portrait_remaining)
        for t in candidates
    )
    tier = [
        t
        for t in candidates
        if _shortfall(t, landscape_remaining=landscape_remaining, portrait_remaining=portrait_remaining)
        == min_shortfall
    ]
    best_deviation = min(proportion_deviation(t) for t in tier)
    close_enough = [
        t
        for t in tier
        if proportion_deviation(t) <= best_deviation + _PROPORTION_SLOT_TOLERANCE
    ]
    max_size = max(t.slot_count for t in close_enough)
    finalists = sorted((t for t in close_enough if t.slot_count == max_size), key=lambda t: t.id)
    return finalists[card_index % len(finalists)]


def _pull_chunk_for_template(
    template: CardTemplate,
    landscape_queue: list[Path],
    portrait_queue: list[Path],
) -> list[Path]:
    """Consume exactly ``template.slot_count`` photos from the two global
    orientation queues (each preserving its own relative order), preferring
    whichever queue each slot actually wants; borrows from the other queue
    only when one runs short (best-effort — same fallback contract as
    ``assign_photos_to_slots``, which still does the final per-slot
    placement below)."""
    landscape_need = _landscape_shaped_slot_count(template)
    portrait_need = template.slot_count - landscape_need
    chunk: list[Path] = []
    for _ in range(landscape_need):
        if landscape_queue:
            chunk.append(landscape_queue.pop(0))
        elif portrait_queue:
            chunk.append(portrait_queue.pop(0))
    for _ in range(portrait_need):
        if portrait_queue:
            chunk.append(portrait_queue.pop(0))
        elif landscape_queue:
            chunk.append(landscape_queue.pop(0))
    return chunk


def plan_cards(photos: list[Path], *, target_per_card: int | None = None) -> list[CardPlan]:
    """Group ``photos`` into cards per §4: orientation-supply-aware slot-count
    + template selection (§4 v0.2 simplification's *only* hard requirement,
    AC-ECC-04, is that every slot's photo actually matches its shape — see
    module docstring for the 2026-08-05 fix) + round-robin template pick
    among equally-good matches (OQ-ECC-04) + orientation role matching.
    Returns ``[]`` for an empty input (callers should validate minimum
    kept-photo count before calling, per platform's own N floor).

    Photos are split into two orientation queues, each preserving its own
    relative order — a card may therefore combine, e.g., an earlier
    landscape photo with a later portrait photo (grouping/shot-order is
    explicitly *not* required by §4); what's guaranteed is every slot gets
    a photo of the shape it actually wants whenever *global* supply allows.
    """
    if not photos:
        return []
    landscape_queue = [p for p in photos if _photo_orientation(p) == "landscape"]
    portrait_queue = [p for p in photos if _photo_orientation(p) != "landscape"]

    plans: list[CardPlan] = []
    card_index = 0

    if target_per_card and target_per_card > 0:
        # Manual "自定义张数" override: keep the *chunk-size sequence* the
        # user asked for (plan_slot_counts' existing page-count contract),
        # but still pick the best-orientation-matching template at each
        # fixed size instead of blind round-robin — e.g. an 8-photo chunk
        # with only 2 landscape photos left in supply should prefer
        # card-8-pinwheel-diagonal (2 landscape-shaped slots) over
        # card-8-grid-equal (8, which would force 6 borrowed photos).
        for n in plan_slot_counts(len(photos), target_per_card=target_per_card):
            template = _best_matching_template(
                templates_by_slot_count(n),
                landscape_remaining=len(landscape_queue),
                portrait_remaining=len(portrait_queue),
                card_index=card_index,
            )
            chunk = _pull_chunk_for_template(template, landscape_queue, portrait_queue)
            ordered = assign_photos_to_slots(chunk, template)
            plans.append(CardPlan(template=template, photos=tuple(ordered)))
            card_index += 1
    else:
        # Auto mode (§5.1): no externally-fixed chunk sizes, so pick *both*
        # the slot count and the template jointly at each step — otherwise
        # committing to a count before checking supply is exactly how the
        # "picked card-16-grid-equal because it's the largest count" bug
        # happened (see module docstring).
        while landscape_queue or portrait_queue:
            remaining_total = len(landscape_queue) + len(portrait_queue)
            candidates = [t for t in CARD_TEMPLATES.values() if t.slot_count <= remaining_total]
            template = _best_matching_template(
                candidates,
                landscape_remaining=len(landscape_queue),
                portrait_remaining=len(portrait_queue),
                card_index=card_index,
            )
            chunk = _pull_chunk_for_template(template, landscape_queue, portrait_queue)
            ordered = assign_photos_to_slots(chunk, template)
            plans.append(CardPlan(template=template, photos=tuple(ordered)))
            card_index += 1

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
