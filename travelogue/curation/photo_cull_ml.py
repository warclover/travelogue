"""Phase 9 W2 · optional pyiqa aesthetic scoring for photo cull."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from travelogue.config import CullConfig

_log = logging.getLogger(__name__)

_PYIQA_METRIC: Any | None = None
_PYIQA_METRIC_KEY: str | None = None


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


def apply_aesthetic_scores(
    assets: list[dict],
    *,
    trip_dir: Path | None,
    cfg: CullConfig,
) -> bool:
    """
    Write quality.aestheticScore for image assets when pyiqa is available.
    Returns True if at least one asset was scored.
    """
    if resolve_effective_mode(cfg) != "ml" or trip_dir is None:
        return False
    try:
        from PIL import Image

        metric = _get_metric(cfg)
    except Exception as exc:
        _log.warning("pyiqa init failed; fallback to rules scoring: %s", exc)
        return False

    scored = 0
    for asset in assets:
        if asset.get("type", "image") == "video":
            continue
        rel = str(asset.get("displayFile") or asset.get("sourceFile") or "")
        if not rel:
            continue
        path = trip_dir / rel
        if not path.is_file():
            continue
        try:
            with Image.open(path) as im:
                rgb = im.convert("RGB")
            import torch
            import torchvision.transforms as T

            tensor = T.ToTensor()(rgb).unsqueeze(0).to(_resolve_device(cfg))
            with torch.no_grad():
                raw = float(metric(tensor).item())
            q = asset.setdefault("quality", {})
            if isinstance(q, dict):
                q["aestheticScore"] = round(_norm_aesthetic(raw), 4)
                scored += 1
        except Exception as exc:
            _log.debug("aesthetic score skip %s: %s", asset.get("id"), exc)
    return scored > 0
