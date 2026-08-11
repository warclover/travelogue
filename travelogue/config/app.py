"""Root application configuration aggregate."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from travelogue.config.aesthetic import AestheticConfig
from travelogue.config.ai_capability import AiCapabilityConfig
from travelogue.config.bookends import BookendsConfig
from travelogue.config.clustering import ClusteringConfig, GeocodeConfig
from travelogue.config.cohort import CohortConfig
from travelogue.config.cover_craft import CoverCraftConfig
from travelogue.config.cull import CullConfig
from travelogue.config.curate import CurateConfig
from travelogue.config.ingest import IngestConfig
from travelogue.config.layout import LayoutConfig
from travelogue.config.misc import (
    ExportConfig,
    LlmConfig,
    NarrativeConfig,
    PipelineConfig,
    RenderConfig,
)
from travelogue.config.mosaic import MosaicConfig
from travelogue.config.phase6 import Phase6ObservabilityConfig
from travelogue.config.shot_grouping import ShotGroupingConfig
from travelogue.config.studio import StudioConfig
from travelogue.config.template import TemplateAdminConfig, TemplateRouterConfig
from travelogue.config.title_art import TitleArtConfig
from travelogue.config.vision import VisionConfig

_log = logging.getLogger(__name__)


from travelogue.paths import default_trips_dir


@dataclass
class AppConfig:
    trips_dir: Path = field(default_factory=default_trips_dir)
    ingest: IngestConfig = field(default_factory=IngestConfig)
    cull: CullConfig = field(default_factory=CullConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    clustering: ClusteringConfig = field(default_factory=ClusteringConfig)
    shot_grouping: ShotGroupingConfig = field(default_factory=ShotGroupingConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    geocode: GeocodeConfig = field(default_factory=GeocodeConfig)
    curate: CurateConfig = field(default_factory=CurateConfig)
    bookends: BookendsConfig = field(default_factory=BookendsConfig)
    studio: StudioConfig = field(default_factory=StudioConfig)
    config_path: Path | None = None
    export: ExportConfig = field(default_factory=ExportConfig)
    render: RenderConfig = field(default_factory=RenderConfig)
    narrative: NarrativeConfig = field(default_factory=NarrativeConfig)
    llm: LlmConfig = field(default_factory=LlmConfig)
    phase6: Phase6ObservabilityConfig = field(default_factory=Phase6ObservabilityConfig)
    template_router: TemplateRouterConfig = field(default_factory=TemplateRouterConfig)
    template_admin: TemplateAdminConfig = field(default_factory=TemplateAdminConfig)
    mosaic: MosaicConfig = field(default_factory=MosaicConfig)
    cohort: CohortConfig = field(default_factory=CohortConfig)
    aesthetic: AestheticConfig = field(default_factory=AestheticConfig)
    title_art: TitleArtConfig = field(default_factory=TitleArtConfig)
    cover_craft: CoverCraftConfig = field(default_factory=CoverCraftConfig)
    ai_capability: AiCapabilityConfig = field(default_factory=AiCapabilityConfig)
