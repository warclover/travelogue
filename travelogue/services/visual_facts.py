"""Lightweight visual fact hints for decorLine brief (tags-based; VLM hook P11.2)."""

from __future__ import annotations


def representative_asset_ids(chapter: dict, *, limit: int = 2) -> list[str]:
    """Pick up to `limit` media-card asset ids (chapter order, de-duplicated)."""
    seen: set[str] = set()
    out: list[str] = []
    for it in chapter.get("items") or []:
        if it.get("type") != "media-card":
            continue
        aid = str(it.get("assetId") or "").strip()
        if not aid or aid in seen:
            continue
        seen.add(aid)
        out.append(aid)
        if len(out) >= limit:
            return out
    for sc in chapter.get("screens") or []:
        for slot in sc.get("slots") or []:
            aid = str(slot.get("assetId") or "").strip()
            if not aid or aid in seen:
                continue
            seen.add(aid)
            out.append(aid)
            if len(out) >= limit:
                return out
    return out


def extract_visual_facts(chapter: dict, trip: dict, *, limit: int = 2) -> list[str]:
    """
    Non-user-facing visual hints from representative assets (tags / mediaClass).
    Future: optional VLM caption per representative_asset_ids().
    """
    assets = {a.get("id"): a for a in trip.get("assets") or [] if a.get("id")}
    facts: list[str] = []
    for aid in representative_asset_ids(chapter, limit=limit):
        asset = assets.get(aid) or {}
        tags = [str(t).strip() for t in (asset.get("tags") or []) if str(t).strip()]
        if tags:
            facts.append(" · ".join(tags[:3]))
        media_class = str(asset.get("mediaClass") or "").strip()
        aspect = str(asset.get("aspectKind") or "").strip()
        if media_class:
            facts.append(media_class)
        elif aspect and aspect not in ("default", "landscape"):
            facts.append(aspect)
    deduped: list[str] = []
    seen: set[str] = set()
    for f in facts:
        key = f.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(f)
    return deduped[: max(limit * 2, limit)]
