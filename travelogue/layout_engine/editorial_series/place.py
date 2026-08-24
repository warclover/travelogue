"""Group → page placement. One page never spans two shot groups (AC-PFM-09).

Slot admission lives in ``slot_match`` (portfolio-only). Journal mosaic
does not import this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from travelogue.layout_engine.editorial_series.slot_match import (
    classify_ratio,
    fallback_take,
    take_for_page,
    take_for_pattern,
)

DENSE_MIN_SLOTS = 5
HERO_LAND_FACE = "page-1-hero-land-wide"
HERO_LAND_43_FACE = "page-1-hero-land-right"
HERO_PORT_FACE = "page-1-hero-port"


def _hero_face_for(
    asset_ids: Sequence[str],
    aspect_kinds: Mapping[str, str] | None,
    aspect_ratios: Mapping[str, float] | None = None,
) -> str:
    aid = str(asset_ids[0]) if asset_ids else ""
    ratio = (aspect_ratios or {}).get(aid)
    if ratio and float(ratio) > 0:
        family = classify_ratio(float(ratio))
        if family == "portrait":
            return HERO_PORT_FACE
        if family == "land43":
            return HERO_LAND_43_FACE
        return HERO_LAND_FACE
    kind = ""
    if aspect_kinds and aid:
        kind = str(aspect_kinds.get(aid) or "").lower()
    if kind in {"portrait", "port", "tall"}:
        return HERO_PORT_FACE
    return HERO_LAND_FACE


@dataclass
class PlacedPage:
    role: str
    program: str
    slot_band: int
    pattern_id: str
    asset_ids: list[str]
    shot_group_id: str
    planned_pattern_id: str = ""
    slot_fits: list[str] = field(default_factory=list)
    slot_display_aspects: list[float | None] = field(default_factory=list)
    slot_roles: list[str | None] = field(default_factory=list)

    def as_screen(self) -> dict[str, Any]:
        refuse_cross_group_screen([self.shot_group_id] * len(self.asset_ids))
        # Do not write series ``role`` onto layoutScreen.role (P23 peak enum).
        slots: list[dict[str, Any]] = []
        for i, aid in enumerate(self.asset_ids):
            fit = "cover"
            if i < len(self.slot_fits) and self.slot_fits[i] in {"cover", "contain"}:
                fit = self.slot_fits[i]
            entry: dict[str, Any] = {"assetId": aid, "slot": i, "fit": fit}
            if i < len(self.slot_roles) and self.slot_roles[i]:
                entry["role"] = self.slot_roles[i]
            if i < len(self.slot_display_aspects) and self.slot_display_aspects[i]:
                entry["displayAspect"] = self.slot_display_aspects[i]
            slots.append(entry)
        screen: dict[str, Any] = {
            "patternId": self.pattern_id,
            "slots": slots,
            "layoutGeometry": {
                "stageAspect": "16:9",
                "gridClass": f"layout-screen__grid--{self.pattern_id}",
            },
        }
        if self.shot_group_id:
            screen["shotGroupId"] = self.shot_group_id
        return screen


@dataclass
class PlaceResult:
    pages: list[PlacedPage] = field(default_factory=list)
    leftover_ids: list[str] = field(default_factory=list)
    dropped_roles: list[str] = field(default_factory=list)
    used_roles: list[str] = field(default_factory=list)
    demoted_pages: int = 0
    fulfilled_pages: int = 0


def refuse_cross_group_screen(asset_group_ids: Sequence[str]) -> None:
    """AC-PFM-09 · hard-reject a page that would mix two shot groups."""
    unique = {str(g) for g in asset_group_ids if str(g)}
    if len(unique) > 1:
        raise ValueError("refusing to place a page across two shot groups")


def _page_spec_band(spec: Mapping[str, Any]) -> int:
    raw = spec.get("slotBand")
    if raw is None:
        raw = spec.get("slot_band")
    try:
        band = int(raw or 1)
    except (TypeError, ValueError):
        band = 1
    return band if band > 0 else 1


def place_groups(
    groups: Sequence[Mapping[str, Any]],
    sequence: Sequence[Mapping[str, Any]],
    *,
    cap: int | None = None,
    aspect_kinds: Mapping[str, str] | None = None,
    aspect_ratios: Mapping[str, float] | None = None,
) -> PlaceResult:
    """Fill pages from groups in order. Never mix two shot groups on one page."""
    queues: list[dict[str, Any]] = []
    for g in groups:
        ids = [str(a) for a in (g.get("asset_ids") or []) if a]
        if not ids:
            continue
        queues.append(
            {
                "id": str(g.get("id") or f"g-{len(queues)}"),
                "kind": str(g.get("kind") or "scene"),
                "ids": ids,
            }
        )

    cap_leftover: list[str] = []
    if cap is not None:
        taken = 0
        trimmed: list[dict[str, Any]] = []
        for g in queues:
            room = int(cap) - taken
            if room <= 0:
                cap_leftover.extend(g["ids"])
                continue
            keep, rest = g["ids"][:room], g["ids"][room:]
            taken += len(keep)
            if keep:
                trimmed.append({**g, "ids": keep})
            cap_leftover.extend(rest)
        queues = trimmed

    result = PlaceResult()
    gi = 0
    for spec in sequence:
        while gi < len(queues) and not queues[gi]["ids"]:
            gi += 1
        if gi >= len(queues):
            break
        group = queues[gi]
        band = _page_spec_band(spec)
        role = str(spec.get("role") or spec.get("i") or "")
        if band >= DENSE_MIN_SLOTS:
            if group["kind"] != "scene" or len(group["ids"]) < band:
                if role:
                    result.dropped_roles.append(role)
                continue
        planned = str(
            spec.get("patternId") or spec.get("faceHint") or f"page-grid-{band}"
        )
        taken = take_for_page(
            group["ids"],
            planned,
            band=band,
            aspect_kinds=aspect_kinds,
            aspect_ratios=aspect_ratios,
        )
        if taken.skip:
            # Same-count cousin first (e.g. land-6 → 2l4p). Else smaller
            # pair/hero. Dense faces still refuse opposite-orient stuffing.
            fb = fallback_take(
                group["ids"],
                planned,
                aspect_kinds=aspect_kinds,
                aspect_ratios=aspect_ratios,
            )
            if fb is None:
                if role:
                    result.dropped_roles.append(role)
                continue
            pattern, fb_take = fb
            group["ids"] = fb_take.leftover
            page = PlacedPage(
                role=role,
                program=str(spec.get("program") or ""),
                slot_band=band,
                pattern_id=pattern,
                asset_ids=list(fb_take.asset_ids),
                shot_group_id=str(group["id"]),
                planned_pattern_id=planned,
                slot_fits=list(fb_take.fits),
                slot_display_aspects=list(fb_take.display_aspects),
                slot_roles=list(fb_take.roles),
            )
            refuse_cross_group_screen([page.shot_group_id] * len(page.asset_ids))
            result.pages.append(page)
            if role:
                result.used_roles.append(role)
            if pattern != planned:
                result.demoted_pages += 1
            continue
        chunk = taken.asset_ids
        group["ids"] = taken.leftover
        take_n = len(chunk)
        pattern = planned
        demoted = False
        fits = list(taken.fits)
        display_aspects = list(taken.display_aspects)
        roles = list(taken.roles)
        # Solo / undersized group on a 2–4 slot face: keep one photo, but do
        # not park it in the first cell of an empty grid (top-left quarter).
        if take_n == 1 and band > 1:
            pattern = _hero_face_for(chunk, aspect_kinds, aspect_ratios)
            demoted = pattern != planned
            if demoted:
                refit = take_for_pattern(
                    chunk,
                    pattern,
                    aspect_kinds=aspect_kinds,
                    aspect_ratios=aspect_ratios,
                )
                if not refit.skip and refit.asset_ids:
                    fits = list(refit.fits)
                    display_aspects = list(refit.display_aspects)
                    roles = list(refit.roles)
        page = PlacedPage(
            role=role,
            program=str(spec.get("program") or ""),
            slot_band=band,
            pattern_id=pattern,
            asset_ids=chunk,
            shot_group_id=str(group["id"]),
            planned_pattern_id=planned,
            slot_fits=fits,
            slot_display_aspects=display_aspects,
            slot_roles=roles,
        )
        refuse_cross_group_screen([page.shot_group_id] * len(page.asset_ids))
        result.pages.append(page)
        if role:
            result.used_roles.append(role)
        if demoted:
            result.demoted_pages += 1
        elif take_n == band:
            result.fulfilled_pages += 1

    for g in queues:
        result.leftover_ids.extend(g["ids"])
    result.leftover_ids.extend(cap_leftover)
    return result


def _chapter_owner_ids(
    ch: Mapping[str, Any],
    index: int,
    buckets: Sequence[Sequence[str]] | None,
) -> list[str]:
    """Prefer compose-time buckets over stale journal ``items`` stubs.

    Chapter ``items`` are an 8-block mobile leftover (D-PFM-27). Using them as
    the owner map dumps every unknown photo onto chapter 0, so later chapters
    keep empty ``screens`` and web render falls back to long-image items.
    """
    if buckets is not None and index < len(buckets) and buckets[index]:
        return [str(x) for x in buckets[index] if x]
    from travelogue.layout_contract.chapter_items import item_asset_ids

    ids: list[str] = []
    for item in ch.get("items") or []:
        ids.extend(item_asset_ids(item))
    return ids


def attach_screens_to_chapters(
    chapters: list[dict[str, Any]],
    pages: Sequence[PlacedPage],
    *,
    buckets: Sequence[Sequence[str]] | None = None,
) -> None:
    """Write screens onto existing chapters (D-PFM-14 · do not recut chapters)."""
    owner: dict[str, int] = {}
    for i, ch in enumerate(chapters):
        for aid in _chapter_owner_ids(ch, i, buckets):
            owner.setdefault(str(aid), i)
        ch["screens"] = []

    if not chapters:
        return
    seq_per_ch: dict[int, int] = {}
    for page in pages:
        idx = owner.get(page.asset_ids[0], 0) if page.asset_ids else 0
        if idx < 0 or idx >= len(chapters):
            idx = 0
        ch = chapters[idx]
        ch_id = str(ch.get("id") or f"ch-{idx + 1:02d}")
        seq_per_ch[idx] = seq_per_ch.get(idx, 0) + 1
        screen = page.as_screen()
        screen["screenId"] = f"{ch_id}-sc-{seq_per_ch[idx]:02d}"
        ch.setdefault("screens", []).append(screen)
