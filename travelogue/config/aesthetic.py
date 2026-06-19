"""Photo aesthetic evaluation configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AestheticWeights:
    """overall = Σ wᵢ·dimᵢ (PA Layer 1). Defaults from design §6."""

    composition: float = 0.25
    exposure: float = 0.20
    color: float = 0.20
    lighting: float = 0.15
    subject_clarity: float = 0.20

    def as_dim_map(self) -> dict[str, float]:
        return {
            "composition": self.composition,
            "exposure": self.exposure,
            "color": self.color,
            "lighting": self.lighting,
            "subjectClarity": self.subject_clarity,
        }


@dataclass
class AestheticPurposePresets:
    """Layer 1 weight presets per use-case (PA · use_purpose_presets)."""

    cover: AestheticWeights = field(
        default_factory=lambda: AestheticWeights(
            composition=0.30,
            exposure=0.15,
            color=0.25,
            lighting=0.15,
            subject_clarity=0.15,
        )
    )
    hero: AestheticWeights = field(
        default_factory=lambda: AestheticWeights(
            composition=0.28,
            exposure=0.18,
            color=0.17,
            lighting=0.12,
            subject_clarity=0.25,
        )
    )
    solo: AestheticWeights = field(
        default_factory=lambda: AestheticWeights(
            composition=0.22,
            exposure=0.15,
            color=0.15,
            lighting=0.28,
            subject_clarity=0.20,
        )
    )
    moment: AestheticWeights = field(
        default_factory=lambda: AestheticWeights(
            composition=0.28,
            exposure=0.12,
            color=0.10,
            lighting=0.22,
            subject_clarity=0.28,
        )
    )


@dataclass
class AestheticMllmConfig:
    """AA · M3 · vision LLM scoring for high-value shortlist only."""

    enabled: bool = False
    provider: str | None = None
    model: str = "qwen-vl-max"
    shortlist_purposes: tuple[str, ...] = ("moment",)
    shortlist_k: int = 5
    max_calls_per_trip: int = 20
    blend: float = 0.45
    temperature: float = 0.0
    cache: bool = True
    rubric: str = "universal"
    image_max_edge: int = 768


DEFAULT_STRATUM_BLENDS: dict[str, float] = {
    "group": 0.10,
    "person": 0.38,
    "landscape": 0.35,
    "food": 0.30,
    "general": 0.35,
}

# G3 · v4 pilot freeze (merged calibration · feat/aesthetic-alignment)
PILOT_V4_STRATUM_BLENDS: dict[str, float] = {
    "group": 0.6,
    "person": 0.6,
    "landscape": 0.6,
    "food": 0.6,
    "general": 0.25,
}


def _pilot_v4_presets() -> AestheticPurposePresets:
    return AestheticPurposePresets(
        cover=AestheticWeights(
            composition=0.3176,
            exposure=0.1589,
            color=0.2647,
            lighting=0.1589,
            subject_clarity=0.4,
        ),
        hero=AestheticWeights(
            composition=0.35,
            exposure=0.18,
            color=0.17,
            lighting=0.12,
            subject_clarity=0.2,
        ),
    )


def _pilot_v4_stratum_blend_by_purpose() -> dict[str, tuple[str, ...]]:
    return {
        "hero": ("landscape", "person"),
        "cover": ("landscape", "person"),
    }


@dataclass
class AestheticConfig:
    """PA · photo aesthetic evaluation (Layer 1, path A · zero-dependency)."""

    enabled: bool = True
    source: str = "rules+ml"  # rules | rules+ml | mllm
    weights: AestheticWeights = field(default_factory=AestheticWeights)
    presets: AestheticPurposePresets = field(default_factory=_pilot_v4_presets)
    ml_calibrate: bool = True
    ml_calibrate_blend: float = 0.4
    learned_metric: str = "nima"
    learned_allow_cpu: bool = True
    learned_device: str | None = None
    warm_learned_on_ingest: bool = False
    use_stratum_blend: bool = True
    stratum_blends: dict[str, float] = field(
        default_factory=lambda: dict(PILOT_V4_STRATUM_BLENDS)
    )
    stratum_blend_only: tuple[str, ...] = ("landscape", "person", "group")
    stratum_blend_only_by_purpose: dict[str, tuple[str, ...]] = field(
        default_factory=_pilot_v4_stratum_blend_by_purpose
    )
    use_album_relative: bool = True
    album_relative_percentile: float = 0.75
    album_relative_lo: float = 0.7
    album_relative_hi: float = 1.3
    portrait_lite_enabled: bool = True
    mllm: AestheticMllmConfig = field(default_factory=AestheticMllmConfig)
    use_purpose_presets: bool = True
    thumb_px: int = 32


def resolve_learned_blend(
    asset: dict,
    cfg: AestheticConfig,
    *,
    purpose: str = "default",
) -> float:
    """Per-stratum learned blend when ``use_stratum_blend`` is on."""
    if not cfg.use_stratum_blend:
        return float(cfg.ml_calibrate_blend)
    from travelogue.curation.aesthetic_blind_review import review_stratum_for_asset

    stratum = review_stratum_for_asset(asset)
    blend_only = cfg.stratum_blend_only
    by_purpose = cfg.stratum_blend_only_by_purpose or {}
    if purpose and purpose != "default" and purpose in by_purpose:
        blend_only = by_purpose[purpose]
    if blend_only:
        if stratum not in frozenset(blend_only):
            return 0.0
    raw = (cfg.stratum_blends or {}).get(stratum)
    if raw is None:
        return float(cfg.ml_calibrate_blend)
    return float(raw)


def _weights_from_dict(raw: dict[str, Any], defaults: AestheticWeights) -> AestheticWeights:
    return AestheticWeights(
        composition=float(raw.get("composition", defaults.composition)),
        exposure=float(raw.get("exposure", defaults.exposure)),
        color=float(raw.get("color", defaults.color)),
        lighting=float(raw.get("lighting", defaults.lighting)),
        subject_clarity=float(
            raw.get(
                "subjectClarity",
                raw.get("subject_clarity", defaults.subject_clarity),
            )
        ),
    )


def _presets_from_dict(raw: dict[str, Any], defaults: AestheticPurposePresets) -> AestheticPurposePresets:
    pr = raw if isinstance(raw, dict) else {}
    return AestheticPurposePresets(
        cover=_weights_from_dict(
            pr.get("cover") if isinstance(pr.get("cover"), dict) else {},
            defaults.cover,
        ),
        hero=_weights_from_dict(
            pr.get("hero") if isinstance(pr.get("hero"), dict) else {},
            defaults.hero,
        ),
        solo=_weights_from_dict(
            pr.get("solo") if isinstance(pr.get("solo"), dict) else {},
            defaults.solo,
        ),
        moment=_weights_from_dict(
            pr.get("moment") if isinstance(pr.get("moment"), dict) else {},
            defaults.moment,
        ),
    )


def aesthetic_from_dict(raw: dict[str, Any]) -> AestheticConfig:
    defaults = AestheticConfig()
    weights_raw = raw.get("weights") if isinstance(raw.get("weights"), dict) else {}
    weights = _weights_from_dict(weights_raw, defaults.weights)
    presets_raw = raw.get("presets") if isinstance(raw.get("presets"), dict) else {}
    presets = _presets_from_dict(presets_raw, defaults.presets)
    learned_raw = raw.get("learned") if isinstance(raw.get("learned"), dict) else {}
    mllm_raw = raw.get("mllm") if isinstance(raw.get("mllm"), dict) else {}
    stratum_raw = raw.get("stratum_blends") if isinstance(raw.get("stratum_blends"), dict) else {}
    source = str(raw.get("source", defaults.source)).strip().lower()
    if source not in ("rules", "rules+ml", "mllm"):
        source = defaults.source
    mllm_defaults = defaults.mllm
    shortlist_raw = mllm_raw.get("shortlist_purposes", mllm_raw.get("shortlistPurposes"))
    if isinstance(shortlist_raw, list):
        shortlist_purposes = tuple(str(x) for x in shortlist_raw if x)
    else:
        shortlist_purposes = mllm_defaults.shortlist_purposes
    stratum_blends = dict(DEFAULT_STRATUM_BLENDS)
    stratum_blends.update({str(k): float(v) for k, v in stratum_raw.items()})
    blend_only_raw = raw.get("stratum_blend_only", raw.get("stratumBlendOnly"))
    if isinstance(blend_only_raw, list):
        stratum_blend_only = tuple(str(x) for x in blend_only_raw if x)
    else:
        stratum_blend_only = defaults.stratum_blend_only
    blend_only_by_purpose_raw = raw.get(
        "stratum_blend_only_by_purpose",
        raw.get("stratumBlendOnlyByPurpose"),
    )
    stratum_blend_only_by_purpose: dict[str, tuple[str, ...]] = dict(
        defaults.stratum_blend_only_by_purpose
    )
    if isinstance(blend_only_by_purpose_raw, dict):
        stratum_blend_only_by_purpose = {
            str(k): tuple(str(x) for x in v if x)
            for k, v in blend_only_by_purpose_raw.items()
            if isinstance(v, list)
        }
    return AestheticConfig(
        enabled=bool(raw.get("enabled", defaults.enabled)),
        source=source,
        weights=weights,
        presets=presets,
        ml_calibrate=bool(raw.get("ml_calibrate", raw.get("mlCalibrate", defaults.ml_calibrate))),
        ml_calibrate_blend=float(
            raw.get("ml_calibrate_blend", raw.get("mlCalibrateBlend", defaults.ml_calibrate_blend))
        ),
        learned_metric=str(
            learned_raw.get("metric", raw.get("learned_metric", raw.get("learnedMetric", defaults.learned_metric)))
        ),
        learned_allow_cpu=bool(
            learned_raw.get(
                "allow_cpu",
                raw.get("learned_allow_cpu", raw.get("learnedAllowCpu", defaults.learned_allow_cpu)),
            )
        ),
        learned_device=(
            str(learned_raw["device"]).strip()
            if learned_raw.get("device")
            else raw.get("learned_device", raw.get("learnedDevice"))
        ),
        warm_learned_on_ingest=bool(
            raw.get(
                "warm_learned_on_ingest",
                raw.get("warmLearnedOnIngest", defaults.warm_learned_on_ingest),
            )
        ),
        use_stratum_blend=bool(
            raw.get("use_stratum_blend", raw.get("useStratumBlend", defaults.use_stratum_blend))
        ),
        stratum_blends=stratum_blends,
        stratum_blend_only=stratum_blend_only,
        stratum_blend_only_by_purpose=stratum_blend_only_by_purpose,
        use_album_relative=bool(
            raw.get("use_album_relative", raw.get("useAlbumRelative", defaults.use_album_relative))
        ),
        album_relative_percentile=float(
            raw.get(
                "album_relative_percentile",
                raw.get("albumRelativePercentile", defaults.album_relative_percentile),
            )
        ),
        album_relative_lo=float(
            raw.get("album_relative_lo", raw.get("albumRelativeLo", defaults.album_relative_lo))
        ),
        album_relative_hi=float(
            raw.get("album_relative_hi", raw.get("albumRelativeHi", defaults.album_relative_hi))
        ),
        portrait_lite_enabled=bool(
            raw.get("portrait_lite_enabled", raw.get("portraitLiteEnabled", defaults.portrait_lite_enabled))
        ),
        mllm=AestheticMllmConfig(
            enabled=bool(mllm_raw.get("enabled", mllm_defaults.enabled)),
            provider=(str(mllm_raw["provider"]).strip() if mllm_raw.get("provider") else None),
            model=str(mllm_raw.get("model", mllm_defaults.model)),
            shortlist_purposes=shortlist_purposes,
            shortlist_k=int(mllm_raw.get("shortlist_k", mllm_raw.get("shortlistK", mllm_defaults.shortlist_k))),
            max_calls_per_trip=int(
                mllm_raw.get("max_calls_per_trip", mllm_raw.get("maxCallsPerTrip", mllm_defaults.max_calls_per_trip))
            ),
            blend=float(mllm_raw.get("blend", mllm_defaults.blend)),
            temperature=float(mllm_raw.get("temperature", mllm_defaults.temperature)),
            cache=bool(mllm_raw.get("cache", mllm_defaults.cache)),
            rubric=str(mllm_raw.get("rubric", mllm_defaults.rubric)),
            image_max_edge=int(
                mllm_raw.get("image_max_edge", mllm_raw.get("imageMaxEdge", mllm_defaults.image_max_edge))
            ),
        ),
        use_purpose_presets=bool(
            raw.get("use_purpose_presets", raw.get("usePurposePresets", defaults.use_purpose_presets))
        ),
        thumb_px=int(raw.get("thumb_px", raw.get("thumbPx", defaults.thumb_px))),
    )
