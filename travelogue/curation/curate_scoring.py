"""Cover / hero scoring and bucket asset ordering for curate."""

from __future__ import annotations

from travelogue.curation.asset_quality import asset_sharpness
from travelogue.curation.composition_signals import (
    mean_thirds_score,
    subject_center_norm as _subject_center_norm,
)
from travelogue.curation.cover_scoring_params import (
    CoverScoringParams,
    resolve_person_demote,
)
from travelogue.curation.cover_scoring_v2 import (
    CoverScoringParamsV2,
    build_cover_explain_v2,
    cover_score_v2,
    hero_score_v2,
    resolve_cover_scoring_version,
    resolve_person_demote_v2,
)
from travelogue.curation.layout_planner import aspect_kind_for_asset
from travelogue.curation.media_classify import cover_class_weight
from travelogue.curation.time_segments import parse_asset_date
from travelogue.media.color_metrics import color_richness_multiplier, dominant_tone_chroma_score

_DEFAULT_COVER_SCORING = CoverScoringParams()


def _cover_params(cover_scoring: CoverScoringParams | None) -> CoverScoringParams:
    return cover_scoring if cover_scoring is not None else _DEFAULT_COVER_SCORING


_DEFAULT_COVER_SCORING_V2 = CoverScoringParamsV2()


def _cover_params_v2(cover_scoring_v2: CoverScoringParamsV2 | None) -> CoverScoringParamsV2:
    return cover_scoring_v2 if cover_scoring_v2 is not None else _DEFAULT_COVER_SCORING_V2


def _resolve_scoring_version(
    *,
    scoring_version: str | None = None,
    cover_scoring_v2: CoverScoringParamsV2 | None = None,
) -> tuple[str, CoverScoringParamsV2]:
    ver = resolve_cover_scoring_version(scoring_version)
    return ver, _cover_params_v2(cover_scoring_v2)

_COVER_EXCLUDED_CLASSES = frozenset({"screenshot", "thumbnail", "reupload"})
_HERO_EXCLUDED_CLASSES = frozenset({"screenshot", "thumbnail", "reupload"})
_MOBILE_COVER_MIN_SHORT_EDGE = 600
_MOBILE_VERTICAL_KINDS = frozenset({"portrait", "tall"})
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
    "aesthetic": "审美评分",
}

_AESTHETIC_MULT_LO = 0.7
_AESTHETIC_MULT_HI = 1.3


def _resolve_aesthetic_enabled(enabled: bool | None) -> bool:
    if enabled is not None:
        return enabled
    try:
        from travelogue.config import get_config

        return get_config().aesthetic.enabled
    except Exception:
        return False


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


def _cover_person_multiplier(asset: dict, *, demote: float) -> float:
    """P5-C2: demote portrait/face-heavy assets for cover."""
    tags = set(asset.get("tags") or [])
    if tags.intersection({"face", "person", "selfie", "portrait"}):
        return demote
    return 1.0


def _cover_face_bbox_multiplier(
    asset: dict,
    *,
    median_sharp: float = 0.0,
    params: CoverScoringParams,
) -> float:
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
    if area < params.face_bbox_min_area or area > params.face_bbox_max_area:
        return 1.0
    sharp = asset_sharpness(asset)
    if median_sharp > 0 and sharp < median_sharp * params.face_bbox_sharp_ratio_min:
        return 1.0
    return params.face_bbox_boost


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


def _cover_rule_of_thirds_multiplier(asset: dict, *, params: CoverScoringParams) -> float:
    """P6-C1 · reward subject near third lines; demote dead-center framing."""
    cx, cy = _subject_center_norm(asset)
    axis = mean_thirds_score(asset)
    center_dist = ((cx - 0.5) ** 2 + (cy - 0.5) ** 2) ** 0.5
    off_center = min(1.0, center_dist / 0.22)
    blend = params.thirds_axis_weight * axis + params.thirds_off_center_weight * off_center
    return params.thirds_base + params.thirds_span * blend


