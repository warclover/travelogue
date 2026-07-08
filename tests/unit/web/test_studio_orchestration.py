"""M-D1 · unified studio pipeline orchestration."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from tests.studio_test_helpers import make_test_album
from travelogue.config import AppConfig, ClusteringConfig, PipelineConfig, VisionConfig
from travelogue.config.misc import pipeline_from_dict
from travelogue.web.studio_pipeline import run_studio_pipeline


def test_pipeline_from_dict_warns_on_removed_legacy_orchestration() -> None:
    with pytest.warns(UserWarning, match="pipeline.orchestration=legacy was removed"):
        cfg = pipeline_from_dict({"orchestration": "legacy"})
    assert cfg.parallel_embed is True


def test_unified_studio_pipeline_imports_album(tmp_path: Path) -> None:
    album = make_test_album(tmp_path, 6)
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="false"),
        vision=VisionConfig(enabled="false"),
        pipeline=PipelineConfig(parallel_embed=False),
    )
    result = run_studio_pipeline(
        album,
        trips_dir=tmp_path / "trips",
        dedupe=False,
        app_config=cfg,
    )
    trip = json.loads(result.trip_json.read_text(encoding="utf-8"))
    assert trip.get("tripId")
    assert result.photo_count >= 1
