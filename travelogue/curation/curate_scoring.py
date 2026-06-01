"""Cover / hero scoring and bucket asset ordering for curate."""

from __future__ import annotations

from travelogue.curation.asset_quality import asset_sharpness
from travelogue.curation.layout_planner import aspect_kind_for_asset
from travelogue.curation.media_classify import cover_class_weight
from travelogue.curation.time_segments import parse_asset_date
from travelogue.media.color_metrics import color_richness_multiplier, dominant_tone_chroma_score

_COVER_EXCLUDED_CLASSES = frozenset({"screenshot", "thumbnail", "reupload"})
_HERO_EXCLUDED_CLASSES = frozenset({"screenshot", "thumbnail", "reupload"})
_MOBILE_COVER_MIN_SHORT_EDGE = 600
_MOBILE_VERTICAL_KINDS = frozenset({"portrait", "tall"})
_THIRD_LINES = (1.0 / 3.0, 2.0 / 3.0)

_COVER_FACTOR_LABELS: dict[str, str] = {
    "aspect": "画幅比例",
    "face_bbox": "人脸构图",
    "sharpness": "清晰度",
    "saturation": "色彩饱和度",
    "color_richness": "色彩丰富度",
    "composition_thirds": "三分法构图",
    "landscape_bias": "横图偏好",
    "portrait_bias": "竖图偏好",
    "person_demote": "人像降权",
    "featured": "精选加权",
    "anchor": "行程锚点",
    "date_confidence": "日期置信",
}


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


def _cover_person_multiplier(asset: dict) -> float:
    """P5-C2: demote portrait/face-heavy assets for cover."""
    tags = set(asset.get("tags") or [])
    if tags.intersection({"face", "person", "selfie", "portrait"}):
        return 0.72
    return 1.0


def _cover_face_bbox_multiplier(asset: dict, *, median_sharp: float = 0.0) -> float:
    """M12-2d · modest boost when ingest face bbox + sharpness support cover quality."""
    tags = set(asset.get("tags") or [])
    if not tags.intersection({"face", "person"}):
        return 1.0
    if tags.intersection({"selfie", "portrait"}):
        return 1.0
    box = asset.get("salientBox")
    if not isinstance(box, dict):
        return 1.0
    area = float(box.get("w", 0)) * float(box.get("h", 0))
    if area < 0.02 or area > 0.38:
        return 1.0
    sharp = asset_sharpness(asset)
    if median_sharp > 0 and sharp < median_sharp * 0.85:
        return 1.0
    return 1.06


def _cover_saturation_multiplier(asset: dict) -> float:
    tone = asset.get("dominantTone")
    if not tone and isinstance(asset.get("color"), dict):
        tone = asset["color"].get("dominantTone")
    mean_luma = asset.get("meanLuma")
    if mean_luma is None and isinstance(asset.get("color"), dict):
        raw_luma = asset["color"].get("meanLuma")
        mean_luma = float(raw_luma) if raw_luma is not None else None
    return color_richness_multiplier(
        hex_color=tone if isinstance(tone, str) and tone.startswith("#") else None,
        mean_luma=float(mean_luma) if mean_luma is not None else None,
    )


def _subject_center_norm(asset: dict) -> tuple[float, float]:
    box = asset.get("salientBox")
    if isinstance(box, dict):
        x = float(box.get("x", 0.5))
        y = float(box.get("y", 0.5))
        w = float(box.get("w", 0.0))
        h = float(box.get("h", 0.0))
        return (
            min(1.0, max(0.0, x + w / 2.0)),
            min(1.0, max(0.0, y + h / 2.0)),
        )
    fp = asset.get("focalPoint") or {}
    return float(fp.get("x", 0.5)), float(fp.get("y", 0.45))


def _nearest_third_distance(coord: float) -> float:
    return min(abs(coord - line) for line in _THIRD_LINES)


def _axis_rule_of_thirds_score(coord: float) -> float:
    dist = _nearest_third_distance(coord)
    return max(0.0, 1.0 - dist / 0.25)


