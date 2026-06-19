"""Load stratified aesthetic pilot config from merged calibration JSON."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from travelogue.config import AestheticConfig, DEFAULT_STRATUM_BLENDS
from travelogue.curation.album_profile import normalize_stratum_preference

STRATUM_PREFERENCE_PRESETS: dict[str, dict[str, Any]] = {
    "landscape": {
        "stratum_blend_only": ("landscape",),
        "stratum_blend_only_by_purpose": {
            "hero": ("landscape",),
            "cover": ("landscape",),
        },
    },
    "portrait": {
        "stratum_blend_only": ("landscape", "person", "group"),
        "stratum_blend_only_by_purpose": {
            "hero": ("landscape", "person"),
            "cover": ("landscape", "person"),
        },
    },
    "mixed": {
        "stratum_blend_only": ("landscape", "person", "group"),
        "stratum_blend_only_by_purpose": {
            "hero": ("landscape", "person", "group"),
            "cover": ("landscape", "person", "group"),
        },
    },
}


def load_recommended_blends(path: Path) -> dict[str, float]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    blends = raw.get("recommendedBlends")
    if not isinstance(blends, dict):
        inner = raw.get("stratumCalibration") or {}
        blends = inner.get("recommendedBlends") if isinstance(inner, dict) else None
    if not isinstance(blends, dict):
        return dict(DEFAULT_STRATUM_BLENDS)
    out = dict(DEFAULT_STRATUM_BLENDS)
    out.update({str(k): float(v) for k, v in blends.items()})
    return out


def landscape_pilot_config(
    calibration_path: Path,
    *,
    use_album_relative: bool = False,
    stratum_blend_only: tuple[str, ...] = ("landscape",),
) -> AestheticConfig:
    """Landscape-only stratum blend pilot (person 等层保持 rules-only)."""
    return AestheticConfig(
        ml_calibrate=True,
        use_stratum_blend=True,
        stratum_blends=load_recommended_blends(calibration_path),
        stratum_blend_only=stratum_blend_only,
        use_purpose_presets=True,
        portrait_lite_enabled=True,
        use_album_relative=use_album_relative,
        source="rules+ml",
    )


def config_summary(cfg: AestheticConfig) -> dict[str, Any]:
    return {
        "mlCalibrate": cfg.ml_calibrate,
        "useStratumBlend": cfg.use_stratum_blend,
        "stratumBlendOnly": list(cfg.stratum_blend_only),
        "stratumBlendOnlyByPurpose": {
            k: list(v) for k, v in (cfg.stratum_blend_only_by_purpose or {}).items()
        },
        "useAlbumRelative": cfg.use_album_relative,
        "stratumBlends": dict(cfg.stratum_blends or {}),
    }


def apply_stratum_preference_overlay(cfg: AestheticConfig, preference: str) -> AestheticConfig:
    """Optional user preset overlay for stratum blend scope (P4-3)."""
    pref = normalize_stratum_preference(preference)
    if pref == "auto":
        return cfg
    overlay = STRATUM_PREFERENCE_PRESETS.get(pref)
    if not overlay:
        return cfg
    return replace(cfg, **overlay)