def _cover_composition_multiplier(
    asset: dict,
    export_layout: str,
    *,
    params: CoverScoringParams,
) -> float:
    """P5-C2: landscape/panorama preference (composition proxy)."""
    kind = aspect_kind_for_asset(asset)
    if export_layout == "web":
        if kind == "panorama":
            return params.web_panorama_mult
        if kind == "landscape":
            return params.web_landscape_mult
        return 1.0
    if kind == "tall":
        return params.mobile_tall_mult
    if kind == "portrait":
        return params.mobile_portrait_mult
    return 1.0


def _quality_multiplier(
    asset: dict,
    *,
    export_layout: str,
    median_sharp: float,
    params: CoverScoringParams,
    median_overall: float = 0.0,
    aesthetic_enabled: bool | None = None,
) -> float:
    _ = export_layout
    mult = 1.0
    if asset.get("dateConfidence") == "low":
        mult *= params.date_confidence_low_mult
    sharp = asset_sharpness(asset)
    if median_sharp > 0 and sharp > 0:
        ratio = sharp / median_sharp
        mult *= min(params.sharp_ratio_cap, max(params.sharp_ratio_floor, ratio))
    if _resolve_aesthetic_enabled(aesthetic_enabled):
        from travelogue.curation.aesthetic_score import aesthetic_multiplier

        mult *= aesthetic_multiplier(
            asset,
            median_overall=median_overall,
            enabled=True,
            lo=_AESTHETIC_MULT_LO,
            hi=_AESTHETIC_MULT_HI,
        )
    return mult


def cover_score(
    asset: dict,
    export_layout: str,
    *,
    median_sharp: float = 0.0,
    median_overall: float = 0.0,
    aesthetic_enabled: bool | None = None,
    enable_phase6_cover_factors: bool = True,
    cover_scoring: CoverScoringParams | None = None,
    cover_scoring_v2: CoverScoringParamsV2 | None = None,
    scoring_version: str | None = None,
    pool: list[dict] | None = None,
    person_demote_mult: float | None = None,
) -> float:
    """Mobile: tall/portrait. Web: landscape/panorama. Uses ingest quality signals."""
    ver, params_v2 = _resolve_scoring_version(
        scoring_version=scoring_version,
        cover_scoring_v2=cover_scoring_v2,
    )
    if ver == "v2":
        search_pool = pool if pool else [asset]
        return cover_score_v2(
            asset,
            export_layout,
            pool=search_pool,
            median_sharp=median_sharp,
            median_overall=median_overall,
            aesthetic_enabled=aesthetic_enabled,
            cover_scoring_v2=params_v2,
            person_demote_mult=person_demote_mult,
        )

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

    params = _cover_params(cover_scoring)
    p6 = enable_phase6_cover_factors and params.enable_phase6_factors
    demote = (
        person_demote_mult
        if person_demote_mult is not None
        else params.person_demote
    )
    thirds_mult = _cover_rule_of_thirds_multiplier(asset, params=params) if p6 else 1.0
    return (
        base
        * _cover_media_weight(asset, export_layout)
        * _quality_multiplier(
            asset,
            export_layout=export_layout,
            median_sharp=median_sharp,
            params=params,
            median_overall=median_overall,
            aesthetic_enabled=aesthetic_enabled,
        )
        * _cover_person_multiplier(asset, demote=demote)
        * _cover_face_bbox_multiplier(
            asset, median_sharp=median_sharp, params=params
        )
        * _cover_saturation_multiplier(asset)
        * _cover_composition_multiplier(asset, export_layout, params=params)
        * thirds_mult
    )