def _cover_rule_of_thirds_multiplier(asset: dict) -> float:
    """P6-C1 · reward subject near third lines; demote dead-center framing."""
    cx, cy = _subject_center_norm(asset)
    axis = (_axis_rule_of_thirds_score(cx) + _axis_rule_of_thirds_score(cy)) / 2.0
    center_dist = ((cx - 0.5) ** 2 + (cy - 0.5) ** 2) ** 0.5
    off_center = min(1.0, center_dist / 0.22)
    blend = 0.55 * axis + 0.45 * off_center
    return 0.88 + 0.12 * blend


def _cover_composition_multiplier(asset: dict, export_layout: str) -> float:
    """P5-C2: landscape/panorama preference (composition proxy)."""
    kind = aspect_kind_for_asset(asset)
    if export_layout == "web":
        if kind == "panorama":
            return 1.1
        if kind == "landscape":
            return 1.06
        return 1.0
    if kind == "tall":
        return 0.92
    if kind == "portrait":
        return 0.96
    return 1.0


def _quality_multiplier(asset: dict, *, export_layout: str, median_sharp: float) -> float:
    mult = 1.0
    if asset.get("dateConfidence") == "low":
        mult *= 0.65
    sharp = asset_sharpness(asset)
    if median_sharp > 0 and sharp > 0:
        ratio = sharp / median_sharp
        mult *= min(1.25, max(0.35, ratio))
    return mult


