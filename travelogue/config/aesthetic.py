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


@dataclass
class AestheticConfig:
    """PA · photo aesthetic evaluation (Layer 1, path A · zero-dependency)."""

    enabled: bool = True
    source: str = "rules"  # rules | rules+ml | mllm
    weights: AestheticWeights = field(default_factory=AestheticWeights)
    presets: AestheticPurposePresets = field(default_factory=AestheticPurposePresets)
    ml_calibrate: bool = False
    ml_calibrate_blend: float = 0.4
    use_purpose_presets: bool = True
    thumb_px: int = 32


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
    )


def aesthetic_from_dict(raw: dict[str, Any]) -> AestheticConfig:
    defaults = AestheticConfig()
    weights_raw = raw.get("weights") if isinstance(raw.get("weights"), dict) else {}
    weights = _weights_from_dict(weights_raw, defaults.weights)
    presets_raw = raw.get("presets") if isinstance(raw.get("presets"), dict) else {}
    presets = _presets_from_dict(presets_raw, defaults.presets)
    source = str(raw.get("source", defaults.source)).strip().lower()
    if source not in ("rules", "rules+ml", "mllm"):
        source = defaults.source
    return AestheticConfig(
        enabled=bool(raw.get("enabled", defaults.enabled)),
        source=source,
        weights=weights,
        presets=presets,
        ml_calibrate=bool(raw.get("ml_calibrate", raw.get("mlCalibrate", defaults.ml_calibrate))),
        ml_calibrate_blend=float(
            raw.get("ml_calibrate_blend", raw.get("mlCalibrateBlend", defaults.ml_calibrate_blend))
        ),
        use_purpose_presets=bool(
            raw.get("use_purpose_presets", raw.get("usePurposePresets", defaults.use_purpose_presets))
        ),
        thumb_px=int(raw.get("thumb_px", raw.get("thumbPx", defaults.thumb_px))),
    )
