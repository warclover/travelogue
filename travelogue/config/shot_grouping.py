"""Smart Shot Grouping (SSG) configuration · PRD-SMART-SHOT-GROUPING-V1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.config._common import TriState, normalize_tri_state
from travelogue.config_helpers import cfg_bool, cfg_float, cfg_int, cfg_str


@dataclass
class ShotGroupingSceneConfig:
    time_soft_split_hours: float = 6.0
    merge_noise: bool = True


@dataclass
class ShotGroupingLookConfig:
    enabled: TriState = "auto"
    delta_threshold: float = 0.28
    sustain_frames: int = 2
    require_face_or_subject: bool = True
    min_max_face_area_ratio: float = 0.15
    max_faces_before_skip: int = 4


@dataclass
class ShotGroupingMosaicConfig:
    """Intent knobs; hard-reject shares near_scene_clone_* helpers (D-SSG-25)."""

    slice_cross_group_hard_reject: bool = True
    same_group_anti_slice: bool = True
    # Logical names only — mapped at screen/pattern layer (D-SSG-17b).
    cross_group_exempt_roles: list[str] = field(
        default_factory=lambda: ["cover", "moment", "chapterHero", "solo", "bookend"]
    )


@dataclass
class ShotGroupingConfig:
    enabled: TriState = "auto"
    min_shot_group_size: int = 2
    scene: ShotGroupingSceneConfig = field(default_factory=ShotGroupingSceneConfig)
    look: ShotGroupingLookConfig = field(default_factory=ShotGroupingLookConfig)
    mosaic: ShotGroupingMosaicConfig = field(default_factory=ShotGroupingMosaicConfig)


def _scene_from_dict(raw: dict[str, Any]) -> ShotGroupingSceneConfig:
    return ShotGroupingSceneConfig(
        time_soft_split_hours=cfg_float(
            raw, "time_soft_split_hours", "timeSoftSplitHours", 6.0
        ),
        merge_noise=cfg_bool(raw, "merge_noise", "mergeNoise", True),
    )


def _look_from_dict(raw: dict[str, Any]) -> ShotGroupingLookConfig:
    enabled_raw = raw.get("enabled", "auto")
    return ShotGroupingLookConfig(
        enabled=normalize_tri_state(enabled_raw, default="auto"),
        delta_threshold=cfg_float(raw, "delta_threshold", "deltaThreshold", 0.28),
        sustain_frames=cfg_int(raw, "sustain_frames", "sustainFrames", 2),
        require_face_or_subject=cfg_bool(
            raw, "require_face_or_subject", "requireFaceOrSubject", True
        ),
        min_max_face_area_ratio=cfg_float(
            raw, "min_max_face_area_ratio", "minMaxFaceAreaRatio", 0.15
        ),
        max_faces_before_skip=cfg_int(
            raw, "max_faces_before_skip", "maxFacesBeforeSkip", 4
        ),
    )


def _mosaic_from_dict(raw: dict[str, Any]) -> ShotGroupingMosaicConfig:
    roles = raw.get("crossGroupExemptRoles") or raw.get("cross_group_exempt_roles")
    if not isinstance(roles, list):
        roles = ["cover", "moment", "chapterHero", "solo", "bookend"]
    return ShotGroupingMosaicConfig(
        slice_cross_group_hard_reject=cfg_bool(
            raw, "slice_cross_group_hard_reject", "sliceCrossGroupHardReject", True
        ),
        same_group_anti_slice=cfg_bool(
            raw, "same_group_anti_slice", "sameGroupAntiSlice", True
        ),
        cross_group_exempt_roles=[str(r) for r in roles],
    )


def shot_grouping_from_dict(raw: dict[str, Any] | None) -> ShotGroupingConfig:
    if not raw:
        return ShotGroupingConfig()
    enabled_raw = raw.get("enabled", "auto")
    scene_raw = raw.get("scene") if isinstance(raw.get("scene"), dict) else {}
    look_raw = raw.get("look") if isinstance(raw.get("look"), dict) else {}
    mosaic_raw = raw.get("mosaic") if isinstance(raw.get("mosaic"), dict) else {}
    return ShotGroupingConfig(
        enabled=normalize_tri_state(enabled_raw, default="auto"),
        min_shot_group_size=max(
            1, cfg_int(raw, "min_shot_group_size", "minShotGroupSize", 2)
        ),
        scene=_scene_from_dict(scene_raw),
        look=_look_from_dict(look_raw),
        mosaic=_mosaic_from_dict(mosaic_raw),
    )


def resolve_shot_grouping_enabled(cfg: ShotGroupingConfig, *, has_scene_clusters: bool) -> bool:
    """auto = on only when scene clusters are available (D-SSG-11)."""
    if cfg.enabled == "false":
        return False
    if cfg.enabled == "true":
        return True
    return bool(has_scene_clusters)


def resolve_look_enabled(
    cfg: ShotGroupingLookConfig,
    *,
    clip_available: bool | None = None,
) -> bool:
    """Look switch · auto = CLIP stack available; true/false explicit (fail-open later)."""
    if cfg.enabled == "false":
        return False
    if cfg.enabled == "true":
        return True
    if clip_available is None:
        try:
            from travelogue.vision.clip_encoder import clip_torch_available

            clip_available = bool(clip_torch_available())
        except Exception:
            clip_available = False
    return bool(clip_available)
