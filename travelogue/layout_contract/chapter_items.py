"""Compact chapter items helpers (layout kernel)."""

from __future__ import annotations

import logging
from typing import Literal

MAX_CHAPTER_ITEMS = 8

_LOG = logging.getLogger("travelogue.layout.narrative")

LongshotMode = Literal["preserve_stack", "representative_badge", "flatten"]


def item_asset_ids(item: dict) -> list[str]:
    if item.get("type") == "media-card":
        aid = item.get("assetId")
        return [aid] if aid else []
    if item.get("type") in ("media-row", "media-scroll"):
        return list(item.get("assetIds") or [])
    return []


def collect_screen_asset_ids(chapter: dict) -> list[str]:
    """Ordered unique asset ids from chapter screens[].slots."""
    aids: list[str] = []
    seen: set[str] = set()
    for sc in chapter.get("screens") or []:
        for sl in sc.get("slots") or []:
            aid = sl.get("assetId")
            if aid and aid not in seen:
                seen.add(aid)
                aids.append(aid)
    return aids


def _row_layout_for_screen(pattern_id: str, slot_count: int) -> str:
    pid = pattern_id or ""
    suffix = "triple" if slot_count >= 3 else "pair"
    # Mixed (e.g. screen-portrait-1-landscape-2) and mosaic screens are
    # landscape-dominant rows: a naive "portrait in pid" substring test would
    # mislabel them portrait-* and render the mobile/legacy stub fallback with
    # the wrong row family. Only label portrait/square when the pattern is a
    # pure single-family grid.
    has_landscape = "landscape" in pid
    is_mosaic = "mosaic" in pid
    if "portrait" in pid and not has_landscape and not is_mosaic:
        return f"portrait-{suffix}"
    if "square" in pid and not has_landscape and not is_mosaic:
        return f"square-{suffix}"
    return f"landscape-{suffix}"


def item_stub_for_screen(screen: dict) -> dict | None:
    """One screens[] entry → one items[] block (schema stub for Web screens engine)."""
    slots = screen.get("slots") or []
    aids = [sl["assetId"] for sl in slots if sl.get("assetId")]
    if not aids:
        return None
    if len(aids) == 1:
        return {
            "type": "media-card",
            "assetId": aids[0],
            "layout": {"fill": True, "bleed": True, "overlay": True},
        }
    row_layout = _row_layout_for_screen(str(screen.get("patternId") or ""), len(aids))
    return {
        "type": "media-row",
        "assetIds": aids[:3],
        "rowLayout": row_layout,
    }


def items_from_screens(
    chapter: dict,
    *,
    max_blocks: int = MAX_CHAPTER_ITEMS,
) -> list[dict]:
    """Build compact items[] — one block per screen (≤ max_blocks)."""
    items: list[dict] = []
    for sc in chapter.get("screens") or []:
        if len(items) >= max_blocks:
            break
        stub = item_stub_for_screen(sc)
        if stub:
            items.append(stub)
    return items


def items_from_asset_ids(
    asset_ids: list[str],
    *,
    max_blocks: int = MAX_CHAPTER_ITEMS,
) -> list[dict]:
    """Rebuild a compact items[] from asset ids (legacy chunk fallback)."""
    items: list[dict] = []
    i = 0
    while i < len(asset_ids) and len(items) < max_blocks:
        chunk = asset_ids[i : i + 3]
        if len(chunk) == 1:
            items.append(
                {
                    "type": "media-card",
                    "assetId": chunk[0],
                    "layout": {"fill": True, "bleed": True, "overlay": True},
                }
            )
            i += 1
        else:
            layout = "landscape-triple" if len(chunk) >= 3 else "landscape-pair"
            items.append(
                {"type": "media-row", "assetIds": chunk[:3], "rowLayout": layout}
            )
            i += len(chunk[:3])
    return items[:max_blocks]


def flatten_screens_to_items(chapter: dict) -> list[dict]:
    """Expand screens[].slots into one media-card each (explicit flatten path)."""
    items: list[dict] = []
    for sc in chapter.get("screens") or []:
        items.extend(_flatten_screen_to_cards(sc))
    return items


def _flatten_screen_to_cards(screen: dict) -> list[dict]:
    items: list[dict] = []
    for slot in screen.get("slots") or []:
        aid = slot.get("assetId")
        if not aid:
            continue
        items.append(
            {
                "type": "media-card",
                "assetId": aid,
                "layout": {"fill": True, "bleed": True, "overlay": False},
                "groupId": screen.get("groupId") or screen.get("screenId"),
                "preserveGroup": False,
            }
        )
    return items


def resolve_longshot_mode(screen: dict) -> LongshotMode:
    """ADR-020 D5 · three-tier longshot mode for one screen."""
    from travelogue.layout_contract.narrative_contract import ensure_narrative_contract

    ensure_narrative_contract(screen)
    if screen.get("preserveGroup") is False:
        return "flatten"
    hints = screen.get("exportHints") if isinstance(screen.get("exportHints"), dict) else {}
    mode = str(hints.get("longshotMode") or "").strip()
    if mode == "representative_badge":
        return "representative_badge"
    if mode == "flatten":
        # Conflict with preserveGroup=true should already be stripped; belt-and-suspenders.
        return "preserve_stack"
    if mode == "preserve_stack":
        return "preserve_stack"
    # Default when preserveGroup is true (or derived true).
    if screen.get("preserveGroup") is True:
        return "preserve_stack"
    return "flatten"


