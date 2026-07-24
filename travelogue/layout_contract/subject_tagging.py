"""Subject tagging placeholder for future person-cluster signals."""

from __future__ import annotations

_CLIP_TO_BUCKET: dict[str, str] = {
    "person": "person",
    "landscape": "landscape",
    "architecture": "landscape",
    "street": "landscape",
    "temple": "landscape",
    "food": "food",
    "indoor": "general",
    "mixed": "general",
}

_L1_CATEGORY_FROM_CLIP: dict[str, str] = {
    "person": "person",
    "portrait": "person",
    "landscape": "landscape",
    "nature": "landscape",
    "sunset": "landscape",
    "mountain": "landscape",
    "sea": "landscape",
    "architecture": "architecture",
    "temple": "temple",
    "street": "street",
    "food": "food",
    "meal": "food",
    "cafe": "food",
    "coffee": "food",
    "dessert": "food",
    "drink": "food",
    "sign": "document",
    "signage": "document",
    "ticket": "document",
    "receipt": "document",
    "document": "document",
    "shop": "shop",
    "store": "shop",
    "vehicle": "transport",
    "train": "transport",
    "plane": "transport",
    "airport": "transport",
    "night": "night",
    "indoor": "general",
    "mixed": "general",
}

_CLIP_CONFIDENCE_FLOOR = 0.35
_FOOD_MUNDANE_TAGS: set[str] = {
    "food",
    "meal",
    "restaurant",
    "coffee",
    "cafe",
    "dessert",
    "drink",
}
_SIGN_MUNDANE_TAGS: set[str] = {"sign", "signage"}
_TICKET_MUNDANE_TAGS: set[str] = {"ticket"}
_SHOP_MUNDANE_TAGS: set[str] = {"shop"}
_MUNDANE_TAG_GROUPS: tuple[tuple[str, set[str]], ...] = (
    ("food", _FOOD_MUNDANE_TAGS),
    ("sign", _SIGN_MUNDANE_TAGS),
    ("ticket", _TICKET_MUNDANE_TAGS),
    ("shop", _SHOP_MUNDANE_TAGS),
)


def _map_clip_to_bucket(subject_class: str) -> str:
    key = subject_class.lower().strip()
    return _CLIP_TO_BUCKET.get(key, "general")


def _heuristic_subject_class(asset: dict) -> str:
    tags = {str(t).lower() for t in (asset.get("tags") or []) if t}
    bucket = str(asset.get("subjectBucket") or "").lower()
    cur = asset.get("curation") or {}
    stags = cur.get("subjectTags") or subject_tags_for_asset(asset)
    if "has_face" in stags or tags & {"person", "face", "portrait"} or bucket in {
        "person",
        "portrait",
    }:
        return "person"
    if tags & {"landscape", "scenery", "mountain", "sea", "sky", "nature"} or bucket in {
        "landscape",
        "scenery",
        "temple",
        "street",
        "nature",
    }:
        return "landscape"
    if tags & {"food", "meal", "restaurant"} or bucket in {"food", "meal"}:
        return "food"
    return "general"


def subject_class_for_asset(asset: dict) -> str:
    """Coarse subject bucket for run scoring (Phase 3a / P9-E bridge)."""
    clip = str(asset.get("subjectClass") or "").lower().strip()
    if clip:
        conf = asset.get("subjectConfidence")
        conf_ok = conf is None
        if not conf_ok:
            try:
                conf_ok = float(conf) >= _CLIP_CONFIDENCE_FLOOR
            except (TypeError, ValueError):
                conf_ok = False
        if conf_ok:
            return _map_clip_to_bucket(clip)
    return _heuristic_subject_class(asset)


def subject_tags_for_asset(asset: dict) -> list[str]:
    """P1: return subject tags; P0 returns hasFace boolean as tag."""
    tags: list[str] = []
    clip = str(asset.get("subjectClass") or "").strip()
    if clip:
        tags.append(f"clip:{clip.lower()}")
    faces = asset.get("faces") or []
    if faces:
        tags.append("has_face")
    heuristic = asset.get("tags") or []
    for t in heuristic:
        if isinstance(t, str) and t.startswith("person"):
            tags.append(t)
    return tags


