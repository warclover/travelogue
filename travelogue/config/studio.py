"""Studio workbench configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from travelogue.config.app import AppConfig


# Studio Popover platforms (Phase A+B). Phase C stays CLI/API-only.
DEFAULT_LONGSHOT2_PLATFORMS: tuple[str, ...] = ("wechat_moments", "xiaohongshu")


@dataclass
class Longshot2Config:
    """Longshot 2.0 platform export flags (PRD §13)."""

    enabled: bool = True
    platforms: tuple[str, ...] = DEFAULT_LONGSHOT2_PLATFORMS
    smart_crop_enabled: bool = False


@dataclass
class StudioConfig:
    """Studio workbench (Phase 4 M17 · G1)."""

    g1_confirm_structure: bool = False
    import_dual_mode_enabled: bool = True
    success_refined_default_enabled: bool = True
    import_sheet_large_enabled: bool = True
    layout_templates_internal: bool = False
    longshot2: Longshot2Config = field(default_factory=Longshot2Config)

    @property
    def longshot2_enabled(self) -> bool:
        return bool(self.longshot2.enabled)

    @property
    def longshot2_platforms(self) -> list[str]:
        return list(self.longshot2.platforms)


def studio_config_expose(cfg: AppConfig) -> dict[str, Any]:
    """Subset of config safe for Studio GET /__travelogue/config."""
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
        },
        "cohort": {
            "enabled": cfg.cohort.enabled,
        },
        "ingest": {
            "copySourceFiles": bool(getattr(cfg.ingest, "copy_source_files", True)),
        },
        "tripsDir": str(cfg.trips_dir) if getattr(cfg, "trips_dir", None) else None,
    }
