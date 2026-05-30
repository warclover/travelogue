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
        self._assets: list[dict] = []
        self._lock = threading.Lock()
        self._worker: threading.Thread | None = None
        self._error: Exception | None = None

    def offer(self, asset: dict) -> None:
        spawn = False
        with self._lock:
            self._assets.append(asset)
            if len(self._assets) % self.chunk_size == 0:
                spawn = True
        if spawn:
            self._spawn_worker()

    def finish(self) -> None:
        with self._lock:
            pending = bool(self._assets)
        if pending:
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
            snapshot = list(self._assets)
        self._worker = threading.Thread(
            target=self._run_snapshot,
            args=(snapshot,),
            name="parallel-embed",
            daemon=True,
        )
        self._worker.start()

    def _run_snapshot(self, assets: list[dict]) -> None:
        try:
            from travelogue.vision.clip_encoder import get_clip_encoder
            from travelogue.vision.cache import prepare_scene_embeddings

            encoder = get_clip_encoder(self.cfg)
            deterministic = (
                self.cfg.clustering.deterministic
                or self.cfg.clustering.deterministic_strict
            )
            prepare_scene_embeddings(
                self.trip_dir,
                assets,
                encoder,
                force_recluster=False,
                deterministic=deterministic,
                cfg=self.cfg,
                apply_subject_class=False,
            )
        except Exception as exc:
            self._error = exc
            _log.warning("parallel embed snapshot failed: %s", exc)
