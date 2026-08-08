"""Studio workbench configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from travelogue.config.app import AppConfig


# Studio Popover platforms (Phase A+B + compose). Phase C stays CLI/API-only.
DEFAULT_LONGSHOT2_PLATFORMS: tuple[str, ...] = (
    "wechat_moments",
    "xiaohongshu",
    "wechat_official",
    "poster_bric",
    "album_spread",
)


@dataclass
class Longshot2Config:
    """Longshot 2.0 platform export flags (PRD §13)."""

    enabled: bool = True
    platforms: tuple[str, ...] = DEFAULT_LONGSHOT2_PLATFORMS
    smart_crop_enabled: bool = False


@dataclass
class OutputRecipeBandsConfig:
    """Output Recipe band thresholds (AC-OR-01)."""

    sparse_max: int = 9
    ambiguous_max: int = 30
    narrative_chapter_hint_at: int = 50


@dataclass
class OutputRecipeConfig:
    """Output Recipe V1 feature flag + bands (D-OR-24)."""

    enabled: bool = False
    bands: OutputRecipeBandsConfig = field(default_factory=OutputRecipeBandsConfig)


@dataclass
class GcsPosterBricConfig:
    """GCS Track B · poster_bric Writer (PRD features.gcs_poster_bric)."""

    enabled: bool = True


@dataclass
class StudioConfig:
    """Studio workbench (Phase 4 M17 · G1)."""

    g1_confirm_structure: bool = False
    import_dual_mode_enabled: bool = True
    success_refined_default_enabled: bool = True
    import_sheet_large_enabled: bool = True
    layout_templates_internal: bool = False
    # NAS · 默认 False；正式面勿 PATCH。亦可用 env TRAVELOGUE_AI_SURFACE=1。
    ai_surface_enabled: bool = False
    longshot2: Longshot2Config = field(default_factory=Longshot2Config)
    output_recipe: OutputRecipeConfig = field(default_factory=OutputRecipeConfig)
    gcs_poster_bric: GcsPosterBricConfig = field(default_factory=GcsPosterBricConfig)

    @property
    def longshot2_enabled(self) -> bool:
        return bool(self.longshot2.enabled)

    @property
    def longshot2_platforms(self) -> list[str]:
        return list(self.longshot2.platforms)


def studio_config_expose(cfg: AppConfig) -> dict[str, Any]:
    """Subset of config safe for Studio GET /__travelogue/config.

    CSC W1: adds ``happyPath`` (recipe_id + L0/L1/Advanced key lists). Existing
    fields stay for backward compatibility; settings UI should prefer ``l1Keys``
    for the common zone (see csc-w0-settings-surface-inventory.md).
    """
    or_cfg = getattr(cfg.studio, "output_recipe", None) or OutputRecipeConfig()
    bands = getattr(or_cfg, "bands", None) or OutputRecipeBandsConfig()
    # Layer-0 constants (must not import orchestrator from config).
    from travelogue.constants import (
        ADVANCED_SETTINGS_KEYS,
        L0_OPS_ROOTS,
        L1_RESULT_KEYS,
        RECIPE_ID_STUDIO_DEFAULT,
    )

    return {
        "clustering": {
            "enabled": cfg.clustering.enabled,
            "segmentCurateMode": cfg.clustering.segment_curate_mode,
            "sceneClusterMode": cfg.clustering.scene_cluster_mode,
        },
        "vision": {
            "enabled": cfg.vision.enabled,
        },
        "layout": {
            "scoring": {
                "enabled": cfg.layout.scoring.enabled,
            },
            "strategyEngine": {
                "enabled": cfg.layout.strategy_engine.enabled,
                "defaultStrategyId": cfg.layout.strategy_engine.default_strategy_id,
            },
        },
        "studio": {
            "g1ConfirmStructure": cfg.studio.g1_confirm_structure,
            "importDualModeEnabled": cfg.studio.import_dual_mode_enabled,
            "successRefinedDefaultEnabled": cfg.studio.success_refined_default_enabled,
            "importSheetLargeEnabled": cfg.studio.import_sheet_large_enabled,
            "layoutTemplatesInternal": cfg.studio.layout_templates_internal,
            "longshot2": {
                "enabled": cfg.studio.longshot2.enabled,
                "platforms": list(cfg.studio.longshot2.platforms),
                "smartCrop": {
                    "enabled": cfg.studio.longshot2.smart_crop_enabled,
                },
            },
            "outputRecipe": {
                "enabled": bool(or_cfg.enabled),
                "bands": {
                    "sparseMax": int(bands.sparse_max),
                    "ambiguousMax": int(bands.ambiguous_max),
                    "narrativeChapterHintAt": int(bands.narrative_chapter_hint_at),
                },
            },
            "gcsPosterBric": {
                "enabled": bool(
                    getattr(
                        getattr(cfg.studio, "gcs_poster_bric", None),
                        "enabled",
                        True,
                    )
                ),
            },
        },
        "cohort": {
            "enabled": cfg.cohort.enabled,
        },
        "titleArt": {
            "enabled": bool(cfg.title_art.enabled),
            "routeCEnabled": bool(cfg.title_art.route_c_enabled),
        },
        "ingest": {
            "copySourceFiles": bool(getattr(cfg.ingest, "copy_source_files", True)),
        },
        "tripsDir": str(cfg.trips_dir) if getattr(cfg, "trips_dir", None) else None,
        "happyPath": {
            "recipeId": RECIPE_ID_STUDIO_DEFAULT,
            "l1Keys": list(L1_RESULT_KEYS),
            "advancedSettingsKeys": list(ADVANCED_SETTINGS_KEYS),
            "l0OpsRoots": list(L0_OPS_ROOTS),
        },
    }
