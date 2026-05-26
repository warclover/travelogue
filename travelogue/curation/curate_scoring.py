"""Cover / hero scoring and bucket asset ordering for curate."""

from __future__ import annotations

from travelogue.curation.asset_quality import asset_sharpness
from travelogue.curation.layout_planner import aspect_kind_for_asset
from travelogue.curation.media_classify import cover_class_weight
from travelogue.curation.time_segments import parse_asset_date

_COVER_EXCLUDED_CLASSES = frozenset({"screenshot", "thumbnail", "reupload"})
_HERO_EXCLUDED_CLASSES = frozenset({"screenshot", "thumbnail", "reupload"})
_MOBILE_COVER_MIN_SHORT_EDGE = 600
_MOBILE_VERTICAL_KINDS = frozenset({"portrait", "tall"})


def median_sharpness(assets: list[dict]) -> float:
    values = [asset_sharpness(a) for a in assets if asset_sharpness(a) > 0]
    if not values:
        return 0.0
    values.sort()
    mid = len(values) // 2
    if len(values) % 2:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2.0


def cover_eligible_assets(assets: list[dict]) -> list[dict]:
    """Exclude screenshot/thumbnail/reupload from cover pool when alternatives exist."""
    good = [a for a in assets if a.get("mediaClass") not in _COVER_EXCLUDED_CLASSES]
    return good if good else list(assets)


def mobile_cover_pool(assets: list[dict]) -> list[dict]:
    """Mobile cover: photos + layout-eligible portrait thumbs (WeChat exports)."""
    base = cover_eligible_assets(assets)
    seen = {a["id"] for a in base}
    extras: list[dict] = []
    for a in assets:
        aid = a.get("id")
        if not aid or aid in seen or a.get("type") == "video":
            continue
        if not a.get("layoutEligible", True):
            continue
        if a.get("mediaClass") in ("reupload", "screenshot"):
            continue
        if aspect_kind_for_asset(a) not in _MOBILE_VERTICAL_KINDS:
            continue
        nw = int(a.get("nativeWidth") or a.get("width") or 0)
        nh = int(a.get("nativeHeight") or a.get("height") or 0)
        if min(nw, nh) < _MOBILE_COVER_MIN_SHORT_EDGE:
            continue
        extras.append(a)
        seen.add(aid)
    combined = base + extras
    return combined if combined else list(assets)


def cover_asset_pool(assets: list[dict], *, export_layout: str) -> list[dict]:
    pool = mobile_cover_pool(assets) if export_layout == "mobile" else cover_eligible_assets(assets)
    if export_layout == "mobile":
        vertical = [a for a in pool if aspect_kind_for_asset(a) in _MOBILE_VERTICAL_KINDS]
        if vertical:
            return vertical
    return pool


def _cover_media_weight(asset: dict, export_layout: str) -> float:
    weight = cover_class_weight(asset.get("mediaClass"))
    if export_layout == "mobile" and asset.get("mediaClass") == "thumbnail":
        if aspect_kind_for_asset(asset) in _MOBILE_VERTICAL_KINDS:
            return max(weight, 0.8)
    return weight


def _quality_multiplier(asset: dict, *, export_layout: str, median_sharp: float) -> float:
    mult = 1.0
    if asset.get("dateConfidence") == "low":
        mult *= 0.65
    sharp = asset_sharpness(asset)
    if median_sharp > 0 and sharp > 0:
        ratio = sharp / median_sharp
        mult *= min(1.25, max(0.35, ratio))
    tags = set(asset.get("tags") or [])
    if export_layout == "mobile" and tags.intersection({"person", "face"}):
        mult *= 1.08
    return mult


def cover_score(
    asset: dict,
    export_layout: str,
    *,
    median_sharp: float = 0.0,
) -> float:
    """Mobile: tall/portrait. Web: landscape/panorama. Uses ingest quality signals."""
    kind = aspect_kind_for_asset(asset)
    if kind == "square":
        return 0.0
    w = int(asset.get("width") or 1)
    h = int(asset.get("height") or 1)
    if w <= 0 or h <= 0:
        return 0.0

    base = 0.0
    if export_layout == "web":
        if kind in ("portrait", "tall"):
            return 0.0
        ratio = w / h
        base = ratio
        if kind == "panorama":
            base *= 1.2
        elif kind == "landscape":
            target = 16 / 9
            base *= 1.0 + 0.35 / (1.0 + abs(ratio - target))
    else:
        if kind in ("landscape", "panorama"):
            return 0.0
        base = h / w
        if kind == "tall":
            base *= 1.1

    return base * _cover_media_weight(asset, export_layout) * _quality_multiplier(
        asset, export_layout=export_layout, median_sharp=median_sharp
    )


