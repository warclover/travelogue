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
from typing import Any

from PIL import Image

from travelogue.config import AestheticConfig
from travelogue.curation.asset_quality import asset_sharpness
from travelogue.curation.curate_scoring import (
    _axis_rule_of_thirds_score,
    _subject_center_norm,
)
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
    cx, cy = _subject_center_norm(asset)
    return round((_axis_rule_of_thirds_score(cx) + _axis_rule_of_thirds_score(cy)) / 2.0, 4)


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

    return {
        "version": AESTHETIC_VERSION,
        "source": str(source or cfg.source or "rules"),
        "overall": round(_clamp01(overall), 4),
        "confidence": round(_clamp01(confidence), 4),
        "dims": dims,
        "signals": out_signals,
        "critique": None,
    }


def asset_aesthetic(asset: dict) -> dict | None:
    q = asset.get("quality")
    if isinstance(q, dict):
        ae = q.get("aesthetic")
        if isinstance(ae, dict):
            return ae
    return None


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
