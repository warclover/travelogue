"""Restore user-protected copy onto a pipeline memory snapshot (no edition branch)."""

from __future__ import annotations

from copy import deepcopy

from travelogue.domain.copy_origin import ORIGIN_USER, is_user_protected

_CHAPTER_COPY = (
    ("title", "titleOrigin"),
    ("lead", "leadOrigin"),
    ("decorLine", "decorLineOrigin"),
)


def snapshot_user_copy(trip: dict) -> dict:
    """Shallow snapshot of copy-bearing objects used to restore after structure push."""
    meta = trip.get("meta")
    return {
        "chapters": deepcopy(trip.get("chapters") or []),
        "screens": deepcopy(trip.get("screens") or []),
        "assets": deepcopy(trip.get("assets") or []),
        "epilogue": trip.get("epilogue"),
        "epilogueOrigin": trip.get("epilogueOrigin"),
        "meta": deepcopy(meta) if isinstance(meta, dict) else {},
    }


def restore_user_copy_onto(target: dict, prior: dict) -> None:
    """Keep disk user copy when pipeline persist pushes a newer structure."""
    if not isinstance(prior, dict):
        return

    prior_meta = prior.get("meta") if isinstance(prior.get("meta"), dict) else {}
    tgt_meta = target.get("meta")
    if not isinstance(tgt_meta, dict):
        tgt_meta = {}
        target["meta"] = tgt_meta
    if is_user_protected(prior_meta, "hookOrigin"):
        tgt_meta["hook"] = prior_meta.get("hook")
        if prior_meta.get("hookOrigin"):
            tgt_meta["hookOrigin"] = prior_meta["hookOrigin"]
        if prior_meta.get("edited"):
            tgt_meta["edited"] = True

    if is_user_protected(prior, "epilogueOrigin"):
        target["epilogue"] = prior.get("epilogue")
        if prior.get("epilogueOrigin"):
            target["epilogueOrigin"] = prior["epilogueOrigin"]

    prior_chapters = {
        ch.get("id"): ch
        for ch in prior.get("chapters") or []
        if isinstance(ch, dict) and ch.get("id")
    }
    for ch in target.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        src = prior_chapters.get(ch.get("id"))
        if not isinstance(src, dict):
            continue
        for field, origin_key in _CHAPTER_COPY:
            if is_user_protected(src, origin_key):
                ch[field] = src.get(field)
                if src.get(origin_key):
                    ch[origin_key] = src[origin_key]
                if src.get("edited"):
                    ch["edited"] = True
        _restore_item_captions(ch, src)
        _restore_screens(ch.setdefault("screens", []), src.get("screens") or [])

    _restore_screens(target.get("screens") or [], prior.get("screens") or [])
    _restore_asset_captions(target.get("assets") or [], prior.get("assets") or [])


def _restore_item_captions(chapter: dict, prior_chapter: dict) -> None:
    prior_items = {
        it.get("assetId"): it
        for it in prior_chapter.get("items") or []
        if isinstance(it, dict) and it.get("assetId")
    }
    for item in chapter.get("items") or []:
        if not isinstance(item, dict):
            continue
        src = prior_items.get(item.get("assetId"))
        if not isinstance(src, dict):
            continue
        if is_user_protected(src, "captionOrigin"):
            item["caption"] = src.get("caption")
            if src.get("captionOrigin"):
                item["captionOrigin"] = src["captionOrigin"]
            if src.get("edited"):
                item["edited"] = True


def _restore_screens(target_screens: list, prior_screens: list) -> None:
    prior = {
        sc.get("screenId"): sc
        for sc in prior_screens
        if isinstance(sc, dict) and sc.get("screenId")
    }
    for screen in target_screens:
        if not isinstance(screen, dict):
            continue
        src = prior.get(screen.get("screenId"))
        if not isinstance(src, dict) or not _screen_user_protected(src):
            continue
        if isinstance(src.get("copy"), dict):
            screen["copy"] = dict(src["copy"])
        if isinstance(src.get("copyMeta"), dict):
            screen["copyMeta"] = dict(src["copyMeta"])
        screen["edited"] = True


def _screen_user_protected(screen: dict) -> bool:
    if screen.get("edited"):
        return True
    meta = screen.get("copyMeta")
    if not isinstance(meta, dict):
        return False
    return meta.get("kickerSource") == ORIGIN_USER or meta.get("bodySource") == ORIGIN_USER


def _restore_asset_captions(target_assets: list, prior_assets: list) -> None:
    prior = {
        asset.get("id"): asset
        for asset in prior_assets
        if isinstance(asset, dict) and asset.get("id")
    }
    for asset in target_assets:
        if not isinstance(asset, dict):
            continue
        src = prior.get(asset.get("id"))
        if not isinstance(src, dict):
            continue
        if is_user_protected(src, "captionOrigin"):
            asset["caption"] = src.get("caption")
            if src.get("captionOrigin"):
                asset["captionOrigin"] = src["captionOrigin"]
            if src.get("edited"):
                asset["edited"] = True
