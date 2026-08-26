"""Portfolio-only slot admission (atelier orient / aspect).

Reads promoted LTE ``page-*`` faces via the layout-template registry.
Does not read ``docs/templates/reserve/`` (ISO-05).
Journal mosaic / ``compose_trip`` must not import this module.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Mapping, Sequence

from travelogue.layout_engine.editorial_series.page_stars import is_disabled, star_of

_LOG = logging.getLogger(__name__)

PORT_MAX = 0.88
SQUARE_MAX = 1.12
LAND43_MAX = 1.55
COVER_LOG_REL = 0.18

_SCHEMA_ROLES = frozenset({"portrait", "landscape", "main", "food"})
_PORT_KINDS = frozenset({"portrait", "port", "tall"})
_LAND_KINDS = frozenset({"landscape", "land", "panorama"})


@dataclass(frozen=True)
class SlotSpec:
    index: int
    role: str
    display_aspect: float
    family: str
    fit: str = "cover"


@dataclass
class SlotTake:
    asset_ids: list[str] = field(default_factory=list)
    fits: list[str] = field(default_factory=list)
    display_aspects: list[float | None] = field(default_factory=list)
    roles: list[str | None] = field(default_factory=list)
    leftover: list[str] = field(default_factory=list)
    skip: bool = False


def classify_ratio(ratio: float) -> str:
    if ratio <= PORT_MAX:
        return "portrait"
    if ratio < SQUARE_MAX:
        return "square"
    if ratio < LAND43_MAX:
        return "land43"
    return "land169"


def _coarse(family: str) -> str:
    if family == "portrait":
        return "portrait"
    if family == "square":
        return "square"
    if family == "unknown":
        return "unknown"
    return "landscape"


def _family_from_kind(kind: str) -> str:
    key = str(kind or "").strip().lower()
    if key in _PORT_KINDS:
        return "portrait"
    if key == "square":
        return "square"
    if key == "panorama":
        return "land169"
    if key in _LAND_KINDS:
        return "land43"
    return "unknown"


def asset_family(
    asset_id: str,
    *,
    aspect_kinds: Mapping[str, str] | None,
    aspect_ratios: Mapping[str, float] | None,
) -> str:
    ratio = (aspect_ratios or {}).get(asset_id)
    if ratio and ratio > 0:
        return classify_ratio(float(ratio))
    return _family_from_kind((aspect_kinds or {}).get(asset_id, ""))


def slot_family(role: str, display_aspect: float | None) -> str:
    if display_aspect and display_aspect > 0:
        return classify_ratio(float(display_aspect))
    key = str(role or "").strip().lower()
    if key == "portrait":
        return "portrait"
    if key == "square":
        return "square"
    return "land43"


def fit_for_pair(asset_ratio: float | None, slot_aspect: float | None) -> str:
    """Atelier ``relative-to-slot``: match covers; mismatch letterboxes."""
    if not asset_ratio or not slot_aspect or asset_ratio <= 0 or slot_aspect <= 0:
        return "cover"
    rel = abs(math.log(float(asset_ratio) / float(slot_aspect)))
    return "cover" if rel <= COVER_LOG_REL else "contain"


def fit_for_slot(slot: SlotSpec, asset_ratio: float | None) -> str:
    """Honor promoted YAML ``fit`` (试印铺满). Relative-to-slot is opt-in."""
    declared = str(slot.fit or "").strip().lower()
    if declared in {"auto", "auto_delegate", "relative", "relative-to-slot"}:
        return fit_for_pair(asset_ratio, slot.display_aspect)
    if declared == "contain":
        return "contain"
    return "cover"


def _schema_role(role: str) -> str | None:
    key = str(role or "").strip().lower()
    if key in _SCHEMA_ROLES:
        return key
    return None


@lru_cache(maxsize=128)
def load_slot_specs(pattern_id: str) -> tuple[SlotSpec, ...]:
    """LTE runtime face only. Unknown / journal ``screen-*`` ids return empty."""
    tid = str(pattern_id or "").strip()
    if not tid.startswith("page-"):
        return ()
    try:
        from travelogue.layout_templates.geometry import slot_aspect_table
        from travelogue.layout_templates.registry import get_layout_template
    except ImportError:  # pragma: no cover
        return ()
    try:
        template = get_layout_template(tid)
    except KeyError:
        return ()
    rows = slot_aspect_table(template)
    declared_fit = {
        int(slot.index): str(slot.fit or "cover").strip().lower()
        for slot in template.slots
    }
    specs: list[SlotSpec] = []
    for row in rows:
        aspect = float(row.display_aspect)
        role = str(row.role or "")
        specs.append(
            SlotSpec(
                index=int(row.index),
                role=role,
                display_aspect=aspect,
                family=slot_family(role, aspect),
                fit=declared_fit.get(int(row.index), "cover") or "cover",
            )
        )
    specs.sort(key=lambda s: s.index)
    return tuple(specs)


def _has_aspect_signal(
    asset_ids: Sequence[str],
    aspect_kinds: Mapping[str, str] | None,
    aspect_ratios: Mapping[str, float] | None,
) -> bool:
    for aid in asset_ids:
        if (aspect_ratios or {}).get(aid):
            return True
        if str((aspect_kinds or {}).get(aid) or "").strip():
            return True
    return False


def _has_ratio_signal(
    asset_ids: Sequence[str],
    aspect_ratios: Mapping[str, float] | None,
) -> bool:
    for aid in asset_ids:
        ratio = (aspect_ratios or {}).get(aid)
        if ratio and float(ratio) > 0:
            return True
    return False


def _can_admit(
    slots: Sequence[SlotSpec],
    families: Sequence[str],
    *,
    fine_wide: bool = False,
) -> bool:
    need_p = sum(1 for s in slots if s.family == "portrait")
    need_l = sum(1 for s in slots if _coarse(s.family) == "landscape")
    need_s = sum(1 for s in slots if s.family == "square")
    have_p = sum(1 for f in families if f == "portrait")
    have_l = sum(1 for f in families if _coarse(f) == "landscape")
    # Square fills square slots only (atelier). Unknown stays flexible
    # so fixtures without pixels keep FIFO admission.
    flex = sum(1 for f in families if f == "unknown")
    if have_p + flex < need_p:
        return False
    used_flex = max(0, need_p - have_p)
    flex_left = flex - used_flex
    if have_l + flex_left < need_l:
        return False
    used_flex += max(0, need_l - have_l)
    flex_left = flex - used_flex
    leftover_p = max(0, have_p - need_p)
    leftover_l = max(0, have_l - need_l)
    if leftover_p + leftover_l + flex_left < need_s:
        return False
    # Promoted land-wide packets (16:9) must not swallow 3:2 / 4:3.
    # Kind-only "landscape" (no pixels) stays coarse so fixtures keep FIFO.
    if fine_wide:
        need_w = sum(1 for s in slots if s.family == "land169")
        have_w = sum(1 for f in families if f == "land169")
        if have_w < need_w:
            return False
    return True


def _pair_score(asset_family_name: str, slot: SlotSpec, asset_ratio: float | None) -> float:
    a_coarse = _coarse(asset_family_name)
    s_coarse = _coarse(slot.family)
    if a_coarse == "unknown":
        return 0.15
    if a_coarse == "square" and s_coarse != "square":
        return -10.0
    if a_coarse != "square" and s_coarse != "square" and a_coarse != s_coarse:
        return -10.0
    # Pixel-known 3:2 must not cover-crop into a 16:9 land-wide cell.
    if (
        asset_family_name == "land43"
        and slot.family == "land169"
        and asset_ratio
        and asset_ratio > 0
    ):
        return -10.0
    closeness = 0.0
    if asset_ratio and slot.display_aspect > 0:
        closeness = 1.0 - min(1.0, abs(math.log(asset_ratio / slot.display_aspect)))
    if asset_family_name == slot.family:
        return 2.0 + closeness
    if a_coarse == s_coarse:
        return 1.0 + 0.5 * closeness
    return 0.35 + 0.25 * closeness


def _assign(
    asset_ids: Sequence[str],
    slots: Sequence[SlotSpec],
    *,
    aspect_kinds: Mapping[str, str] | None,
    aspect_ratios: Mapping[str, float] | None,
) -> list[str]:
    families = [
        asset_family(aid, aspect_kinds=aspect_kinds, aspect_ratios=aspect_ratios)
        for aid in asset_ids
    ]
    order = {aid: i for i, aid in enumerate(asset_ids)}
    pairs: list[tuple[float, int, int]] = []
    for si, slot in enumerate(slots):
        for ai, aid in enumerate(asset_ids):
            ratio = (aspect_ratios or {}).get(aid)
            score = _pair_score(families[ai], slot, ratio)
            pairs.append((score, order[aid], si, ai))
    pairs.sort(key=lambda row: (-row[0], row[1], row[2]))
    used_assets: set[int] = set()
    used_slots: set[int] = set()
    chosen: dict[int, str] = {}
    for score, _ord, si, ai in pairs:
        if si in used_slots or ai in used_assets:
            continue
        if score < 0:
            continue
        used_slots.add(si)
        used_assets.add(ai)
        chosen[si] = asset_ids[ai]
        if len(chosen) == len(slots):
            break
    return [chosen[i] for i in range(len(slots)) if i in chosen]


def take_for_page(
    asset_ids: Sequence[str],
    pattern_id: str,
    *,
    band: int,
    aspect_kinds: Mapping[str, str] | None = None,
    aspect_ratios: Mapping[str, float] | None = None,
) -> SlotTake:
    ids = [str(a) for a in asset_ids if a]
    if is_disabled(pattern_id):
        return SlotTake(leftover=list(ids), skip=True)
    take_n = min(max(int(band), 1), len(ids))
    if take_n <= 0:
        return SlotTake(leftover=list(ids), skip=True)

    slots = list(load_slot_specs(pattern_id))
    if not slots or not _has_aspect_signal(ids, aspect_kinds, aspect_ratios):
        chunk = ids[:take_n]
        return SlotTake(
            asset_ids=chunk,
            fits=["cover"] * len(chunk),
            display_aspects=[None] * len(chunk),
            roles=[None] * len(chunk),
            leftover=ids[take_n:],
        )

    # Do not underfill a face (empty cells look like broken geometry).
    # Caller substitutes a same-mix / smaller cousin instead.
    if len(ids) < len(slots):
        return SlotTake(leftover=list(ids), skip=True)
    if len(slots) < take_n:
        take_n = len(slots)

    families = [
        asset_family(aid, aspect_kinds=aspect_kinds, aspect_ratios=aspect_ratios)
        for aid in ids
    ]
    if not _can_admit(
        slots,
        families,
        fine_wide=_has_ratio_signal(ids, aspect_ratios),
    ):
        return SlotTake(leftover=list(ids), skip=True)

    assigned = _assign(
        ids,
        slots,
        aspect_kinds=aspect_kinds,
        aspect_ratios=aspect_ratios,
    )
    if len(assigned) < len(slots):
        return SlotTake(leftover=list(ids), skip=True)

    taken = set(assigned)
    leftover = [aid for aid in ids if aid not in taken]
    fits: list[str] = []
    aspects: list[float | None] = []
    roles: list[str | None] = []
    for aid, slot in zip(assigned, slots, strict=True):
        ratio = (aspect_ratios or {}).get(aid)
        fits.append(fit_for_slot(slot, ratio))
        aspects.append(round(slot.display_aspect, 4))
        roles.append(_schema_role(slot.role))
    return SlotTake(
        asset_ids=assigned,
        fits=fits,
        display_aspects=aspects,
        roles=roles,
        leftover=leftover,
    )


@lru_cache(maxsize=1)
def _official_face_ids() -> frozenset[str]:
    from travelogue.layout_engine.editorial_series.catalog import load_official_series

    ids: set[str] = set()
    for row in load_official_series():
        for step in row.get("sequence") or []:
            pid = str(step.get("patternId") or "")
            if pid.startswith("page-"):
                ids.add(pid)
    return frozenset(ids)


@lru_cache(maxsize=1)
def _page_faces_by_n() -> dict[int, tuple[str, ...]]:
    from travelogue.layout_templates.registry import get_engine

    engine = get_engine()
    by: dict[int, list[str]] = {}
    for n, ids in engine._by_photo_count.items():
        pages = [i for i in ids if str(i).startswith("page-")]
        if pages:
            by[int(n)] = tuple(pages)
    return by


def _family_hist(items: Sequence[str]) -> tuple[int, int, int]:
    port = sum(1 for f in items if f == "portrait")
    land = sum(1 for f in items if _coarse(f) == "landscape")
    square = sum(1 for f in items if f == "square")
    return port, land, square


def _mix_dist(planned: Sequence[SlotSpec], cand: Sequence[SlotSpec]) -> int:
    a = _family_hist([s.family for s in planned])
    b = _family_hist([s.family for s in cand])
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def _cousin_rank_key(
    planned: Sequence[SlotSpec],
    planned_n: int,
    tid: str,
    specs: Sequence[SlotSpec],
    official: frozenset[str],
) -> tuple:
    """BLK-PIS-01 · 槽差 → overlap → mix → 星 → official → ultra → id."""
    return (
        planned_n - len(specs),
        -_fine_overlap(planned, specs),
        _mix_dist(planned, specs),
        -star_of(tid),
        0 if tid in official else 1,
        0 if "ultra" not in tid else 1,
        tid,
    )


def _fine_overlap(planned: Sequence[SlotSpec], cand: Sequence[SlotSpec]) -> int:
    from collections import Counter

    need = Counter(s.family for s in planned)
    hit = 0
    for spec in cand:
        if need[spec.family] > 0:
            need[spec.family] -= 1
            hit += 1
    return hit


def _cousin_faces(planned_pattern_id: str, *, max_n: int, have_n: int) -> list[str]:
    planned = list(load_slot_specs(planned_pattern_id))
    planned_n = len(planned) or max_n
    official = _official_face_ids()
    ranked: list[tuple] = []
    for n in range(min(planned_n, have_n), 0, -1):
        for tid in _page_faces_by_n().get(n, ()):
            if tid == planned_pattern_id or is_disabled(tid):
                continue
            specs = load_slot_specs(tid)
            if len(specs) != n:
                continue
            ranked.append(
                _cousin_rank_key(planned, planned_n, tid, specs, official)
            )
    ranked.sort()
    return [row[-1] for row in ranked]


def maybe_star_upgrade(
    asset_ids: Sequence[str],
    planned_pattern_id: str,
    planned_take: SlotTake,
    *,
    aspect_kinds: Mapping[str, str] | None = None,
    aspect_ratios: Mapping[str, float] | None = None,
) -> tuple[str, SlotTake]:
    """Same-slot higher-star cousin. Geometry first; never counts as demote."""
    planned = list(load_slot_specs(planned_pattern_id))
    planned_n = len(planned)
    planned_star = star_of(planned_pattern_id)
    if planned_n <= 0 or planned_star >= 3 or is_disabled(planned_pattern_id):
        return planned_pattern_id, planned_take

    official = _official_face_ids()
    planned_overlap = _fine_overlap(planned, planned)
    best_tid = planned_pattern_id
    best_take = planned_take
    best_key = _cousin_rank_key(
        planned, planned_n, planned_pattern_id, planned, official
    )
    ids = [str(a) for a in asset_ids if a]
    for tid in _cousin_faces(
        planned_pattern_id, max_n=planned_n, have_n=planned_n
    ):
        if is_disabled(tid) or star_of(tid) <= planned_star:
            continue
        specs = load_slot_specs(tid)
        if len(specs) != planned_n:
            continue
        if _mix_dist(planned, specs) > 0:
            continue
        if _fine_overlap(planned, specs) < planned_overlap:
            continue
        taken = take_for_page(
            ids,
            tid,
            band=planned_n,
            aspect_kinds=aspect_kinds,
            aspect_ratios=aspect_ratios,
        )
        if taken.skip or not taken.asset_ids:
            continue
        key = _cousin_rank_key(planned, planned_n, tid, specs, official)
        if key < best_key:
            best_key = key
            best_tid = tid
            best_take = taken
    if best_tid != planned_pattern_id:
        _LOG.info(
            "face_star_upgrade from=%s to=%s stars=%s->%s",
            planned_pattern_id,
            best_tid,
            planned_star,
            star_of(best_tid),
        )
    return best_tid, best_take


def pick_hero_face(
    asset_ids: Sequence[str],
    *,
    aspect_kinds: Mapping[str, str] | None = None,
    aspect_ratios: Mapping[str, float] | None = None,
) -> str:
    """Orientation family first, then -star. Wrong-family 3-star loses."""
    aid = str(asset_ids[0]) if asset_ids else ""
    preferred = _preferred_hero_family(aid, aspect_kinds, aspect_ratios)
    official = _official_face_ids()
    ranked: list[tuple] = []
    ids = [str(a) for a in asset_ids if a][:1]
    for tid in _page_faces_by_n().get(1, ()):
        if not str(tid).startswith("page-1-hero-") or is_disabled(tid):
            continue
        specs = load_slot_specs(tid)
        if len(specs) != 1:
            continue
        taken = take_for_page(
            ids,
            tid,
            band=1,
            aspect_kinds=aspect_kinds,
            aspect_ratios=aspect_ratios,
        )
        if taken.skip or not taken.asset_ids:
            continue
        fam = specs[0].family
        ranked.append(
            (
                0 if fam == preferred else 1,
                -star_of(tid),
                0 if tid in official else 1,
                0 if "ultra" not in tid else 1,
                tid,
            )
        )
    if ranked:
        ranked.sort()
        return str(ranked[0][-1])
    if preferred == "portrait":
        return "page-1-hero-port"
    if preferred == "land43":
        return "page-1-hero-land-right"
    return "page-1-hero-land-wide"


def _preferred_hero_family(
    asset_id: str,
    aspect_kinds: Mapping[str, str] | None,
    aspect_ratios: Mapping[str, float] | None,
) -> str:
    ratio = (aspect_ratios or {}).get(asset_id)
    if ratio and float(ratio) > 0:
        return classify_ratio(float(ratio))
    kind = ""
    if aspect_kinds and asset_id:
        kind = str(aspect_kinds.get(asset_id) or "").lower()
    if kind in {"portrait", "port", "tall"}:
        return "portrait"
    if kind == "square":
        return "square"
    # No ratio: keep the historic default (16:9 wide), not 4:3.
    return "land169"


def fallback_take(
    asset_ids: Sequence[str],
    planned_pattern_id: str,
    *,
    aspect_kinds: Mapping[str, str] | None = None,
    aspect_ratios: Mapping[str, float] | None = None,
) -> tuple[str, SlotTake] | None:
    """Substitute a same-mix / smaller atelier face; never opposite-orient.

    Journal mosaic does not call this.
    """
    ids = [str(a) for a in asset_ids if a]
    if not ids:
        return None
    planned_slots = load_slot_specs(planned_pattern_id)
    planned_n = len(planned_slots) or 1
    candidates = _cousin_faces(
        planned_pattern_id, max_n=planned_n, have_n=len(ids)
    )
    land_slots = sum(1 for s in planned_slots if _coarse(s.family) == "landscape")
    port_slots = sum(1 for s in planned_slots if s.family == "portrait")
    prefer_land = land_slots >= port_slots
    tail = (
        (
            "page-1-hero-land-right",
            "page-2-pair-land",
            "page-2-1l1p",
            "page-1-hero-land-wide",
            "page-2-pair-port",
            "page-1-hero-port",
        )
        if prefer_land
        else (
            "page-2-pair-port",
            "page-2-1l1p",
            "page-1-hero-port",
            "page-1-hero-land-right",
            "page-2-pair-land",
            "page-1-hero-land-wide",
        )
    )
    seen: set[str] = set()
    for face in [*candidates, *tail]:
        if not face or face in seen or is_disabled(face):
            continue
        seen.add(face)
        specs = load_slot_specs(face)
        band = len(specs) if specs else 1
        taken = take_for_page(
            ids,
            face,
            band=band,
            aspect_kinds=aspect_kinds,
            aspect_ratios=aspect_ratios,
        )
        if not taken.skip and taken.asset_ids:
            return face, taken
    return None


def take_for_pattern(
    asset_ids: Sequence[str],
    pattern_id: str,
    *,
    aspect_kinds: Mapping[str, str] | None = None,
    aspect_ratios: Mapping[str, float] | None = None,
) -> SlotTake:
    """Re-fit an already chosen set (hero demote) against a face."""
    ids = [str(a) for a in asset_ids if a]
    slots = list(load_slot_specs(pattern_id))
    if not slots or not ids:
        return SlotTake(
            asset_ids=list(ids),
            fits=["cover"] * len(ids),
            display_aspects=[None] * len(ids),
            roles=[None] * len(ids),
        )
    slots = slots[: len(ids)]
    return take_for_page(
        ids,
        pattern_id,
        band=len(slots),
        aspect_kinds=aspect_kinds,
        aspect_ratios=aspect_ratios,
    )


def collect_asset_aspects(
    assets: Sequence[Mapping[str, Any]] | None,
) -> tuple[dict[str, str], dict[str, float]]:
    """Pixel-first kinds/ratios. Empty kind when the asset has no signal."""
    from travelogue.layout_contract.orientations import classify_aspect

    kinds: dict[str, str] = {}
    ratios: dict[str, float] = {}
    for raw in assets or []:
        if not isinstance(raw, Mapping):
            continue
        aid = str(raw.get("id") or raw.get("assetId") or "").strip()
        if not aid:
            continue
        w = int(raw.get("nativeWidth") or raw.get("width") or 0)
        h = int(raw.get("nativeHeight") or raw.get("height") or 0)
        stored = str(raw.get("aspectKind") or raw.get("aspect_kind") or "").strip()
        if w > 0 and h > 0:
            ratios[aid] = w / h
            kinds[aid] = classify_aspect(w, h)
        elif stored:
            kinds[aid] = stored
    return kinds, ratios
