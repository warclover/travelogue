"""Phase 7 rollback flag smoke tests (M29-B-04)."""

from __future__ import annotations

from travelogue.config import (
    AppConfig,
    IngestConfig,
    LayoutConfig,
    LayoutScoringConfig,
    PipelineConfig,
    VisionConfig,
)


def test_p6_rollback_values() -> None:
    """P7 fast-path defaults can revert to P6-equivalent flags."""
    p7 = AppConfig()
    assert p7.vision.batch_size == 16
    assert p7.ingest.webp_method == 2

    p6 = AppConfig(
        vision=VisionConfig(batch_size=0, prefer_web_derivative=False, session_singleton=False),
        pipeline=PipelineConfig(parallel_embed=False),
        ingest=IngestConfig(webp_method=6),
        layout=LayoutConfig(scoring=LayoutScoringConfig(incremental=False, skip_duplicate_signatures=False)),
    )
    assert p6.vision.batch_size == 0
    assert p6.pipeline.parallel_embed is False
    assert p6.ingest.webp_method == 6
