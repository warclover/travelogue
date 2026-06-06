"""Smaller domain configs: export, render, narrative, llm, pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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
    decor_line_max_chars: int = 30
    decor_line_candidates: int = 3
    decor_line_allow_empty: bool = True
    decor_line_intent_enabled: bool = True
    decor_line_intent_optional: bool = True
    decor_line_intent_note_max_chars: int = 30


@dataclass
class LlmConfig:
    provider: str = "stub"  # stub | deepseek | dashscope
    model: str = "deepseek-chat"
    api_key_env: str = "DEEPSEEK_API_KEY"
    base_url: str | None = None
    timeout_sec: int = 120


@dataclass
class PipelineConfig:
    parallel_embed: bool = True
    parallel_embed_chunk: int = 32


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


def pipeline_from_dict(raw: dict[str, Any]) -> PipelineConfig:
    return PipelineConfig(
        parallel_embed=cfg_bool(raw, "parallel_embed", "parallelEmbed", True),
        parallel_embed_chunk=cfg_int(raw, "parallel_embed_chunk", "parallelEmbedChunk", 32),
    )
