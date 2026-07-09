"""Config-only cover / hero additive logit parameters."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from travelogue.config.cover_scoring_params import CoverScoringParams


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
            sharpness=float(weights_raw.get("sharpness", defaults.sharpness)),
            color=float(weights_raw.get("color", defaults.color)),
            thirds=float(weights_raw.get("thirds", defaults.thirds)),
            person=float(weights_raw.get("person", defaults.person)),
            face_bbox=float(
                weights_raw.get("face_bbox", weights_raw.get("faceBbox", defaults.face_bbox))
            ),
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
            face_bbox_boost=float(raw.get("face_bbox_boost", raw.get("faceBboxBoost", 0.06))),
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
            mobile_aspect_cap=float(raw.get("mobile_aspect_cap", raw.get("mobileAspectCap", 0.95))),
            aspect_sigma=float(raw.get("aspect_sigma", raw.get("aspectSigma", 0.15))),
            enable_thirds=bool(raw.get("enable_thirds", raw.get("enableThirds", True))),
            v1_params=v1,
        )
