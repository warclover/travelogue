"""Mosaic composition configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.config_helpers import cfg_bool, cfg_float, cfg_int


@dataclass
class MosaicDensityBudgetConfig:
    """P21 · dense collage frequency caps (PRD-PHASE21)."""

    enabled: bool = True
    min_slots: int = 4
    window_order: tuple[int, ...] = (5, 4, 6, 9)
    large_mosaic_min_slots: int = 5
    max_per_template_per_trip: int = 2
    max_large_mosaic_per_chapter: int = 1


@dataclass
class TemplateContractConfig:
    """TPC · unified template contract (PRD-TEMPLATE-CONTRACT-V1).

    Defaults keep runtime on the legacy candidate path (AC-TPC-01).
    Unknown keys under this root fail-loud (AC-TPC-13).
    """

    enabled: bool = False
    shadow_log: bool = False


_TEMPLATE_CONTRACT_KNOWN_KEYS = frozenset(
    {
        "enabled",
        "shadow_log",
        "shadowLog",
    }
)


@dataclass
class NearSceneCloneGateConfig:
    """AC-TPC-15 · hard-reject non-burst mosaics that absorb same-scene clones.

    ``enabled`` force-on (yaml dogfood). ``conditional`` (ALG-V3 B7, default True)
    auto-enables when SSG is off/empty on the window or vision is degraded.
    Unknown keys fail-loud.
    """

    enabled: bool = False
    conditional: bool = True


_NEAR_SCENE_CLONE_GATE_KNOWN_KEYS = frozenset(
    {
        "enabled",
        "conditional",
    }
)


# EGA · pure landscape equal-grid admission (PRD-EQUAL-GRID-ADMISSION-V1).
_DEFAULT_EGA_PATTERNS: tuple[str, ...] = (
    "screen-landscape-4",
    "screen-landscape-6",
)


@dataclass
class EqualGridAdmissionAntiSliceConfig:
    """anti_slice mode for EGA patterns (D-EGA-03 · OQ-01)."""

    mode: str = "exempt"  # exempt | soft_penalty | hard
    score_mul: float = 0.90


@dataclass
class EqualGridAdmissionCloneConfig:
    """near_scene_clone mode for EGA patterns (D-EGA-04 · OQ-02)."""

    mode: str = "soft_penalty"  # soft_penalty | hard
    score_mul: float = 0.85


@dataclass
class EqualGridAdmissionSize6Config:
    """PR-B/E · size=6 equal-grid funnel + auto-match knobs.

    Product lock 2026-08-04: L6 auto-match defaults stay **on**
    (see docs/acceptance-records/ega-l6-auto-match-dogfood-2026-08-04.md).
    """

    keep_equal_grid_after_hero_precheck_fail: bool = True
    # P0 · allow sceneCluster valid/-1 mix on EGA equal-grid (same shotGroup).
    soften_atom_valid_invalid_mix: bool = True
    # P1 · pure 6×landscape window → try size=6 before 4/5.
    prefer_pure_landscape_window: bool = True
    # P2 · landscape-6 does not consume / is not blocked by large-mosaic chapter quota.
    large_mosaic_quota_exempt: bool = True
    # P3 · after N consecutive landscape-1, reopen size=6 MCS (0 = off).
    landscape1_flood_reopen_after: int = 4


@dataclass
class EqualGridAdmissionScoringConfig:
    """PR-C · flat-window equal-grid bias (defaults ready; wired in M2)."""

    flat_window_equal_bonus: float = 0.08
    wasted_hero_ega_extra: float = 0.10


@dataclass
class EqualGridAdmissionMegcLegacyConfig:
    """PR-D · optional soft demote (default off · M3 deferred)."""

    soften_penalize_emit: bool = False


@dataclass
class EqualGridAdmissionConfig:
    """EGA · equal-grid admission parent (PRD-EQUAL-GRID-ADMISSION-V1).

    When ``enabled`` is false, behavior ≡ pre-EGA (hard anti_slice / clone).
    Unknown keys under this root fail-loud.
    """

    enabled: bool = True
    patterns: tuple[str, ...] = _DEFAULT_EGA_PATTERNS
    anti_slice: EqualGridAdmissionAntiSliceConfig = field(
        default_factory=EqualGridAdmissionAntiSliceConfig
    )
    near_scene_clone: EqualGridAdmissionCloneConfig = field(
        default_factory=EqualGridAdmissionCloneConfig
    )
    size6: EqualGridAdmissionSize6Config = field(
        default_factory=EqualGridAdmissionSize6Config
    )
    scoring: EqualGridAdmissionScoringConfig = field(
        default_factory=EqualGridAdmissionScoringConfig
    )
    megc_legacy_demote: EqualGridAdmissionMegcLegacyConfig = field(
        default_factory=EqualGridAdmissionMegcLegacyConfig
    )


_EQUAL_GRID_ADMISSION_KNOWN_KEYS = frozenset(
    {
        "enabled",
        "patterns",
        "anti_slice",
        "antiSlice",
        "near_scene_clone",
        "nearSceneClone",
        "size6",
        "scoring",
        "megc_legacy_demote",
        "megcLegacyDemote",
    }
)

_EGA_ANTI_SLICE_KNOWN_KEYS = frozenset({"mode", "score_mul", "scoreMul"})
_EGA_CLONE_KNOWN_KEYS = frozenset({"mode", "score_mul", "scoreMul"})
_EGA_SIZE6_KNOWN_KEYS = frozenset(
    {
        "keep_equal_grid_after_hero_precheck_fail",
        "keepEqualGridAfterHeroPrecheckFail",
        "soften_atom_valid_invalid_mix",
        "softenAtomValidInvalidMix",
        "prefer_pure_landscape_window",
        "preferPureLandscapeWindow",
        "large_mosaic_quota_exempt",
        "largeMosaicQuotaExempt",
        "landscape1_flood_reopen_after",
        "landscape1FloodReopenAfter",
    }
)
_EGA_SCORING_KNOWN_KEYS = frozenset(
    {
        "flat_window_equal_bonus",
        "flatWindowEqualBonus",
        "wasted_hero_ega_extra",
        "wastedHeroEgaExtra",
    }
)
_EGA_MEGC_LEGACY_KNOWN_KEYS = frozenset(
    {"soften_penalize_emit", "softenPenalizeEmit"}
)


# Product defaults: triple collage + 3P2L five-up portrait-hero family.
# cohort ``*`` = all trips; empty cohort remains fail-closed (nobody).
_DEFAULT_TRIPLE_COLLAGE_ALLOWLIST: tuple[str, ...] = (
    "screen-landscape-3-asymmetric-left",
    "screen-landscape-3-asymmetric-right",
    "screen-landscape-2-portrait-1",
    "screen-mosaic-5-3p2l-portrait-hero-quad",
    "screen-mosaic-5-3p2l-portrait-hero-lp-stack",
)


@dataclass
class TemplateExperimentsConfig:
    """MTSO · experimental / soft-rotation templates (orthogonal to template_contract).

    Fail-closed: enabled + empty cohort ⇒ nobody sees experimentals.
    Product default (whole section absent): enabled with triple-collage allowlist
    and cohort ``*``. Partial blocks that omit allowlist/cohort keep empty tuples
    (do not silently inject product defaults).
    Unknown keys under this root fail-loud.
    """

    enabled: bool = True
    allowlist: tuple[str, ...] = _DEFAULT_TRIPLE_COLLAGE_ALLOWLIST
    cohort_trip_ids: tuple[str, ...] = ("*",)


_TEMPLATE_EXPERIMENTS_KNOWN_KEYS = frozenset(
    {
        "enabled",
        "allowlist",
        "cohort_trip_ids",
        "cohortTripIds",
    }
)


@dataclass
class SelectionOptimizationConfig:
    """MTSO · selection optimization parent switch (PR-B+; PR-A shell only).

    When ``enabled`` is false, nested knobs are ineffective.
    """

    enabled: bool = False
    hero_six_opportunity_enabled: bool = True
    mixed_hero_routing_enabled: bool = True
    hero_gap_threshold: float | None = None


_SELECTION_OPTIMIZATION_KNOWN_KEYS = frozenset(
    {
        "enabled",
        "hero_six_opportunity",
        "heroSixOpportunity",
        "mixed_hero_routing",
        "mixedHeroRouting",
        "hero_gap_threshold",
        "heroGapThreshold",
    }
)


@dataclass
class SlotAdaptationSolveConfig:
    """MSA · track solve bounds (PRD §5.1)."""

    max_iters: int = 32
    track_weight_min: float = 0.5
    track_weight_max: float = 24.0


@dataclass
class SlotAdaptationConfig:
    """MSA · mosaic slot adaptation parent switch (PRD-MOSAIC-SLOT-ADAPTATION-V1).

    When ``enabled`` is false, nested knobs are ineffective (fail-closed to M3).
    Unknown keys under this root fail-loud.
    """

    enabled: bool = False
    whitespace_max: float = 0.08
    crop_risk_contain_threshold: float = 0.55
    hero_target_clamp: tuple[float, float] = (1.30, 1.60)
    land_peaks: dict[str, float] = field(
        default_factory=lambda: {
            "three_two": 1.50,
            "four_three": 1.3333,
            "sixteen_nine": 1.7778,
        }
    )
    wide_peak_fraction: float = 0.50
    solve: SlotAdaptationSolveConfig = field(default_factory=SlotAdaptationSolveConfig)


_SLOT_ADAPTATION_KNOWN_KEYS = frozenset(
    {
        "enabled",
        "whitespace_max",
        "whitespaceMax",
        "crop_risk_contain_threshold",
        "cropRiskContainThreshold",
        "hero_target_clamp",
        "heroTargetClamp",
        "land_peaks",
        "landPeaks",
        "wide_peak_fraction",
        "widePeakFraction",
        "solve",
    }
)

_SLOT_ADAPTATION_SOLVE_KNOWN_KEYS = frozenset(
    {
        "max_iters",
        "maxIters",
        "track_weight_min",
        "trackWeightMin",
        "track_weight_max",
        "trackWeightMax",
    }
)


_DEFAULT_MEGC_PATTERNS: tuple[str, ...] = (
    "screen-landscape-4",
    "screen-portrait-2-landscape-2",
    "screen-mosaic-4-2l2p-weighted",
)


@dataclass
class EqualGridSelectionGateConfig:
    """MEGC · P-选 selection gate (PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1 · M2).

    Soft path uses multiplicative ``score_mul`` (SUP-MEGC-01); additive
    ``penalty`` is rejected as an unknown key.
    """

    enabled: bool = True
    mode: str = "soft_penalty"  # soft_penalty | hard_reject
    allow_peaks: tuple[str, ...] = ("sixteen_nine",)
    allow_mixed_median_min: float = 1.70
    score_mul: float = 0.62


@dataclass
class EqualGridContractConfig:
    """MEGC · equal-grid geometric contract parent switch.

    When ``enabled`` is false, nested knobs are ineffective (fail-closed).
    CSS hotfix (``fix_stage_css``) may ship independently of this parent (O-05).
    Default ON since 2026-08-03 (see megc-default-on-decision); M3 knobs stay false.
    Unknown keys under this root fail-loud.
    """

    enabled: bool = True
    fix_stage_css: bool = True
    selection_gate: EqualGridSelectionGateConfig = field(
        default_factory=EqualGridSelectionGateConfig
    )
    release_stage_on_narrow_peak: bool = False  # M3 deferred
    page_letterbox: bool = False  # M3 deferred
    patterns: tuple[str, ...] = _DEFAULT_MEGC_PATTERNS


_EQUAL_GRID_CONTRACT_KNOWN_KEYS = frozenset(
    {
        "enabled",
        "fix_stage_css",
        "fixStageCss",
        "selection_gate",
        "selectionGate",
        "release_stage_on_narrow_peak",
        "releaseStageOnNarrowPeak",
        "page_letterbox",
        "pageLetterbox",
        "patterns",
    }
)

_EQUAL_GRID_SELECTION_GATE_KNOWN_KEYS = frozenset(
    {
        "enabled",
        "mode",
        "allow_peaks",
        "allowPeaks",
        "allow_mixed_median_min",
        "allowMixedMedianMin",
        "score_mul",
        "scoreMul",
    }
)


@dataclass
class MosaicConfig:
    """Phase 15 mosaic composition (DESIGN-PHASE15 · S1)."""

    enabled: bool = True
    scorer_version: str = "p15-s3"
    deterministic_strict: bool = True
    min_candidate_score: float = 0.35
    enabled_window_sizes: tuple[int, ...] = (4, 5, 6, 9)
    unified_mode: bool = True
    fallback_to_legacy: bool = True
    self_heal_enabled: bool = True
    allow_drop: bool = False
    max_drop_ratio: float = 0.5
    # ALG-V3 B6 · cap expensive self-heal branches (tightened rescore / drop rebuild).
    self_heal_max_rescore: int = 8
    self_heal_max_drop_attempts: int = 1
    candidate_top_k: int = 4
    log_level: str = "window"
    density_budget: MosaicDensityBudgetConfig = field(default_factory=MosaicDensityBudgetConfig)
    template_contract: TemplateContractConfig = field(default_factory=TemplateContractConfig)
    template_experiments: TemplateExperimentsConfig = field(
        default_factory=TemplateExperimentsConfig
    )
    selection_optimization: SelectionOptimizationConfig = field(
        default_factory=SelectionOptimizationConfig
    )
    slot_adaptation: SlotAdaptationConfig = field(default_factory=SlotAdaptationConfig)
    equal_grid_contract: EqualGridContractConfig = field(
        default_factory=EqualGridContractConfig
    )
    near_scene_clone_gate: NearSceneCloneGateConfig = field(
        default_factory=NearSceneCloneGateConfig
    )
    equal_grid_admission: EqualGridAdmissionConfig = field(
        default_factory=EqualGridAdmissionConfig
    )
    # When false, restores pre-v4 hero-3-2-plus-4 geometry/scorer guards (rollback).
    hero_weighted_geometry_guard: bool = True
    # PRD-6张拼图优化 · R-MAIN-AR-01: conventional AR only for hero+tile main slot.
    main_ar_guard: bool = True
    main_ar_ladder_tol: float = 0.08
    main_ar_prefer_16_9: bool = True
    # Skip dense windows (size≥6) when the window has ≥2 standard portraits.
    skip_dense_window_multi_portrait: bool = True
    # Prefer 5-slot main-portrait-3land over hero+6 for 1P+5L mixed windows.
    prefer_five_slot_single_portrait: bool = True
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "aspect_match": 0.20,
            "sharpness": 0.15,
            "hero_separation": 0.10,
            "temporal_coherence": 0.15,
            "subject_run": 0.10,
            "layout_rhythm": 0.10,
            "diversity": 0.10,
            "category_coherence": 0.10,
            "cohort_coherence": 0.0,
        }
    )
    penalties: dict[str, float] = field(
        default_factory=lambda: {
            "face_crop": 0.30,
            "main_quality": 0.25,
            "duplicate_density": 0.20,
            "hero_narrow_tiles": 0.35,
            "hero_slot_aspect": 0.4,
            "flat_six_grid": 0.35,
            "flat_nine_grid": 0.45,
            "dense_without_hero": 0.25,
            "wasted_hero": 0.35,
            "main_ar_ineligible": 0.95,
            # LTN C8 · D-03 slot-role soft penalties
            "main_not_window_best": 0.4,
            "main_clone_in_sidebar": 0.3,
            "main_area_ratio": 0.35,
            # MSA · S-MSA-06 soft penalties (active only when slot_adaptation ON)
            "crop_risk_penalty": 0.25,
            "whitespace_penalty": 0.20,
            "aspect_fit": 0.15,
            # Cluster-Boundary-First W1 soft (category jump; hard gate is separate)
            "category_jump_soft": 0.20,
        }
    )
    # LSE W3b capability flags (set via layout_engine.adapter mosaic_config_from_pack)
    lse_saliency_scoring: bool = False
    lse_tone_harmony: bool = False
    lse_beat_profile: str = "flat"
    lse_hungarian_assignment: bool = False
    lse_quality_unified: bool = False
    lse_slot_max_matrix_n: int = 16
    lse_highlight_boost: float = 1.0
    # LTN C7 · track overlay (see layout_contract.mosaic_track)
    enable_size3_aux: bool = False
    track_id: str | None = None
    track_dense_collage_cap: int | None = None


def _density_budget_from_dict(raw: dict[str, Any]) -> MosaicDensityBudgetConfig:
    defaults = MosaicDensityBudgetConfig()
    db = raw.get("density_budget") if isinstance(raw.get("density_budget"), dict) else {}
    if isinstance(raw.get("densityBudget"), dict):
        db = raw["densityBudget"]
    order_raw = db.get("window_order", db.get("windowOrder", defaults.window_order))
    if isinstance(order_raw, (list, tuple)):
        order = tuple(int(x) for x in order_raw)
    else:
        order = defaults.window_order
    return MosaicDensityBudgetConfig(
        enabled=cfg_bool(db, "enabled", "enabled", defaults.enabled),
        min_slots=int(db.get("min_slots", db.get("minSlots", defaults.min_slots))),
        window_order=order or defaults.window_order,
        large_mosaic_min_slots=int(
            db.get("large_mosaic_min_slots", db.get("largeMosaicMinSlots", defaults.large_mosaic_min_slots))
        ),
        max_per_template_per_trip=int(
            db.get(
                "max_per_template_per_trip",
                db.get("maxPerTemplatePerTrip", defaults.max_per_template_per_trip),
            )
        ),
        max_large_mosaic_per_chapter=int(
            db.get(
                "max_large_mosaic_per_chapter",
                db.get("maxLargeMosaicPerChapter", defaults.max_large_mosaic_per_chapter),
            )
        ),
    )


def _template_contract_from_dict(raw: dict[str, Any]) -> TemplateContractConfig:
    defaults = TemplateContractConfig()
    tc = raw.get("template_contract")
    if not isinstance(tc, dict):
        tc = raw.get("templateContract")
    if not isinstance(tc, dict):
        return defaults
    unknown = sorted(str(k) for k in tc if str(k) not in _TEMPLATE_CONTRACT_KNOWN_KEYS)
    if unknown:
        raise ValueError(
            "mosaic.template_contract unknown keys (fail-loud): " + ", ".join(unknown)
        )
    return TemplateContractConfig(
        enabled=cfg_bool(tc, "enabled", "enabled", defaults.enabled),
        shadow_log=cfg_bool(tc, "shadow_log", "shadowLog", defaults.shadow_log),
    )


def _near_scene_clone_gate_from_dict(raw: dict[str, Any]) -> NearSceneCloneGateConfig:
    defaults = NearSceneCloneGateConfig()
    gate = raw.get("near_scene_clone_gate")
    if not isinstance(gate, dict):
        gate = raw.get("nearSceneCloneGate")
    if not isinstance(gate, dict):
        return defaults
    unknown = sorted(str(k) for k in gate if str(k) not in _NEAR_SCENE_CLONE_GATE_KNOWN_KEYS)
    if unknown:
        raise ValueError(
            "mosaic.near_scene_clone_gate unknown keys (fail-loud): " + ", ".join(unknown)
        )
    return NearSceneCloneGateConfig(
        enabled=cfg_bool(gate, "enabled", "enabled", defaults.enabled),
        conditional=cfg_bool(gate, "conditional", "conditional", defaults.conditional),
    )


def _ega_anti_slice_from_dict(raw: object) -> EqualGridAdmissionAntiSliceConfig:
    defaults = EqualGridAdmissionAntiSliceConfig()
    if not isinstance(raw, dict):
        return defaults
    unknown = sorted(str(k) for k in raw if str(k) not in _EGA_ANTI_SLICE_KNOWN_KEYS)
    if unknown:
        raise ValueError(
            "mosaic.equal_grid_admission.anti_slice unknown keys (fail-loud): "
            + ", ".join(unknown)
        )
    mode = str(raw.get("mode", defaults.mode)).strip().lower() or defaults.mode
    if mode not in ("exempt", "soft_penalty", "hard"):
        raise ValueError(
            "mosaic.equal_grid_admission.anti_slice.mode must be "
            "exempt|soft_penalty|hard"
        )
    mul = float(raw.get("score_mul", raw.get("scoreMul", defaults.score_mul)))
    if not (0.0 < mul <= 1.0):
        raise ValueError(
            "mosaic.equal_grid_admission.anti_slice.score_mul must be in (0, 1]"
        )
    return EqualGridAdmissionAntiSliceConfig(mode=mode, score_mul=mul)


def _ega_clone_from_dict(raw: object) -> EqualGridAdmissionCloneConfig:
    defaults = EqualGridAdmissionCloneConfig()
    if not isinstance(raw, dict):
        return defaults
    unknown = sorted(str(k) for k in raw if str(k) not in _EGA_CLONE_KNOWN_KEYS)
    if unknown:
        raise ValueError(
            "mosaic.equal_grid_admission.near_scene_clone unknown keys (fail-loud): "
            + ", ".join(unknown)
        )
    mode = str(raw.get("mode", defaults.mode)).strip().lower() or defaults.mode
    if mode not in ("soft_penalty", "hard"):
        raise ValueError(
            "mosaic.equal_grid_admission.near_scene_clone.mode must be soft_penalty|hard"
        )
    mul = float(raw.get("score_mul", raw.get("scoreMul", defaults.score_mul)))
    if not (0.0 < mul <= 1.0):
        raise ValueError(
            "mosaic.equal_grid_admission.near_scene_clone.score_mul must be in (0, 1]"
        )
    return EqualGridAdmissionCloneConfig(mode=mode, score_mul=mul)


def _ega_size6_from_dict(raw: object) -> EqualGridAdmissionSize6Config:
    defaults = EqualGridAdmissionSize6Config()
    if not isinstance(raw, dict):
        return defaults
    unknown = sorted(str(k) for k in raw if str(k) not in _EGA_SIZE6_KNOWN_KEYS)
    if unknown:
        raise ValueError(
            "mosaic.equal_grid_admission.size6 unknown keys (fail-loud): "
            + ", ".join(unknown)
        )
    return EqualGridAdmissionSize6Config(
        keep_equal_grid_after_hero_precheck_fail=cfg_bool(
            raw,
            "keep_equal_grid_after_hero_precheck_fail",
            "keepEqualGridAfterHeroPrecheckFail",
            defaults.keep_equal_grid_after_hero_precheck_fail,
        ),
        soften_atom_valid_invalid_mix=cfg_bool(
            raw,
            "soften_atom_valid_invalid_mix",
            "softenAtomValidInvalidMix",
            defaults.soften_atom_valid_invalid_mix,
        ),
        prefer_pure_landscape_window=cfg_bool(
            raw,
            "prefer_pure_landscape_window",
            "preferPureLandscapeWindow",
            defaults.prefer_pure_landscape_window,
        ),
        large_mosaic_quota_exempt=cfg_bool(
            raw,
            "large_mosaic_quota_exempt",
            "largeMosaicQuotaExempt",
            defaults.large_mosaic_quota_exempt,
        ),
        landscape1_flood_reopen_after=cfg_int(
            raw,
            "landscape1_flood_reopen_after",
            "landscape1FloodReopenAfter",
            defaults.landscape1_flood_reopen_after,
        ),
    )


def _ega_scoring_from_dict(raw: object) -> EqualGridAdmissionScoringConfig:
    defaults = EqualGridAdmissionScoringConfig()
    if not isinstance(raw, dict):
        return defaults
    unknown = sorted(str(k) for k in raw if str(k) not in _EGA_SCORING_KNOWN_KEYS)
    if unknown:
        raise ValueError(
            "mosaic.equal_grid_admission.scoring unknown keys (fail-loud): "
            + ", ".join(unknown)
        )
    return EqualGridAdmissionScoringConfig(
        flat_window_equal_bonus=cfg_float(
            raw,
            "flat_window_equal_bonus",
            "flatWindowEqualBonus",
            defaults.flat_window_equal_bonus,
        ),
        wasted_hero_ega_extra=cfg_float(
            raw,
            "wasted_hero_ega_extra",
            "wastedHeroEgaExtra",
            defaults.wasted_hero_ega_extra,
        ),
    )


def _ega_megc_legacy_from_dict(raw: object) -> EqualGridAdmissionMegcLegacyConfig:
    defaults = EqualGridAdmissionMegcLegacyConfig()
    if not isinstance(raw, dict):
        return defaults
    unknown = sorted(str(k) for k in raw if str(k) not in _EGA_MEGC_LEGACY_KNOWN_KEYS)
    if unknown:
        raise ValueError(
            "mosaic.equal_grid_admission.megc_legacy_demote unknown keys (fail-loud): "
            + ", ".join(unknown)
        )
    return EqualGridAdmissionMegcLegacyConfig(
        soften_penalize_emit=cfg_bool(
            raw,
            "soften_penalize_emit",
            "softenPenalizeEmit",
            defaults.soften_penalize_emit,
        )
    )


def _equal_grid_admission_from_dict(raw: dict[str, Any]) -> EqualGridAdmissionConfig:
    defaults = EqualGridAdmissionConfig()
    ega = raw.get("equal_grid_admission")
    if not isinstance(ega, dict):
        ega = raw.get("equalGridAdmission")
    if not isinstance(ega, dict):
        return defaults
    unknown = sorted(str(k) for k in ega if str(k) not in _EQUAL_GRID_ADMISSION_KNOWN_KEYS)
    if unknown:
        raise ValueError(
            "mosaic.equal_grid_admission unknown keys (fail-loud): " + ", ".join(unknown)
        )
    patterns_raw = ega.get("patterns")
    if patterns_raw is None:
        patterns = defaults.patterns
    else:
        patterns = _str_tuple(patterns_raw) or defaults.patterns
    return EqualGridAdmissionConfig(
        enabled=cfg_bool(ega, "enabled", "enabled", defaults.enabled),
        patterns=patterns,
        anti_slice=_ega_anti_slice_from_dict(
            ega.get("anti_slice", ega.get("antiSlice"))
        ),
        near_scene_clone=_ega_clone_from_dict(
            ega.get("near_scene_clone", ega.get("nearSceneClone"))
        ),
        size6=_ega_size6_from_dict(ega.get("size6")),
        scoring=_ega_scoring_from_dict(ega.get("scoring")),
        megc_legacy_demote=_ega_megc_legacy_from_dict(
            ega.get("megc_legacy_demote", ega.get("megcLegacyDemote"))
        ),
    )


def effective_equal_grid_admission_enabled(cfg: MosaicConfig | None) -> bool:
    """Parent OFF ⇒ EGA soft/exempt paths inert (pre-EGA hard gates)."""
    if cfg is None:
        return False
    ega = getattr(cfg, "equal_grid_admission", None)
    return bool(ega is not None and getattr(ega, "enabled", False))


def is_ega_equal_grid_pattern(pattern_id: str, cfg: MosaicConfig | None = None) -> bool:
    """D-EGA-02 · whitelist only (default L4+L6)."""
    pid = str(pattern_id or "")
    if not pid:
        return False
    if cfg is None:
        patterns = _DEFAULT_EGA_PATTERNS
    else:
        ega = getattr(cfg, "equal_grid_admission", None)
        patterns = (
            getattr(ega, "patterns", None) if ega is not None else None
        ) or _DEFAULT_EGA_PATTERNS
    return pid in set(patterns)


def ega_anti_slice_mode(cfg: MosaicConfig | None) -> str:
    if not effective_equal_grid_admission_enabled(cfg):
        return "hard"
    ega = getattr(cfg, "equal_grid_admission", None)
    anti = getattr(ega, "anti_slice", None) if ega is not None else None
    mode = str(getattr(anti, "mode", "exempt") or "exempt").strip().lower()
    return mode if mode in ("exempt", "soft_penalty", "hard") else "exempt"


def ega_clone_mode(cfg: MosaicConfig | None) -> str:
    if not effective_equal_grid_admission_enabled(cfg):
        return "hard"
    ega = getattr(cfg, "equal_grid_admission", None)
    clone = getattr(ega, "near_scene_clone", None) if ega is not None else None
    mode = str(getattr(clone, "mode", "soft_penalty") or "soft_penalty").strip().lower()
    return mode if mode in ("soft_penalty", "hard") else "soft_penalty"


def ega_clone_score_mul(cfg: MosaicConfig | None) -> float:
    ega = getattr(cfg, "equal_grid_admission", None) if cfg is not None else None
    clone = getattr(ega, "near_scene_clone", None) if ega is not None else None
    mul = getattr(clone, "score_mul", 0.85) if clone is not None else 0.85
    return float(mul)


def ega_anti_slice_score_mul(cfg: MosaicConfig | None) -> float:
    ega = getattr(cfg, "equal_grid_admission", None) if cfg is not None else None
    anti = getattr(ega, "anti_slice", None) if ega is not None else None
    mul = getattr(anti, "score_mul", 0.90) if anti is not None else 0.90
    return float(mul)


def ega_flat_window_equal_bonus(cfg: MosaicConfig | None) -> float:
    """PR-C · additive score boost for equal-grid on flat windows (0 = off)."""
    if not effective_equal_grid_admission_enabled(cfg):
        return 0.0
    ega = getattr(cfg, "equal_grid_admission", None)
    scoring = getattr(ega, "scoring", None) if ega is not None else None
    bonus = getattr(scoring, "flat_window_equal_bonus", 0.08) if scoring is not None else 0.08
    return max(0.0, float(bonus))


def ega_wasted_hero_extra(cfg: MosaicConfig | None) -> float:
    """PR-C · extra mul penalty for hero-70 on flat windows (0 = off)."""
    if not effective_equal_grid_admission_enabled(cfg):
        return 0.0
    ega = getattr(cfg, "equal_grid_admission", None)
    scoring = getattr(ega, "scoring", None) if ega is not None else None
    extra = (
        getattr(scoring, "wasted_hero_ega_extra", 0.10) if scoring is not None else 0.10
    )
    return max(0.0, min(1.0, float(extra)))


def is_ega_hero70_family(pattern_id: str) -> bool:
    """D-EGA-07 · weighted mosaic-4 hero family (not equal-grid whitelist)."""
    pid = str(pattern_id or "")
    return pid == "screen-mosaic-4-hero-70-sidebar" or "hero-70" in pid


def _ega_size6(cfg: MosaicConfig | None) -> EqualGridAdmissionSize6Config | None:
    if not effective_equal_grid_admission_enabled(cfg):
        return None
    ega = getattr(cfg, "equal_grid_admission", None) if cfg is not None else None
    size6 = getattr(ega, "size6", None) if ega is not None else None
    return size6 if isinstance(size6, EqualGridAdmissionSize6Config) else None


def effective_ega_keep_equal_six(cfg: MosaicConfig | None) -> bool:
    """PR-B · keep evaluating landscape-6 after hero-6 precheck fail."""
    size6 = _ega_size6(cfg)
    if size6 is None and not effective_equal_grid_admission_enabled(cfg):
        return False
    if size6 is None:
        return True
    return bool(getattr(size6, "keep_equal_grid_after_hero_precheck_fail", True))


def effective_ega_soften_atom_valid_invalid_mix(cfg: MosaicConfig | None) -> bool:
    """P0 · EGA equal-grid may pass scene_cluster valid/-1 mix (same shotGroup)."""
    size6 = _ega_size6(cfg)
    if size6 is None:
        return False
    return bool(getattr(size6, "soften_atom_valid_invalid_mix", True))


def effective_ega_prefer_pure_landscape_six(cfg: MosaicConfig | None) -> bool:
    """P1 · pure 6×L window prefers size=6 MCS order."""
    size6 = _ega_size6(cfg)
    if size6 is None:
        return False
    return bool(getattr(size6, "prefer_pure_landscape_window", True))


def effective_ega_l6_large_quota_exempt(cfg: MosaicConfig | None) -> bool:
    """P2 · landscape-6 exempt from large-mosaic chapter quota."""
    size6 = _ega_size6(cfg)
    if size6 is None:
        return False
    return bool(getattr(size6, "large_mosaic_quota_exempt", True))


def effective_ega_landscape1_flood_reopen_after(cfg: MosaicConfig | None) -> int:
    """P3 · consecutive landscape-1 count before forcing size=6 retry (0=off)."""
    size6 = _ega_size6(cfg)
    if size6 is None:
        return 0
    return max(0, int(getattr(size6, "landscape1_flood_reopen_after", 0) or 0))


def _str_tuple(raw: object) -> tuple[str, ...]:
    if not isinstance(raw, (list, tuple)):
        return ()
    out: list[str] = []
    for item in raw:
        s = str(item).strip()
        if s:
            out.append(s)
    return tuple(out)


def _template_experiments_from_dict(raw: dict[str, Any]) -> TemplateExperimentsConfig:
    defaults = TemplateExperimentsConfig()
    te = raw.get("template_experiments")
    if not isinstance(te, dict):
        te = raw.get("templateExperiments")
    if not isinstance(te, dict):
        return defaults
    unknown = sorted(str(k) for k in te if str(k) not in _TEMPLATE_EXPERIMENTS_KNOWN_KEYS)
    if unknown:
        raise ValueError(
            "mosaic.template_experiments unknown keys (fail-loud): " + ", ".join(unknown)
        )
    # Partial block: missing allowlist/cohort stay empty (fail-closed).
    # Product defaults apply only when the whole template_experiments section is absent.
    allow_raw = te.get("allowlist")
    cohort_raw = te.get("cohort_trip_ids", te.get("cohortTripIds"))
    return TemplateExperimentsConfig(
        enabled=cfg_bool(te, "enabled", "enabled", defaults.enabled),
        allowlist=_str_tuple(allow_raw) if allow_raw is not None else (),
        cohort_trip_ids=_str_tuple(cohort_raw) if cohort_raw is not None else (),
    )


def _nested_enabled(block: object, *, default: bool) -> bool:
    if not isinstance(block, dict):
        return default
    return cfg_bool(block, "enabled", "enabled", default)


def _selection_optimization_from_dict(raw: dict[str, Any]) -> SelectionOptimizationConfig:
    defaults = SelectionOptimizationConfig()
    so = raw.get("selection_optimization")
    if not isinstance(so, dict):
        so = raw.get("selectionOptimization")
    if not isinstance(so, dict):
        return defaults
    unknown = sorted(str(k) for k in so if str(k) not in _SELECTION_OPTIMIZATION_KNOWN_KEYS)
    if unknown:
        raise ValueError(
            "mosaic.selection_optimization unknown keys (fail-loud): " + ", ".join(unknown)
        )
    gap_raw = so.get("hero_gap_threshold", so.get("heroGapThreshold"))
    gap: float | None
    if gap_raw is None:
        gap = defaults.hero_gap_threshold
    else:
        gap = float(gap_raw)
    return SelectionOptimizationConfig(
        enabled=cfg_bool(so, "enabled", "enabled", defaults.enabled),
        hero_six_opportunity_enabled=_nested_enabled(
            so.get("hero_six_opportunity", so.get("heroSixOpportunity")),
            default=defaults.hero_six_opportunity_enabled,
        ),
        mixed_hero_routing_enabled=_nested_enabled(
            so.get("mixed_hero_routing", so.get("mixedHeroRouting")),
            default=defaults.mixed_hero_routing_enabled,
        ),
        hero_gap_threshold=gap,
    )


def effective_selection_optimization_enabled(cfg: MosaicConfig | None) -> bool:
    """Parent OFF ⇒ all nested MTSO selection knobs are inert."""
    if cfg is None:
        return False
    so = getattr(cfg, "selection_optimization", None)
    return bool(so is not None and getattr(so, "enabled", False))


def _slot_adaptation_solve_from_dict(raw: object) -> SlotAdaptationSolveConfig:
    defaults = SlotAdaptationSolveConfig()
    if not isinstance(raw, dict):
        return defaults
    unknown = sorted(str(k) for k in raw if str(k) not in _SLOT_ADAPTATION_SOLVE_KNOWN_KEYS)
    if unknown:
        raise ValueError(
            "mosaic.slot_adaptation.solve unknown keys (fail-loud): " + ", ".join(unknown)
        )
    return SlotAdaptationSolveConfig(
        max_iters=int(raw.get("max_iters", raw.get("maxIters", defaults.max_iters))),
        track_weight_min=float(
            raw.get("track_weight_min", raw.get("trackWeightMin", defaults.track_weight_min))
        ),
        track_weight_max=float(
            raw.get("track_weight_max", raw.get("trackWeightMax", defaults.track_weight_max))
        ),
    )


def _slot_adaptation_from_dict(raw: dict[str, Any]) -> SlotAdaptationConfig:
    defaults = SlotAdaptationConfig()
    sa = raw.get("slot_adaptation")
    if not isinstance(sa, dict):
        sa = raw.get("slotAdaptation")
    if not isinstance(sa, dict):
        return defaults
    unknown = sorted(str(k) for k in sa if str(k) not in _SLOT_ADAPTATION_KNOWN_KEYS)
    if unknown:
        raise ValueError(
            "mosaic.slot_adaptation unknown keys (fail-loud): " + ", ".join(unknown)
        )
    clamp_raw = sa.get("hero_target_clamp", sa.get("heroTargetClamp"))
    if isinstance(clamp_raw, (list, tuple)) and len(clamp_raw) == 2:
        clamp = (float(clamp_raw[0]), float(clamp_raw[1]))
    else:
        clamp = defaults.hero_target_clamp
    peaks_raw = sa.get("land_peaks", sa.get("landPeaks"))
    peaks = dict(defaults.land_peaks)
    if isinstance(peaks_raw, dict):
        for key, val in peaks_raw.items():
            peaks[str(key)] = float(val)
    return SlotAdaptationConfig(
        enabled=cfg_bool(sa, "enabled", "enabled", defaults.enabled),
        whitespace_max=cfg_float(
            sa, "whitespace_max", "whitespaceMax", defaults.whitespace_max
        ),
        crop_risk_contain_threshold=cfg_float(
            sa,
            "crop_risk_contain_threshold",
            "cropRiskContainThreshold",
            defaults.crop_risk_contain_threshold,
        ),
        hero_target_clamp=clamp,
        land_peaks=peaks,
        wide_peak_fraction=cfg_float(
            sa, "wide_peak_fraction", "widePeakFraction", defaults.wide_peak_fraction
        ),
        solve=_slot_adaptation_solve_from_dict(sa.get("solve")),
    )


def effective_slot_adaptation_enabled(cfg: MosaicConfig | None) -> bool:
    """Parent OFF ⇒ all nested MSA knobs are inert."""
    if cfg is None:
        return False
    sa = getattr(cfg, "slot_adaptation", None)
    return bool(sa is not None and getattr(sa, "enabled", False))


def _equal_grid_selection_gate_from_dict(raw: object) -> EqualGridSelectionGateConfig:
    defaults = EqualGridSelectionGateConfig()
    if not isinstance(raw, dict):
        return defaults
    unknown = sorted(
        str(k) for k in raw if str(k) not in _EQUAL_GRID_SELECTION_GATE_KNOWN_KEYS
    )
    if unknown:
        raise ValueError(
            "mosaic.equal_grid_contract.selection_gate unknown keys (fail-loud): "
            + ", ".join(unknown)
        )
    peaks_raw = raw.get("allow_peaks", raw.get("allowPeaks", defaults.allow_peaks))
    if isinstance(peaks_raw, (list, tuple)):
        peaks = tuple(str(p).strip() for p in peaks_raw if str(p).strip())
    else:
        peaks = defaults.allow_peaks
    mode = str(raw.get("mode", defaults.mode) or defaults.mode).strip()
    if mode not in ("soft_penalty", "hard_reject"):
        raise ValueError(
            "mosaic.equal_grid_contract.selection_gate.mode must be "
            "'soft_penalty' or 'hard_reject'"
        )
    mul = float(raw.get("score_mul", raw.get("scoreMul", defaults.score_mul)))
    if not (0.0 < mul <= 1.0):
        raise ValueError(
            "mosaic.equal_grid_contract.selection_gate.score_mul must be in (0, 1]"
        )
    return EqualGridSelectionGateConfig(
        enabled=cfg_bool(raw, "enabled", "enabled", defaults.enabled),
        mode=mode,
        allow_peaks=peaks or defaults.allow_peaks,
        allow_mixed_median_min=cfg_float(
            raw,
            "allow_mixed_median_min",
            "allowMixedMedianMin",
            defaults.allow_mixed_median_min,
        ),
        score_mul=mul,
    )


def _equal_grid_contract_from_dict(raw: dict[str, Any]) -> EqualGridContractConfig:
    defaults = EqualGridContractConfig()
    egc = raw.get("equal_grid_contract")
    if not isinstance(egc, dict):
        egc = raw.get("equalGridContract")
    if not isinstance(egc, dict):
        return defaults
    unknown = sorted(str(k) for k in egc if str(k) not in _EQUAL_GRID_CONTRACT_KNOWN_KEYS)
    if unknown:
        raise ValueError(
            "mosaic.equal_grid_contract unknown keys (fail-loud): " + ", ".join(unknown)
        )
    patterns_raw = egc.get("patterns")
    if patterns_raw is None:
        patterns = defaults.patterns
    else:
        patterns = _str_tuple(patterns_raw) or defaults.patterns
    return EqualGridContractConfig(
        enabled=cfg_bool(egc, "enabled", "enabled", defaults.enabled),
        fix_stage_css=cfg_bool(
            egc, "fix_stage_css", "fixStageCss", defaults.fix_stage_css
        ),
        selection_gate=_equal_grid_selection_gate_from_dict(
            egc.get("selection_gate", egc.get("selectionGate"))
        ),
        release_stage_on_narrow_peak=cfg_bool(
            egc,
            "release_stage_on_narrow_peak",
            "releaseStageOnNarrowPeak",
            defaults.release_stage_on_narrow_peak,
        ),
        page_letterbox=cfg_bool(
            egc, "page_letterbox", "pageLetterbox", defaults.page_letterbox
        ),
        patterns=patterns,
    )


def effective_equal_grid_contract_enabled(cfg: MosaicConfig | None) -> bool:
    """Parent OFF ⇒ MEGC selection gate is inert (CSS may still be live via O-05)."""
    if cfg is None:
        return False
    egc = getattr(cfg, "equal_grid_contract", None)
    return bool(egc is not None and getattr(egc, "enabled", False))


def effective_megc_selection_gate_enabled(cfg: MosaicConfig | None) -> bool:
    """Parent + selection_gate both ON."""
    if not effective_equal_grid_contract_enabled(cfg):
        return False
    egc = getattr(cfg, "equal_grid_contract", None)
    gate = getattr(egc, "selection_gate", None) if egc is not None else None
    return bool(gate is not None and getattr(gate, "enabled", False))


def mosaic_from_dict(raw: dict[str, Any]) -> MosaicConfig:
    defaults = MosaicConfig()
    sizes_raw = raw.get("enabled_window_sizes", raw.get("enabledWindowSizes", defaults.enabled_window_sizes))
    if isinstance(sizes_raw, (list, tuple)):
        sizes = tuple(int(x) for x in sizes_raw)
    else:
        sizes = defaults.enabled_window_sizes
    weights_raw = raw.get("weights") if isinstance(raw.get("weights"), dict) else {}
    penalties_raw = raw.get("penalties") if isinstance(raw.get("penalties"), dict) else {}
    self_heal = raw.get("self_heal") if isinstance(raw.get("self_heal"), dict) else {}
    if isinstance(raw.get("selfHeal"), dict):
        self_heal = raw["selfHeal"]
    allow_drop = bool(self_heal.get("allow_drop", self_heal.get("allowDrop", defaults.allow_drop)))
    self_heal_enabled = bool(
        self_heal.get("enabled", raw.get("self_heal_enabled", defaults.self_heal_enabled))
    )
    max_drop = self_heal.get("max_drop_ratio", self_heal.get("maxDropRatio", defaults.max_drop_ratio))
    return MosaicConfig(
        enabled=bool(raw.get("enabled", defaults.enabled)),
        scorer_version=str(raw.get("scorer_version", raw.get("scorerVersion", defaults.scorer_version))),
        deterministic_strict=cfg_bool(
            raw, "deterministic_strict", "deterministicStrict", defaults.deterministic_strict
        ),
        min_candidate_score=cfg_float(
            raw, "min_candidate_score", "minCandidateScore", defaults.min_candidate_score
        ),
        enabled_window_sizes=sizes or defaults.enabled_window_sizes,
        unified_mode=bool(raw.get("unified_mode", raw.get("unifiedMode", defaults.unified_mode))),
        fallback_to_legacy=bool(
            raw.get("fallback_to_legacy", raw.get("fallbackToLegacy", defaults.fallback_to_legacy))
        ),
        self_heal_enabled=self_heal_enabled,
        allow_drop=allow_drop,
        max_drop_ratio=float(max_drop) if max_drop is not None else defaults.max_drop_ratio,
        self_heal_max_rescore=cfg_int(
            self_heal,
            "max_rescore",
            "maxRescore",
            defaults.self_heal_max_rescore,
        ),
        self_heal_max_drop_attempts=cfg_int(
            self_heal,
            "max_drop_attempts",
            "maxDropAttempts",
            defaults.self_heal_max_drop_attempts,
        ),
        candidate_top_k=int(raw.get("candidate_top_k", raw.get("candidateTopK", defaults.candidate_top_k))),
        log_level=str(raw.get("log_level", raw.get("logLevel", defaults.log_level))),
        hero_weighted_geometry_guard=cfg_bool(
            raw,
            "hero_weighted_geometry_guard",
            "heroWeightedGeometryGuard",
            defaults.hero_weighted_geometry_guard,
        ),
        main_ar_guard=cfg_bool(
            raw,
            "main_ar_guard",
            "mainArGuard",
            defaults.main_ar_guard,
        ),
        main_ar_ladder_tol=cfg_float(
            raw,
            "main_ar_ladder_tol",
            "mainArLadderTol",
            defaults.main_ar_ladder_tol,
        ),
        main_ar_prefer_16_9=cfg_bool(
            raw,
            "main_ar_prefer_16_9",
            "mainArPrefer169",
            defaults.main_ar_prefer_16_9,
        ),
        skip_dense_window_multi_portrait=cfg_bool(
            raw,
            "skip_dense_window_multi_portrait",
            "skipDenseWindowMultiPortrait",
            defaults.skip_dense_window_multi_portrait,
        ),
        prefer_five_slot_single_portrait=cfg_bool(
            raw,
            "prefer_five_slot_single_portrait",
            "preferFiveSlotSinglePortrait",
            defaults.prefer_five_slot_single_portrait,
        ),
        weights={k: float(weights_raw.get(k, defaults.weights.get(k, 0.0))) for k in defaults.weights},
        penalties={
            k: float(penalties_raw.get(k, defaults.penalties.get(k, 0.0))) for k in defaults.penalties
        },
        density_budget=_density_budget_from_dict(raw),
        template_contract=_template_contract_from_dict(raw),
        template_experiments=_template_experiments_from_dict(raw),
        selection_optimization=_selection_optimization_from_dict(raw),
        slot_adaptation=_slot_adaptation_from_dict(raw),
        equal_grid_contract=_equal_grid_contract_from_dict(raw),
        near_scene_clone_gate=_near_scene_clone_gate_from_dict(raw),
        equal_grid_admission=_equal_grid_admission_from_dict(raw),
        enable_size3_aux=cfg_bool(
            raw, "enable_size3_aux", "enableSize3Aux", defaults.enable_size3_aux
        ),
        track_id=(
            str(raw["track_id"]).strip()
            if isinstance(raw.get("track_id"), str) and raw["track_id"].strip()
            else (
                str(raw["trackId"]).strip()
                if isinstance(raw.get("trackId"), str) and raw["trackId"].strip()
                else defaults.track_id
            )
        ),
        track_dense_collage_cap=(
            int(raw["track_dense_collage_cap"])
            if raw.get("track_dense_collage_cap") is not None
            else (
                int(raw["trackDenseCollageCap"])
                if raw.get("trackDenseCollageCap") is not None
                else defaults.track_dense_collage_cap
            )
        ),
    )
