"""PRD-PIPELINE-PERF-V1 · R4.1 · NIMA warm coordinator batching."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from travelogue.config import AppConfig
from travelogue.curation.aesthetic_warm import AestheticWarmCoordinator


def test_warm_coordinator_batches_and_finish(tmp_path: Path) -> None:
    cfg = AppConfig()
    cfg.aesthetic.ml_calibrate = True
    cfg.aesthetic.warm_learned_on_ingest = True
    coord = AestheticWarmCoordinator(tmp_path, app_cfg=cfg, batch_size=2)
    calls: list[int] = []

    def _fake_score(assets, **_kwargs):
        calls.append(len(assets))
        return True

    with patch(
        "travelogue.curation.photo_cull_ml.apply_aesthetic_scores",
        side_effect=_fake_score,
    ):
        with patch(
            "travelogue.curation.aesthetic_score.refresh_aesthetic_ml_blend",
            return_value=False,
        ):
            coord.offer({"id": "a1", "type": "image", "displayFile": "assets/x.webp"})
            assert calls == []  # not yet at batch size
            coord.offer({"id": "a2", "type": "image", "displayFile": "assets/y.webp"})
            # batch of 2 should have flushed on a background thread
            stats = coord.finish()
    assert sum(calls) >= 2
    assert stats.errors == 0
