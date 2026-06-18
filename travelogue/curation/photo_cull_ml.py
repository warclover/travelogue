"""Phase 9 W2 · optional pyiqa aesthetic scoring for photo cull."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from PIL import Image

from travelogue.config import CullConfig

_log = logging.getLogger(__name__)

_PYIQA_METRIC: Any | None = None
_PYIQA_METRIC_KEY: str | None = None
_ML_BATCH_SIZE = 16
_ML_INPUT_SIDE = 512
_AESTHETIC_CACHE_FILE = "phase9_aesthetic.json"

# AA · M1: human-aesthetic models (AVA-trained etc.) vs IQA (topiq).
LEARNED_AESTHETIC_METRICS: frozenset[str] = frozenset(
    {"nima", "nima-v2", "nima-koniq", "clipiqa", "clipiqa+", "topiq_nr"}
)
DEFAULT_LEARNED_AESTHETIC_METRIC = "nima"


def pyiqa_available() -> bool:
    try:
        import pyiqa  # noqa: F401
    except ImportError:
        return False
    return True


def _cuda_available() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except ImportError:
        return False


def resolve_effective_mode(cfg: CullConfig) -> str:
    """Map config mode to runtime scorer: rules | ml."""
    mode = str(cfg.mode or "rules").lower().strip()
    if mode == "rules":
        return "rules"
    if mode in ("ml", "auto"):
        if not pyiqa_available():
            return "rules"
        if _cuda_available():
            return "ml"
        if cfg.allow_cpu_ml or str(cfg.ml_device).lower() == "cpu":
            return "ml"
        return "rules"
    return "rules"


def _resolve_device(cfg: CullConfig) -> str:
    device = str(cfg.ml_device or "auto").lower()
    if device == "auto":
        return "cuda" if _cuda_available() else "cpu"
    return device


def _get_metric(cfg: CullConfig):
    global _PYIQA_METRIC, _PYIQA_METRIC_KEY
    metric_name = str(cfg.aesthetic_metric or "topiq_nr")
    if _PYIQA_METRIC is not None and _PYIQA_METRIC_KEY == metric_name:
        return _PYIQA_METRIC
    import pyiqa

    device = _resolve_device(cfg)
    _PYIQA_METRIC = pyiqa.create_metric(metric_name, device=device)
    _PYIQA_METRIC_KEY = metric_name
    return _PYIQA_METRIC


def _norm_aesthetic(raw: float, *, metric_name: str = "") -> float:
    """Map pyiqa output to [0, 1] (metric-specific heuristics)."""
    value = float(raw)
    name = str(metric_name or "").lower()
    if "nima" in name:
        if 1.0 < value <= 10.0:
            return max(0.0, min(1.0, (value - 1.0) / 9.0))
        return max(0.0, min(1.0, value))
    if value <= 1.0:
        return max(0.0, min(1.0, value))
    if value <= 10.0:
        return max(0.0, min(1.0, value / 10.0))
    return max(0.0, min(1.0, value / 100.0))


def _write_ml_aesthetic_fields(asset: dict, *, score: float, metric_name: str) -> None:
    """Legacy flat fields + PA ``quality.aesthetic.signals.learnedAesthetic``."""
    q = asset.setdefault("quality", {})
    if not isinstance(q, dict):
        return
    rounded = round(float(score), 4)
    q["aestheticScore"] = rounded
    q["aestheticMetric"] = metric_name
    ae = q.get("aesthetic")
    if not isinstance(ae, dict):
        ae = {}
        q["aesthetic"] = ae
    sig = ae.get("signals")
    if not isinstance(sig, dict):
        sig = {}
        ae["signals"] = sig
    sig["learnedAesthetic"] = rounded
    sig["learnedMetric"] = metric_name


def _ml_input_tensor(im: Image.Image, to_tensor: Any) -> Any:
    """Resize/pad to fixed square so batched pyiqa inference is shape-safe."""
    rgb = im.convert("RGB")
    side = int(_ML_INPUT_SIDE)
    w, h = rgb.size
    scale = side / max(w, h, 1)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    resized = rgb.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (side, side), (0, 0, 0))
    canvas.paste(resized, ((side - nw) // 2, (side - nh) // 2))
    return to_tensor(canvas)


def _cache_key_for_asset(asset: dict, path: Path, *, metric_name: str) -> str:
    sig = str(asset.get("contentSig") or "").strip()
    inp = f"inp{_ML_INPUT_SIDE}"
    if sig:
        return f"{metric_name}|{inp}|sig:{sig}"
    try:
        stat = path.stat()
        stamp = f"{int(stat.st_mtime)}:{stat.st_size}"
    except OSError:
        stamp = "0:0"
    rel = str(asset.get("displayFile") or asset.get("sourceFile") or path.name)
    return f"{metric_name}|{inp}|rel:{rel}|stamp:{stamp}"


def _load_aesthetic_cache(cache_path: Path) -> dict[str, float]:
    if not cache_path.is_file():
        return {}
    try:
        raw = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        _log.debug("aesthetic cache read skipped for %s", cache_path, exc_info=True)
        return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for k, v in raw.items():
        try:
            out[str(k)] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def _save_aesthetic_cache(cache_path: Path, cache: dict[str, float]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(cache, ensure_ascii=False, sort_keys=True, indent=2)
    cache_path.write_text(payload + "\n", encoding="utf-8")


def _aesthetic_score(asset: dict) -> float | None:
    q = asset.get("quality")
    if isinstance(q, dict) and q.get("aestheticScore") is not None:
        try:
            return float(q["aestheticScore"])
        except (TypeError, ValueError):
            return None
    return None


def _ml_runtime_available(cfg: CullConfig, *, force_ml: bool = False) -> bool:
    """Whether pyiqa scoring can run (cull ML mode or PA calibration force)."""
    if not pyiqa_available():
        return False
    if not force_ml and resolve_effective_mode(cfg) != "ml":
        return False
    if _cuda_available():
        return True
    return bool(cfg.allow_cpu_ml or str(cfg.ml_device).lower() == "cpu")


def apply_aesthetic_scores(
    assets: list[dict],
    *,
    trip_dir: Path | None,
    cfg: CullConfig,
    force_ml: bool = False,
) -> bool:
    """
    Write quality.aestheticScore for image assets when pyiqa is available.
    Returns True if at least one asset was scored.

    When *force_ml* is True (PA-4 calibration), scoring runs even if cull mode is
    ``rules``, subject to the same device / pyiqa availability checks.
    """
    if trip_dir is None or not _ml_runtime_available(cfg, force_ml=force_ml):
        return False
    try:
        metric = _get_metric(cfg)
    except Exception as exc:
        _log.warning("pyiqa init failed; fallback to rules scoring: %s", exc)
        return False

    try:
        import torch
        import torchvision.transforms as T
    except Exception as exc:
        _log.warning("torch/torchvision unavailable for ML cull path: %s", exc)
        return False

    metric_name = str(cfg.aesthetic_metric or "topiq_nr")
    device = _resolve_device(cfg)
    to_tensor = T.ToTensor()
    cache_path = trip_dir / "cache" / _AESTHETIC_CACHE_FILE
    cache = _load_aesthetic_cache(cache_path)
    cache_dirty = False
    pending: list[tuple[dict, Path]] = []
    for asset in assets:
        if asset.get("type", "image") == "video":
            continue
        q = asset.get("quality")
        if isinstance(q, dict) and q.get("aestheticScore") is not None:
            metric_ok = str(q.get("aestheticMetric") or "") == metric_name
            sig = q.get("aesthetic")
            learned_ok = False
            if isinstance(sig, dict):
                inner = sig.get("signals")
                if isinstance(inner, dict):
                    learned_ok = str(inner.get("learnedMetric") or "") == metric_name
            if metric_ok and learned_ok:
                continue
        rel = str(asset.get("displayFile") or asset.get("sourceFile") or "")
        if not rel:
            continue
        path = trip_dir / rel
        if not path.is_file():
            continue
        key = _cache_key_for_asset(asset, path, metric_name=metric_name)
        cached = cache.get(key)
        if cached is not None:
            _write_ml_aesthetic_fields(asset, score=float(cached), metric_name=metric_name)
            continue
        pending.append((asset, path))

    def _score_batch(batch_assets: list[dict], batch_tensors: list[Any]) -> None:
        nonlocal cache_dirty
        if not batch_assets:
            return
        tensor = torch.stack(batch_tensors, dim=0).to(device)
        with torch.no_grad():
            out = metric(tensor)
        if hasattr(out, "detach"):
            values = out.detach().flatten().tolist()
            raw_scores = [float(v) for v in values]
        else:
            raw_scores = [float(out)]
        if len(raw_scores) == 1 and len(batch_assets) > 1:
            raw_scores = raw_scores * len(batch_assets)
        for asset, raw in zip(batch_assets, raw_scores, strict=False):
            score = round(_norm_aesthetic(raw, metric_name=metric_name), 4)
            _write_ml_aesthetic_fields(asset, score=score, metric_name=metric_name)
            rel = str(asset.get("displayFile") or asset.get("sourceFile") or "")
            if rel:
                key = _cache_key_for_asset(asset, trip_dir / rel, metric_name=metric_name)
                cache[key] = float(score)
                cache_dirty = True

    batch_assets: list[dict] = []
    batch_tensors: list[Any] = []
    for asset, path in pending:
        try:
            with Image.open(path) as im:
                batch_assets.append(asset)
                batch_tensors.append(_ml_input_tensor(im, to_tensor))
            if len(batch_assets) >= _ML_BATCH_SIZE:
                _score_batch(batch_assets, batch_tensors)
                batch_assets = []
                batch_tensors = []
        except Exception as exc:
            _log.debug("aesthetic score skip %s: %s", asset.get("id"), exc)
    _score_batch(batch_assets, batch_tensors)
    if cache_dirty:
        try:
            _save_aesthetic_cache(cache_path, cache)
        except Exception as exc:
            _log.debug("aesthetic cache write skipped: %s", exc)
    return any(_aesthetic_score(a) is not None for a in assets)
