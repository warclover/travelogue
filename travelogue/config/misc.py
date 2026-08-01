"""Smaller domain configs: export, render, narrative, llm, pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.config._common import TriState
from travelogue.config_helpers import cfg_bool, cfg_int


@dataclass
class ExportConfig:
    max_zip_mb: int = 25


@dataclass
class RenderReadingConfig:
    default_profile: str = "default_hybrid"
    share_profile: str = "performance"
    mobile_profile: str = "legacy"
    longshot_surface_profile: str = "performance"


@dataclass
class RenderConfig:
    reading: RenderReadingConfig = field(default_factory=RenderReadingConfig)


@dataclass
class NarrativeConfig:
    tone_default: str = "relaxed"
    max_auto_fix_retries: int = 2
    banned_phrases: tuple[str, ...] = ()
    scope: str = "frame"
    decor_line_enabled: bool = True
    """Master switch for lite copy (hook / decorLine / epilogue generation)."""
    copy_generation_enabled: bool = True
    """When false, narrate skips all generated copy including decorLine."""
    show_hook_in_draft: bool = True
    """Draft preview: show hook on cover even if it matches stub/system patterns."""
    decor_line_max_chars: int = 30
    decor_line_candidates: int = 3
    decor_line_allow_empty: bool = True
    decor_line_intent_enabled: bool = True
    decor_line_intent_optional: bool = True
    decor_line_intent_note_max_chars: int = 30
    decor_line_min_fact_count: int = 2
    decor_line_voice_first: bool = True
    decor_line_llm_enabled: bool = False
    decor_line_visual_facts_enabled: bool = True


@dataclass
class LlmConfig:
    provider: str = "stub"  # stub | deepseek | dashscope
    model: str = "deepseek-chat"
    api_key_env: str = "DEEPSEEK_API_KEY"
    base_url: str | None = None
    timeout_sec: int = 120
    # ALG-V3 · Ready 层 TriState（可解析探测；不等于 MayCall / Import 实调）
    capability: TriState = "auto"
    # ALG-V3 · Import 层：有 Ready 时是否倾向走 LLM（默认 false → 导入恒 stub）
    prefer_llm_when_ready: bool = False
    # Pipeline Throughput · Phase B placeholders (G2 前默认 concurrency=1)
    narrate_concurrency: int = 1
    narrate_concurrency_backoff: bool = True


@dataclass
class PipelineConfig:
    parallel_embed: bool = True
    parallel_embed_chunk: int = 32
    # Pipeline Throughput · Phase A（G1 前默认 parallel_ingest=false）
    parallel_ingest: bool = False
    parallel_ingest_workers: int = 0  # 0 = auto
    parallel_ingest_min_photos: int = 12
    persist_every_n: int = 8
    # PRD-PIPELINE-PERF-V1 · R2.1/R2.2：ingest 预览档 + 选片后物化大图
    deferred_derivatives: bool = True


def pipeline_from_dict(raw: dict[str, Any]) -> PipelineConfig:
    import warnings

    legacy_orch = str(raw.get("orchestration") or "").strip().lower()
    if legacy_orch == "legacy":
        warnings.warn(
            "pipeline.orchestration=legacy was removed (M-D1); using unified run_trip path",
            UserWarning,
            stacklevel=2,
        )
    return PipelineConfig(
        parallel_embed=cfg_bool(raw, "parallel_embed", "parallelEmbed", True),
        parallel_embed_chunk=cfg_int(raw, "parallel_embed_chunk", "parallelEmbedChunk", 32),
        parallel_ingest=cfg_bool(raw, "parallel_ingest", "parallelIngest", False),
        parallel_ingest_workers=cfg_int(
            raw, "parallel_ingest_workers", "parallelIngestWorkers", 0
        ),
        parallel_ingest_min_photos=cfg_int(
            raw, "parallel_ingest_min_photos", "parallelIngestMinPhotos", 12
        ),
        persist_every_n=cfg_int(raw, "persist_every_n", "persistEveryN", 8),
        deferred_derivatives=cfg_bool(
            raw, "deferred_derivatives", "deferredDerivatives", True
        ),
    )


def render_reading_from_dict(raw: dict[str, Any]) -> RenderReadingConfig:
    return RenderReadingConfig(
        default_profile=str(raw.get("default_profile", "default_hybrid")),
        share_profile=str(raw.get("share_profile", "performance")),
        mobile_profile=str(raw.get("mobile_profile", "legacy")),
        longshot_surface_profile=str(raw.get("longshot_surface_profile", "performance")),
    )


def render_from_dict(raw: dict[str, Any]) -> RenderConfig:
    reading_raw = raw.get("reading") if isinstance(raw.get("reading"), dict) else {}
    return RenderConfig(reading=render_reading_from_dict(reading_raw))
