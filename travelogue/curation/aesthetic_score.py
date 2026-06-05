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

from travelogue.config import AestheticConfig, AestheticWeights
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
AestheticPurpose = Literal["default", "cover", "hero", "solo"]
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
    """``quality.aestheticScore`` from pyiqa (topiq), or ``None`` when absent."""
    q = asset.get("quality")
    if isinstance(q, dict) and q.get("aestheticScore") is not None:
        try:
            return _clamp01(float(q["aestheticScore"]))
        except (TypeError, ValueError):
            return None
    return None


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
    blended, _, _ = _blend_ml_overall(rules, asset, cfg=cfg)
    return blended


def _blend_ml_overall(
    rules_overall: float,
    asset: dict,
    *,
    cfg: AestheticConfig,
) -> tuple[float, str, dict[str, float]]:
    """Blend rules overall with topiq when ``ml_calibrate`` is enabled."""
    base_source = str(cfg.source or "rules")
    if not cfg.ml_calibrate:
        return rules_overall, base_source, {}
    ml = _read_topiq_score(asset)
    if ml is None:
        return rules_overall, base_source, {}
    blend = _clamp01(cfg.ml_calibrate_blend)
    blended = (1.0 - blend) * rules_overall + blend * ml
    extra = {
        "rulesOverall": round(rules_overall, 4),
        "mlScore": round(ml, 4),
    }
    return round(_clamp01(blended), 4), "rules+ml", extra


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
    source: str | None = None,
) -> dict[str, Any]:
    """Synthesise the ``quality.aesthetic`` block from *signals* + asset fields."""
    cfg = cfg or AestheticConfig()
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
        "source": str(source or final_source),
        "overall": round(_clamp01(overall), 4),
        "confidence": round(_clamp01(confidence), 4),
        "dims": dims,
        "signals": out_signals,
        "critique": None,
    }


def refresh_aesthetic_ml_blend(asset: dict, *, cfg: AestheticConfig | None = None) -> bool:
    """Re-blend ``quality.aesthetic.overall`` after topiq scores are written (PA-4)."""
    cfg = cfg or AestheticConfig()
    if not cfg.ml_calibrate:
        return False
    ml = _read_topiq_score(asset)
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
    """Run topiq scoring + refresh ``quality.aesthetic.overall`` (curate hook, PA-4).

    Fail-open: returns False when ``ml_calibrate`` is off, pyiqa/torch unavailable,
    or no assets were scored — existing rules-only overall values are kept.
    """
    from travelogue.config import AppConfig

    app_cfg = cfg if cfg is not None else AppConfig()
    ae_cfg = app_cfg.aesthetic
    if not ae_cfg.enabled or not ae_cfg.ml_calibrate:
        return False
    from travelogue.curation.photo_cull_ml import apply_aesthetic_scores

    scored = apply_aesthetic_scores(
        assets,
        trip_dir=trip_dir,
        cfg=app_cfg.cull,
        force_ml=True,
    )
    refreshed = sum(1 for a in assets if refresh_aesthetic_ml_blend(a, cfg=ae_cfg))
    return scored or refreshed > 0


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