def cover_score(
    asset: dict,
    export_layout: str,
    *,
    median_sharp: float = 0.0,
    enable_phase6_cover_factors: bool = True,
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

    thirds_mult = (
        _cover_rule_of_thirds_multiplier(asset) if enable_phase6_cover_factors else 1.0
    )
    return (
        base
        * _cover_media_weight(asset, export_layout)
        * _quality_multiplier(asset, export_layout=export_layout, median_sharp=median_sharp)
        * _cover_person_multiplier(asset)
        * _cover_face_bbox_multiplier(asset, median_sharp=median_sharp)
        * _cover_saturation_multiplier(asset)
        * _cover_composition_multiplier(asset, export_layout)
        * thirds_mult
    )


def _cover_score_factors(
    asset: dict,
    export_layout: str,
    *,
    median_sharp: float = 0.0,
) -> list[tuple[str, float]]:
    """Return (factor_code, multiplier) for explain output."""
    if cover_score(asset, export_layout, median_sharp=median_sharp) <= 0:
        return []
    factors: list[tuple[str, float]] = []
    media_w = _cover_media_weight(asset, export_layout)
    if abs(media_w - 1.0) > 0.01:
        factors.append(("aspect", media_w))
    quality_w = _quality_multiplier(asset, export_layout=export_layout, median_sharp=median_sharp)
    if abs(quality_w - 1.0) > 0.01:
        factors.append(("sharpness" if median_sharp > 0 else "date_confidence", quality_w))
    person_w = _cover_person_multiplier(asset)
    if abs(person_w - 1.0) > 0.01:
        factors.append(("person_demote", person_w))
    face_w = _cover_face_bbox_multiplier(asset, median_sharp=median_sharp)
    if abs(face_w - 1.0) > 0.01:
        factors.append(("face_bbox", face_w))
    sat_w = _cover_saturation_multiplier(asset)
    if abs(sat_w - 1.0) > 0.01:
        factors.append(("color_richness", sat_w))
    comp_w = _cover_composition_multiplier(asset, export_layout)
    if abs(comp_w - 1.0) > 0.01:
        code = "landscape_bias" if export_layout == "web" else "portrait_bias"
        factors.append((code, comp_w))
    thirds_w = _cover_rule_of_thirds_multiplier(asset)
    if abs(thirds_w - 1.0) > 0.01:
        factors.append(("composition_thirds", thirds_w))
    return factors


def build_cover_explain(
    asset: dict,
    export_layout: str,
    *,
    median_sharp: float = 0.0,
    limit: int = 4,
) -> list[dict[str, str | float]]:
    """P6-C3 · top readable reasons for cover score."""
    factors = _cover_score_factors(asset, export_layout, median_sharp=median_sharp)
    ranked = sorted(factors, key=lambda item: abs(item[1] - 1.0), reverse=True)
    out: list[dict[str, str | float]] = []
    for code, mult in ranked[:limit]:
        label = _COVER_FACTOR_LABELS.get(code, code)
        direction = "提升" if mult > 1.0 else "降低"
        out.append(
            {
                "code": code,
                "label": label,
                "multiplier": round(mult, 3),
                "reason": f"{label}{direction}封面优先级",
            }
        )
    return out


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


def featured_weight_multiplier(asset: dict, *, weight: float = 1.35) -> float:
    if asset.get("userTier") == "featured":
        return weight
    return 1.0


def anchor_match_multiplier(
    asset: dict,
    anchors: list[str] | None,
    *,
    meta_places: list[str] | None = None,
) -> float:
    """+5% when asset tags / place fields hit a memory anchor substring (M19)."""
    if not anchors:
        return 1.0
    parts: list[str] = []
    parts.extend(str(t) for t in (asset.get("tags") or []))
    for key in ("place", "location", "city", "placeName"):
        value = asset.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    if meta_places:
        parts.extend(str(p) for p in meta_places if p)
    haystack = " ".join(parts).casefold()
    if not haystack:
        return 1.0
    for anchor in anchors:
        needle = str(anchor).strip().casefold()
        if len(needle) >= 1 and needle in haystack:
            from travelogue.curation.intent_hints import ANCHOR_MATCH_MULTIPLIER

            return ANCHOR_MATCH_MULTIPLIER
    return 1.0


def featured_eligible(assets: list[dict]) -> list[dict]:
    return [a for a in assets if a.get("userTier") == "featured"]


def effective_cover_score(
    asset: dict,
    export_layout: str,
    *,
    median_sharp: float = 0.0,
    featured_weight: float = 1.35,
    memory_anchors: list[str] | None = None,
    meta_places: list[str] | None = None,
    enable_phase6_cover_factors: bool = True,
) -> float:
    return (
        cover_score(
            asset,
            export_layout,
            median_sharp=median_sharp,
            enable_phase6_cover_factors=enable_phase6_cover_factors,
        )
        * featured_weight_multiplier(asset, weight=featured_weight)
        * anchor_match_multiplier(asset, memory_anchors, meta_places=meta_places)
    )


def effective_hero_score(
    asset: dict,
    *,
    median_sharp: float = 0.0,
    featured_weight: float = 1.35,
    memory_anchors: list[str] | None = None,
    meta_places: list[str] | None = None,
) -> float:
    return (
        hero_score(asset, median_sharp=median_sharp)
        * featured_weight_multiplier(asset, weight=featured_weight)
        * anchor_match_multiplier(asset, memory_anchors, meta_places=meta_places)
    )


def pick_cover_asset_id(
    assets: list[dict],
    *,
    export_layout: str = "mobile",
    exclude: set[str] | None = None,
    featured_weight: float = 1.35,
    enable_phase6_cover_factors: bool = True,
) -> str:
    exclude = exclude or set()
    pool = cover_asset_pool(assets, export_layout=export_layout)
    featured_pool = [
        a
        for a in pool
        if a.get("userTier") == "featured" and a["id"] not in exclude and a.get("type") != "video"
    ]
    search_pool = featured_pool if featured_pool else pool
    median_sharp = median_sharpness(search_pool)
    best_id = ""
    best_score = 0.0
    for a in search_pool:
        if a["id"] in exclude or a.get("type") == "video":
            continue
        score = effective_cover_score(
            a,
            export_layout,
            median_sharp=median_sharp,
            featured_weight=featured_weight,
            enable_phase6_cover_factors=enable_phase6_cover_factors,
        )
        if score > best_score:
            best_score = score
            best_id = a["id"]
    if not best_id and featured_pool and export_layout == "web":
        material_pool = [a for a in pool if a.get("userTier") != "featured"]
        if material_pool:
            median_sharp = median_sharpness(material_pool)
            for a in material_pool:
                if a["id"] in exclude or a.get("type") == "video":
                    continue
                score = effective_cover_score(
                    a,
                    export_layout,
                    median_sharp=median_sharp,
                    featured_weight=featured_weight,
                    enable_phase6_cover_factors=enable_phase6_cover_factors,
                )
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
    featured_weight: float = 1.35,
    featured_min: int = 2,
    enable_phase6_cover_factors: bool = True,
) -> list[str]:
    """Top covers with diverse aspect / day when possible."""
    pool = cover_asset_pool(assets, export_layout=export_layout)
    median_sharp = median_sharpness(pool)
    scored: list[tuple[float, dict]] = []
    for a in pool:
        if a["id"] == cover_id or a.get("type") == "video":
            continue
        score = effective_cover_score(
            a,
            export_layout,
            median_sharp=median_sharp,
            featured_weight=featured_weight,
            enable_phase6_cover_factors=enable_phase6_cover_factors,
        )
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

    featured_in_out = 1 if (cover_asset and cover_asset.get("userTier") == "featured") else 0

    for _, a in scored:
        if len(out) >= limit:
            break
        aspect = aspect_kind_for_asset(a)
        day = parse_asset_date(a)
        day_key = day.isoformat() if day else ""
        if aspect in seen_aspects and day_key in seen_days:
            continue
        out.append(a["id"])
        if a.get("userTier") == "featured":
            featured_in_out += 1
        seen_aspects.add(aspect)
        if day_key:
            seen_days.add(day_key)

    for _, a in scored:
        if len(out) >= limit:
            break
        if a["id"] not in out:
            out.append(a["id"])
            if a.get("userTier") == "featured":
                featured_in_out += 1

    if featured_min > 0:
        featured_ids = [a["id"] for _, a in scored if a.get("userTier") == "featured"]
        need = featured_min - featured_in_out
        for fid in featured_ids:
            if need <= 0 or len(out) >= limit:
                break
            if fid not in out and fid != cover_id:
                if len(out) >= limit:
                    out[-1] = fid
                else:
                    out.append(fid)
                need -= 1
    return out[:limit]


