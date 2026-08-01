"""Smart Shot Grouping (SSG) configuration · PRD-SMART-SHOT-GROUPING-V1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.config._common import TriState, normalize_tri_state
from travelogue.config_helpers import cfg_bool, cfg_float, cfg_int, cfg_str

_UNSET = object()


@dataclass
class ShotGroupingSceneConfig:
    time_soft_split_hours: float = 6.0
    merge_noise: bool = True
    # ALG-V3 A3 · opt-in adaptive soft-split (default OFF → fixed hours path).
    adaptive_soft_split: bool = False
    adaptive_soft_split_k: float = 3.0
    adaptive_soft_split_hours_lo: float = 1.0
    adaptive_soft_split_hours_hi: float = 12.0


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

    Product default: ``enabled=True`` (全站边界门). Set ``enabled=False`` to
    roll back to pre-atom packing for a cohort / emergency.
    """

    enabled: bool = True
    max_gap_seconds: float = 600.0
    max_window_span_seconds: float = 7200.0
    # compatible = 半硬 sc（两侧皆有效 id 才要求相同；-1 不与非 -1 混）
    # force_same = 草案原文（已否决，过碎）；off = 忽略 sceneCluster
    scene_cluster_mode: str = "compatible"
    category_jump_is_hard: bool = False
    allow_tail_cross_atom: bool = False
    # W3 scarce-template admission (null = no hard span gate; soft for scoring later)
    strong_template_max_span_seconds: float | None = None
    strong_template_span_soft_seconds: float = 900.0
    # Observe-only floor vs baseline multi-slot share (never auto-widens atom).
    mosaic_share_floor_observe: float = 0.70
    # Both sides missing shotGroupId:
    #   time_bridge = still join on gap + half-hard sc (weak-SSG albums)
    #   reject = old fail-closed (every missing-sg pair becomes its own atom)
    missing_shot_group_mode: str = "time_bridge"


_POLICY_RESOLVE_FALLBACKS = 0


def policy_resolve_fallback_count() -> int:
    """P0-2 · how often resolve fell back to defaults (fail-loud counter)."""
    return int(_POLICY_RESOLVE_FALLBACKS)


def reset_policy_resolve_fallback_count() -> None:
    global _POLICY_RESOLVE_FALLBACKS
    _POLICY_RESOLVE_FALLBACKS = 0


def _note_policy_resolve_fallback(message: str, *, warn: bool) -> None:
    global _POLICY_RESOLVE_FALLBACKS
    _POLICY_RESOLVE_FALLBACKS += 1
    if warn:
        import logging

        logging.getLogger(__name__).warning("%s (count=%s)", message, _POLICY_RESOLVE_FALLBACKS)


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
    lo = cfg_float(
        raw, "adaptive_soft_split_hours_lo", "adaptiveSoftSplitHoursLo", 1.0
    )
    hi = cfg_float(
        raw, "adaptive_soft_split_hours_hi", "adaptiveSoftSplitHoursHi", 12.0
    )
    if lo > hi:
        lo, hi = hi, lo
    return ShotGroupingSceneConfig(
        time_soft_split_hours=cfg_float(
            raw, "time_soft_split_hours", "timeSoftSplitHours", 6.0
        ),
        merge_noise=cfg_bool(raw, "merge_noise", "mergeNoise", True),
        adaptive_soft_split=cfg_bool(
            raw, "adaptive_soft_split", "adaptiveSoftSplit", False
        ),
        adaptive_soft_split_k=cfg_float(
            raw, "adaptive_soft_split_k", "adaptiveSoftSplitK", 3.0
        ),
        adaptive_soft_split_hours_lo=lo,
        adaptive_soft_split_hours_hi=hi,
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
    strong_span_raw = raw.get("strong_template_max_span_seconds", raw.get("strongTemplateMaxSpanSeconds", _UNSET))
    if strong_span_raw is _UNSET:
        strong_span: float | None = None
    elif strong_span_raw is None:
        strong_span = None
    else:
        try:
            strong_span = float(strong_span_raw)
        except (TypeError, ValueError):
            strong_span = None
    return AtomConfig(
        enabled=cfg_bool(raw, "enabled", "enabled", True),
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
        strong_template_max_span_seconds=strong_span,
        strong_template_span_soft_seconds=cfg_float(
            raw,
            "strong_template_span_soft_seconds",
            "strongTemplateSpanSoftSeconds",
            900.0,
        ),
        mosaic_share_floor_observe=cfg_float(
            raw,
            "mosaic_share_floor_observe",
            "mosaicShareFloorObserve",
            0.70,
        ),
        missing_shot_group_mode=_missing_sg_mode_from_dict(raw),
    )


def _missing_sg_mode_from_dict(raw: dict[str, Any]) -> str:
    mode = cfg_str(
        raw, "missing_shot_group_mode", "missingShotGroupMode", "time_bridge"
    )
    mode_n = str(mode or "time_bridge").strip().lower()
    if mode_n not in ("time_bridge", "reject"):
        return "time_bridge"
    return mode_n


def _mosaic_from_dict(raw: dict[str, Any]) -> ShotGroupingMosaicConfig:
    roles = raw.get("crossGroupExemptRoles") or raw.get("cross_group_exempt_roles")
    if not isinstance(roles, list):
        roles = ["cover", "moment", "chapterHero", "solo", "bookend"]
    atom_raw = raw.get("atom") if isinstance(raw.get("atom"), dict) else {}
    # Prefer camelCase atom nested under mosaic when both present
    if not atom_raw and isinstance(raw.get("Atom"), dict):
        atom_raw = raw.get("Atom") or {}
    return ShotGroupingMosaicConfig(
        slice_cross_group_hard_reject=cfg_bool(
            raw, "slice_cross_group_hard_reject", "sliceCrossGroupHardReject", True
        ),
        same_group_anti_slice=cfg_bool(
            raw, "same_group_anti_slice", "sameGroupAntiSlice", True
        ),
        cross_group_exempt_roles=[str(r) for r in roles],
        atom=_atom_from_dict(atom_raw if isinstance(atom_raw, dict) else {}),
    )


def resolve_shot_group_mosaic_policy(
    app_cfg: Any | None = None,
    *,
    warn_if_missing: bool = True,
) -> ShotGroupMosaicPolicy:
    """Resolve SSG mosaic + atom policy from AppConfig (never MosaicConfig).

    PLAN-CLUSTER-BOUNDARY-FIRST P0: candidates must receive this value object
    (or resolve via this helper). Passing MosaicConfig to legacy
    ``ssg_*_active`` is a silent no-op.

    P0-2 · default ``warn_if_missing=True`` so missing AppConfig / shot_grouping
    is fail-loud (warning + counter), not a silent False gate.
    """
    cfg = app_cfg
    if cfg is None:
        try:
            from travelogue.config import get_config

            cfg = get_config()
        except Exception:
            _note_policy_resolve_fallback(
                "shot_group mosaic policy: AppConfig unavailable; using defaults",
                warn=warn_if_missing,
            )
            return ShotGroupMosaicPolicy()
    ssg = getattr(cfg, "shot_grouping", None)
    if ssg is None:
        _note_policy_resolve_fallback(
            "shot_group mosaic policy: cfg has no shot_grouping "
            "(MosaicConfig mistake?); using defaults",
            warn=warn_if_missing,
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
    # Layer rule: config must not import vision. Callers should pass
    # vision_available; unset → auto stays off (fail-closed).
    if vision_available is None:
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
    # Layer rule: config must not import vision. Callers pass clip_available.
    if clip_available is None:
        clip_available = False
    return bool(clip_available)