def longshot_group_item_for_screen(screen: dict) -> dict | None:
    """One preserve_stack group → media-row with full assetIds (no [:3] truncate)."""
    from travelogue.layout_contract.narrative_contract import (
        derive_representative_asset_id,
        ensure_narrative_contract,
    )

    ensure_narrative_contract(screen)
    slots = screen.get("slots") or []
    aids = [sl["assetId"] for sl in slots if sl.get("assetId")]
    if not aids:
        return None
    if len(aids) == 1:
        return {
            "type": "media-card",
            "assetId": aids[0],
            "layout": {"fill": True, "bleed": True, "overlay": False},
            "groupId": screen.get("groupId") or screen.get("screenId"),
            "preserveGroup": True,
            "patternId": screen.get("patternId"),
        }
    return {
        "type": "media-row",
        "assetIds": aids,
        "rowLayout": "preserve-stack",
        "groupId": screen.get("groupId") or screen.get("screenId"),
        "preserveGroup": True,
        "patternId": screen.get("patternId"),
        "groupCount": len(aids),
        "groupMark": f"一组 · {len(aids)}",
        "representativeAssetId": derive_representative_asset_id(screen),
    }


def longshot_representative_item_for_screen(screen: dict) -> dict | None:
    """Tier-2 · representativeAssetId + N badge."""
    from travelogue.layout_contract.narrative_contract import (
        derive_representative_asset_id,
        ensure_narrative_contract,
    )

    ensure_narrative_contract(screen)
    slots = screen.get("slots") or []
    aids = [sl["assetId"] for sl in slots if sl.get("assetId")]
    if not aids:
        return None
    rep = derive_representative_asset_id(screen) or aids[0]
    n = len(aids)
    return {
        "type": "media-card",
        "assetId": rep,
        "layout": {"fill": True, "bleed": True, "overlay": True},
        "groupId": screen.get("groupId") or screen.get("screenId"),
        "preserveGroup": True,
        "patternId": screen.get("patternId"),
        "groupCount": n,
        "groupBadge": f"+{n - 1}" if n > 1 else None,
        "groupMark": f"一组 · {n}",
    }


def screens_to_longshot_items(
    chapter: dict, *, compact: bool = False
) -> list[dict]:
    """LTN B2 / ADR-020 · longshot items with preserveGroup three-tier degradation.

    SFI D-SFI-11 · ``compact=True`` folds multi-slot preserve groups to
    representative_badge (tier ②) without skipping B2 / flattening.
    """
    items: list[dict] = []
    for sc in chapter.get("screens") or []:
        if not isinstance(sc, dict):
            continue
        mode = resolve_longshot_mode(sc)
        if mode == "flatten":
            _LOG.info(
                "ltn.preserve_group_false screenId=%s patternId=%s",
                sc.get("screenId"),
                sc.get("patternId"),
            )
            items.extend(_flatten_screen_to_cards(sc))
            continue
        if mode == "preserve_stack" and compact:
            slots = [sl for sl in (sc.get("slots") or []) if sl.get("assetId")]
            if len(slots) > 1:
                mode = "representative_badge"
        if mode == "representative_badge":
            stub = longshot_representative_item_for_screen(sc)
            if stub:
                items.append(stub)
            continue
        stub = longshot_group_item_for_screen(sc)
        if stub:
            items.append(stub)
    return items


def count_chapter_screen_slots(chapter: dict) -> int:
    n = 0
    for sc in chapter.get("screens") or []:
        n += len(sc.get("slots") or [])
    return n


def compact_chapter_items_for_screens(chapters: list[dict]) -> None:
    """
    When layoutEngine=screens, items[] is a legacy/mobile stub (≤8 blocks).

    Web render reads screens[]; compact items keeps trip.json schema-valid.
    """
    for ch in chapters:
        if not ch.get("screens"):
            continue
        stub_items = items_from_screens(ch)
        if stub_items:
            ch["items"] = stub_items
            ch_cur = ch.setdefault("curation", {})
            ch_cur["layoutStub"] = True
        elif len(ch.get("items") or []) > MAX_CHAPTER_ITEMS:
            flat: list[str] = []
            for it in ch.get("items") or []:
                for aid in item_asset_ids(it):
                    if aid not in flat:
                        flat.append(aid)
            ch["items"] = items_from_asset_ids(flat)
            ch.setdefault("curation", {})["layoutStub"] = True


def collect_displayed_asset_ids(
    chapters: list[dict],
    *,
    extra_asset_ids: list[str] | None = None,
) -> list[str]:
    """Ordered unique ids on screens plus optional cover/extra heroes."""
    seen: set[str] = set()
    out: list[str] = []
    for aid in extra_asset_ids or []:
        if aid and aid not in seen:
            seen.add(aid)
            out.append(aid)
    for ch in chapters:
        for aid in collect_screen_asset_ids(ch):
            if aid not in seen:
                seen.add(aid)
                out.append(aid)
    return out


def summarize_screen_patterns(chapters: list[dict]) -> dict[str, int]:
    """Count screen patternId usage across chapters (layout observability)."""
    counts: dict[str, int] = {}
    for ch in chapters:
        for sc in ch.get("screens") or []:
            pid = str(sc.get("patternId") or "unknown")
            counts[pid] = counts.get(pid, 0) + 1
    return counts