def _cover_score_factors(
    asset: dict,
    export_layout: str,
    *,
    median_sharp: float = 0.0,
    median_overall: float = 0.0,
    aesthetic_enabled: bool | None = None,
    cover_scoring: CoverScoringParams | None = None,
    person_demote_mult: float | None = None,
    enable_phase6_cover_factors: bool = True,
) -> list[tuple[str, float]]:
    """Return (factor_code, multiplier) for explain output."""
    params = _cover_params(cover_scoring)
    demote = (
        person_demote_mult
        if person_demote_mult is not None
        else params.person_demote
    )
    if (
        cover_score(
            asset,
            export_layout,
            median_sharp=median_sharp,
            median_overall=median_overall,
            aesthetic_enabled=aesthetic_enabled,
            enable_phase6_cover_factors=enable_phase6_cover_factors,
            cover_scoring=cover_scoring,
            person_demote_mult=demote,
        )
        <= 0
    ):
        return []
    factors: list[tuple[str, float]] = []
    media_w = _cover_media_weight(asset, export_layout)
    if abs(media_w - 1.0) > 0.01:
        factors.append(("aspect", media_w))
    if asset.get("dateConfidence") == "low":
        dc_w = params.date_confidence_low_mult
        if abs(dc_w - 1.0) > 0.01:
            factors.append(("date_confidence", dc_w))
    sharp = asset_sharpness(asset)
    if median_sharp > 0 and sharp > 0:
        sharp_w = min(
            params.sharp_ratio_cap,
            max(params.sharp_ratio_floor, sharp / median_sharp),
        )
        if abs(sharp_w - 1.0) > 0.01:
            factors.append(("sharpness", sharp_w))
    if _resolve_aesthetic_enabled(aesthetic_enabled):
        from travelogue.curation.aesthetic_score import aesthetic_multiplier

        aest_w = aesthetic_multiplier(
            asset,
            median_overall=median_overall,
            enabled=True,
            lo=_AESTHETIC_MULT_LO,
            hi=_AESTHETIC_MULT_HI,
        )
        if abs(aest_w - 1.0) > 0.01:
            factors.append(("aesthetic", aest_w))
    person_w = _cover_person_multiplier(asset, demote=demote)
    if abs(person_w - 1.0) > 0.01:
        factors.append(("person_demote", person_w))
    face_w = _cover_face_bbox_multiplier(
        asset, median_sharp=median_sharp, params=params
    )
    if abs(face_w - 1.0) > 0.01:
        factors.append(("face_bbox", face_w))
    sat_w = _cover_saturation_multiplier(asset)
    if abs(sat_w - 1.0) > 0.01:
        factors.append(("color_richness", sat_w))
    comp_w = _cover_composition_multiplier(asset, export_layout, params=params)
    if abs(comp_w - 1.0) > 0.01:
        code = "landscape_bias" if export_layout == "web" else "portrait_bias"
        factors.append((code, comp_w))
    if enable_phase6_cover_factors and params.enable_phase6_factors:
        thirds_w = _cover_rule_of_thirds_multiplier(asset, params=params)
        if abs(thirds_w - 1.0) > 0.01:
            factors.append(("composition_thirds", thirds_w))
    return factors


def build_cover_explain(
    asset: dict,
    export_layout: str,
    *,
    median_sharp: float = 0.0,
    median_overall: float = 0.0,
    aesthetic_enabled: bool | None = None,
    limit: int = 4,
    cover_scoring: CoverScoringParams | None = None,
    cover_scoring_v2: CoverScoringParamsV2 | None = None,
    scoring_version: str | None = None,
    pool: list[dict] | None = None,
    person_demote_mult: float | None = None,
    enable_phase6_cover_factors: bool = True,
) -> list[dict[str, str | float]]:
    """P6-C3 · top readable reasons for cover score."""
    ver, params_v2 = _resolve_scoring_version(
        scoring_version=scoring_version,
        cover_scoring_v2=cover_scoring_v2,
    )
    if ver == "v2":
        search_pool = pool if pool else [asset]
        return build_cover_explain_v2(
            asset,
            export_layout,
            search_pool,
            params=params_v2,
            person_demote_mult=person_demote_mult,
            aesthetic_enabled=aesthetic_enabled,
            limit=limit,
        )

    factors = _cover_score_factors(
        asset,
        export_layout,
        median_sharp=median_sharp,
        median_overall=median_overall,
        aesthetic_enabled=aesthetic_enabled,
        cover_scoring=cover_scoring,
        person_demote_mult=person_demote_mult,
        enable_phase6_cover_factors=enable_phase6_cover_factors,
    )
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


