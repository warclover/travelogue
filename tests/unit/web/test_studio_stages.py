"""Studio stage hints and pipeline estimates (P5-I2)."""

from __future__ import annotations

from travelogue.web.studio_stages import (
    ingest_stage_hint,
    pipeline_estimate_hint,
    pipeline_estimate_tiers,
)


def test_ingest_stage_hint_tiers() -> None:
    assert "30" in ingest_stage_hint(20)
    assert "分钟" in ingest_stage_hint(120)


def test_pipeline_estimate_hint_by_photo_count() -> None:
    assert pipeline_estimate_hint(30) == "约 3–5 分钟"
    assert pipeline_estimate_hint(80) == "约 5–8 分钟"
    assert pipeline_estimate_hint(150) == "约 8–15 分钟"
    assert pipeline_estimate_hint(300) == "约 12–25 分钟"


def test_pipeline_estimate_tiers_shape() -> None:
    tiers = pipeline_estimate_tiers()
    assert tiers
    assert all("maxPhotos" in row and "hint" in row for row in tiers)
