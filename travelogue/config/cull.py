"""Photo cull configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from travelogue.config_helpers import cfg_bool, cfg_float, cfg_int


@dataclass
class CullConfig:
    enabled: bool = True
    mode: str = "rules"
    keep_ratio_floor: float = 0.90
    min_keep: int = 15
    featured_exempt: bool = True
    featured_hard_exclude: bool = False
    featured_exempt_low_res: bool = True
    max_photos_warn_only: bool = True
    sharpness_absolute_min: float = 0.0
    blur_percentile: float = 2.0
    hard_exclude_media_classes: tuple[str, ...] = ("screenshot", "thumbnail", "reupload")
    recalc_strict_groups: bool = False
    bucketed_blur_thresholds: bool = False
    bucketed_blur_min_samples: int = 3
    score_sharpness_weight_rules: float = 0.55
    score_media_weight_rules: float = 0.25
    score_sharpness_weight_ml: float = 0.35
    score_media_weight_ml: float = 0.20
    score_aesthetic_weight_ml: float = 0.35
    score_bias_ml: float = 0.10
    score_duplicate_group_penalty: float = 0.0
    score_threshold: float = 0.0
    score_topk_ratio: float = 1.0
    enable_cull_explain: bool = True
    aesthetic_metric: str = "topiq_nr"
    portrait_face_aesthetic: bool = True
    allow_cpu_ml: bool = False
    ml_device: str = "auto"
    portrait_quality_enabled: bool = True
    face_ratio_portrait_min: float = 0.15
    face_ratio_gray_low: float = 0.10
    face_ratio_gray_high: float = 0.20
    score_branch_weight_portrait: float = 0.15
    score_branch_weight_landscape: float = 0.15


def cull_from_dict(raw: dict[str, Any]) -> CullConfig:
    ml_raw = raw.get("ml") if isinstance(raw.get("ml"), dict) else {}
    score_raw = raw.get("score") if isinstance(raw.get("score"), dict) else {}
    score_rules_raw = (
        score_raw.get("rules")
        if isinstance(score_raw.get("rules"), dict)
        else {}
    )
    score_ml_raw = (
        score_raw.get("ml")
        if isinstance(score_raw.get("ml"), dict)
        else {}
    )
    hard_raw = raw.get("hard_exclude_media_classes") or raw.get("hardExcludeMediaClasses") or [
        "screenshot",
        "thumbnail",
        "reupload",
    ]
    return CullConfig(
        enabled=bool(raw.get("enabled", True)),
        mode=str(raw.get("mode", "rules")),
        keep_ratio_floor=float(raw.get("keep_ratio_floor", raw.get("keepRatioFloor", 0.90))),
        min_keep=int(raw.get("min_keep", raw.get("minKeep", 15))),
        featured_exempt=bool(raw.get("featured_exempt", raw.get("featuredExempt", True))),
        featured_hard_exclude=bool(raw.get("featured_hard_exclude", raw.get("featuredHardExclude", False))),
        featured_exempt_low_res=bool(
            raw.get("featured_exempt_low_res", raw.get("featuredExemptLowRes", True))
        ),
        max_photos_warn_only=bool(raw.get("max_photos_warn_only", raw.get("maxPhotosWarnOnly", True))),
        sharpness_absolute_min=float(raw.get("sharpness_absolute_min", raw.get("sharpnessAbsoluteMin", 0.0))),
        blur_percentile=float(raw.get("blur_percentile", raw.get("blurPercentile", 2.0))),
        hard_exclude_media_classes=tuple(str(x) for x in hard_raw if x),
        recalc_strict_groups=cfg_bool(
            raw, "recalc_strict_groups", "recalcStrictGroups", False
        ),
        bucketed_blur_thresholds=cfg_bool(
            raw, "bucketed_blur_thresholds", "bucketedBlurThresholds", False
        ),
        bucketed_blur_min_samples=cfg_int(
            raw, "bucketed_blur_min_samples", "bucketedBlurMinSamples", 3
        ),
        score_sharpness_weight_rules=float(
            score_rules_raw.get("sharpness_weight", score_rules_raw.get("sharpnessWeight", 0.55))
        ),
        score_media_weight_rules=float(
            score_rules_raw.get("media_weight", score_rules_raw.get("mediaWeight", 0.25))
        ),
        score_sharpness_weight_ml=float(
            score_ml_raw.get("sharpness_weight", score_ml_raw.get("sharpnessWeight", 0.35))
        ),
        score_media_weight_ml=float(
            score_ml_raw.get("media_weight", score_ml_raw.get("mediaWeight", 0.20))
        ),
        score_aesthetic_weight_ml=float(
            score_ml_raw.get("aesthetic_weight", score_ml_raw.get("aestheticWeight", 0.35))
        ),
        score_bias_ml=float(
            score_ml_raw.get("bias", 0.10)
        ),
        score_duplicate_group_penalty=float(
            score_raw.get("duplicate_group_penalty", score_raw.get("duplicateGroupPenalty", 0.0))
        ),
        score_threshold=float(
            score_raw.get("threshold", score_raw.get("scoreThreshold", 0.0))
        ),
        score_topk_ratio=float(
            score_raw.get("topk_ratio", score_raw.get("topkRatio", 1.0))
        ),
        enable_cull_explain=cfg_bool(
            raw, "enable_cull_explain", "enableCullExplain", True
        ),
        aesthetic_metric=str(ml_raw.get("aesthetic_metric", ml_raw.get("aestheticMetric", "topiq_nr"))),
        portrait_face_aesthetic=bool(
            ml_raw.get("portrait_face_aesthetic", ml_raw.get("portraitFaceAesthetic", True))
        ),
        allow_cpu_ml=bool(ml_raw.get("allow_cpu_ml", ml_raw.get("allowCpuMl", False))),
        ml_device=str(ml_raw.get("device", "auto")),
        portrait_quality_enabled=cfg_bool(
            raw, "portrait_quality_enabled", "portraitQualityEnabled", True
        ),
        face_ratio_portrait_min=cfg_float(
            raw, "face_ratio_portrait_min", "faceRatioPortraitMin", 0.15
        ),
        face_ratio_gray_low=cfg_float(
            raw, "face_ratio_gray_low", "faceRatioGrayLow", 0.10
        ),
        face_ratio_gray_high=cfg_float(
            raw, "face_ratio_gray_high", "faceRatioGrayHigh", 0.20
        ),
        score_branch_weight_portrait=cfg_float(
            raw, "score_branch_weight_portrait", "scoreBranchWeightPortrait", 0.15
        ),
        score_branch_weight_landscape=cfg_float(
            raw, "score_branch_weight_landscape", "scoreBranchWeightLandscape", 0.15
        ),
    )
