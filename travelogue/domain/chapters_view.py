"""Chapter / screen traversal helpers (M-C4)."""

from __future__ import annotations

from collections.abc import Iterator


def chapter_ids(trip: dict) -> list[str]:
    return [str(ch["id"]) for ch in (trip.get("chapters") or []) if ch.get("id")]


def iter_screens(trip: dict) -> Iterator[tuple[str, dict]]:
    for ch in trip.get("chapters") or []:
        ch_id = str(ch.get("id") or "")
        for scr in ch.get("screens") or []:
            yield ch_id, scr


def screen_asset_ids(trip: dict) -> list[str]:
    ids: list[str] = []
    for _ch_id, scr in iter_screens(trip):
        for slot in scr.get("slots") or []:
            aid = slot.get("assetId")
            if aid:
                ids.append(str(aid))
    return ids


def find_screen(trip: dict, screen_id: str) -> tuple[dict, dict] | None:
    target = str(screen_id)
    for ch in trip.get("chapters") or []:
        for scr in ch.get("screens") or []:
            if str(scr.get("screenId") or "") == target:
                return ch, scr
    return None
