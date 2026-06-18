"""PA Layer 1 · aesthetic synthesiser (PA-T04).

Turns the per-image CV signals (exposure / lighting / colour harmony) plus the
existing asset fields (sharpness / salientBox / dominantTone / meanLuma) into a
five-dimensional aesthetic score with an ``overall`` + ``confidence`` and a
human-readable explanation. Everything is deterministic and PIL-only.

Design fail-open contract: missing signals never raise — the affected term is
dropped, the blend is renormalised over what remains, and ``confidence`` is
discounted accordingly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from PIL import Image

from travelogue.config import AestheticConfig, AestheticWeights, resolve_learned_blend
from travelogue.curation.asset_quality import asset_sharpness
from travelogue.curation.composition_signals import mean_thirds_score
from travelogue.media.color_metrics import (
    color_harmony_score,
    dominant_tone_chroma_score,
    triangular_score,
)
from travelogue.media.exposure_metrics import (
    histogram_stats,
    lighting_stats,
    quadrant_balance,
    subject_contrast_score,
)

AESTHETIC_VERSION = "pa-v0.1"
SIGNAL_CACHE_FILE = "phase_pa_aesthetic.json"
AestheticPurpose = Literal["default", "cover", "hero", "solo", "moment"]
_SHARP_NORM_K = 150.0
_LOW_CONF_MEDIA = frozenset({"screenshot", "thumbnail", "reupload"})

_DIM_LABELS: dict[str, str] = {
    "composition": "构图",
    "exposure": "曝光影调",
    "color": "色彩",
    "lighting": "光影",
    "subjectClarity": "主体清晰",
}


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


def _read_mean_luma(asset: dict) -> float | None:
    """meanLuma with the documented compat order: quality → color → top-level."""
    q = asset.get("quality")
    if isinstance(q, dict) and q.get("meanLuma") is not None:
        try:
            return float(q["meanLuma"])
        except (TypeError, ValueError):
            pass
    color = asset.get("color")
    if isinstance(color, dict) and color.get("meanLuma") is not None:
        try:
            return float(color["meanLuma"])
        except (TypeError, ValueError):
            pass
    if asset.get("meanLuma") is not None:
        try:
            return float(asset["meanLuma"])
        except (TypeError, ValueError):
            pass
    return None


def _read_topiq_score(asset: dict) -> float | None:
    """``quality.aestheticScore`` from pyiqa (legacy flat field)."""
    q = asset.get("quality")
    if isinstance(q, dict) and q.get("aestheticScore") is not None:
        try:
            return _clamp01(float(q["aestheticScore"]))
        except (TypeError, ValueError):
            return None
    return None


def _read_learned_aesthetic_score(asset: dict) -> float | None:
    """``quality.aesthetic.signals.learnedAesthetic`` with flat-field fallback."""
    q = asset.get("quality")
    if isinstance(q, dict):
        ae = q.get("aesthetic")
        if isinstance(ae, dict):
            sig = ae.get("signals")
            if isinstance(sig, dict) and sig.get("learnedAesthetic") is not None:
                try:
                    return _clamp01(float(sig["learnedAesthetic"]))
                except (TypeError, ValueError):
                    pass
    return _read_topiq_score(asset)


def _read_mllm_score(asset: dict) -> float | None:
    q = asset.get("quality")
    if isinstance(q, dict):
        ae = q.get("aesthetic")
        if isinstance(ae, dict):
            sig = ae.get("signals")
            if isinstance(sig, dict) and sig.get("mllmScore") is not None:
                try:
                    return _clamp01(float(sig["mllmScore"]))
                except (TypeError, ValueError):
                    pass
    return None


def _blend_mllm_overall(
    base: float,
    asset: dict,
    *,
    cfg: AestheticConfig,
    purpose: str = "default",
) -> tuple[float, str]:
    mllm = _read_mllm_score(asset)
    if mllm is None or not cfg.mllm.enabled:
        return base, "rules+ml"
    if purpose and purpose != "default":
        allowed = cfg.mllm.shortlist_purposes or ()
        if allowed and purpose not in allowed:
            return base, "rules+ml"
    blend = _clamp01(cfg.mllm.blend)
    if blend <= 0:
        return base, "rules+ml"
    out = round(_clamp01((1.0 - blend) * base + blend * mllm), 4)
    return out, "mllm" if blend >= 0.35 else "rules+ml"


def _rules_overall_from_weights(dims: dict[str, float], weights: AestheticWeights) -> float:
    w_map = weights.as_dim_map()
    w_total = sum(w_map.values()) or 1.0
    return sum(w_map[k] * float(dims[k]) for k in dims if k in w_map) / w_total


def _rules_overall_from_dims(dims: dict[str, float], cfg: AestheticConfig) -> float:
    return _rules_overall_from_weights(dims, cfg.weights)


def resolve_aesthetic_weights(
    cfg: AestheticConfig,
    purpose: AestheticPurpose = "default",
) -> AestheticWeights:
    """Purpose-specific Layer 1 weights when ``use_purpose_presets`` is on."""
    if not cfg.use_purpose_presets or purpose == "default":
        return cfg.weights
    if purpose == "cover":
        return cfg.presets.cover
    if purpose == "hero":
        return cfg.presets.hero
    if purpose == "solo":
        return cfg.presets.solo
    if purpose == "moment":
        return cfg.presets.moment
    return cfg.weights


def purpose_overall(
    asset: dict,
    purpose: AestheticPurpose,
    *,
    cfg: AestheticConfig | None = None,
) -> float | None:
    """Recompute overall from stored dims with purpose weights (+ optional ML blend)."""
    if purpose == "default":
        return aesthetic_overall(asset)
    cfg = cfg or AestheticConfig()
    if not cfg.use_purpose_presets:
        return aesthetic_overall(asset)
    ae = asset_aesthetic(asset)
    if not ae:
        return None
    dims = ae.get("dims")
    if not isinstance(dims, dict) or not dims:
        return aesthetic_overall(asset)
    required = frozenset(
        {"composition", "exposure", "color", "lighting", "subjectClarity"}
    )
    if not required.issubset(dims.keys()):
        return aesthetic_overall(asset)
    rules = _rules_overall_from_weights(dims, resolve_aesthetic_weights(cfg, purpose))
    blended, _, _ = _blend_ml_overall(rules, asset, cfg=cfg, purpose=purpose)
    return blended


def _blend_ml_overall(
    rules_overall: float,
    asset: dict,
    *,
    cfg: AestheticConfig,
    purpose: str = "default",
) -> tuple[float, str, dict[str, float]]:
    """Blend rules overall with learned aesthetic when ``ml_calibrate`` is enabled."""
    base_source = str(cfg.source or "rules")
    if not cfg.ml_calibrate:
        return rules_overall, base_source, {}
    ml = _read_learned_aesthetic_score(asset)
    if ml is None:
        return rules_overall, base_source, {}
    blend = _clamp01(resolve_learned_blend(asset, cfg, purpose=purpose))
    blended = (1.0 - blend) * rules_overall + blend * ml
    blended, final_source = _blend_mllm_overall(blended, asset, cfg=cfg, purpose=purpose)
    extra: dict[str, float] = {
        "rulesOverall": round(rules_overall, 4),
        "mlScore": round(ml, 4),
        "learnedAesthetic": round(ml, 4),
    }
    mllm = _read_mllm_score(asset)
    if mllm is not None:
        extra["mllmScore"] = round(mllm, 4)
    return round(_clamp01(blended), 4), final_source, extra


def _read_dominant_tone(asset: dict) -> str | None:
    tone = asset.get("dominantTone")
    if isinstance(tone, str) and tone.startswith("#"):
        return tone
    color = asset.get("color")
    if isinstance(color, dict):
        ct = color.get("dominantTone")
        if isinstance(ct, str) and ct.startswith("#"):
            return ct
    return None


def normalize_sharpness(sharp: float, *, k: float = _SHARP_NORM_K) -> float:
    """Saturating map from raw edge-variance sharpness to ``[0, 1]``.

    Batch-relative lo/hi (``_norm_sharpness``) is unavailable at ingest time, so
    a deterministic single-image curve ``s / (s + k)`` is used instead.
    """
    s = max(0.0, float(sharp))
    if s <= 0:
        return 0.0
    return _clamp01(s / (s + max(1.0, float(k))))


def _negative_space_score(asset: dict) -> float | None:
    box = asset.get("salientBox")
    if not isinstance(box, dict):
        return None
    try:
        area = float(box.get("w", 0.0)) * float(box.get("h", 0.0))
    except (TypeError, ValueError):
        return None
    if area <= 0:
        return None
    # Peak ≈ subject filling 15–35% of frame → pleasant negative space.
    return round(triangular_score(area, low=0.02, peak=0.25, high=0.75), 4)


def _thirds_score(asset: dict) -> float:
    return round(mean_thirds_score(asset), 4)


def _blend(parts: list[tuple[float, float | None]]) -> tuple[float, float]:
    """Weighted blend ignoring ``None`` terms.

    Returns ``(value, completeness)`` where completeness is the fraction of the
    nominal weight that had a usable signal (1.0 = fully observed).
    """
    total_weight = sum(w for w, _ in parts) or 1.0
    present_weight = 0.0
    acc = 0.0
    for weight, value in parts:
        if value is None:
            continue
        present_weight += weight
        acc += weight * _clamp01(value)
    if present_weight <= 0:
        return 0.5, 0.0
    return _clamp01(acc / present_weight), present_weight / total_weight


def compute_aesthetic_signals(
    img: Image.Image,
    asset: dict,
    *,
    cfg: AestheticConfig | None = None,
) -> dict[str, float]:
    """Pure per-image CV signals (cacheable by contentSig)."""
    cfg = cfg or AestheticConfig()
    thumb_px = int(cfg.thumb_px)
    mean_luma = _read_mean_luma(asset)
    signals: dict[str, float] = {}
    signals.update(histogram_stats(img, thumb_px=thumb_px, mean_luma=mean_luma))
    signals.update(lighting_stats(img, thumb_px=thumb_px))
    signals["balance"] = quadrant_balance(img, thumb_px=thumb_px)
    signals["colorHarmony"] = color_harmony_score(img, thumb_px=thumb_px)
    subj = subject_contrast_score(img, asset.get("salientBox"))
    if subj is not None:
        signals["subjectContrast"] = subj
    return signals


def compute_aesthetic(
    asset: dict,
    *,
    signals: dict[str, Any] | None = None,
    cfg: AestheticConfig | None = None,
    portrait_cfg: Any | None = None,
) -> dict[str, Any]:
    """Synthesise the ``quality.aesthetic`` block from *signals* + asset fields."""
    cfg = cfg or AestheticConfig()
    from travelogue.config.portrait import PortraitConfig
    from travelogue.curation.portrait_subject_clarity import (
        compute_portrait_subject_clarity,
        portrait_has_signal,
        read_portrait_block,
    )

    p_cfg = portrait_cfg if portrait_cfg is not None else PortraitConfig()
    sig = dict(signals or {})

    def _sig(key: str) -> float | None:
        val = sig.get(key)
        try:
            return None if val is None else float(val)
        except (TypeError, ValueError):
            return None

    thirds = _thirds_score(asset)
    neg_space = _negative_space_score(asset)
    balance = _sig("balance")
    composition, comp_c = _blend(
        [(0.45, thirds), (0.30, balance), (0.25, neg_space)]
    )

    dynamic_range = _sig("dynamicRange")
    midtone = _sig("midtoneCenter")
    clip_high = _sig("clipHighRatio") or 0.0
    clip_low = _sig("clipLowRatio") or 0.0
    clip_headroom = None if dynamic_range is None and midtone is None else _clamp01(
        1.0 - clip_high - clip_low
    )
    exposure, expo_c = _blend(
        [(0.5, dynamic_range), (0.3, midtone), (0.2, clip_headroom)]
    )

    richness = dominant_tone_chroma_score(_read_dominant_tone(asset))
    harmony = _sig("colorHarmony")
    color, color_c = _blend([(0.55, richness), (0.45, harmony)])

    luma_gradient = _sig("lumaGradient")
    contrast = _sig("contrast")
    lighting, light_c = _blend([(0.5, luma_gradient), (0.5, contrast)])

    norm_sharp = normalize_sharpness(asset_sharpness(asset))
    subj_contrast = _sig("subjectContrast")
    subject_clarity, subj_c = _blend([(0.7, norm_sharp), (0.3, subj_contrast)])
    portrait_sigs: dict[str, float] = {}
    portrait_block = read_portrait_block(asset)
    if portrait_has_signal(asset, min_confidence=p_cfg.min_confidence) and portrait_block:
        subject_clarity, portrait_sigs = compute_portrait_subject_clarity(
            norm_sharp=norm_sharp,
            portrait=portrait_block,
            cfg=p_cfg,
        )
        subj_c = 1.0
    elif cfg.portrait_lite_enabled:
        from travelogue.curation.portrait_lite import portrait_lite_subject_clarity_factor

        subject_clarity = _clamp01(subject_clarity * portrait_lite_subject_clarity_factor(asset))

    dims = {
        "composition": round(composition, 4),
        "exposure": round(exposure, 4),
        "color": round(color, 4),
        "lighting": round(lighting, 4),
        "subjectClarity": round(subject_clarity, 4),
    }

    weights = cfg.weights.as_dim_map()
    w_total = sum(weights.values()) or 1.0
    overall = sum(weights[k] * dims[k] for k in dims) / w_total

    completeness = {
        "composition": comp_c,
        "exposure": expo_c,
        "color": color_c,
        "lighting": light_c,
        "subjectClarity": subj_c,
    }
    base_conf = sum(weights[k] * completeness[k] for k in dims) / w_total
    confidence = base_conf
    if not sig:
        confidence *= 0.5
    if str(asset.get("mediaClass") or "") in _LOW_CONF_MEDIA:
        confidence *= 0.5
    if (clip_high + clip_low) > 0.5:
        confidence *= 0.7
    if not isinstance(asset.get("salientBox"), dict):
        confidence *= 0.9

    out_signals: dict[str, float] = {"thirdsScore": thirds, "richness": round(richness, 4)}
    if neg_space is not None:
        out_signals["negativeSpace"] = neg_space
    out_signals["normSharp"] = round(norm_sharp, 4)
    out_signals.update(portrait_sigs)
    for key in (
        "dynamicRange",
        "clipHighRatio",
        "clipLowRatio",
        "midtoneCenter",
        "colorHarmony",
        "lumaGradient",
        "contrast",
        "balance",
        "subjectContrast",
    ):
        val = _sig(key)
        if val is not None:
            out_signals[key] = round(val, 4)

    overall, final_source, ml_signals = _blend_ml_overall(overall, asset, cfg=cfg)
    out_signals.update(ml_signals)

    return {
        "version": AESTHETIC_VERSION,
        "source": str(final_source),
        "overall": round(_clamp01(overall), 4),
        "confidence": round(_clamp01(confidence), 4),
        "dims": dims,
        "signals": out_signals,
        "critique": None,
    }


def refresh_aesthetic_ml_blend(asset: dict, *, cfg: AestheticConfig | None = None) -> bool:
    """Re-blend ``quality.aesthetic.overall`` after learned scores are written (PA-4 / AA-M1)."""
    cfg = cfg or AestheticConfig()
    if not cfg.ml_calibrate:
        return False
    ml = _read_learned_aesthetic_score(asset)
    if ml is None:
        return False
    q = asset.get("quality")
    if not isinstance(q, dict):
        return False
    ae = q.get("aesthetic")
    if not isinstance(ae, dict):
        return False
    dims = ae.get("dims")
    if not isinstance(dims, dict) or not dims:
        return False
    rules = _rules_overall_from_dims(dims, cfg)
    overall, final_source, ml_signals = _blend_ml_overall(rules, asset, cfg=cfg)
    ae["overall"] = overall
    ae["source"] = final_source
    sig = ae.setdefault("signals", {})
    if isinstance(sig, dict):
        sig.update(ml_signals)
    return True


def apply_aesthetic_ml_calibration(
    assets: list[dict],
    *,
    trip_dir: Path,
    cfg: Any | None = None,
) -> bool:
    """Run learned pyiqa scoring + refresh ``quality.aesthetic.overall`` (curate hook, AA-M1).

    Fail-open: returns False when ``ml_calibrate`` is off, pyiqa/torch unavailable,
    or no assets were scored — existing rules-only overall values are kept.
    """
    from dataclasses import replace

    from travelogue.config import AppConfig

    app_cfg = cfg if cfg is not None else AppConfig()
    ae_cfg = app_cfg.aesthetic
    if not ae_cfg.enabled or not ae_cfg.ml_calibrate:
        return False
    from travelogue.curation.photo_cull_ml import apply_aesthetic_scores

    metric = str(ae_cfg.learned_metric or app_cfg.cull.aesthetic_metric or "nima")
    ml_device = ae_cfg.learned_device or app_cfg.cull.ml_device
    cull_cfg = replace(
        app_cfg.cull,
        aesthetic_metric=metric,
        allow_cpu_ml=ae_cfg.learned_allow_cpu or app_cfg.cull.allow_cpu_ml,
        ml_device=str(ml_device or "auto"),
    )
    scored = apply_aesthetic_scores(
        assets,
        trip_dir=trip_dir,
        cfg=cull_cfg,
        force_ml=True,
    )
    refreshed = sum(1 for a in assets if refresh_aesthetic_ml_blend(a, cfg=ae_cfg))
    return scored or refreshed > 0


def refresh_portrait_lite_overall(asset: dict, *, cfg: AestheticConfig | None = None) -> bool:
    """Recompute rules overall after portrait-lite ``subjectClarity`` adjustment."""
    cfg = cfg or AestheticConfig()
    if not cfg.portrait_lite_enabled:
        return False
    ae = asset_aesthetic(asset)
    if not ae:
        return False
    dims = ae.get("dims")
    if not isinstance(dims, dict) or "subjectClarity" not in dims:
        return False
    from travelogue.curation.portrait_lite import portrait_lite_subject_clarity_factor

    sig = ae.setdefault("signals", {})
    if not isinstance(sig, dict):
        return False
    base = sig.get("subjectClarityBase")
    if base is None:
        legacy = dims.pop("_subjectClarityBase", None)
        if legacy is not None:
            base = legacy
        else:
            try:
                base = float(dims["subjectClarity"])
            except (TypeError, ValueError):
                return False
        sig["subjectClarityBase"] = round(float(base), 4)
    else:
        try:
            base = float(base)
        except (TypeError, ValueError):
            return False
    factor = portrait_lite_subject_clarity_factor(asset)
    dims["subjectClarity"] = round(_clamp01(base * factor), 4)
    rules = _rules_overall_from_dims(dims, cfg)
    overall, final_source, ml_signals = _blend_ml_overall(rules, asset, cfg=cfg)
    ae["overall"] = overall
    ae["source"] = final_source
    if isinstance(sig, dict):
        sig.update(ml_signals)
        sig["portraitLiteFactor"] = round(factor, 4)
    return True


def refresh_portrait_subject_clarity_overall(
    asset: dict,
    *,
    cfg: AestheticConfig | None = None,
    portrait_cfg: Any | None = None,
) -> bool:
    """Recompute rules overall after §6.3 portrait ``subjectClarity`` injection."""
    from travelogue.config.portrait import PortraitConfig
    from travelogue.curation.portrait_subject_clarity import (
        compute_portrait_subject_clarity,
        portrait_has_signal,
        read_portrait_block,
    )

    cfg = cfg or AestheticConfig()
    p_cfg = portrait_cfg if portrait_cfg is not None else PortraitConfig()
    if not portrait_has_signal(asset, min_confidence=p_cfg.min_confidence):
        return False
    ae = asset_aesthetic(asset)
    if not ae:
        return False
    dims = ae.get("dims")
    if not isinstance(dims, dict) or "subjectClarity" not in dims:
        return False
    portrait_block = read_portrait_block(asset)
    if not portrait_block:
        return False
    sig = ae.setdefault("signals", {})
    if not isinstance(sig, dict):
        return False
    norm_sharp = sig.get("normSharp")
    if norm_sharp is None:
        norm_sharp = normalize_sharpness(asset_sharpness(asset))
    else:
        try:
            norm_sharp = float(norm_sharp)
        except (TypeError, ValueError):
            norm_sharp = normalize_sharpness(asset_sharpness(asset))
    subject_clarity, portrait_sigs = compute_portrait_subject_clarity(
        norm_sharp=norm_sharp,
        portrait=portrait_block,
        cfg=p_cfg,
    )
    dims["subjectClarity"] = subject_clarity
    sig.update(portrait_sigs)
    rules = _rules_overall_from_dims(dims, cfg)
    overall, final_source, ml_signals = _blend_ml_overall(rules, asset, cfg=cfg)
    ae["overall"] = overall
    ae["source"] = final_source
    sig.update(ml_signals)
    return True


def _eligible_aesthetic_images(assets: list[dict]) -> list[dict]:
    return [
        a
        for a in assets
        if a.get("type", "image") != "video"
        and a.get("layoutEligible") is not False
        and a.get("id")
    ]


def build_aesthetic_alignment_telemetry(
    assets: list[dict],
    report: dict[str, Any],
    *,
    cfg: AestheticConfig,
) -> dict[str, Any]:
    """GAP-11 · coverage / fail-open summary for trip.curation.aestheticAlignment."""
    eligible = _eligible_aesthetic_images(assets)
    n = len(eligible)
    learned_n = sum(1 for a in eligible if _read_learned_aesthetic_score(a) is not None)
    mllm_n = sum(1 for a in eligible if _read_mllm_score(a) is not None)
    mllm_rep = report.get("mllm") if isinstance(report.get("mllm"), dict) else {}
    return {
        "version": "1",
        "source": str(cfg.source),
        "mlCalibrate": bool(cfg.ml_calibrate),
        "mllmEnabled": bool(cfg.mllm.enabled),
        "portraitLiteEnabled": bool(cfg.portrait_lite_enabled),
        "eligibleImages": n,
        "learnedScored": learned_n,
        "learnedHitRate": round(learned_n / n, 4) if n else None,
        "mllmScored": mllm_n,
        "mllmHitRate": round(mllm_n / n, 4) if n and cfg.mllm.enabled else None,
        "portraitLiteAdjusted": int(report.get("portraitLite") or 0),
        "mlApplied": bool(report.get("ml")),
        "mllmCalls": int(mllm_rep.get("calls") or 0),
        "mllmCached": int(mllm_rep.get("cached") or 0),
        "mllmFailed": int(mllm_rep.get("failed") or 0),
        "failOpen": {
            "mlSkipped": bool(cfg.ml_calibrate and not report.get("ml")),
            "mllmSkipped": bool(cfg.mllm.enabled and not mllm_rep),
            "mllmFailures": int(mllm_rep.get("failed") or 0),
        },
    }


def persist_aesthetic_alignment(
    trip: dict,
    report: dict[str, Any],
    *,
    cfg: AestheticConfig | None = None,
) -> dict[str, Any]:
    """Write telemetry to ``trip.curation.aestheticAlignment`` + algorithmProfile."""
    from datetime import UTC, datetime

    cfg = cfg or AestheticConfig()
    assets = list(trip.get("assets") or [])
    telemetry = build_aesthetic_alignment_telemetry(assets, report, cfg=cfg)
    telemetry["appliedAt"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    curation = trip.setdefault("curation", {})
    curation["aestheticAlignment"] = telemetry
    profile = curation.setdefault("algorithmProfile", {})
    profile["aestheticAlignmentAt"] = telemetry["appliedAt"]
    profile["aestheticMlCalibrate"] = telemetry["mlCalibrate"]
    profile["aestheticMllmEnabled"] = telemetry["mllmEnabled"]
    profile["aestheticLearnedHitRate"] = telemetry.get("learnedHitRate")
    profile["aestheticMllmHitRate"] = telemetry.get("mllmHitRate")
    return telemetry


def apply_aesthetic_alignment(
    assets: list[dict],
    *,
    trip_dir: Path,
    cfg: Any | None = None,
    trip: dict | None = None,
) -> dict[str, Any]:
    """Curate hook: learned blend + optional MLLM shortlist (fail-open)."""
    from travelogue.config import AppConfig
    from dataclasses import replace

    app_cfg = cfg if cfg is not None else AppConfig()
    if trip is not None:
        from travelogue.config.aesthetic_stratified import apply_stratum_preference_overlay
        from travelogue.curation.album_profile import stratum_preference_for_trip

        pref = stratum_preference_for_trip(trip)
        app_cfg = replace(
            app_cfg,
            aesthetic=apply_stratum_preference_overlay(app_cfg.aesthetic, pref),
        )
    ae_cfg = app_cfg.aesthetic
    report: dict[str, Any] = {"ml": False, "mllm": None, "portraitLite": 0, "portraitSubjectClarity": 0}
    if not ae_cfg.enabled:
        return report
    report["ml"] = apply_aesthetic_ml_calibration(assets, trip_dir=trip_dir, cfg=app_cfg)
    portrait_cfg = app_cfg.cull.portrait
    report["portraitSubjectClarity"] = sum(
        1
        for a in assets
        if refresh_portrait_subject_clarity_overall(a, cfg=ae_cfg, portrait_cfg=portrait_cfg)
    )
    if ae_cfg.portrait_lite_enabled:
        from travelogue.curation.portrait_subject_clarity import portrait_has_signal

        report["portraitLite"] = sum(
            1
            for a in assets
            if not portrait_has_signal(a, min_confidence=portrait_cfg.min_confidence)
            and refresh_portrait_lite_overall(a, cfg=ae_cfg)
        )
    if ae_cfg.mllm.enabled:
        from travelogue.vision.aesthetic_mllm import apply_aesthetic_mllm_scores

        try:
            report["mllm"] = apply_aesthetic_mllm_scores(
                assets, trip_dir=trip_dir, cfg=ae_cfg, trip=trip
            )
        except Exception as exc:
            report["mllm"] = {
                "enabled": True,
                "scored": 0,
                "cached": 0,
                "failed": 0,
                "skipped": 0,
                "calls": 0,
                "error": str(exc),
            }
    report["telemetry"] = build_aesthetic_alignment_telemetry(assets, report, cfg=ae_cfg)
    if trip is not None:
        persist_aesthetic_alignment(trip, report, cfg=ae_cfg)
    return report


def asset_aesthetic(asset: dict) -> dict | None:
    q = asset.get("quality")
    if isinstance(q, dict):
        ae = q.get("aesthetic")
        if isinstance(ae, dict):
            return ae
    return None


def aesthetic_overall(asset: dict) -> float | None:
    """``quality.aesthetic.overall`` or ``None`` when absent (fail-open)."""
    ae = asset_aesthetic(asset)
    if not ae:
        return None
    try:
        val = ae.get("overall")
        return None if val is None else float(val)
    except (TypeError, ValueError):
        return None


def aesthetic_dim(asset: dict, dim: str) -> float | None:
    ae = asset_aesthetic(asset)
    if not ae:
        return None
    dims = ae.get("dims")
    if not isinstance(dims, dict):
        return None
    try:
        val = dims.get(dim)
        return None if val is None else float(val)
    except (TypeError, ValueError):
        return None


def median_aesthetic_overall(
    assets: list[dict],
    *,
    purpose: AestheticPurpose = "default",
    cfg: AestheticConfig | None = None,
) -> float:
    cfg = cfg or AestheticConfig()
    values: list[float] = []
    for asset in assets:
        if purpose == "default" and not cfg.use_purpose_presets:
            val = aesthetic_overall(asset)
        else:
            val = purpose_overall(asset, purpose, cfg=cfg)
        if val is not None and val > 0:
            values.append(val)
    if not values:
        return 0.0
    values.sort()
    mid = len(values) // 2
    if len(values) % 2:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2.0


def _percentile_sorted(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    p = min(1.0, max(0.0, float(percentile)))
    idx = int(round(p * (len(values) - 1)))
    return values[idx]


def stratum_score_percentiles(
    assets: list[dict],
    *,
    purpose: AestheticPurpose = "default",
    cfg: AestheticConfig | None = None,
    percentile: float = 0.75,
) -> dict[str, float]:
    """Per-stratum score percentile within a trip pool (album-relative baseline)."""
    from travelogue.curation.aesthetic_blind_review import review_stratum_for_asset

    cfg = cfg or AestheticConfig()
    buckets: dict[str, list[float]] = {}
    for asset in assets:
        if asset.get("layoutEligible") is False or asset.get("type") == "video":
            continue
        stratum = review_stratum_for_asset(asset)
        if purpose == "default":
            score = aesthetic_overall(asset)
        else:
            score = purpose_overall(asset, purpose, cfg=cfg)
        if score is None:
            continue
        buckets.setdefault(stratum, []).append(float(score))
    return {s: round(_percentile_sorted(vals, percentile), 4) for s, vals in buckets.items() if vals}


def album_relative_multiplier(
    asset: dict,
    *,
    p_by_stratum: dict[str, float],
    purpose: AestheticPurpose = "cover",
    cfg: AestheticConfig | None = None,
    lo: float | None = None,
    hi: float | None = None,
) -> float:
    """Score ratio vs within-album stratum P75, clamped (PRD-SC §7.2)."""
    cfg = cfg or AestheticConfig()
    if not cfg.use_album_relative:
        return 1.0
    from travelogue.curation.aesthetic_blind_review import review_stratum_for_asset

    stratum = review_stratum_for_asset(asset)
    baseline = float(p_by_stratum.get(stratum) or 0.0)
    if purpose == "default":
        overall = aesthetic_overall(asset)
    else:
        overall = purpose_overall(asset, purpose, cfg=cfg)
    if overall is None or baseline <= 0:
        return 1.0
    ratio = float(overall) / baseline
    lo_v = float(lo if lo is not None else cfg.album_relative_lo)
    hi_v = float(hi if hi is not None else cfg.album_relative_hi)
    return min(hi_v, max(lo_v, ratio))


def relative_purpose_score(
    asset: dict,
    purpose: AestheticPurpose,
    *,
    p_by_stratum: dict[str, float],
    cfg: AestheticConfig | None = None,
) -> float | None:
    """Purpose score scaled by album-relative multiplier for within-stratum ranking."""
    cfg = cfg or AestheticConfig()
    base = purpose_overall(asset, purpose, cfg=cfg)
    if base is None:
        return None
    mult = album_relative_multiplier(
        asset,
        p_by_stratum=p_by_stratum,
        purpose=purpose,
        cfg=cfg,
    )
    return round(float(base) * mult, 4)


def aesthetic_multiplier(
    asset: dict,
    *,
    median_overall: float,
    enabled: bool = True,
    lo: float = 0.7,
    hi: float = 1.3,
    purpose: AestheticPurpose = "cover",
    cfg: AestheticConfig | None = None,
) -> float:
    """Overall relative to batch median, clamped (PA-T07 · U-COVER)."""
    if not enabled:
        return 1.0
    cfg = cfg or AestheticConfig()
    overall = purpose_overall(asset, purpose, cfg=cfg)
    if overall is None or median_overall <= 0:
        return 1.0
    ratio = overall / median_overall
    return min(hi, max(lo, ratio))


def build_aesthetic_explain(asset: dict, *, limit: int = 3) -> list[dict[str, Any]]:
    """Top contributing dimensions (mirrors ``build_cover_explain``)."""
    ae = asset_aesthetic(asset)
    if not ae:
        return []
    dims = ae.get("dims") if isinstance(ae.get("dims"), dict) else {}
    ranked = sorted(dims.items(), key=lambda kv: float(kv[1] or 0.0), reverse=True)
    out: list[dict[str, Any]] = []
    for code, value in ranked[:limit]:
        score = float(value or 0.0)
        label = _DIM_LABELS.get(code, code)
        direction = "突出" if score >= 0.6 else ("中等" if score >= 0.4 else "偏弱")
        out.append(
            {
                "code": code,
                "label": label,
                "score": round(score, 3),
                "reason": f"{label}表现{direction}",
            }
        )
    return out


def load_signal_cache(trip_dir: Path | None) -> dict[str, dict]:
    if trip_dir is None:
        return {}
    cache_path = Path(trip_dir) / "cache" / SIGNAL_CACHE_FILE
    if not cache_path.is_file():
        return {}
    try:
        raw = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict] = {}
    for key, val in raw.items():
        if isinstance(val, dict) and isinstance(val.get("signals"), dict):
            out[str(key)] = val
    return out


def save_signal_cache(trip_dir: Path | None, cache: dict[str, dict]) -> None:
    if trip_dir is None or not cache:
        return
    cache_path = Path(trip_dir) / "cache" / SIGNAL_CACHE_FILE
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(cache, ensure_ascii=False, sort_keys=True, indent=2)
        cache_path.write_text(payload + "\n", encoding="utf-8")
    except Exception:
        pass