def semantic_category_for_asset(asset: dict) -> str:
    """Phase 12 L1 semantic category (11-way, conservative fallback)."""
    semantic = asset.get("semanticTag")
    if isinstance(semantic, dict):
        cat = str(semantic.get("category") or "").lower().strip()
        if cat:
            return cat

    clip = str(asset.get("subjectClass") or "").lower().strip()
    if clip:
        mapped = _L1_CATEGORY_FROM_CLIP.get(clip)
        if mapped:
            return mapped

    tags = {str(t).lower().strip() for t in (asset.get("tags") or []) if t}
    tags.update(str(t).lower().strip() for t in (asset.get("curation") or {}).get("subjectTags") or [] if t)
    for tag in list(tags):
        norm = tag.split(":", 1)[-1] if tag.startswith("clip:") else tag
        mapped = _L1_CATEGORY_FROM_CLIP.get(norm)
        if mapped:
            return mapped

    bucket = str(asset.get("subjectBucket") or "").lower().strip()
    if bucket:
        mapped = _L1_CATEGORY_FROM_CLIP.get(bucket)
        if mapped:
            return mapped
    return "general"


def refresh_semantic_tag_for_asset(asset: dict) -> str:
    """Recompute L1 category after CLIP subjectClass or tags change (Phase 12)."""
    asset.pop("semanticTag", None)
    category = semantic_category_for_asset(asset)
    asset["semanticTag"] = {"category": category}
    return category


_FOOD_L1_CATEGORIES: set[str] = {"food", "meal", "cafe", "restaurant"}


def is_mundane_clusterable(asset: dict) -> str | None:
    """Return mundane bucket key if asset is clusterable mundane, else None."""
    if subject_class_for_asset(asset) == "food":
        return "food"

    tags = {str(t).lower().strip() for t in (asset.get("tags") or []) if t}
    cur = asset.get("curation") or {}
    for t in cur.get("subjectTags") or []:
        if isinstance(t, str):
            norm = t.lower().strip()
            if norm.startswith("clip:"):
                norm = norm.split(":", 1)[1]
            if norm:
                tags.add(norm)

    # Phase 8 兼容预留：读取 semanticTag.category（当前不作为必需信号）。
    semantic = asset.get("semanticTag")
    if isinstance(semantic, dict):
        category = str(semantic.get("category") or "").lower().strip()
        if category:
            tags.add(category)

    for bucket, tag_set in _MUNDANE_TAG_GROUPS:
        if tags & tag_set:
            return bucket
    return None


def is_food_asset(asset: dict) -> bool:
    """True when asset is coarse food (CLIP / mundane / L1), for FRP demote & grid."""
    if subject_class_for_asset(asset) == "food":
        return True
    if is_mundane_clusterable(asset) == "food":
        return True
    category = semantic_category_for_asset(asset)
    return category in _FOOD_L1_CATEGORIES


def mundane_run_length(
    ids: list[str],
    assets_map: dict[str, dict],
    start: int,
    *,
    tolerance: int = 1,
    allowed_buckets: tuple[str, ...] = ("food",),
) -> int:
    """Count consecutive allowed mundane from start; allow tolerance non-mundane inserts."""
    if start < 0 or start >= len(ids):
        return 0
    run = 0
    misses = 0
    i = start
    allowed = set(allowed_buckets)
    while i < len(ids):
        aid = ids[i]
        bucket = is_mundane_clusterable(assets_map.get(aid, {}))
        if bucket in allowed:
            run += 1
            i += 1
            continue
        misses += 1
        if misses > tolerance:
            break
        i += 1
    return run


def enrich_assets_subject_tags(assets: list[dict]) -> list[dict]:
    """Non-destructive copy with curation.subjectTags when missing."""
    out: list[dict] = []
    for a in assets:
        copy = dict(a)
        cur = dict(copy.get("curation") or {})
        if "subjectTags" not in cur:
            cur["subjectTags"] = subject_tags_for_asset(a)
        copy["curation"] = cur
        out.append(copy)
    return out
