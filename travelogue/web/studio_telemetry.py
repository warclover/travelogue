"""Read pipeline / CLIP telemetry from trip.json for Studio and benchmarks."""

from __future__ import annotations

from travelogue.types.trip_telemetry import (
    EmbedStatsDict,
    IngestElapsedDict,
    PipelineTelemetrySummary,
    PipelineTimingsDict,
)


def build_pipeline_telemetry_summary(trip: dict) -> PipelineTelemetrySummary:
    """Compact, schema-aligned telemetry for API and CLI."""
    pipe = trip.get("pipeline") or {}
    clustering = (trip.get("curation") or {}).get("clustering") or {}
    embed_raw = clustering.get("embedStats") or {}
    vision = clustering.get("vision") or {}
    ingest_stats = trip.get("ingestStats") or {}

    timings: PipelineTimingsDict = {}
    for key, val in (pipe.get("timings") or {}).items():
        if isinstance(val, (int, float)):
            timings[key] = float(val)

    embed: EmbedStatsDict = {}
    for key in (
        "elapsedMs",
        "batchSize",
        "batches",
        "cacheHitRatio",
        "prefetchEnabled",
        "webDerivativeHits",
        "webDerivativeFallbacks",
        "fallbackSingle",
        "oomHalves",
        "autoBatchTuned",
        "recommendedBatchSize",
    ):
        if key in embed_raw and embed_raw[key] is not None:
            embed[key] = embed_raw[key]  # type: ignore[literal-required]

    ingest_elapsed: IngestElapsedDict = {}
    raw_elapsed = ingest_stats.get("elapsedMs")
    if isinstance(raw_elapsed, dict):
        for key, val in raw_elapsed.items():
            if isinstance(val, (int, float)):
                ingest_elapsed[key] = float(val)  # type: ignore[literal-required]

    summary: PipelineTelemetrySummary = {
        "pipelineStatus": str(pipe.get("status") or ""),
    }
    if timings:
        summary["timingsMs"] = timings
    if embed:
        summary["embed"] = embed
    if clustering.get("embedSkipped") is True:
        summary["embedSkipped"] = True
    if vision.get("source"):
        summary["visionSource"] = str(vision["source"])
    if ingest_elapsed:
        summary["ingestElapsedMs"] = ingest_elapsed
    return summary


def format_telemetry_lines(summary: PipelineTelemetrySummary) -> list[str]:
    """Human-readable lines for logs and benchmark output."""
    lines: list[str] = []
    status = summary.get("pipelineStatus")
    if status:
        lines.append(f"pipeline.status={status}")
    timings = summary.get("timingsMs") or {}
    if timings:
        parts = ", ".join(f"{k}={v:.1f}" for k, v in sorted(timings.items()))
        lines.append(f"pipeline.timings: {parts}")
    embed = summary.get("embed") or {}
    if embed:
        bits = []
        if "elapsedMs" in embed:
            bits.append(f"elapsedMs={embed['elapsedMs']}")
        if "batchSize" in embed:
            bits.append(f"batchSize={embed['batchSize']}")
        if "cacheHitRatio" in embed:
            bits.append(f"cacheHitRatio={embed['cacheHitRatio']}")
        if bits:
            lines.append(f"embedStats: {', '.join(bits)}")
    if summary.get("embedSkipped"):
        lines.append("embedStats: skipped (cache reuse)")
    if summary.get("visionSource"):
        lines.append(f"vision.source={summary['visionSource']}")
    ingest = summary.get("ingestElapsedMs") or {}
    if ingest:
        parts = ", ".join(f"{k}={v:.1f}" for k, v in sorted(ingest.items()))
        lines.append(f"ingestStats.elapsedMs: {parts}")
    return lines
