"""Place-name heuristics for narrative grounding (layer-0 pure helpers).

Moved out of ``services.narrative_validate`` so ``curation`` may call them
without importing the services layer (Arch Opt V2 · M2-A1).
"""

from __future__ import annotations

from travelogue.domain.copy_subject import is_generic_place

# Common overseas destination names (Chinese) for VR-N02 / VR-N05 heuristics.
OVERSEAS_PLACE_HINTS: frozenset[str] = frozenset(
    {
        "东京",
        "大阪",
        "京都",
        "巴黎",
        "伦敦",
        "纽约",
        "首尔",
        "曼谷",
        "新加坡",
        "悉尼",
        "罗马",
        "米兰",
        "威尼斯",
        "巴塞罗那",
        "阿姆斯特丹",
        "柏林",
        "慕尼黑",
        "苏黎世",
        "温哥华",
        "洛杉矶",
        "旧金山",
        "夏威夷",
        "迪拜",
        "伊斯坦布尔",
        "普吉岛",
        "巴厘岛",
        "马尔代夫",
        "札幌",
        "福冈",
        "名古屋",
        "横滨",
        "奈良",
        "镰仓",
    }
)


def _asset_map(trip: dict) -> dict[str, dict]:
    """Inline equivalent of ``services.validate.asset_map`` (1-line dict)."""
    return {a["id"]: a for a in trip.get("assets", [])}


def _asset_cities(assets: dict[str, dict]) -> set[str]:
    cities: set[str] = set()
    for a in assets.values():
        place = a.get("place") or {}
        city = place.get("city")
        if isinstance(city, str) and city.strip():
            cities.add(city.strip())
    return cities


def allowed_place_names(trip: dict) -> set[str]:
    """Authoritative place tokens for copy grounding (meta.places + EXIF cities).

    Chapter ``curation.places`` are intentionally excluded — they can be polluted
    by prior LLM / segment labels and must not widen the VR-N05 allow-list.
    """
    allowed: set[str] = set()
    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    for p in meta.get("places") or []:
        if isinstance(p, str) and p.strip() and not is_generic_place(p):
            allowed.add(p.strip())
    legacy = meta.get("place")
    if isinstance(legacy, str) and legacy.strip() and not is_generic_place(legacy):
        allowed.add(legacy.strip())
    for city in _asset_cities(_asset_map(trip)):
        if city and not is_generic_place(city):
            allowed.add(city)
    return allowed


def _place_covered(hint: str, allowed: set[str]) -> bool:
    h = (hint or "").strip()
    if not h:
        return True
    for a in allowed:
        if not a:
            continue
        if h == a or h in a or a in h:
            return True
    return False


def unauthorized_place_mentions(text: str, allowed: set[str]) -> list[str]:
    """Known place hints appearing in text but not covered by ``allowed`` (VR-N05)."""
    raw = (text or "").strip()
    if not raw:
        return []
    hits: list[str] = []
    for hint in sorted(OVERSEAS_PLACE_HINTS, key=len, reverse=True):
        if hint not in raw:
            continue
        if _place_covered(hint, allowed):
            continue
        # Prefer longest match; skip shorter hints already subsumed.
        if any(hint in prev for prev in hits):
            continue
        hits.append(hint)
    return hits
