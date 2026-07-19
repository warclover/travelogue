"""NIMA / learned-aesthetic warm during ingest (PRD-PIPELINE-PERF-V1 · R4.1).

Overlaps pyiqa scoring with ingest workers. Input path and cache keys match
``photo_cull_ml.apply_aesthetic_scores`` (D4: overlap only, no source change).
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

# Keep warm torch compute from starving ProcessPool WebP workers (MF-04).
_DEFAULT_TORCH_THREADS = 1


@dataclass
class AestheticWarmStats:
    hits: int = 0
    misses: int = 0
    warmed: int = 0
    errors: int = 0


class AestheticWarmCoordinator:
    """Batch learned-aesthetic scoring while assets arrive during ingest."""

    def __init__(
        self,
        trip_dir: Path,
        *,
        app_cfg: Any,
        batch_size: int = 16,
        torch_threads: int = _DEFAULT_TORCH_THREADS,
    ) -> None:
        self.trip_dir = Path(trip_dir)
        self.app_cfg = app_cfg
        self.batch_size = max(1, int(batch_size))
        self.torch_threads = max(1, int(torch_threads))
        self._pending: list[dict] = []
        self._lock = threading.Lock()
        self._worker: threading.Thread | None = None
        self._error: Exception | None = None
        self.stats = AestheticWarmStats()
        self._finished = False

    def offer(self, asset: dict) -> None:
        if self._finished:
            return
        run_chunk = False
        with self._lock:
            self._pending.append(asset)
            if len(self._pending) >= self.batch_size:
                run_chunk = True
        if run_chunk:
            self._spawn_worker()

    def finish(self) -> AestheticWarmStats:
        self._finished = True
        run_chunk = False
        with self._lock:
            if self._pending:
                run_chunk = True
        if run_chunk:
            self._spawn_worker()
        worker = self._worker
        if worker is not None:
            worker.join()
        if self._error is not None:
            _log.warning("aesthetic warm worker failed: %s", self._error)
            self.stats.errors += 1
        return self.stats

    def _spawn_worker(self) -> None:
        prior = self._worker
        if prior is not None:
            prior.join()
        with self._lock:
            batch = list(self._pending)
            self._pending.clear()
        if not batch:
            return
        self._worker = threading.Thread(
            target=self._run_batch,
            args=(batch,),
            name="aesthetic-warm",
            daemon=True,
        )
        self._worker.start()

    def _run_batch(self, assets: list[dict]) -> None:
        try:
            self._score_assets(assets)
        except Exception as exc:  # noqa: BLE001 — fail-open warm path
            self._error = exc
            _log.warning("aesthetic warm batch failed: %s", exc)

    def _score_assets(self, assets: list[dict]) -> None:
        from dataclasses import replace

        from travelogue.curation.aesthetic_score import refresh_aesthetic_ml_blend
        from travelogue.curation.photo_cull_ml import (
            _aesthetic_score,
            _cache_key_for_asset,
            _load_aesthetic_cache,
            apply_aesthetic_scores,
        )

        ae_cfg = self.app_cfg.aesthetic
        if not ae_cfg.enabled or not ae_cfg.ml_calibrate:
            return

        metric = str(ae_cfg.learned_metric or self.app_cfg.cull.aesthetic_metric or "nima")
        ml_device = ae_cfg.learned_device or self.app_cfg.cull.ml_device
        cull_cfg = replace(
            self.app_cfg.cull,
            aesthetic_metric=metric,
            allow_cpu_ml=ae_cfg.learned_allow_cpu or self.app_cfg.cull.allow_cpu_ml,
            ml_device=str(ml_device or "auto"),
        )

        cache_path = self.trip_dir / "cache" / "phase9_aesthetic.json"
        cache = _load_aesthetic_cache(cache_path)
        hits = 0
        pending_paths = 0
        for asset in assets:
            if asset.get("type", "image") == "video":
                continue
            rel = str(asset.get("displayFile") or asset.get("sourceFile") or "")
            if not rel:
                continue
            path = self.trip_dir / rel
            if not path.is_file():
                continue
            key = _cache_key_for_asset(asset, path, metric_name=metric)
            if cache.get(key) is not None or _aesthetic_score(asset) is not None:
                hits += 1
            else:
                pending_paths += 1

        try:
            import torch

            torch.set_num_threads(self.torch_threads)
        except Exception:
            pass

        scored = apply_aesthetic_scores(
            assets,
            trip_dir=self.trip_dir,
            cfg=cull_cfg,
            force_ml=True,
        )
        refreshed = sum(1 for a in assets if refresh_aesthetic_ml_blend(a, cfg=ae_cfg))
        with self._lock:
            self.stats.hits += hits
            self.stats.misses += pending_paths
            if scored or refreshed:
                self.stats.warmed += len(assets)
