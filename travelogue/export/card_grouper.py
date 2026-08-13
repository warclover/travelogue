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

2026-08-06 diversity fix (user report: "会大量采用同一种模板，导致导出的
拼图样式高度雷同"): two distinct causes, fixed together.

1. **Fake round-robin.** The former Tier-4 tie-break was
   ``card_index % len(candidates)`` — ``card_index`` is a *global*,
   monotonically-increasing counter, but the tied-candidate set's identity
   and size change from step to step as supply depletes. Whenever that set
   happened to stay small (e.g. 2 templates) across several steps, the
   modulo aliased back to the *same* index over and over — e.g. a real trip
   (``demo-2019``, 72 photos) picked ``card-6-bookend-rows`` 4 times out of
   11 cards despite 3 other equally-valid 6-slot templates existing, purely
   because the tied set kept landing at size 2 with ``card_index`` parity
   always even. This wasn't "the best match repeating because the photo mix
   demanded it" (that *is* legitimate — see point 2) — it was noise.
   ``_best_matching_template`` now tracks real usage counts across the
   whole plan (``usage_counts``) and picks the *least-used-so-far*
   candidate among ties, which naturally spreads usage evenly over the
   whole export regardless of how the tied set's membership fluctuates
   step to step.
2. **Structural repetition.** Separately, a photo pool overwhelmingly
   skewed to one orientation (e.g. 96% landscape) genuinely has only one
   good template at a given size — no amount of round-robin can or should
   "fix" that without reintroducing AC-ECC-04 violations. `xiaohongshu` /
   `wechat_official` address the *perceived* sameness for this case with a
   dedicated **opening "总览宫格" card** (``plan_cards_with_dominant_
   opener``): when one orientation is clearly dominant (≥60% of the whole
   pool) and there's enough supply, the very first card is a fixed equal
   grid (``card-9-grid-equal`` for portrait-dominant, ``card-8-grid-equal``
   for landscape-dominant) — mirroring the common "总览宫格 + 后续特写" 小红书
   排版习惯— after which the remaining photos flow through the normal
   algorithm unchanged. `album_spread` doesn't get this opener (it isn't a
   "feed" with a first-impression card the same way), but gets an extra
   hard constraint instead: ``avoid_immediate_repeat`` forbids two
   consecutive cards from using the identical template unless it's the
   *only* eligible candidate (an unavoidable structural repeat, per point
   2) — album readers flip through spread by spread, so back-to-back
   identical templates read as more repetitive there than in a scrolling
   feed.

