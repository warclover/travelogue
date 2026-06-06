"""Cover / hero additive logit scoring (Algorithm V2 · PRD-ALGORITHM-OPTIMIZATION-V2)."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from travelogue.curation.asset_quality import normalized_sharpness
from travelogue.curation.composition_signals import mean_thirds_score
from travelogue.curation.cover_scoring_params import (
    CoverScoringParams,
    asset_has_person_tag,
    person_tag_ratio,
)
from travelogue.curation.layout_planner import aspect_kind_for_asset
from travelogue.curation.media_classify import cover_class_weight
from travelogue.media.color_metrics import color_richness_multiplier

_PERSON_TAGS = frozenset({"face", "person", "selfie", "portrait"})
_FEATURE_LABELS: dict[str, str] = {
    "layout_fit": "画幅适配",
    "media": "媒体类型",
    "sharpness": "清晰度",
    "color": "色彩丰富度",
    "thirds": "三分法构图",
    "person": "人像偏好",
    "face_bbox": "人脸构图",
    "date_confidence": "日期置信",
    "aesthetic": "审美评分",
}


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


@dataclass(frozen=True)
class CoverScoringWeightsV2:
    layout_fit: float = 0.23
    media: float = 0.05
    sharpness: float = 0.25
    color: float = 0.12
    thirds: float = 0.15
    person: float = 0.10
    face_bbox: float = 0.05
    date_confidence: float = 0.05
    aesthetic: float = 0.18

    def normalized(self, *, aesthetic_enabled: bool = False) -> CoverScoringWeightsV2:
        w = self
        if aesthetic_enabled and w.sharpness > 0.12:
            w = CoverScoringWeightsV2(
                layout_fit=w.layout_fit,
                media=w.media,
                sharpness=0.12,
                color=w.color,
                thirds=w.thirds,
                person=w.person,
                face_bbox=w.face_bbox,
                date_confidence=w.date_confidence,
                aesthetic=w.aesthetic,
            )
        total = (
            w.layout_fit
            + w.media
            + w.sharpness
            + w.color
            + w.thirds
            + w.person
            + w.face_bbox
            + w.date_confidence
            + (w.aesthetic if aesthetic_enabled else 0.0)
        )
        if total <= 1e-9:
            return w

        def div(v: float) -> float:
            return v / total

        return CoverScoringWeightsV2(
            layout_fit=div(w.layout_fit),
            media=div(w.media),
            sharpness=div(w.sharpness),
            color=div(w.color),
            thirds=div(w.thirds),
            person=div(w.person),
            face_bbox=div(w.face_bbox),
            date_confidence=div(w.date_confidence),
            aesthetic=div(w.aesthetic) if aesthetic_enabled else 0.0,
        )


@dataclass(frozen=True)
class CoverScoringParamsV2:
    """Additive logit parameters; defaults from PRD v2.0.0-rc."""

    bias_mobile: float = 0.0
    bias_web: float = 0.0
    weights: CoverScoringWeightsV2 = field(default_factory=CoverScoringWeightsV2)
    person_demote_penalty: float = 0.28
    person_demote_portrait_trip_penalty: float = 0.0
    person_dominant_tag_ratio: float = 0.40
    face_bbox_boost: float = 0.06
    face_bbox_min_area: float = 0.02
    face_bbox_max_area: float = 0.38
    face_bbox_sharp_ratio_min: float = 0.85
    panorama_aspect_cap: float = 0.90
    mobile_aspect_cap: float = 0.95
    aspect_sigma: float = 0.15
    web_landscape_target: float = 16 / 9
    enable_thirds: bool = True
    v1_params: CoverScoringParams = field(default_factory=CoverScoringParams)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any] | None) -> CoverScoringParamsV2:
        if not raw:
            return cls()
        weights_raw = raw.get("weights") or {}
        defaults = CoverScoringWeightsV2()
        weights = CoverScoringWeightsV2(
            layout_fit=float(weights_raw.get("layout_fit", defaults.layout_fit)),
            media=float(weights_raw.get("media", defaults.media)),
            sharpness=float(
                weights_raw.get("sharpness", weights_raw.get("sharpness", defaults.sharpness))
            ),
            color=float(weights_raw.get("color", defaults.color)),
            thirds=float(weights_raw.get("thirds", defaults.thirds)),
            person=float(weights_raw.get("person", defaults.person)),
            face_bbox=float(weights_raw.get("face_bbox", weights_raw.get("faceBbox", defaults.face_bbox))),
            date_confidence=float(
                weights_raw.get(
                    "date_confidence",
                    weights_raw.get("dateConfidence", defaults.date_confidence),
                )
            ),
            aesthetic=float(weights_raw.get("aesthetic", defaults.aesthetic)),
        )
        v1 = CoverScoringParams.from_mapping(raw.get("v1_compat") or raw.get("v1Compat"))
        return cls(
            bias_mobile=float(raw.get("bias_mobile", raw.get("biasMobile", 0.0))),
            bias_web=float(raw.get("bias_web", raw.get("biasWeb", 0.0))),
            weights=weights,
            person_demote_penalty=float(
                raw.get(
                    "person_demote_penalty",
                    raw.get("personDemotePenalty", 0.28),
                )
            ),
            person_demote_portrait_trip_penalty=float(
                raw.get(
                    "person_demote_portrait_trip_penalty",
                    raw.get("personDemotePortraitTripPenalty", 0.0),
                )
            ),
            person_dominant_tag_ratio=float(
                raw.get(
                    "person_dominant_tag_ratio",
                    raw.get("personDominantTagRatio", 0.40),
                )
            ),
            face_bbox_boost=float(
                raw.get("face_bbox_boost", raw.get("faceBboxBoost", 0.06))
            ),
            face_bbox_min_area=float(
                raw.get("face_bbox_min_area", raw.get("faceBboxMinArea", 0.02))
            ),
            face_bbox_max_area=float(
                raw.get("face_bbox_max_area", raw.get("faceBboxMaxArea", 0.38))
            ),
            face_bbox_sharp_ratio_min=float(
                raw.get(
                    "face_bbox_sharp_ratio_min",
                    raw.get("faceBboxSharpRatioMin", 0.85),
                )
            ),
            panorama_aspect_cap=float(
                raw.get("panorama_aspect_cap", raw.get("panoramaAspectCap", 0.90))
            ),
            mobile_aspect_cap=float(
                raw.get("mobile_aspect_cap", raw.get("mobileAspectCap", 0.95))
            ),
            aspect_sigma=float(raw.get("aspect_sigma", raw.get("aspectSigma", 0.15))),
            enable_thirds=bool(raw.get("enable_thirds", raw.get("enableThirds", True))),
            v1_params=v1,
        )


def resolve_cover_scoring_version(explicit: str | None = None) -> str:
    if explicit in ("v1", "v2"):
        return explicit
    try:
        from travelogue.config import get_config

        ver = getattr(get_config().curate, "cover_scoring_version", "v2")
        return ver if ver in ("v1", "v2") else "v2"
    except Exception:
        return "v1"


def _layout_fit_feature(
    asset: dict,
    export_layout: str,
    *,
    params: CoverScoringParamsV2,
) -> float:
    """Bounded layout preference (aspect + composition bias merged)."""
    kind = aspect_kind_for_asset(asset)
    w = int(asset.get("width") or 1)
    h = int(asset.get("height") or 1)
    if w <= 0 or h <= 0:
        return 0.0

    aspect_part = 0.0
    if export_layout == "web":
        if kind in ("portrait", "tall", "square"):
            return 0.0
        ratio = w / h
        if kind == "panorama":
            flat = _sigmoid((ratio - 2.2) / max(params.aspect_sigma, 1e-6))
            aspect_part = min(params.panorama_aspect_cap, 0.75 + 0.15 * flat)
        elif kind == "landscape":
            dist = abs(ratio - params.web_landscape_target)
            aspect_part = _sigmoid(-dist / max(params.aspect_sigma, 1e-6))
        else:
            aspect_part = 0.5
        v1 = params.v1_params
        if kind == "panorama":
            bias = v1.web_panorama_mult
        elif kind == "landscape":
            bias = v1.web_landscape_mult
        else:
            bias = 1.0
    else:
        if kind in ("landscape", "panorama", "square"):
            return 0.0
        ratio = h / w
        aspect_part = min(
            params.mobile_aspect_cap,
            _sigmoid((ratio - 1.0) / max(params.aspect_sigma, 1e-6)),
        )
        v1 = params.v1_params
        if kind == "tall":
            bias = v1.mobile_tall_mult
        elif kind == "portrait":
            bias = v1.mobile_portrait_mult
        else:
            bias = 1.0

    bias_part = max(0.0, min(1.0, (bias - 0.9) / 0.2))
    return max(0.0, min(1.0, 0.65 * aspect_part + 0.35 * bias_part))


def _media_feature(asset: dict, export_layout: str) -> float:
    weight = cover_class_weight(asset.get("mediaClass"))
    if export_layout == "mobile" and asset.get("mediaClass") == "thumbnail":
        if aspect_kind_for_asset(asset) in ("portrait", "tall"):
            weight = max(weight, 0.8)
    return max(0.0, min(1.0, weight))


def _color_feature(asset: dict) -> float:
    tone = asset.get("dominantTone")
    if not tone and isinstance(asset.get("color"), dict):
        tone = asset["color"].get("dominantTone")
    mean_luma = asset.get("meanLuma")
    if mean_luma is None and isinstance(asset.get("color"), dict):
        raw_luma = asset["color"].get("meanLuma")
        mean_luma = float(raw_luma) if raw_luma is not None else None
    mult = color_richness_multiplier(
        hex_color=tone if isinstance(tone, str) and tone.startswith("#") else None,
        mean_luma=float(mean_luma) if mean_luma is not None else None,
    )
    return max(0.0, min(1.0, (mult - 0.75) / 0.45))


def _thirds_feature(asset: dict, *, params: CoverScoringParamsV2) -> float:
    if not params.enable_thirds:
        return 0.5
    v1 = params.v1_params
    cx, cy = _subject_center(asset)
    center_dist = ((cx - 0.5) ** 2 + (cy - 0.5) ** 2) ** 0.5
    off_center = min(1.0, center_dist / 0.22)
    blend = v1.thirds_axis_weight * mean_thirds_score(asset) + v1.thirds_off_center_weight * off_center
    mult = v1.thirds_base + v1.thirds_span * blend
    return max(0.0, min(1.0, (mult - v1.thirds_base) / max(v1.thirds_span, 1e-6)))


def _subject_center(asset: dict) -> tuple[float, float]:
    from travelogue.curation.composition_signals import subject_center_norm

    return subject_center_norm(asset)


def _person_feature(
    asset: dict,
    pool: list[dict],
    *,
    params: CoverScoringParamsV2,
    person_demote_mult: float | None = None,
) -> float:
    if not asset_has_person_tag(asset):
        return 1.0
    if person_demote_mult is not None:
        penalty = max(0.0, 1.0 - person_demote_mult)
    elif person_tag_ratio(pool) >= params.person_dominant_tag_ratio:
        penalty = params.person_demote_portrait_trip_penalty
    else:
        penalty = params.person_demote_penalty
    return max(0.0, 1.0 - penalty)


def _face_bbox_feature(
    asset: dict,
    pool: list[dict],
    *,
    params: CoverScoringParamsV2,
) -> float:
    tags = set(asset.get("tags") or [])
    if not tags.intersection({"face", "person"}):
        return 0.0
    if tags.intersection({"selfie", "portrait"}):
        return 0.0
    box = asset.get("salientBox")
    if not isinstance(box, dict):
        return 0.0
    area = float(box.get("w", 0)) * float(box.get("h", 0))
    if area < params.face_bbox_min_area or area > params.face_bbox_max_area:
        return 0.0
    sharp_feat = normalized_sharpness(asset, pool, bucket_by="mediaClass")
    if sharp_feat < params.face_bbox_sharp_ratio_min * 0.5:
        return 0.0
    return max(0.0, min(1.0, params.face_bbox_boost / 0.10))


def _date_confidence_feature(asset: dict) -> float:
    return 0.0 if asset.get("dateConfidence") == "low" else 1.0


def _aesthetic_feature(asset: dict, pool: list[dict]) -> float:
    from travelogue.curation.aesthetic_score import purpose_overall

    overall = purpose_overall(asset, "cover")
    if overall is None:
        return 0.5
    return max(0.0, min(1.0, float(overall)))


def _resolve_aesthetic_enabled(enabled: bool | None) -> bool:
    if enabled is not None:
        return enabled
    try:
        from travelogue.config import get_config

        return get_config().aesthetic.enabled
    except Exception:
        return False


def extract_cover_features(
    asset: dict,
    export_layout: str,
    pool: list[dict],
    *,
    params: CoverScoringParamsV2 | None = None,
    person_demote_mult: float | None = None,
    aesthetic_enabled: bool | None = None,
) -> dict[str, float]:
    """Normalized feature vector for cover / hero logit scoring."""
    p = params or CoverScoringParamsV2()
    kind = aspect_kind_for_asset(asset)
    if kind == "square":
        return {}
    if export_layout == "web" and kind in ("portrait", "tall"):
        return {}
    if export_layout != "web" and kind in ("landscape", "panorama"):
        return {}

    features: dict[str, float] = {
        "layout_fit": _layout_fit_feature(asset, export_layout, params=p),
        "media": _media_feature(asset, export_layout),
        "sharpness": normalized_sharpness(asset, pool, bucket_by="mediaClass"),
        "color": _color_feature(asset),
        "thirds": _thirds_feature(asset, params=p),
        "person": _person_feature(
            asset, pool, params=p, person_demote_mult=person_demote_mult
        ),
        "face_bbox": _face_bbox_feature(asset, pool, params=p),
        "date_confidence": _date_confidence_feature(asset),
    }
    if _resolve_aesthetic_enabled(aesthetic_enabled):
        features["aesthetic"] = _aesthetic_feature(asset, pool)
    return features


def cover_logit_v2(
    asset: dict,
    export_layout: str,
    pool: list[dict],
    *,
    params: CoverScoringParamsV2 | None = None,
    person_demote_mult: float | None = None,
    aesthetic_enabled: bool | None = None,
) -> float:
    p = params or CoverScoringParamsV2()
    features = extract_cover_features(
        asset,
        export_layout,
        pool,
        params=p,
        person_demote_mult=person_demote_mult,
        aesthetic_enabled=aesthetic_enabled,
    )
    if not features:
        return float("-inf")

    aest_on = _resolve_aesthetic_enabled(aesthetic_enabled)
    weights = p.weights.normalized(aesthetic_enabled=aest_on)
    bias = p.bias_web if export_layout == "web" else p.bias_mobile

    logit = bias
    for key, feat in features.items():
        w = getattr(weights, key, 0.0)
        if key == "date_confidence" and feat < 0.5:
            logit -= w * (1.0 - feat)
        elif key == "person" and feat < 1.0:
            logit -= w * (1.0 - feat)
        else:
            logit += w * feat
    return logit


def cover_score_v2(
    asset: dict,
    export_layout: str,
    *,
    pool: list[dict] | None = None,
    median_sharp: float = 0.0,
    median_overall: float = 0.0,
    aesthetic_enabled: bool | None = None,
    cover_scoring_v2: CoverScoringParamsV2 | None = None,
    person_demote_mult: float | None = None,
    **_ignored: object,
) -> float:
    """Additive logit cover score; returns exp(logit) for display compatibility."""
    del median_sharp, median_overall
    p = cover_scoring_v2 or CoverScoringParamsV2()
    search_pool = pool or [asset]
    logit = cover_logit_v2(
        asset,
        export_layout,
        search_pool,
        params=p,
        person_demote_mult=person_demote_mult,
        aesthetic_enabled=aesthetic_enabled,
    )
    if logit == float("-inf"):
        return 0.0
    return math.exp(logit)


def hero_logit_v2(
    asset: dict,
    pool: list[dict],
    *,
    params: CoverScoringParamsV2 | None = None,
    aesthetic_enabled: bool | None = None,
) -> float:
    p = params or CoverScoringParamsV2()
    hero_weights = CoverScoringWeightsV2(
        layout_fit=0.28,
        media=p.weights.media,
        sharpness=p.weights.sharpness,
        color=p.weights.color * 0.8,
        thirds=p.weights.thirds,
        person=0.0,
        face_bbox=0.0,
        date_confidence=p.weights.date_confidence,
        aesthetic=max(p.weights.aesthetic, 0.15),
    )
    hero_params = CoverScoringParamsV2(
        bias_web=p.bias_web + 0.05,
        weights=hero_weights,
        person_demote_penalty=0.0,
        v1_params=p.v1_params,
        enable_thirds=p.enable_thirds,
    )
    return cover_logit_v2(
        asset,
        "web",
        pool,
        params=hero_params,
        aesthetic_enabled=aesthetic_enabled,
    )


def hero_score_v2(
    asset: dict,
    *,
    pool: list[dict] | None = None,
    median_sharp: float = 0.0,
    aesthetic_enabled: bool | None = None,
    cover_scoring_v2: CoverScoringParamsV2 | None = None,
    **_ignored: object,
) -> float:
    del median_sharp
    if asset.get("mediaClass") in ("screenshot", "thumbnail", "reupload"):
        return 0.0
    kind = aspect_kind_for_asset(asset)
    if kind in ("portrait", "tall", "square"):
        return 0.0
    search_pool = pool or [asset]
    logit = hero_logit_v2(
        asset,
        search_pool,
        params=cover_scoring_v2,
        aesthetic_enabled=aesthetic_enabled,
    )
    if logit == float("-inf"):
        return 0.0
    return math.exp(logit)


def build_cover_explain_v2(
    asset: dict,
    export_layout: str,
    pool: list[dict],
    *,
    params: CoverScoringParamsV2 | None = None,
    person_demote_mult: float | None = None,
    aesthetic_enabled: bool | None = None,
    limit: int = 4,
) -> list[dict[str, str | float]]:
    p = params or CoverScoringParamsV2()
    features = extract_cover_features(
        asset,
        export_layout,
        pool,
        params=p,
        person_demote_mult=person_demote_mult,
        aesthetic_enabled=aesthetic_enabled,
    )
    if not features:
        return []

    aest_on = _resolve_aesthetic_enabled(aesthetic_enabled)
    weights = p.weights.normalized(aesthetic_enabled=aest_on)
    rows: list[tuple[str, float, float, float]] = []

    for key, feat in features.items():
        w = getattr(weights, key, 0.0)
        if key == "date_confidence" and feat < 0.5:
            contrib = -w * (1.0 - feat)
        elif key == "person" and feat < 1.0:
            contrib = -w * (1.0 - feat)
        else:
            contrib = w * feat
        if abs(contrib) < 0.001:
            continue
        rows.append((key, feat, w, contrib))

    rows.sort(key=lambda item: abs(item[3]), reverse=True)
    out: list[dict[str, str | float]] = []
    for code, feat, weight, contrib in rows[:limit]:
        label = _FEATURE_LABELS.get(code, code)
        direction = "提升" if contrib > 0 else "降低"
        out.append(
            {
                "code": code,
                "label": label,
                "feature": round(feat, 4),
                "weight": round(weight, 4),
                "contribution": round(contrib, 4),
                "reason": f"{label}{direction}封面优先级",
            }
        )
    return out


def resolve_person_demote_v2(
    params: CoverScoringParamsV2, pool: list[dict]
) -> float | None:
    """Return v1-style demote mult for API compat, or None when no demote."""
    if person_tag_ratio(pool) >= params.person_dominant_tag_ratio:
        if params.person_demote_portrait_trip_penalty <= 0:
            return 1.0
        return 1.0 - params.person_demote_portrait_trip_penalty
    return 1.0 - params.person_demote_penalty
