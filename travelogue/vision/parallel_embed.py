"""Background incremental CLIP embed during ingest (P7-C1)."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)


class ParallelEmbedCoordinator:
    """Embed asset chunks during ingest; clustering merges cache afterward."""

    def __init__(
        self,
        trip_dir: Path,
        *,
        cfg: Any,
        chunk_size: int = 32,
    ) -> None:
        self.trip_dir = trip_dir
        self.cfg = cfg
        self.chunk_size = max(1, int(chunk_size))
        self._all_offered: list[dict] = []
        self._pending: list[dict] = []
        self._lock = threading.Lock()
        self._worker: threading.Thread | None = None
        self._error: Exception | None = None

    def offer(self, asset: dict) -> None:
        run_chunk = False
        with self._lock:
            self._all_offered.append(asset)
            self._pending.append(asset)
            if len(self._pending) % self.chunk_size == 0:
                run_chunk = True
        if run_chunk:
            self._spawn_worker()

    def finish(self) -> None:
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
            _log.warning("parallel embed worker failed: %s", self._error)

    def _spawn_worker(self) -> None:
        prior = self._worker
        if prior is not None:
            prior.join()
        with self._lock:
            trip_assets = list(self._all_offered)
            self._pending.clear()
        self._worker = threading.Thread(
            target=self._run_snapshot,
            args=(trip_assets,),
            name="parallel-embed",
            daemon=True,
        )
        self._worker.start()

    def _run_snapshot(self, trip_assets: list[dict]) -> None:
        try:
            from travelogue.vision.cache import prepare_scene_embeddings
            from travelogue.vision.clip_encoder import get_clip_encoder

            encoder = get_clip_encoder(self.cfg)
            deterministic = (
                self.cfg.clustering.deterministic
                or self.cfg.clustering.deterministic_strict
            )
            prepare_scene_embeddings(
                self.trip_dir,
                trip_assets,
                encoder,
                force_recluster=False,
                deterministic=deterministic,
                cfg=self.cfg,
                apply_subject_class=False,
            )
        except Exception as exc:
            self._error = exc
            _log.warning("parallel embed snapshot failed: %s", exc)