def hero_score(
    asset: dict,
    *,
    median_sharp: float = 0.0,
    aesthetic_enabled: bool | None = None,
    cover_scoring_v2: CoverScoringParamsV2 | None = None,
    scoring_version: str | None = None,
    pool: list[dict] | None = None,
) -> float:
    """Chapter hero: wide compositions, sharp, not screenshot."""
    ver, params_v2 = _resolve_scoring_version(
        scoring_version=scoring_version,
        cover_scoring_v2=cover_scoring_v2,
    )
    if ver == "v2":
        return hero_score_v2(
            asset,
            pool=pool if pool else [asset],
            median_sharp=median_sharp,
            aesthetic_enabled=aesthetic_enabled,
            cover_scoring_v2=params_v2,
        )

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
    media = cover_class_weight(asset.get("mediaClass"))
    if _resolve_aesthetic_enabled(aesthetic_enabled):
        from travelogue.curation.aesthetic_score import aesthetic_dim, purpose_overall

        overall = purpose_overall(asset, "hero")
        if overall is not None:
            comp = aesthetic_dim(asset, "composition")
            subj = aesthetic_dim(asset, "subjectClarity")
            ae_mult = overall * (comp if comp is not None else 1.0) * (
                subj if subj is not None else 1.0
            )
            return base * media * ae_mult
    return base * media * _quality_multiplier(
        asset,
        export_layout="web",
        median_sharp=median_sharp,
        params=_DEFAULT_COVER_SCORING,
        aesthetic_enabled=False,
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


def _cover_batch_medians(
    pool: list[dict],
    *,
    aesthetic_enabled: bool | None,
) -> tuple[float, float]:
    median_sharp = median_sharpness(pool)
    median_overall = 0.0
    if _resolve_aesthetic_enabled(aesthetic_enabled):
        from travelogue.curation.aesthetic_score import median_aesthetic_overall

        median_overall = median_aesthetic_overall(pool, purpose="cover")
    return median_sharp, median_overall


def effective_cover_score(
    asset: dict,
    export_layout: str,
    *,
    median_sharp: float = 0.0,
    median_overall: float = 0.0,
    aesthetic_enabled: bool | None = None,
    featured_weight: float = 1.35,
    memory_anchors: list[str] | None = None,
    meta_places: list[str] | None = None,
    enable_phase6_cover_factors: bool = True,
    cover_scoring: CoverScoringParams | None = None,
    cover_scoring_v2: CoverScoringParamsV2 | None = None,
    scoring_version: str | None = None,
    pool: list[dict] | None = None,
    person_demote_mult: float | None = None,
) -> float:
    return (
        cover_score(
            asset,
            export_layout,
            median_sharp=median_sharp,
            median_overall=median_overall,
            aesthetic_enabled=aesthetic_enabled,
            enable_phase6_cover_factors=enable_phase6_cover_factors,
            cover_scoring=cover_scoring,
            cover_scoring_v2=cover_scoring_v2,
            scoring_version=scoring_version,
            pool=pool,
            person_demote_mult=person_demote_mult,
        )
        * featured_weight_multiplier(asset, weight=featured_weight)
        * anchor_match_multiplier(asset, memory_anchors, meta_places=meta_places)
    )


def effective_hero_score(
    asset: dict,
    *,
    median_sharp: float = 0.0,
    aesthetic_enabled: bool | None = None,
    featured_weight: float = 1.35,
    memory_anchors: list[str] | None = None,
    meta_places: list[str] | None = None,
    cover_scoring_v2: CoverScoringParamsV2 | None = None,
    scoring_version: str | None = None,
    pool: list[dict] | None = None,
) -> float:
    return (
        hero_score(
            asset,
            median_sharp=median_sharp,
            aesthetic_enabled=aesthetic_enabled,
            cover_scoring_v2=cover_scoring_v2,
            scoring_version=scoring_version,
            pool=pool,
        )
        * featured_weight_multiplier(asset, weight=featured_weight)
        * anchor_match_multiplier(asset, memory_anchors, meta_places=meta_places)
    )


def _curate_scoring_context(
    cover_scoring: CoverScoringParams | None = None,
    cover_scoring_v2: CoverScoringParamsV2 | None = None,
    scoring_version: str | None = None,
) -> tuple[str, CoverScoringParams, CoverScoringParamsV2]:
    ver, params_v2 = _resolve_scoring_version(
        scoring_version=scoring_version,
        cover_scoring_v2=cover_scoring_v2,
    )
    return ver, _cover_params(cover_scoring), params_v2


def pick_cover_asset_id(
    assets: list[dict],
    *,
    export_layout: str = "mobile",
    exclude: set[str] | None = None,
    featured_weight: float = 1.35,
    enable_phase6_cover_factors: bool = True,
    cover_scoring: CoverScoringParams | None = None,
    cover_scoring_v2: CoverScoringParamsV2 | None = None,
    scoring_version: str | None = None,
    aesthetic_enabled: bool | None = None,
) -> str:
    exclude = exclude or set()
    ver, params, params_v2 = _curate_scoring_context(
        cover_scoring, cover_scoring_v2, scoring_version
    )
    p6 = enable_phase6_cover_factors and params.enable_phase6_factors
    pool = cover_asset_pool(assets, export_layout=export_layout)
    featured_pool = [
        a
        for a in pool
        if a.get("userTier") == "featured" and a["id"] not in exclude and a.get("type") != "video"
    ]
    search_pool = featured_pool if featured_pool else pool
    person_demote = (
        resolve_person_demote_v2(params_v2, search_pool)
        if ver == "v2"
        else resolve_person_demote(params, search_pool)
    )
    median_sharp, median_overall = _cover_batch_medians(
        search_pool, aesthetic_enabled=aesthetic_enabled
    )
    best_id = ""
    best_score = 0.0
    for a in search_pool:
        if a["id"] in exclude or a.get("type") == "video":
            continue
        score = effective_cover_score(
            a,
            export_layout,
            median_sharp=median_sharp,
            median_overall=median_overall,
            aesthetic_enabled=aesthetic_enabled,
            featured_weight=featured_weight,
            enable_phase6_cover_factors=p6,
            cover_scoring=params,
            cover_scoring_v2=params_v2,
            scoring_version=ver,
            pool=search_pool,
            person_demote_mult=person_demote,
        )
        if score > best_score:
            best_score = score
            best_id = a["id"]
    if not best_id and featured_pool and export_layout == "web":
        material_pool = [a for a in pool if a.get("userTier") != "featured"]
        if material_pool:
            person_demote = (
                resolve_person_demote_v2(params_v2, material_pool)
                if ver == "v2"
                else resolve_person_demote(params, material_pool)
            )
            median_sharp, median_overall = _cover_batch_medians(
                material_pool, aesthetic_enabled=aesthetic_enabled
            )
            for a in material_pool:
                if a["id"] in exclude or a.get("type") == "video":
                    continue
                score = effective_cover_score(
                    a,
                    export_layout,
                    median_sharp=median_sharp,
                    median_overall=median_overall,
                    aesthetic_enabled=aesthetic_enabled,
                    featured_weight=featured_weight,
                    enable_phase6_cover_factors=p6,
                    cover_scoring=params,
                    cover_scoring_v2=params_v2,
                    scoring_version=ver,
                    pool=material_pool,
                    person_demote_mult=person_demote,
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


def score_ranked_cover_ids(
    assets: list[dict],
    *,
    export_layout: str = "mobile",
    exclude: set[str] | None = None,
    featured_weight: float = 1.35,
    enable_phase6_cover_factors: bool = True,
    cover_scoring: CoverScoringParams | None = None,
    cover_scoring_v2: CoverScoringParamsV2 | None = None,
    scoring_version: str | None = None,
    limit: int = 10,
) -> list[dict[str, object]]:
    """Score-ranked cover list for blind review (PRD scoreRankedTop3)."""
    exclude = exclude or set()
    ver, params, params_v2 = _curate_scoring_context(
        cover_scoring, cover_scoring_v2, scoring_version
    )
    p6 = enable_phase6_cover_factors and params.enable_phase6_factors
    pool = cover_asset_pool(assets, export_layout=export_layout)
    featured_pool = [
        a
        for a in pool
        if a.get("userTier") == "featured" and a["id"] not in exclude and a.get("type") != "video"
    ]
    search_pool = featured_pool if featured_pool else pool
    person_demote = (
        resolve_person_demote_v2(params_v2, search_pool)
        if ver == "v2"
        else resolve_person_demote(params, search_pool)
    )
    median_sharp, median_overall = _cover_batch_medians(
        search_pool, aesthetic_enabled=None
    )
    rows: list[tuple[float, str]] = []
    for a in search_pool:
        aid = a.get("id")
        if not aid or aid in exclude or a.get("type") == "video":
            continue
        score = effective_cover_score(
            a,
            export_layout,
            median_sharp=median_sharp,
            median_overall=median_overall,
            featured_weight=featured_weight,
            enable_phase6_cover_factors=p6,
            cover_scoring=params,
            cover_scoring_v2=params_v2,
            scoring_version=ver,
            pool=search_pool,
            person_demote_mult=person_demote,
        )
        if score > 0:
            rows.append((score, str(aid)))
    rows.sort(key=lambda item: (-item[0], item[1]))
    out: list[dict[str, object]] = []
    for rank, (score, aid) in enumerate(rows[:limit], start=1):
        out.append(
            {
                "rank": rank,
                "assetId": aid,
                "score": round(score, 6),
                "scoringVersion": ver,
            }
        )
    return out


def build_cover_layout_review(
    assets: list[dict],
    cover_id: str,
    *,
    export_layout: str = "mobile",
    featured_weight: float = 1.35,
    enable_phase6_cover_factors: bool = True,
    cover_scoring: CoverScoringParams | None = None,
    cover_scoring_v2: CoverScoringParamsV2 | None = None,
    scoring_version: str | None = None,
) -> dict[str, object]:
    """Snapshot for acceptance: ranked top-N, explain, person-dominant flag."""
    from travelogue.curation.cover_scoring_params import person_tag_ratio

    ver, params, params_v2 = _curate_scoring_context(
        cover_scoring, cover_scoring_v2, scoring_version
    )
    pool = cover_asset_pool(assets, export_layout=export_layout)
    featured_pool = [a for a in pool if a.get("userTier") == "featured"]
    search_pool = featured_pool if featured_pool else pool
    person_demote = (
        resolve_person_demote_v2(params_v2, search_pool)
        if ver == "v2"
        else resolve_person_demote(params, search_pool)
    )
    asset = next((a for a in assets if a.get("id") == cover_id), None)
    ranked = score_ranked_cover_ids(
        assets,
        export_layout=export_layout,
        featured_weight=featured_weight,
        enable_phase6_cover_factors=enable_phase6_cover_factors,
        cover_scoring=cover_scoring,
        cover_scoring_v2=cover_scoring_v2,
        scoring_version=ver,
        limit=10,
    )
    explain: list[dict[str, str | float]] = []
    if asset:
        med_sharp, med_overall = _cover_batch_medians(
            search_pool, aesthetic_enabled=None
        )
        explain = build_cover_explain(
            asset,
            export_layout,
            median_sharp=med_sharp,
            median_overall=med_overall,
            cover_scoring=cover_scoring,
            cover_scoring_v2=params_v2,
            scoring_version=ver,
            pool=search_pool,
            person_demote_mult=person_demote,
            enable_phase6_cover_factors=enable_phase6_cover_factors,
        )
    return {
        "exportLayout": export_layout,
        "scoringVersion": ver,
        "coverAssetId": cover_id,
        "scoreRankedTop3": ranked[:3],
        "scoreRankedTop10": ranked,
        "personTagRatio": round(person_tag_ratio(search_pool), 4),
        "personDemoteApplied": person_demote,
        "featuredPoolOnly": bool(featured_pool),
        "coverExplain": explain,
    }


def cover_candidates(
    assets: list[dict],
    cover_id: str,
    *,
    export_layout: str = "mobile",
    limit: int = 5,
    featured_weight: float = 1.35,
    featured_min: int = 2,
    enable_phase6_cover_factors: bool = True,
    cover_scoring: CoverScoringParams | None = None,
    cover_scoring_v2: CoverScoringParamsV2 | None = None,
    scoring_version: str | None = None,
) -> list[str]:
    """Top covers with diverse aspect / day when possible."""
    ver, params, params_v2 = _curate_scoring_context(
        cover_scoring, cover_scoring_v2, scoring_version
    )
    p6 = enable_phase6_cover_factors and params.enable_phase6_factors
    pool = cover_asset_pool(assets, export_layout=export_layout)
    featured_pool = [a for a in pool if a.get("userTier") == "featured"]
    search_pool = featured_pool if featured_pool else pool
    person_demote = (
        resolve_person_demote_v2(params_v2, search_pool)
        if ver == "v2"
        else resolve_person_demote(params, search_pool)
    )
    median_sharp, median_overall = _cover_batch_medians(pool, aesthetic_enabled=None)
    scored: list[tuple[float, dict]] = []
    for a in pool:
        if a["id"] == cover_id or a.get("type") == "video":
            continue
        score = effective_cover_score(
            a,
            export_layout,
            median_sharp=median_sharp,
            median_overall=median_overall,
            featured_weight=featured_weight,
            enable_phase6_cover_factors=p6,
            cover_scoring=params,
            cover_scoring_v2=params_v2,
            scoring_version=ver,
            pool=pool,
            person_demote_mult=person_demote,
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
        out_set = set(out)
        for fid in featured_ids:
            if need <= 0:
                break
            if fid in out_set or fid == cover_id:
                continue
            if len(out) >= limit:
                # Swap out the lowest-priority tail slot so featured quota is met
                # without leaving the replaced id in the dedup set.
                out_set.discard(out[-1])
                out[-1] = fid
            else:
                out.append(fid)
            out_set.add(fid)
            featured_in_out += 1
            need -= 1
    return out[:limit]


def pick_chapter_hero(
    bucket: list[str],
    assets_by_id: dict[str, dict],
    *,
    exclude: set[str] | None = None,
    median_sharp: float = 0.0,
    aesthetic_enabled: bool | None = None,
    featured_weight: float = 1.35,
    memory_anchors: list[str] | None = None,
    meta_places: list[str] | None = None,
    cover_scoring_v2: CoverScoringParamsV2 | None = None,
    scoring_version: str | None = None,
) -> str | None:
    exclude = exclude or set()
    ver, _, params_v2 = _curate_scoring_context(None, cover_scoring_v2, scoring_version)
    hero_pool = [assets_by_id[aid] for aid in bucket if aid in assets_by_id]
    best_id: str | None = None
    best_key: tuple[float, float] = (-1.0, -1.0)
    for aid in bucket:
        if aid in exclude:
            continue
        a = assets_by_id.get(aid)
        if not a:
            continue
        score = effective_hero_score(
            a,
            median_sharp=median_sharp,
            aesthetic_enabled=aesthetic_enabled,
            featured_weight=featured_weight,
            memory_anchors=memory_anchors,
            meta_places=meta_places,
            cover_scoring_v2=params_v2,
            scoring_version=ver,
            pool=hero_pool,
        )
        key = (score, asset_sharpness(a))
        if key > best_key:
            best_key = key
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
