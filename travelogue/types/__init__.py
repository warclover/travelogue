"""Shared TypedDict contracts (incremental)."""

from travelogue.types.trip_hot import (
    ChapterRecord,
    ScreenRecord,
    StudioBlock,
    TitleArtMeta,
    TripHot,
)
from travelogue.types.trip_telemetry import (
    EmbedStatsDict,
    IngestElapsedDict,
    PipelineTelemetrySummary,
    PipelineTimingsDict,
)

__all__ = [
    "ChapterRecord",
    "ScreenRecord",
    "StudioBlock",
    "TitleArtMeta",
    "TripHot",
    "EmbedStatsDict",
    "IngestElapsedDict",
    "PipelineTelemetrySummary",
    "PipelineTimingsDict",
]
