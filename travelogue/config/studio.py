"""Studio workbench configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from travelogue.config.app import AppConfig


@dataclass
class StudioConfig:
    """Studio workbench (Phase 4 M17 · G1)."""

    g1_confirm_structure: bool = False
    import_dual_mode_enabled: bool = True
    success_refined_default_enabled: bool = True
    import_sheet_large_enabled: bool = True
    layout_templates_internal: bool = False


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
        },
        "studio": {
            "g1ConfirmStructure": cfg.studio.g1_confirm_structure,
            "importDualModeEnabled": cfg.studio.import_dual_mode_enabled,
            "successRefinedDefaultEnabled": cfg.studio.success_refined_default_enabled,
            "importSheetLargeEnabled": cfg.studio.import_sheet_large_enabled,
            "layoutTemplatesInternal": cfg.studio.layout_templates_internal,
        },
        "cohort": {
            "enabled": cfg.cohort.enabled,
        },
    }
