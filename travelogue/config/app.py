"""Root application configuration aggregate."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from travelogue.config.aesthetic import AestheticConfig
from travelogue.config.clustering import ClusteringConfig, GeocodeConfig
from travelogue.config.cohort import CohortConfig
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
from travelogue.config.studio import StudioConfig
from travelogue.config.template import TemplateAdminConfig, TemplateRouterConfig
from travelogue.config.vision import VisionConfig
from travelogue.paths import ROOT

_log = logging.getLogger(__name__)


def default_trips_dir() -> Path:
    try:
        from travelogue.desktop.bundle import default_trips_dir

        return default_trips_dir()
    except Exception:
        _log.debug(
            "desktop default_trips_dir unavailable; using ROOT/trips", exc_info=True
        )
        return ROOT / "trips"


@dataclass
class AppConfig:
    trips_dir: Path = field(default_factory=default_trips_dir)
    ingest: IngestConfig = field(default_factory=IngestConfig)
    cull: CullConfig = field(default_factory=CullConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    clustering: ClusteringConfig = field(default_factory=ClusteringConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    geocode: GeocodeConfig = field(default_factory=GeocodeConfig)
    curate: CurateConfig = field(default_factory=CurateConfig)
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
