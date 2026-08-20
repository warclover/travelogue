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
    summary.update(_portfolio_telemetry(trip))
    return summary


def _portfolio_telemetry(trip: dict) -> dict:
    """AC-PFM-21 · 仅作品集写 edition / series / overflow；游记事件不加 edition。"""
    from travelogue.config.edition import EDITION_PORTFOLIO, resolve_edition

    if resolve_edition(trip) != EDITION_PORTFOLIO:
        return {}
    studio = trip.get("studio") if isinstance(trip.get("studio"), dict) else {}
    raw = studio.get("portfolio") if isinstance(studio.get("portfolio"), dict) else {}
    overflow = raw.get("overflow") if isinstance(raw.get("overflow"), dict) else {}
    out: dict = {"edition": EDITION_PORTFOLIO}
    if raw.get("seriesId"):
        out["seriesId"] = str(raw["seriesId"])
    if raw.get("pageCountSource"):
        out["pageCountSource"] = str(raw["pageCountSource"])
    count = overflow.get("count")
    if isinstance(count, (int, float)):
        out["overflowCount"] = int(count)
    return out


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
    if summary.get("edition"):
        bits = [f"edition={summary['edition']}"]
        if summary.get("seriesId"):
            bits.append(f"seriesId={summary['seriesId']}")
        if summary.get("pageCountSource"):
            bits.append(f"pageCountSource={summary['pageCountSource']}")
        if "overflowCount" in summary:
            bits.append(f"overflow.count={summary['overflowCount']}")
        lines.append("portfolio: " + ", ".join(bits))
    return lines