def hero_score(asset: dict, *, median_sharp: float = 0.0) -> float:
    """Chapter hero: wide compositions, sharp, not screenshot."""
    if asset.get("mediaClass") in _HERO_EXCLUDED_CLASSES:
        return 0.0
    kind = aspect_kind_for_asset(asset)
    if kind in ("portrait", "tall", "square"):
        return 0.0
    w = int(asset.get("width") or 1)
    h = int(asset.get("height") or 1)
    if h <= 0:
        return 0.0
    base = w / h
    if kind == "panorama":
        base *= 1.25
    return base * cover_class_weight(asset.get("mediaClass")) * _quality_multiplier(
        asset, export_layout="web", median_sharp=median_sharp
    )


def pick_cover_asset_id(
    assets: list[dict],
    *,
    export_layout: str = "mobile",
    exclude: set[str] | None = None,
) -> str:
    exclude = exclude or set()
    pool = cover_asset_pool(assets, export_layout=export_layout)
    median_sharp = median_sharpness(pool)
    best_id = ""
    best_score = 0.0
    for a in pool:
        if a["id"] in exclude or a.get("type") == "video":
            continue
        score = cover_score(a, export_layout, median_sharp=median_sharp)
        if score > best_score:
            best_score = score
            best_id = a["id"]
    if best_id:
        return best_id
    for a in assets:
        if a["id"] not in exclude and a.get("type") != "video":
            return a["id"]
    return assets[0]["id"]


def cover_candidates(
    assets: list[dict],
    cover_id: str,
    *,
    export_layout: str = "mobile",
    limit: int = 5,
) -> list[str]:
    """Top covers with diverse aspect / day when possible."""
    pool = cover_asset_pool(assets, export_layout=export_layout)
    median_sharp = median_sharpness(pool)
    scored: list[tuple[float, dict]] = []
    for a in pool:
        if a["id"] == cover_id or a.get("type") == "video":
            continue
        score = cover_score(a, export_layout, median_sharp=median_sharp)
        if score > 0:
            scored.append((score, a))
    scored.sort(key=lambda x: x[0], reverse=True)

    out = [cover_id]
    seen_aspects: set[str] = set()
    seen_days: set[str] = set()
    cover_asset = next((a for a in assets if a["id"] == cover_id), None)
    if cover_asset:
        seen_aspects.add(aspect_kind_for_asset(cover_asset))
        d = parse_asset_date(cover_asset)
        if d:
            seen_days.add(d.isoformat())

    for _, a in scored:
        if len(out) >= limit:
            break
        aspect = aspect_kind_for_asset(a)
        day = parse_asset_date(a)
        day_key = day.isoformat() if day else ""
        if aspect in seen_aspects and day_key in seen_days:
            continue
        out.append(a["id"])
        seen_aspects.add(aspect)
        if day_key:
            seen_days.add(day_key)

    for _, a in scored:
        if len(out) >= limit:
            break
        if a["id"] not in out:
            out.append(a["id"])
    return out[:limit]


def pick_chapter_hero(
    bucket: list[str],
    assets_by_id: dict[str, dict],
    *,
    exclude: set[str] | None = None,
    median_sharp: float = 0.0,
) -> str | None:
    exclude = exclude or set()
    best_id: str | None = None
    best = 0.0
    for aid in bucket:
        if aid in exclude:
            continue
        a = assets_by_id.get(aid)
        if not a:
            continue
        score = hero_score(a, median_sharp=median_sharp)
        if score > best:
            best = score
            best_id = aid
    return best_id


def sort_bucket_asset_ids(bucket: list[str], assets_by_id: dict[str, dict]) -> list[str]:
    """Sort by takenAt; keep burstGroupId contiguous; sharpest first within burst."""
    items = [(aid, assets_by_id.get(aid, {})) for aid in bucket]
    items.sort(key=lambda x: x[1].get("takenAt") or "")

    result: list[str] = []
    i = 0
    while i < len(items):
        aid, a = items[i]
        bg = a.get("burstGroupId")
        if bg:
            group_ids = [aid]
            j = i + 1
            while j < len(items) and items[j][1].get("burstGroupId") == bg:
                group_ids.append(items[j][0])
                j += 1
            group_ids.sort(key=lambda x: -asset_sharpness(assets_by_id.get(x, {})))
            result.extend(group_ids)
            i = j
        else:
            result.append(aid)
            i += 1
    return result
