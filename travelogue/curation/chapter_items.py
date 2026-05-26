"""Compact chapter items[] for schema limits and screens engine sync."""

from __future__ import annotations

MAX_CHAPTER_ITEMS = 8


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


def items_from_asset_ids(
    asset_ids: list[str],
    *,
    max_blocks: int = MAX_CHAPTER_ITEMS,
) -> list[dict]:
    """Rebuild a compact items[] from asset ids (schema max blocks)."""
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
    """Expand screens[].slots into one media-card each (longshot vertical stack)."""
    items: list[dict] = []
    for sc in chapter.get("screens") or []:
        for slot in sc.get("slots") or []:
            aid = slot.get("assetId")
            if not aid:
                continue
            items.append(
                {
                    "type": "media-card",
                    "assetId": aid,
                    "layout": {"fill": True, "bleed": True, "overlay": False},
                }
            )
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
        aids = collect_screen_asset_ids(ch)
        if aids:
            ch["items"] = items_from_asset_ids(aids)
        elif len(ch.get("items") or []) > MAX_CHAPTER_ITEMS:
            flat: list[str] = []
            for it in ch.get("items") or []:
                for aid in item_asset_ids(it):
                    if aid not in flat:
                        flat.append(aid)
            ch["items"] = items_from_asset_ids(flat)
