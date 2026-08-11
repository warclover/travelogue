"""Load config.yaml (see config.yaml.example). Public API unchanged after P2-2 split."""

from __future__ import annotations

from travelogue.config._common import TriState
from travelogue.config.aesthetic import (
    DEFAULT_STRATUM_BLENDS,
    AestheticConfig,
    AestheticMllmConfig,
    AestheticPurposePresets,
    AestheticWeights,
    resolve_learned_blend,
)
from travelogue.config.app import AppConfig
from travelogue.config.bookends import (
    BookendsConfig,
    BookendsPairingConfig,
    BookendsPluginsConfig,
    BookendsTitleSafeConfig,
    bookends_config_from_dict,
)
from travelogue.config.clustering import (
    ClusteringConfig,
    GeoClusterConfig,
    GeocodeConfig,
    SceneClusterConfig,
)
from travelogue.config.cohort import CohortConfig
from travelogue.config.cull import CullConfig
from travelogue.config.curate import CurateConfig
from travelogue.config.errors import ConfigError
from travelogue.config.food_role import FoodRoleConfig, food_role_config_from_dict
from travelogue.config.ingest import DEFAULT_RAW_BLOCKLIST_SUFFIXES, IngestConfig
from travelogue.config.layout import LayoutConfig, LayoutFeedbackConfig, LayoutScoringConfig
from travelogue.config.layout_vibe import (
    VIBE_FIT_PHOTO_EXPERIMENTAL,
    VIBE_MAGAZINE_DEFAULT,
    apply_layout_vibe_to_config,
    mosaic_profile_for_vibe,
    resolve_layout_vibe,
    set_trip_layout_vibe,
)
from travelogue.config.loader import load_config, patch_config_file
from travelogue.config.misc import (
    ExportConfig,
    LlmConfig,
    NarrativeConfig,
    PipelineConfig,
    RenderConfig,
    RenderReadingConfig,
)
from travelogue.config.mosaic import (
    EqualGridAdmissionConfig,
    MosaicConfig,
    MosaicDensityBudgetConfig,
    NearSceneCloneGateConfig,
    SelectionOptimizationConfig,
    TemplateContractConfig,
    TemplateExperimentsConfig,
)
from travelogue.config.phase6 import (
    Phase6AcThresholds,
    Phase6AlertThresholds,
    Phase6ObservabilityConfig,
    Phase6RolloutConfig,
)
from travelogue.config.runtime import (
    app_config_scope,
    config_override,
    default_enable_food_grid,
    default_mixed_proximity_seconds,
    default_mundane_grid_buckets,
    default_screen_plan_scope,
    default_web_layout_engine,
    get_config,
    reading_profile_defaults,
    reset_config_cache,
)
from travelogue.config.shot_grouping import (
    ShotGroupingConfig,
    ShotGroupingLookConfig,
    ShotGroupingMosaicConfig,
    ShotGroupingSceneConfig,
    resolve_look_enabled,
    resolve_shot_group_mosaic_policy,
    resolve_shot_grouping_enabled,
    shot_grouping_from_dict,
)
from travelogue.config.studio import (
    GcsPosterBricConfig,
    OutputRecipeBandsConfig,
    OutputRecipeConfig,
    StudioConfig,
    studio_config_expose,
)
from travelogue.config.template import TemplateAdminConfig, TemplateRouterConfig
from travelogue.config.ai_capability import (
    AiCapabilityConfig,
    AiEvalConfig,
    IntentBriefConfig,
    LayoutCriticConfig,
    MosaicJudgeConfig,
    ai_capability_config_from_dict,
)
from travelogue.config.title_art import TitleArtConfig, title_art_config_from_dict
from travelogue.config.cover_craft import (
    CoverCraftConfig,
    cover_craft_config_from_dict,
)
from travelogue.config.vision import VisionConfig

__all__ = [
    "DEFAULT_RAW_BLOCKLIST_SUFFIXES",
    "DEFAULT_STRATUM_BLENDS",
    "TriState",
    "AestheticConfig",
    "AestheticMllmConfig",
    "AestheticPurposePresets",
    "AestheticWeights",
    "AppConfig",
    "BookendsConfig",
    "BookendsPairingConfig",
    "BookendsPluginsConfig",
    "BookendsTitleSafeConfig",
    "ClusteringConfig",
    "ConfigError",
    "CohortConfig",
    "CullConfig",
    "CurateConfig",
    "FoodRoleConfig",
    "food_role_config_from_dict",
    "ExportConfig",
    "GeoClusterConfig",
    "GeocodeConfig",
    "IngestConfig",
    "LayoutConfig",
    "LayoutFeedbackConfig",
    "LayoutScoringConfig",
    "VIBE_FIT_PHOTO_EXPERIMENTAL",
    "VIBE_MAGAZINE_DEFAULT",
    "apply_layout_vibe_to_config",
    "mosaic_profile_for_vibe",
    "resolve_layout_vibe",
    "set_trip_layout_vibe",
    "LlmConfig",
    "MosaicConfig",
    "EqualGridAdmissionConfig",
    "NearSceneCloneGateConfig",
    "MosaicDensityBudgetConfig",
    "TemplateContractConfig",
    "TemplateExperimentsConfig",
    "SelectionOptimizationConfig",
    "NarrativeConfig",
    "Phase6AcThresholds",
    "Phase6AlertThresholds",
    "Phase6ObservabilityConfig",
    "Phase6RolloutConfig",
    "PipelineConfig",
    "RenderConfig",
    "RenderReadingConfig",
    "SceneClusterConfig",
    "ShotGroupingConfig",
    "ShotGroupingLookConfig",
    "ShotGroupingMosaicConfig",
    "ShotGroupingSceneConfig",
    "resolve_look_enabled",
    "resolve_shot_grouping_enabled",
    "resolve_shot_group_mosaic_policy",
    "shot_grouping_from_dict",
    "OutputRecipeBandsConfig",
    "GcsPosterBricConfig",
    "OutputRecipeConfig",
    "StudioConfig",
    "TemplateAdminConfig",
    "TemplateRouterConfig",
    "TitleArtConfig",
    "title_art_config_from_dict",
    "CoverCraftConfig",
    "cover_craft_config_from_dict",
    "AiCapabilityConfig",
    "AiEvalConfig",
    "IntentBriefConfig",
    "LayoutCriticConfig",
    "MosaicJudgeConfig",
    "ai_capability_config_from_dict",
    "VisionConfig",
    "app_config_scope",
    "bookends_config_from_dict",
    "config_override",
    "default_enable_food_grid",
    "default_mundane_grid_buckets",
    "default_mixed_proximity_seconds",
    "default_screen_plan_scope",
    "default_web_layout_engine",
    "get_config",
    "load_config",
    "patch_config_file",
    "reading_profile_defaults",
    "reset_config_cache",
    "resolve_learned_blend",
    "studio_config_expose",
]