2026-08-07 quality-aware small-pool feed default (user request: "如果用户
的图片较少...允许单张图片优先...一起凑够4-6张居多"). Product review of the
literal ask (cap collage count, rest singles) surfaced a sharper version
worth implementing instead of a blind count cap: 小红书/公众号创作者普遍把
"最强的照片"独立成单图（尤其是第一张，它同时是 feed 缩略图），把普通/相似的
照片凑进拼贴省版面 —— i.e. the split should be *quality*-driven, not just
"first N are singles". ``plan_cards_for_feed`` implements this:
  · Pools of >20 kept photos are entirely unaffected (falls straight through
    to ``plan_cards_with_dominant_opener`` — this feature only targets the
    "较少" case the user actually asked about).
  · A manual "自定义张数" request (``target_per_card`` set) also falls
    straight through unchanged — a user who explicitly asked for N slides
    gets the existing supply-aware behavior, not a surprise quality re-split.
  · Otherwise (auto mode, ≤20 photos): a small "collage budget" (1 card for
    ≤10 photos, 2 cards for 11-20) is filled with the *lowest*-scoring
    photos (``cover_score_v2``-ranked, ascending) in compact 2-6 slot
    templates (never the big 7/8/9/16-slot grids — those would recreate the
    exact "过度雷同宫格" problem this feature exists to avoid for small
    pools). Every other photo becomes its own ``card-1-full-frame`` single;
    the single strongest-scoring photo among those is promoted to the very
    first card (feed thumbnail hook) instead of a fixed opener grid.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from travelogue.export.card_templates import (
    AVAILABLE_SLOT_COUNTS,
    CARD_TEMPLATES,
    CardSlot,
    CardTemplate,
)
from travelogue.layout_contract.editorial_role import editorial_role_for_asset
from travelogue.layout_contract.subject_tagging import is_food_asset
from travelogue.media.image_ops import peek_image_meta

Orientation = str  # "landscape" | "portrait"
AssetLookup = Callable[[Path], Mapping[str, Any] | None]
_WIDE_SLOT_AR = 1.35


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


def _role_soft_penalty(
    template: CardTemplate,
    peek_photos: list[Path],
    lookup: AssetLookup | None,
) -> float:
    """Soft cost for photo-role vs slot-role. Orientation shortfall already won."""
    if lookup is None or len(peek_photos) != template.slot_count:
        return 0.0
    ordered = assign_photos_to_slots(list(peek_photos), template)
    tagged: list[tuple[str, bool, bool]] = []
    for path in ordered:
        raw = lookup(path)
        asset = dict(raw) if isinstance(raw, Mapping) else {}
        role, group = editorial_role_for_asset(asset)
        tagged.append((role, group, is_food_asset(asset)))
    has_hero = any(role in ("vista", "portrait") for role, _g, _f in tagged)
    pen = 0.0
    for slot, (role, group, food) in zip(template.slots, tagged, strict=True):
        skinny = float(slot.display_aspect) >= _WIDE_SLOT_AR
        if role == "portrait" and skinny and not group:
            pen += 2.0
        if group and skinny:
            pen += 1.2
        if role == "detail" and slot.role == "main" and has_hero:
            pen += 1.5
        if food and slot.role == "main":
            pen += 3.0
        if role == "vista" and slot.role != "main" and template.has_main_slot:
            pen += 0.35
        if role == "sequence" and "grid-equal" not in template.id:
            pen += 0.25
    return pen


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
    usage_counts: dict[str, int],
    target_per_card: int | None = None,
    avoid_template_id: str | None = None,
    role_penalty: dict[str, float] | None = None,
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
    Tier 3 — among the surviving "close enough" candidates:
      · if ``target_per_card`` is given (2026-08-06, "自定义张数" soft-target
        decision — see module docstring), prefer whichever slot count sits
        closest to it, since orientation-fit (tiers 1-2) already ruled out
        anything meaningfully worse — the user's requested card size is a
        *preference* to honor once correctness is no longer at stake, not a
        hard override of it (that was the pre-fix bug: a fixed target size
        could force a template like ``card-5-hero-mid-landscape``, 100%
        landscape, onto a mostly-portrait remainder).
      · otherwise, prefer the larger slot count (fewer total cards; keeps
        the "greedy largest" spirit of §5.1 as the deciding factor once
        orientation-fit is already good, not an override of it).
    Tier 3.5 (2026-08-06 diversity fix — see module docstring) — ``tier``
    (min-shortfall) already guarantees every member is *equally fillable*
    from current supply with zero forced-orientation borrowing; the
    ``_PROPORTION_SLOT_TOLERANCE`` window above only exists to decide *how
    big* the card should be (max_size), by anchoring to whichever template
    (of any size) best matches the remaining ratio. Once max_size is
    settled, re-widen the pool back to *every* same-``max_size`` member of
    ``tier`` — not just the ones that happened to also fall inside that
    size-selection tolerance window — since they're all zero-mismatch for
    this step regardless of exact proportion fit. This is what stops a
    template like ``card-7-triband-hero-mid`` from becoming the *sole*
    eligible 7-slot template for many consecutive steps just because the
    ratio anchor point drifted a few percent and pushed its siblings
    (``card-7-triband-2-2-3`` / ``-2-3-2``) barely outside the window.
    Tier 3.75 — if ``avoid_template_id`` is given (album_spread's
    "相邻跨页不得重复" hard constraint), drop it from contention *unless* it's
    the only survivor at this point (an unavoidable structural repeat —
    never sacrifice orientation-fit just to dodge a repeat).
    Tier 4 — among the max-size survivors, pick whichever has been used
    *least so far this plan* (``usage_counts``, 2026-08-06 real round-robin
    fix — see module docstring for why the old ``card_index % len(...)``
    scheme wasn't actually round-robining); ties on usage count (e.g. the
    very first time a size is picked, before any usage history exists) fall
    back to the *best* proportion fit — this is what keeps that first pick
    from landing on a genuinely poorly-fitting sibling (e.g.
    ``card-7-hero-top-halves``, 0% landscape) purely because it happens to
    sort first alphabetically — then finally template id for determinism.
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

    if target_per_card and target_per_card > 0:
        best_size_gap = min(abs(t.slot_count - target_per_card) for t in close_enough)
        close_enough = [
            t for t in close_enough if abs(t.slot_count - target_per_card) == best_size_gap
        ]

    # Tier 3.5: max_size is decided from the (possibly target-narrowed)
    # proportion window, but the final candidate pool re-widens to every
    # zero-extra-shortfall sibling of that same size (see docstring above).
    max_size = max(t.slot_count for t in close_enough)
    finalists = [t for t in tier if t.slot_count == max_size]

    if avoid_template_id is not None:
        without_avoided = [t for t in finalists if t.id != avoid_template_id]
        if without_avoided:
            finalists = without_avoided

    finalists = sorted(
        finalists,
        key=lambda t: (
            usage_counts.get(t.id, 0),
            (role_penalty or {}).get(t.id, 0.0),
            proportion_deviation(t),
            t.id,
        ),
    )
    return finalists[0]


def _cluster_key(path: Path, lookup: AssetLookup | None) -> str:
    if lookup is None:
        return ""
    asset = lookup(path)
    if not isinstance(asset, dict):
        return ""
    return str(asset.get("shotGroupId") or asset.get("sceneClusterId") or "").strip()


def _pop_with_cluster(
    queue: list[Path],
    n: int,
    *,
    pref_key: str,
    lookup: AssetLookup | None,
) -> list[Path]:
    if n <= 0:
        return []
    if not pref_key or lookup is None:
        taken = queue[:n]
        del queue[:n]
        return taken
    taken: list[Path] = []
    rest: list[Path] = []
    for p in queue:
        if len(taken) < n and _cluster_key(p, lookup) == pref_key:
            taken.append(p)
        else:
            rest.append(p)
    queue[:] = rest
    while len(taken) < n and queue:
        taken.append(queue.pop(0))
    return taken


def _pull_chunk_for_template(
    template: CardTemplate,
    landscape_queue: list[Path],
    portrait_queue: list[Path],
    *,
    lookup: AssetLookup | None = None,
    cluster_soft: bool = False,
) -> list[Path]:
    """Consume exactly ``template.slot_count`` photos from the two global
    orientation queues (each preserving its own relative order), preferring
    whichever queue each slot actually wants; borrows from the other queue
    only when one runs short (best-effort — same fallback contract as
    ``assign_photos_to_slots``, which still does the final per-slot
    placement below)."""
    landscape_need = _landscape_shaped_slot_count(template)
    portrait_need = template.slot_count - landscape_need
    pref = ""
    if cluster_soft:
        if landscape_queue:
            pref = _cluster_key(landscape_queue[0], lookup)
        elif portrait_queue:
            pref = _cluster_key(portrait_queue[0], lookup)
    chunk: list[Path] = []
    chunk.extend(
        _pop_with_cluster(
            landscape_queue, landscape_need, pref_key=pref, lookup=lookup
        )
    )
    # If landscape queue ran short, borrow portraits (same as before).
    while len(chunk) < landscape_need and portrait_queue:
        chunk.append(portrait_queue.pop(0))
    chunk.extend(
        _pop_with_cluster(
            portrait_queue, portrait_need, pref_key=pref, lookup=lookup
        )
    )
    while len(chunk) < landscape_need + portrait_need and landscape_queue:
        chunk.append(landscape_queue.pop(0))
    return chunk


def plan_cards(
    photos: list[Path],
    *,
    target_per_card: int | None = None,
    avoid_immediate_repeat: bool = False,
    max_slot_count: int | None = None,
    assets_by_path: Mapping[Path, Mapping[str, Any]] | None = None,
    role_soft: bool = False,
    cluster_soft: bool = False,
) -> list[CardPlan]:
    """Group ``photos`` into cards per §4: orientation-supply-aware slot-count
    + template selection (§4 v0.2 simplification's *only* hard requirement,
    AC-ECC-04, is that every slot's photo actually matches its shape — see
    module docstring for the 2026-08-05 fix) + usage-balanced template pick
    among equally-good matches (OQ-ECC-04, 2026-08-06 real-round-robin fix)
    + orientation role matching. Returns ``[]`` for an empty input (callers
    should validate minimum kept-photo count before calling, per platform's
    own N floor).

    Photos are split into two orientation queues, each preserving its own
    relative order — a card may therefore combine, e.g., an earlier
    landscape photo with a later portrait photo (grouping/shot-order is
    explicitly *not* required by §4); what's guaranteed is every slot gets
    a photo of the shape it actually wants whenever *global* supply allows.

    ``target_per_card`` (manual "自定义张数", 2026-08-06 soft-target
    decision): no longer a hard chunk-size sequence (that's what let a
    5-photo remainder get force-locked onto the 100%-landscape
    ``card-5-hero-mid-landscape`` with no alternative — see module
    docstring for the incident this fixes). It's now just one more scoring
    input to the *same* per-step joint size+template selection auto mode
    uses: orientation-fit is decided first (tiers 1-2 of
    ``_best_matching_template``), and only among the templates that are
    already "close enough" on that front does the planner then prefer
    whichever size sits closest to what the user asked for. The resulting
    page count may therefore drift from a literal reading of
    ``target_per_card`` when the photo mix doesn't support it exactly —
    that's intentional (AC-ECC-04 outranks the page-count preference).

    ``avoid_immediate_repeat`` (album_spread only, 2026-08-06 diversity
    decision — see module docstring): forbids picking the *same* template
    as the immediately-preceding card unless it's the only eligible
    candidate at that step. Combined with the usage-balanced tie-break
    above, this is what keeps facing/adjacent album pages from reading as
    copy-pasted.

    Soft-target safety rail (2026-08-06 follow-up): if a ``target_per_card``
    bias produces *strictly more* orientation mismatches than the same pool
    under plain auto mode, fall back to the auto plan. Per-step soft bias
    can otherwise prefer near-target sizes that leave awkward remainders
    (e.g. landscape leftovers forced into portrait-shaped ``card-1``) even
    though a zero-mismatch auto plan exists — which would violate the
    product rule that AC-ECC-04 outranks page-count preference.

    ``assets_by_path`` / ``role_soft`` / ``cluster_soft`` (AEL L2): album-only
    soft constraints. xhs/mp callers omit them. Orientation shortfall still
    outranks role scoring. Cluster affinity never leaves a slot empty.
    """
    extra = dict(
        assets_by_path=assets_by_path,
        role_soft=role_soft,
        cluster_soft=cluster_soft,
    )
    if not photos:
        return []
    plans = _plan_cards_once(
        photos,
        target_per_card=target_per_card,
        avoid_immediate_repeat=avoid_immediate_repeat,
        max_slot_count=max_slot_count,
        **extra,
    )
    if target_per_card and target_per_card > 0:
        auto_plans = _plan_cards_once(
            photos,
            target_per_card=None,
            avoid_immediate_repeat=avoid_immediate_repeat,
            max_slot_count=max_slot_count,
            **extra,
        )
        if count_orientation_mismatches(plans) > count_orientation_mismatches(auto_plans):
            return auto_plans
    return plans


def _lookup_from_map(
    assets_by_path: Mapping[Path, Mapping[str, Any]] | None,
) -> AssetLookup | None:
    if not assets_by_path:
        return None

    def _lookup(path: Path) -> Mapping[str, Any] | None:
        return assets_by_path.get(path)

    return _lookup


def _plan_cards_once(
    photos: list[Path],
    *,
    target_per_card: int | None = None,
    avoid_immediate_repeat: bool = False,
    max_slot_count: int | None = None,
    assets_by_path: Mapping[Path, Mapping[str, Any]] | None = None,
    role_soft: bool = False,
    cluster_soft: bool = False,
) -> list[CardPlan]:
    """Single greedy pass used by ``plan_cards`` (and its soft-target rail)."""
    landscape_queue = [p for p in photos if _photo_orientation(p) == "landscape"]
    portrait_queue = [p for p in photos if _photo_orientation(p) != "landscape"]
    lookup = _lookup_from_map(assets_by_path)

    plans: list[CardPlan] = []
    usage_counts: dict[str, int] = {}
    last_template_id: str | None = None
    while landscape_queue or portrait_queue:
        remaining_total = len(landscape_queue) + len(portrait_queue)
        candidates = [
            t
            for t in CARD_TEMPLATES.values()
            if t.slot_count <= remaining_total
            and (max_slot_count is None or t.slot_count <= max_slot_count)
        ]
        penalties: dict[str, float] | None = None
        if role_soft and lookup is not None:
            penalties = {}
            for t in candidates:
                peek = _pull_chunk_for_template(
                    t,
                    list(landscape_queue),
                    list(portrait_queue),
                )
                penalties[t.id] = _role_soft_penalty(t, peek, lookup)
        template = _best_matching_template(
            candidates,
            landscape_remaining=len(landscape_queue),
            portrait_remaining=len(portrait_queue),
            usage_counts=usage_counts,
            target_per_card=target_per_card,
            avoid_template_id=last_template_id if avoid_immediate_repeat else None,
            role_penalty=penalties,
        )
        chunk = _pull_chunk_for_template(
            template,
            landscape_queue,
            portrait_queue,
            lookup=lookup,
            cluster_soft=cluster_soft,
        )
        ordered = assign_photos_to_slots(chunk, template)
        plans.append(CardPlan(template=template, photos=tuple(ordered)))
        usage_counts[template.id] = usage_counts.get(template.id, 0) + 1
        last_template_id = template.id

    return plans


#: Opener-card decision thresholds (2026-08-06, "开篇总览宫格" — see module
#: docstring). A pool needs to be *clearly* dominated by one orientation
#: (not just a bare majority) before the opener kicks in, so a near-50/50
#: mix still goes straight through the normal supply-aware algorithm.
_DOMINANT_ORIENTATION_THRESHOLD = 0.6
_OPENER_LANDSCAPE_TEMPLATE_ID = "card-8-grid-equal"
_OPENER_PORTRAIT_TEMPLATE_ID = "card-9-grid-equal"


def plan_cards_with_dominant_opener(
    photos: list[Path],
    *,
    target_per_card: int | None = None,
    avoid_immediate_repeat: bool = False,
) -> list[CardPlan]:
    """``plan_cards`` with a fixed "开篇总览宫格" first card (xiaohongshu /
    wechat_official, 2026-08-06): when one orientation makes up at least
    ``_DOMINANT_ORIENTATION_THRESHOLD`` of the *whole* pool and there's
    enough of it to fill the corresponding equal-grid template outright
    (``card-9-grid-equal`` for portrait-dominant, ``card-8-grid-equal`` for
    landscape-dominant — no partial/undersized opener), the first card is
    fixed to that grid, drawn from the front of the pool in original
    relative order; the rest of the pool then flows through the regular
    ``plan_cards`` unchanged. Falls through to plain ``plan_cards`` (no
    opener) whenever the pool isn't clearly dominated by one orientation,
    or is too small for the opener template it would otherwise pick — this
    is a UX nicety, not something worth inventing a smaller/awkward grid
    for.
    """
    if not photos:
        return []
    landscape = [p for p in photos if _photo_orientation(p) == "landscape"]
    portrait = [p for p in photos if _photo_orientation(p) != "landscape"]
    total = len(photos)
    landscape_ratio = len(landscape) / total if total else 0.0

    if landscape_ratio >= _DOMINANT_ORIENTATION_THRESHOLD:
        opener_template_id, opener_pool = _OPENER_LANDSCAPE_TEMPLATE_ID, landscape
    elif (1.0 - landscape_ratio) >= _DOMINANT_ORIENTATION_THRESHOLD:
        opener_template_id, opener_pool = _OPENER_PORTRAIT_TEMPLATE_ID, portrait
    else:
        opener_template_id, opener_pool = None, []

    opener_template = CARD_TEMPLATES.get(opener_template_id) if opener_template_id else None
    if opener_template is None or len(opener_pool) < opener_template.slot_count:
        return plan_cards(
            photos,
            target_per_card=target_per_card,
            avoid_immediate_repeat=avoid_immediate_repeat,
        )

    opener_photos = opener_pool[: opener_template.slot_count]
    opener_ids = {id(p) for p in opener_photos}
    remaining_photos = [p for p in photos if id(p) not in opener_ids]
    opener_plan = CardPlan(
        template=opener_template,
        photos=tuple(assign_photos_to_slots(opener_photos, opener_template)),
    )
    rest = plan_cards(
        remaining_photos,
        target_per_card=target_per_card,
        avoid_immediate_repeat=avoid_immediate_repeat,
    )
    return [opener_plan, *rest]


#: Small-pool feed quality-aware allocation thresholds (2026-08-07 — see
#: module docstring). ≤10 photos → 1 collage-card budget; 11-20 → 2; above
#: that, ``plan_cards_for_feed`` falls straight through to the existing
#: dominant-opener behavior (unchanged for larger pools).
_FEED_SMALL_POOL_MAX = 10
_FEED_MEDIUM_POOL_MAX = 20
#: Collage-card sizes considered for the budgeted cards, largest-fits-first;
#: derived from the template library's own available counts within [2, 6] —
#: deliberately excludes 1 (that's a "single", not a collage) and anything
#: above 6 (the "总览宫格"-style big grids this feature exists to de-emphasize
#: for small pools).
_FEED_COMPACT_SIZES: tuple[int, ...] = tuple(
    sorted({c for c in AVAILABLE_SLOT_COUNTS if 2 <= c <= 6}, reverse=True)
)


def feed_collage_budget(n_photos: int) -> int | None:
    """Max number of collage cards ``plan_cards_for_feed`` will build for a
    pool of ``n_photos`` kept photos; ``None`` means "no cap" (falls through
    to the existing dominant-opener algorithm unchanged — see module
    docstring). Exposed (no leading underscore) so callers can decide
    whether to surface a "quality-aware split" hint without duplicating the
    thresholds."""
    if n_photos <= _FEED_SMALL_POOL_MAX:
        return 1
    if n_photos <= _FEED_MEDIUM_POOL_MAX:
        return 2
    return None


def _pick_feed_collage_size(available: int) -> int | None:
    """Largest compact size (see ``_FEED_COMPACT_SIZES``) that fits within
    ``available`` remaining candidate photos; ``None`` when even the
    smallest compact size (2) doesn't fit — caller should stop budgeting
    collage cards and let the rest fall through as singles."""
    for size in _FEED_COMPACT_SIZES:
        if available >= size:
            return size
    return None


def plan_cards_for_feed(
    photos: list[Path],
    *,
    scores: dict[Path, float] | None = None,
    target_per_card: int | None = None,
) -> list[CardPlan]:
    """xiaohongshu / wechat_official entry point (2026-08-07): quality-aware
    small-pool allocation — see module docstring for the full rationale.
    Falls through unchanged to ``plan_cards_with_dominant_opener`` when the
    pool is >20 photos or a manual ``target_per_card`` was requested.

    ``scores``: optional ``cover_score_v2``-style per-photo score (higher =
    stronger solo-card candidate); missing/``None`` entries default to 0.0,
    which — combined with the stable sort's original-index tie-break —
    degrades gracefully to "front-loaded" chunking when no signal is
    available (e.g. every photo scores 0.0 for whatever reason).
    """
    if not photos:
        return []
    budget = feed_collage_budget(len(photos))
    if budget is None or (target_per_card and target_per_card > 0):
        return plan_cards_with_dominant_opener(photos, target_per_card=target_per_card)

    def _score_of(path: Path) -> float:
        return (scores or {}).get(path, 0.0)

    # Weakest-first (ascending score); ties keep original relative order —
    # this is what makes an all-zero-score pool degrade to "first N get
    # bundled" rather than an arbitrary/unstable ordering.
    weak_order = sorted(
        range(len(photos)), key=lambda i: (_score_of(photos[i]), i)
    )
    remaining_weak: list[Path] = [photos[i] for i in weak_order]

    collage_plans: list[CardPlan] = []
    collage_ids: set[int] = set()
    for _ in range(budget):
        size = _pick_feed_collage_size(len(remaining_weak))
        if size is None:
            break
        chunk, remaining_weak = remaining_weak[:size], remaining_weak[size:]
        sub_plans = plan_cards(chunk, max_slot_count=size)
        if not sub_plans:
            break
        collage_plans.extend(sub_plans)
        collage_ids.update(id(p) for plan in sub_plans for p in plan.photos)

    singles_photos = [p for p in photos if id(p) not in collage_ids]
    if not singles_photos:
        return collage_plans

    # Opener: the single strongest-scoring photo becomes the very first
    # card — it doubles as the feed thumbnail, so a real single "hero" beats
    # a fixed grid for a small pool (the grid opener is still used for
    # larger pools via the >20-photo fallback above).
    cover_idx = max(range(len(singles_photos)), key=lambda i: _score_of(singles_photos[i]))
    cover_photo = singles_photos.pop(cover_idx)

    card1 = CARD_TEMPLATES["card-1-full-frame"]
    opener_plan = CardPlan(template=card1, photos=(cover_photo,))
    single_plans = [CardPlan(template=card1, photos=(p,)) for p in singles_photos]
    return [opener_plan, *collage_plans, *single_plans]


def count_orientation_mismatches(plans: list[CardPlan]) -> int:
    """How many slots across ``plans`` ended up with a photo whose native
    orientation doesn't match the slot's actual shape — i.e. a forced crop
    AC-ECC-04 couldn't avoid given the trip's real landscape/portrait
    supply (2026-08-06, post-hoc mismatch surfacing decision: callers use
    this to append a heads-up to the export result rather than silently
    shipping the crop — see ``export_collage_pack``)."""
    return sum(
        1
        for plan in plans
        for photo, slot in zip(plan.photos, plan.template.slots, strict=True)
        if _slot_is_landscape_shaped(slot) != (_photo_orientation(photo) == "landscape")
    )


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
