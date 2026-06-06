"""Phase 9 W2 · optional pyiqa aesthetic scoring for photo cull."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from travelogue.config import CullConfig

_log = logging.getLogger(__name__)

_PYIQA_METRIC: Any | None = None
_PYIQA_METRIC_KEY: str | None = None
_ML_BATCH_SIZE = 16
_AESTHETIC_CACHE_FILE = "phase9_aesthetic.json"


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


def _norm_aesthetic(raw: float) -> float:
    """Map pyiqa output to [0, 1] (metrics are typically ~0–1 or 0–100)."""
    if raw <= 1.0:
        return max(0.0, min(1.0, raw))
    return max(0.0, min(1.0, raw / 100.0))


def _cache_key_for_asset(asset: dict, path: Path, *, metric_name: str) -> str:
    sig = str(asset.get("contentSig") or "").strip()
    if sig:
        return f"{metric_name}|sig:{sig}"
    try:
        stat = path.stat()
        stamp = f"{int(stat.st_mtime)}:{stat.st_size}"
    except OSError:
        stamp = "0:0"
    rel = str(asset.get("displayFile") or asset.get("sourceFile") or path.name)
    return f"{metric_name}|rel:{rel}|stamp:{stamp}"


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
        from PIL import Image

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
            if str(q.get("aestheticMetric") or "") == metric_name:
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
            q = asset.setdefault("quality", {})
            if isinstance(q, dict):
                q["aestheticScore"] = round(float(cached), 4)
                q["aestheticMetric"] = metric_name
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
            score = round(_norm_aesthetic(raw), 4)
            q = asset.setdefault("quality", {})
            if isinstance(q, dict):
                q["aestheticScore"] = score
                q["aestheticMetric"] = metric_name
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
                rgb = im.convert("RGB")
            batch_assets.append(asset)
            batch_tensors.append(to_tensor(rgb))
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
