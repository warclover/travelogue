"""Configurable cover scoring parameters (cover-selection-plan v0.2 · S1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_PERSON_TAGS = frozenset({"face", "person", "selfie", "portrait"})


@dataclass(frozen=True)
class CoverScoringParams:
    """Tunable multipliers; defaults match pre-S1 curate_scoring.py behavior."""

    person_demote: float = 0.72
    person_demote_portrait_trip: float = 1.0
    person_dominant_tag_ratio: float = 0.40
    face_bbox_boost: float = 1.06
    face_bbox_min_area: float = 0.02
    face_bbox_max_area: float = 0.38
    face_bbox_sharp_ratio_min: float = 0.85
    sharp_ratio_cap: float = 1.25
    sharp_ratio_floor: float = 0.35
    date_confidence_low_mult: float = 0.65
    thirds_axis_weight: float = 0.55
    thirds_off_center_weight: float = 0.45
    thirds_base: float = 0.88
    thirds_span: float = 0.12
    web_panorama_mult: float = 1.1
    web_landscape_mult: float = 1.06
    mobile_tall_mult: float = 0.92
    mobile_portrait_mult: float = 0.96
    enable_phase6_factors: bool = True

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> CoverScoringParams:
        if not raw:
            return cls()
        return cls(
            person_demote=float(raw.get("person_demote", raw.get("personDemote", 0.72))),
            person_demote_portrait_trip=float(
                raw.get(
                    "person_demote_portrait_trip",
                    raw.get("personDemotePortraitTrip", 1.0),
                )
            ),
            person_dominant_tag_ratio=float(
                raw.get(
                    "person_dominant_tag_ratio",
                    raw.get("personDominantTagRatio", 0.40),
                )
            ),
            face_bbox_boost=float(
                raw.get("face_bbox_boost", raw.get("faceBboxBoost", 1.06))
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
            sharp_ratio_cap=float(
                raw.get("sharp_ratio_cap", raw.get("sharpRatioCap", 1.25))
            ),
            sharp_ratio_floor=float(
                raw.get("sharp_ratio_floor", raw.get("sharpRatioFloor", 0.35))
            ),
            date_confidence_low_mult=float(
                raw.get(
                    "date_confidence_low_mult",
                    raw.get("dateConfidenceLowMult", 0.65),
                )
            ),
            thirds_axis_weight=float(
                raw.get("thirds_axis_weight", raw.get("thirdsAxisWeight", 0.55))
            ),
            thirds_off_center_weight=float(
                raw.get(
                    "thirds_off_center_weight",
                    raw.get("thirdsOffCenterWeight", 0.45),
                )
            ),
            thirds_base=float(raw.get("thirds_base", raw.get("thirdsBase", 0.88))),
            thirds_span=float(raw.get("thirds_span", raw.get("thirdsSpan", 0.12))),
            web_panorama_mult=float(
                raw.get("web_panorama_mult", raw.get("webPanoramaMult", 1.1))
            ),
            web_landscape_mult=float(
                raw.get("web_landscape_mult", raw.get("webLandscapeMult", 1.06))
            ),
            mobile_tall_mult=float(
                raw.get("mobile_tall_mult", raw.get("mobileTallMult", 0.92))
            ),
            mobile_portrait_mult=float(
                raw.get("mobile_portrait_mult", raw.get("mobilePortraitMult", 0.96))
            ),
            enable_phase6_factors=bool(
                raw.get(
                    "enable_phase6_factors",
                    raw.get("enablePhase6Factors", True),
                )
            ),
        )


def asset_has_person_tag(asset: dict) -> bool:
    tags = {str(t).lower() for t in (asset.get("tags") or []) if t}
    return bool(tags.intersection(_PERSON_TAGS))


def person_tag_ratio(assets: list[dict]) -> float:
    """Share of non-video assets with face/person/selfie/portrait tags."""
    eligible = [a for a in assets if a.get("type") != "video" and a.get("id")]
    if not eligible:
        return 0.0
    tagged = sum(1 for a in eligible if asset_has_person_tag(a))
    return tagged / len(eligible)


def resolve_person_demote(params: CoverScoringParams, pool: list[dict]) -> float:
    """PRD v0.2 §1.4: portrait-dominant trips skip person demote."""
    if person_tag_ratio(pool) >= params.person_dominant_tag_ratio:
        return params.person_demote_portrait_trip
    return params.person_demote
