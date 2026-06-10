"""Lightweight visual fact hints for decorLine brief (tags-based; VLM hook P11.2)."""

from __future__ import annotations

# Tags / labels that describe capture mechanics, layout, or detector primitives
# rather than the trip's story. Feeding them to the decorLine LLM makes copy read
# like a tag dump ("白天，人像，竖图"), so they are excluded from facts. Time-of-day
# (白天/夜晚…) and real scene/object tags are intentionally NOT listed: they are
# legitimate context when combined with places/notes.
_NON_NARRATIVE_TAGS = frozenset(
    {
        # orientation / layout / framing
        "竖图", "横图", "方图", "竖版", "横版", "全景", "全景图", "宽幅", "特写",
        "portrait", "landscape", "square", "panorama", "tall", "vertical",
        "horizontal", "wide", "closeup", "close-up",
        # generic media class
        "photo", "image", "picture", "snapshot", "照片", "图片", "图像",
        # detector primitives (people without context)
        "person", "people", "face", "faces", "human", "humans", "selfie",
        "人像", "人物", "人脸", "自拍",
    }
)


def is_narrative_tag(tag: str) -> bool:
    """False for layout/media/detector tags that should not appear in copy."""
    t = str(tag or "").strip()
    if not t:
        return False
    return t.lower() not in _NON_NARRATIVE_TAGS


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
        tags = [
            str(t).strip()
            for t in (asset.get("tags") or [])
            if str(t).strip() and is_narrative_tag(str(t))
        ]
        if tags:
            facts.append(" · ".join(tags[:3]))
        media_class = str(asset.get("mediaClass") or "").strip()
        aspect = str(asset.get("aspectKind") or "").strip()
        if media_class and is_narrative_tag(media_class):
            facts.append(media_class)
        elif aspect and aspect not in ("default", "landscape") and is_narrative_tag(aspect):
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
