"""Group → page placement. One page never spans two shot groups (AC-PFM-09)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

DENSE_MIN_SLOTS = 5


@dataclass
class PlacedPage:
    role: str
    program: str
    slot_band: int
    pattern_id: str
    asset_ids: list[str]
    shot_group_id: str

    def as_screen(self) -> dict[str, Any]:
        refuse_cross_group_screen([self.shot_group_id] * len(self.asset_ids))
        # Do not write series ``role`` onto layoutScreen.role (P23 peak enum).
        screen: dict[str, Any] = {
            "patternId": self.pattern_id,
            "slots": [
                {"assetId": aid, "slot": i, "fit": "cover"}
                for i, aid in enumerate(self.asset_ids)
            ],
        }
        if self.shot_group_id:
            screen["shotGroupId"] = self.shot_group_id
        return screen


@dataclass
class PlaceResult:
    pages: list[PlacedPage] = field(default_factory=list)
    leftover_ids: list[str] = field(default_factory=list)
    dropped_roles: list[str] = field(default_factory=list)


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
        take_n = min(band, len(group["ids"]))
        chunk = group["ids"][:take_n]
        group["ids"] = group["ids"][take_n:]
        pattern = str(
            spec.get("patternId") or spec.get("faceHint") or f"page-grid-{take_n}"
        )
        page = PlacedPage(
            role=role,
            program=str(spec.get("program") or ""),
            slot_band=band,
            pattern_id=pattern,
            asset_ids=chunk,
            shot_group_id=str(group["id"]),
        )
        refuse_cross_group_screen([page.shot_group_id] * len(page.asset_ids))
        result.pages.append(page)

    for g in queues:
        result.leftover_ids.extend(g["ids"])
    result.leftover_ids.extend(cap_leftover)
    return result


def attach_screens_to_chapters(
    chapters: list[dict[str, Any]],
    pages: Sequence[PlacedPage],
    *,
    buckets: Sequence[Sequence[str]] | None = None,
) -> None:
    """Write screens onto existing chapters (D-PFM-14 · do not recut chapters)."""
    from travelogue.layout_contract.chapter_items import item_asset_ids

    owner: dict[str, int] = {}
    for i, ch in enumerate(chapters):
        ids: list[str] = []
        for item in ch.get("items") or []:
            ids.extend(item_asset_ids(item))
        if not ids and buckets is not None and i < len(buckets):
            ids = [str(x) for x in buckets[i] if x]
        for aid in ids:
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
