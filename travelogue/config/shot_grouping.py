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
class AtomConfig:
    """Cluster-Boundary-First · Scene Atom (PLAN V1 已审定稿).

    Product-safe default: ``enabled=False``. Dogfood / cohort turns it on.
    """

    enabled: bool = False
    max_gap_seconds: float = 600.0
    max_window_span_seconds: float = 7200.0
    # compatible = 半硬 sc（两侧皆有效 id 才要求相同；-1 不与非 -1 混）
    # force_same = 草案原文（已否决，过碎）；off = 忽略 sceneCluster
    scene_cluster_mode: str = "compatible"
    category_jump_is_hard: bool = False
    allow_tail_cross_atom: bool = False


@dataclass
class ShotGroupingMosaicConfig:
    """Intent knobs; hard-reject shares near_scene_clone_* helpers (D-SSG-25)."""

    slice_cross_group_hard_reject: bool = True
    same_group_anti_slice: bool = True
    # Documented intent names (D-SSG-17). Runtime exempt uses screen/pattern
    # mapping in shot_group_gate (D-SSG-17b) — this list is not a live override.
    cross_group_exempt_roles: list[str] = field(
        default_factory=lambda: ["cover", "moment", "chapterHero", "solo", "bookend"]
    )
    atom: AtomConfig = field(default_factory=AtomConfig)


@dataclass
class ShotGroupMosaicPolicy:
    """Resolved layout-time policy · never read MosaicConfig.shot_grouping."""

    cross_group_hard_reject: bool = True
    same_group_anti_slice: bool = True
    atom: AtomConfig = field(default_factory=AtomConfig)
    ssg_layer_enabled: bool = True


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


def _atom_from_dict(raw: dict[str, Any] | None) -> AtomConfig:
    if not isinstance(raw, dict):
        return AtomConfig()
    mode = cfg_str(raw, "scene_cluster_mode", "sceneClusterMode", "compatible")
    mode_n = str(mode or "compatible").strip().lower()
    if mode_n not in ("compatible", "force_same", "off"):
        mode_n = "compatible"
    return AtomConfig(
        enabled=cfg_bool(raw, "enabled", "enabled", False),
        max_gap_seconds=cfg_float(raw, "max_gap_seconds", "maxGapSeconds", 600.0),
        max_window_span_seconds=cfg_float(
            raw, "max_window_span_seconds", "maxWindowSpanSeconds", 7200.0
        ),
        scene_cluster_mode=mode_n,
        category_jump_is_hard=cfg_bool(
            raw, "category_jump_is_hard", "categoryJumpIsHard", False
        ),
        allow_tail_cross_atom=cfg_bool(
            raw, "allow_tail_cross_atom", "allowTailCrossAtom", False
        ),
    )


def _mosaic_from_dict(raw: dict[str, Any]) -> ShotGroupingMosaicConfig:
    roles = raw.get("crossGroupExemptRoles") or raw.get("cross_group_exempt_roles")
    if not isinstance(roles, list):
        roles = ["cover", "moment", "chapterHero", "solo", "bookend"]
    atom_raw = raw.get("atom") if isinstance(raw.get("atom"), dict) else {}
    return ShotGroupingMosaicConfig(
        slice_cross_group_hard_reject=cfg_bool(
            raw, "slice_cross_group_hard_reject", "sliceCrossGroupHardReject", True
        ),
        same_group_anti_slice=cfg_bool(
            raw, "same_group_anti_slice", "sameGroupAntiSlice", True
        ),
        cross_group_exempt_roles=[str(r) for r in roles],
        atom=_atom_from_dict(atom_raw),
    )


def resolve_shot_group_mosaic_policy(
    app_cfg: Any | None = None,
    *,
    warn_if_missing: bool = False,
) -> ShotGroupMosaicPolicy:
    """Resolve SSG mosaic + atom policy from AppConfig (never MosaicConfig).

    PLAN-CLUSTER-BOUNDARY-FIRST P0: candidates must receive this value object
    (or resolve via this helper). Passing MosaicConfig to legacy
    ``ssg_*_active`` is a silent no-op.
    """
    cfg = app_cfg
    if cfg is None:
        try:
            from travelogue.config import get_config

            cfg = get_config()
        except Exception:
            if warn_if_missing:
                import logging

                logging.getLogger(__name__).warning(
                    "shot_group mosaic policy: AppConfig unavailable; using defaults"
                )
            return ShotGroupMosaicPolicy()
    ssg = getattr(cfg, "shot_grouping", None)
    if ssg is None:
        if warn_if_missing:
            import logging

            logging.getLogger(__name__).warning(
                "shot_group mosaic policy: cfg has no shot_grouping "
                "(MosaicConfig mistake?); using defaults"
            )
        return ShotGroupMosaicPolicy()
    mosaic = getattr(ssg, "mosaic", None) or ShotGroupingMosaicConfig()
    atom = getattr(mosaic, "atom", None) or AtomConfig()
    layer_on = getattr(ssg, "enabled", "auto") != "false"
    return ShotGroupMosaicPolicy(
        cross_group_hard_reject=bool(
            layer_on and getattr(mosaic, "slice_cross_group_hard_reject", True)
        ),
        same_group_anti_slice=bool(
            layer_on and getattr(mosaic, "same_group_anti_slice", True)
        ),
        atom=atom,
        ssg_layer_enabled=bool(layer_on),
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


def resolve_shot_grouping_enabled(
    cfg: ShotGroupingConfig,
    *,
    has_scene_clusters: bool,
    vision_available: bool | None = None,
) -> bool:
    """auto = vision available AND scene clusters non-empty (D-SSG-11)."""
    if cfg.enabled == "false":
        return False
    if cfg.enabled == "true":
        return True
    if vision_available is None:
        try:
            from travelogue.vision.clip_encoder import clip_torch_available

            vision_available = bool(clip_torch_available())
        except Exception:
            vision_available = False
    return bool(has_scene_clusters and vision_available)


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
