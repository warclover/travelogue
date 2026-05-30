"""TypedDict contracts for trip telemetry (P7 · incremental)."""

from __future__ import annotations

from typing import TypedDict


class PipelineTimingsDict(TypedDict, total=False):
    ingestMs: float
    embedMs: float
    clusterMs: float
    curateMs: float
    narrateMs: float
    renderMs: float
    exportMs: float
    totalMs: float


class EmbedStatsDict(TypedDict, total=False):
    elapsedMs: float
    batchSize: int
    batches: int
    cacheHitRatio: float
    prefetchEnabled: bool
    webDerivativeHits: int
    webDerivativeFallbacks: int
    fallbackSingle: int
    oomHalves: int
    autoBatchTuned: bool
    recommendedBatchSize: int


class IngestElapsedDict(TypedDict, total=False):
    decode: float
    webp: float
    faces: float
    dedupe: float
    total: float


class PipelineTelemetrySummary(TypedDict, total=False):
    pipelineStatus: str
    timingsMs: PipelineTimingsDict
    embed: EmbedStatsDict
    embedSkipped: bool
    visionSource: str
    ingestElapsedMs: IngestElapsedDict