def pick_chapter_hero(
    bucket: list[str],
    assets_by_id: dict[str, dict],
    *,
    exclude: set[str] | None = None,
    median_sharp: float = 0.0,
    featured_weight: float = 1.35,
    memory_anchors: list[str] | None = None,
    meta_places: list[str] | None = None,
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
        score = effective_hero_score(
            a,
            median_sharp=median_sharp,
            featured_weight=featured_weight,
            memory_anchors=memory_anchors,
            meta_places=meta_places,
        )
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


def build_user_tier_curation(
    trip: dict,
    layout_assets: list[dict],
    *,
    cover_by_layout: dict[str, str] | None,
    chapter_heroes: dict[str, str],
    featured_weight: float = 1.35,
    warn_featured_above: int = 30,
) -> tuple[dict, list[str]]:
    """Write curation.userTierSummary and related fields; return extra warnings."""
    from travelogue.media.user_tier import count_user_tiers

    warnings: list[str] = []
    all_assets = trip.get("assets") or []
    counts = count_user_tiers(all_assets)
    if counts["featured"] == 0:
        return {}, warnings

    layout_featured = sum(1 for a in layout_assets if a.get("userTier") == "featured")
    fields: dict = {
        "userTierSummary": {
            "featured": counts["featured"],
            "material": counts["material"],
            "featuredInLayout": layout_featured,
        },
        "featuredHeroByChapter": dict(chapter_heroes),
    }

    featured_cover_pool: list[str] = []
    for layout in ("mobile", "web"):
        pool = cover_asset_pool(layout_assets, export_layout=layout)
        for asset in pool:
            if asset.get("userTier") != "featured":
                continue
            if effective_cover_score(asset, layout, featured_weight=featured_weight) <= 0:
                continue
            if asset["id"] not in featured_cover_pool:
                featured_cover_pool.append(asset["id"])
    if featured_cover_pool:
        fields["featuredCoverPool"] = featured_cover_pool

    if counts["featured"] > warn_featured_above:
        warnings.append(
            f"精选照片 {counts['featured']} 张，超过建议上限 {warn_featured_above}"
        )

    web_cover = (cover_by_layout or {}).get("web") if isinstance(cover_by_layout, dict) else None
    if web_cover:
        cover_asset = next((a for a in layout_assets if a.get("id") == web_cover), None)
        featured_web = [a for a in layout_assets if a.get("userTier") == "featured"]
        if featured_web and cover_asset and cover_asset.get("userTier") != "featured":
            if not any(effective_cover_score(a, "web", featured_weight=featured_weight) > 0 for a in featured_web):
                warnings.append("精选均为竖图，Web 封面已回退到素材横图")

    return fields, warnings
