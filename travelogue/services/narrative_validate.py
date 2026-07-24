"""VR-N* narrative content checks (L2 manifest)."""

from __future__ import annotations

from travelogue.config import AppConfig, get_config
from travelogue.services.narrate import BANNED_PHRASES
from travelogue.services.validate import asset_map

# Common overseas destination names (Chinese) for VR-N02 heuristic.
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


def banned_phrases(cfg: AppConfig | None = None) -> tuple[str, ...]:
    narrative = (cfg or get_config()).narrative
    if narrative.banned_phrases:
        return tuple(narrative.banned_phrases)
    return BANNED_PHRASES


def _text_fields(trip: dict) -> list[tuple[str, str]]:
    """Yield (path, text) for narrative strings to scan."""
    meta = trip.get("meta") or {}
    fields: list[tuple[str, str]] = []
    for key in ("title", "subtitle", "hook", "epilogue"):
        val = meta.get(key) if key != "epilogue" else trip.get("epilogue")
        if isinstance(val, str) and val.strip() != "":
            path = f"meta.{key}" if key != "epilogue" else "epilogue"
            fields.append((path, val))
    for i, ch in enumerate(trip.get("chapters") or []):
        for key in ("title", "lead", "decorLine"):
            val = ch.get(key)
            if isinstance(val, str) and val.strip():
                fields.append((f"chapters[{i}].{key}", val))
        for j, it in enumerate(ch.get("items") or []):
            cap = it.get("caption")
            if isinstance(cap, str) and cap.strip():
                fields.append((f"chapters[{i}].items[{j}].caption", cap))
    return fields


def _asset_cities(assets: dict[str, dict]) -> set[str]:
    cities: set[str] = set()
    for a in assets.values():
        place = a.get("place") or {}
        city = place.get("city")
        if isinstance(city, str) and city.strip():
            cities.add(city.strip())
    return cities


def _is_overseas_place(name: str) -> bool:
    n = name.strip()
    if not n:
        return False
    if n in OVERSEAS_PLACE_HINTS:
        return True
    for hint in OVERSEAS_PLACE_HINTS:
        if hint in n or n in hint:
            return True
    return False


def lead_repeats_title(title: str, lead: str, *, place: str = "") -> bool:
    """True when lead mostly echoes chapter title (VR-N04)."""
    title = (title or "").strip()
    lead = (lead or "").strip()
    place = (place or "").strip()
    if not title or not lead:
        return False
    if lead.startswith(title):
        return True
    if place and lead in (f"{title}，{place}。", f"{title}，{place}"):
        return True
    return _overlap_ratio(lead, title) >= 0.85


def _overlap_ratio(a: str, b: str) -> float:
    a, b = a.strip(), b.strip()
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if shorter in longer:
        return len(shorter) / len(longer)
    common = sum(1 for c in shorter if c in longer)
    return common / max(len(longer), 1)


def validate_narrative(trip: dict, *, cfg: AppConfig | None = None) -> list[str]:
    """Return VR-N01/N02/N03 messages (errors or WARN: warnings)."""
    issues: list[str] = []
    assets = asset_map(trip)
    asset_cities = _asset_cities(assets)

    for path, text in _text_fields(trip):
        for phrase in banned_phrases(cfg):
            if phrase and phrase in text:
                issues.append(
                    f"E_VALIDATE_MANIFEST banned phrase {phrase!r} in {path} (VR-N01)"
                )

    declared: list[tuple[str, str]] = []
    meta_places = trip.get("meta", {}).get("places") or []
    for p in meta_places:
        if isinstance(p, str) and p.strip():
            declared.append(("meta.places", p.strip()))
    for i, ch in enumerate(trip.get("chapters") or []):
        for p in (ch.get("curation") or {}).get("places") or []:
            if isinstance(p, str) and p.strip():
                declared.append((f"chapters[{i}].curation.places", p.strip()))

    for path, place in declared:
        if place in asset_cities:
            continue
        if _is_overseas_place(place):
            issues.append(
                f"WARN: overseas place {place!r} in {path} not found in asset cities (VR-N02)"
            )

    from travelogue.curation.chapter_titles import is_ordinal_face_title

    for i, ch in enumerate(trip.get("chapters") or []):
        title = (ch.get("title") or "").strip()
        # SFP D-SFP-01 · 读者面禁序号腔章名
        if title and is_ordinal_face_title(title):
            issues.append(
                f"E_VALIDATE_MANIFEST ordinal chapter title {title!r} in chapters[{i}] (SFP-01)"
            )
        lead = (ch.get("lead") or "").strip()
        if title and lead:
            places = (ch.get("curation") or {}).get("places") or []
            place = places[0] if places else ""
            if not place:
                meta_places = trip.get("meta", {}).get("places") or []
                place = meta_places[0] if meta_places else ""
            if lead_repeats_title(title, lead, place=str(place)):
                issues.append(
                    f"E_VALIDATE_MANIFEST lead repeats chapter title in chapters[{i}] (VR-N04)"
                )
        for j, it in enumerate(ch.get("items") or []):
            if it.get("type") != "media-card":
                continue
            cap = (it.get("caption") or "").strip()
            if not cap:
                continue
            aid = it.get("assetId")
            if not aid or aid not in assets:
                continue
            voice = assets[aid].get("voice") or {}
            transcript = (voice.get("transcript") or voice.get("transcriptPreview") or "").strip()
            if not transcript:
                continue
            if _overlap_ratio(cap, transcript) >= 0.8:
                issues.append(
                    f"WARN: caption overlaps transcript on chapters[{i}].items[{j}] (VR-N03)"
                )
        decor = ch.get("decorLine")
        if isinstance(decor, str) and decor.strip():
            from travelogue.services.decor_line import validate_decor_line

            for err in validate_decor_line(decor.strip(), ch, cfg=cfg):
                issues.append(f"E_VALIDATE_MANIFEST {err} in chapters[{i}]")
        from travelogue.services.decor_line import validate_copy_intent

        for err in validate_copy_intent(ch, chapter_index=i):
            issues.append(f"E_VALIDATE_MANIFEST {err}")

    return issues
