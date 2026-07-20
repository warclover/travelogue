"""Layout engine and scoring configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.config_helpers import cfg_bool


@dataclass
class LayoutScoringConfig:
    """V2 layout search (ADR-002); disabled by default = legacy behavior."""

    enabled: bool = False
    beam_width: int = 3
    prefix_beam_enabled: bool = False  # AAD-20 PrefixBeam · default off (VariantRerank)
    max_screens_per_chapter: int = 12
    min_layout_eligible: int = 3
    min_aspect_kinds: int = 1
    search_timeout_ms: int = 2000
    max_candidates_per_bucket: int = 12
    max_evaluations_per_trip: int = 500
    max_evaluations_per_segment: int = 0
    allow_burst_split: bool = False
    subject_run_tolerance: int = 1
    skip_duplicate_signatures: bool = True
    incremental: bool = False
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "aspect_match": 0.0,
            "sharpness": 0.0,
            "hero_separation": 0.0,
            "temporal_coherence": 0.0,
            "diversity": 0.0,
            "arc_fit": 0.0,
            "burst_integrity": 0.0,
            "luminance_continuity": 0.0,
            "subject_run": 0.0,
            "tone_continuity": 0.0,
            "layout_rhythm": 0.0,
            "gravity_balance": 0.0,
            "category_coherence": 0.0,
        }
    )


@dataclass
class LayoutFeedbackConfig:
    enabled: bool = False
    log_path: str | None = None


@dataclass
class LayoutLateChapterPairingConfig:
    """后几章竖版收束：前几章维持 defer/carry  outward，后章加强成对。"""

    from_chapter_index: int = 3  # 1-based · 含第 3 章
    reset_orientation_streak: bool = True
    reset_pair_streak: bool = True
    no_outward_portrait_carry: bool = True
    flush_lookahead_portraits: int = 3  # 0 = 关闭章内 look-ahead
    beam_portrait_single_penalty: float = 0.12
    beam_portrait_pair_bonus: float = 0.06


@dataclass
class LayoutRhythmConfig:
    """排版规则优化 v0.5 · 节奏阈值（G-07 可配置；默认 = 规划器既有硬编码）。

    单一来源：travelogue/curation/screen_layout_state.py 的 RhythmRules 读取本段；
    LSE 策略包 rhythm 段（启用时）优先级更高。
    """

    max_portrait_pair_streak: int = 2  # R-06 · portrait-2 连续上限
    max_portrait_orientation_streak: int = 6  # R-08 · 全竖版屏朝向连续上限
    portrait_carry_max_hops: int = 0  # 0 = auto · 可顺延至后续全部章节
    post_check_mode: str = "log"  # log | enforce（OQ-09=B 渐进；CI 断言见 tests/unit/layout_engine/test_rhythm_ci_gate.py）
    late_chapter_pairing: LayoutLateChapterPairingConfig = field(
        default_factory=LayoutLateChapterPairingConfig
    )


@dataclass
class LayoutStrategyCapabilitiesConfig:
    """P17 LSE CAP 能力开关 · FROZEN（2026-06 处置建议路线 A）。

    消融实测屏级变更率 0~4%，观感收益未证明：保留代码与开关、默认全关，
    不再扩展新能力；复评门槛见 docs/P17-LSE-处置建议.md §5。
    """

    saliency_scoring: bool = False
    beat_profile: str = "flat"
    tone_harmony: bool = False
    hungarian_assignment: bool = False
    quality_unified: bool = False
    segment_order_optimizer: bool = False
    implicit_feedback_export: bool = False
    pace_profile: bool = False
    highlight_windows: bool = False
    editorial_hints: bool = False


@dataclass
class LayoutStrategyTelemetryConfig:
    emit_per_window: bool = True
    decision_log_max_events: int = 2000


@dataclass
class LayoutStrategyOverridesConfig:
    disable_stages: tuple[str, ...] = ()
    disable_profiles: tuple[str, ...] = ()


@dataclass
class LayoutStrategyEngineConfig:
    """Phase 17 LSE · default disabled = P16 behavior (R-P17-05)."""

    enabled: bool = False
    default_strategy_id: str = "lse-default-2026-06"
    policy_path: str = "travelogue/layout_engine/lse_policy.yaml"
    runtime_store: str = "data/lse_runtime.json"
    overrides: LayoutStrategyOverridesConfig = field(default_factory=LayoutStrategyOverridesConfig)
    telemetry: LayoutStrategyTelemetryConfig = field(default_factory=LayoutStrategyTelemetryConfig)
    feedback: LayoutFeedbackConfig = field(default_factory=LayoutFeedbackConfig)
    capabilities: LayoutStrategyCapabilitiesConfig = field(
        default_factory=LayoutStrategyCapabilitiesConfig
    )


@dataclass
class LayoutTemplateEngineConfig:
    enabled: bool = True
    registry_path: str = "travelogue/layout_templates/templates"
    registry_version: str = "p16-2026-06"
    policy_path: str = "travelogue/layout_templates/lte_policy.yaml"
    read_templates_from_lte: bool = True
    exclude_collage_from_mosaic: bool = True
    max_mosaic_slots: int = 9
    emit_per_template: bool = True
    telemetry_registry_versions_max: int = 8
    overrides_disable: tuple[str, ...] = ()
    diversity_mode: str | None = None
    diversity_lambda: float | None = None


@dataclass
class EditorialPortraitRowConfig:
    """PRD portrait-row-editorial · default off (legacy screen-portrait-3 unchanged)."""

    enabled: bool = False
    replace_patterns: tuple[str, ...] = ("screen-portrait-3",)
    scope: str = "all"  # all | person | scenery
    trip_allowlist: tuple[str, ...] = ()


@dataclass
class Editorial4MixConfig:
    """PRD screen-editorial-4mix · default off (legacy mosaic-4 unchanged)."""

    enabled: bool = False
    replace_patterns: tuple[str, ...] = ("screen-portrait-2-landscape-2",)
    trip_allowlist: tuple[str, ...] = ()
    scenery_portrait_cover_random: bool = True


@dataclass
class UsageRulesConfig:
    """URO · usage-driven layout rules (PRD-USAGE-RULES-LAYOUT-OPTIMIZATION)."""

    enabled: bool = False
    hero_gap_threshold: float = 0.15
    hero_gap_prefer_threshold: float = 0.15  # == threshold → UT-01 edge 区关闭
    tiebreak_enabled: bool = True
    log_rejections: bool = True
    disabled_rules: tuple[str, ...] = ()


@dataclass
class LayoutConfig:
    """Web layout engine default when exportLayout is web (see docs/web端模板升级计划.md)."""

    web_layout_engine: str = "screens"  # legacy | screens
    screen_plan_scope: str = "day"  # chapter | day — day = 按策展日桶全序列组屏
    mixed_proximity_seconds: float = 1800.0  # 混排/拼图连拍 takenAt 跨度上限（秒）· 默认 30min
    layout_density_enabled: bool = True  # PRD-FINE-CRAFT-LAYOUT-DENSITY · false → balanced
    editorial_portrait_row: EditorialPortraitRowConfig = field(
        default_factory=EditorialPortraitRowConfig
    )
    editorial_4mix: Editorial4MixConfig = field(default_factory=Editorial4MixConfig)
    usage_rules: UsageRulesConfig = field(default_factory=UsageRulesConfig)
    rhythm: LayoutRhythmConfig = field(default_factory=LayoutRhythmConfig)
    template_engine: LayoutTemplateEngineConfig = field(default_factory=LayoutTemplateEngineConfig)
    strategy_engine: LayoutStrategyEngineConfig = field(default_factory=LayoutStrategyEngineConfig)
    scoring: LayoutScoringConfig = field(default_factory=LayoutScoringConfig)
    feedback: LayoutFeedbackConfig = field(default_factory=LayoutFeedbackConfig)


def layout_scoring_from_dict(raw: dict[str, Any]) -> LayoutScoringConfig:
    weights_raw = raw.get("weights") if isinstance(raw.get("weights"), dict) else {}
    default_weights = LayoutScoringConfig().weights
    weights = {k: float(weights_raw.get(k, default_weights.get(k, 0.0))) for k in default_weights}
    return LayoutScoringConfig(
        enabled=bool(raw.get("enabled", False)),
        beam_width=int(raw.get("beam_width", 3)),
        prefix_beam_enabled=cfg_bool(
            raw, "prefix_beam_enabled", "prefixBeamEnabled", False
        ),
        max_screens_per_chapter=int(raw.get("max_screens_per_chapter", 12)),
        min_layout_eligible=int(raw.get("min_layout_eligible", 3)),
        min_aspect_kinds=int(raw.get("min_aspect_kinds", 1)),
        search_timeout_ms=int(raw.get("search_timeout_ms", 2000)),
        max_candidates_per_bucket=int(raw.get("max_candidates_per_bucket", 12)),
        max_evaluations_per_trip=int(raw.get("max_evaluations_per_trip", 500)),
        max_evaluations_per_segment=int(
            raw.get("max_evaluations_per_segment", raw.get("maxEvaluationsPerSegment", 0))
        ),
        allow_burst_split=bool(raw.get("allow_burst_split", False)),
        subject_run_tolerance=int(raw.get("subject_run_tolerance", 1)),
        skip_duplicate_signatures=cfg_bool(
            raw, "skip_duplicate_signatures", "skipDuplicateSignatures", True
        ),
        incremental=bool(raw.get("incremental", False)),
        weights=weights,
    )


def layout_template_engine_from_dict(raw: dict[str, Any]) -> LayoutTemplateEngineConfig:
    overrides = raw.get("overrides") if isinstance(raw.get("overrides"), dict) else {}
    disable_raw = overrides.get("disable") or raw.get("overrides_disable") or []
    disable = tuple(str(x) for x in disable_raw if x) if isinstance(disable_raw, list) else ()
    mcs = raw.get("mcs_integration") if isinstance(raw.get("mcs_integration"), dict) else {}
    telemetry = raw.get("telemetry") if isinstance(raw.get("telemetry"), dict) else {}
    scoring = mcs.get("scoring") if isinstance(mcs.get("scoring"), dict) else {}
    diversity = scoring.get("diversity") if isinstance(scoring.get("diversity"), dict) else {}
    div_mode_raw = diversity.get("mode")
    div_mode = str(div_mode_raw).strip().lower() if div_mode_raw is not None else None
    if div_mode not in (None, "off", "mmr", "dpp"):
        div_mode = None
    div_lambda_raw = diversity.get("lambda")
    div_lambda: float | None = None
    if div_lambda_raw is not None:
        try:
            div_lambda = float(div_lambda_raw)
        except (TypeError, ValueError):
            div_lambda = None
    return LayoutTemplateEngineConfig(
        enabled=bool(raw.get("enabled", True)),
        registry_path=str(raw.get("registry_path", "travelogue/layout_templates/templates")),
        registry_version=str(raw.get("registry_version", "p16-2026-06")),
        policy_path=str(raw.get("policy_path", "travelogue/layout_templates/lte_policy.yaml")),
        read_templates_from_lte=bool(mcs.get("read_templates_from_lte", raw.get("read_templates_from_lte", True))),
        exclude_collage_from_mosaic=bool(
            mcs.get("exclude_collage_from_mosaic", raw.get("exclude_collage_from_mosaic", True))
        ),
        max_mosaic_slots=int(raw.get("max_mosaic_slots", 9)),
        emit_per_template=bool(telemetry.get("emit_per_template", raw.get("emit_per_template", True))),
        telemetry_registry_versions_max=int(
            telemetry.get("registry_versions_max", raw.get("telemetry_registry_versions_max", 8))
        ),
        overrides_disable=disable,
        diversity_mode=div_mode,
        diversity_lambda=div_lambda,
    )


def layout_late_chapter_pairing_from_dict(
    raw: dict[str, Any] | None,
) -> LayoutLateChapterPairingConfig:
    defaults = LayoutLateChapterPairingConfig()
    if not raw:
        return defaults
    return LayoutLateChapterPairingConfig(
        from_chapter_index=int(
            raw.get("from_chapter_index", defaults.from_chapter_index)
        ),
        reset_orientation_streak=bool(
            raw.get("reset_orientation_streak", defaults.reset_orientation_streak)
        ),
        reset_pair_streak=bool(
            raw.get("reset_pair_streak", defaults.reset_pair_streak)
        ),
        no_outward_portrait_carry=bool(
            raw.get("no_outward_portrait_carry", defaults.no_outward_portrait_carry)
        ),
        flush_lookahead_portraits=int(
            raw.get("flush_lookahead_portraits", defaults.flush_lookahead_portraits)
        ),
        beam_portrait_single_penalty=float(
            raw.get("beam_portrait_single_penalty", defaults.beam_portrait_single_penalty)
        ),
        beam_portrait_pair_bonus=float(
            raw.get("beam_portrait_pair_bonus", defaults.beam_portrait_pair_bonus)
        ),
    )


def layout_rhythm_from_dict(raw: dict[str, Any]) -> LayoutRhythmConfig:
    defaults = LayoutRhythmConfig()
    mode = str(raw.get("post_check_mode", defaults.post_check_mode)).strip().lower()
    if mode not in ("log", "enforce"):
        mode = defaults.post_check_mode
    late_raw = raw.get("late_chapter_pairing")
    late = (
        layout_late_chapter_pairing_from_dict(late_raw)
        if isinstance(late_raw, dict)
        else defaults.late_chapter_pairing
    )
    return LayoutRhythmConfig(
        max_portrait_pair_streak=int(
            raw.get("max_portrait_pair_streak", defaults.max_portrait_pair_streak)
        ),
        max_portrait_orientation_streak=int(
            raw.get(
                "max_portrait_orientation_streak",
                raw.get(
                    "portrait_orientation_max_streak",
                    defaults.max_portrait_orientation_streak,
                ),
            )
        ),
        post_check_mode=mode,
        portrait_carry_max_hops=int(
            raw.get("portrait_carry_max_hops", defaults.portrait_carry_max_hops)
        ),
        late_chapter_pairing=late,
    )


def editorial_portrait_row_from_dict(raw: dict[str, Any] | None) -> EditorialPortraitRowConfig:
    defaults = EditorialPortraitRowConfig()
    if not raw:
        return defaults
    scope = str(raw.get("scope", defaults.scope)).strip().lower()
    if scope not in ("all", "person", "scenery"):
        scope = defaults.scope
    replace_raw = raw.get("replace_patterns") or list(defaults.replace_patterns)
    replace = (
        tuple(str(x) for x in replace_raw if x)
        if isinstance(replace_raw, list)
        else defaults.replace_patterns
    )
    allow_raw = raw.get("trip_allowlist") or []
    allowlist = (
        tuple(str(x) for x in allow_raw if x)
        if isinstance(allow_raw, list)
        else defaults.trip_allowlist
    )
    return EditorialPortraitRowConfig(
        enabled=bool(raw.get("enabled", defaults.enabled)),
        replace_patterns=replace or defaults.replace_patterns,
        scope=scope,
        trip_allowlist=allowlist,
    )


def usage_rules_from_dict(raw: dict[str, Any] | None) -> UsageRulesConfig:
    defaults = UsageRulesConfig()
    if not raw:
        return defaults
    disabled_raw = raw.get("disabled_rules") or []
    disabled = (
        tuple(str(x) for x in disabled_raw if x)
        if isinstance(disabled_raw, list)
        else defaults.disabled_rules
    )
    return UsageRulesConfig(
        enabled=bool(raw.get("enabled", defaults.enabled)),
        hero_gap_threshold=float(raw.get("hero_gap_threshold", defaults.hero_gap_threshold)),
        hero_gap_prefer_threshold=float(
            raw.get("hero_gap_prefer_threshold", defaults.hero_gap_prefer_threshold)
        ),
        tiebreak_enabled=bool(raw.get("tiebreak_enabled", defaults.tiebreak_enabled)),
        log_rejections=bool(raw.get("log_rejections", defaults.log_rejections)),
        disabled_rules=disabled,
    )


def editorial_4mix_from_dict(raw: dict[str, Any] | None) -> Editorial4MixConfig:
    defaults = Editorial4MixConfig()
    if not raw:
        return defaults
    replace_raw = raw.get("replace_patterns") or list(defaults.replace_patterns)
    replace = (
        tuple(str(x) for x in replace_raw if x)
        if isinstance(replace_raw, list)
        else defaults.replace_patterns
    )
    allow_raw = raw.get("trip_allowlist") or []
    allowlist = (
        tuple(str(x) for x in allow_raw if x)
        if isinstance(allow_raw, list)
        else defaults.trip_allowlist
    )
    return Editorial4MixConfig(
        enabled=bool(raw.get("enabled", defaults.enabled)),
        replace_patterns=replace or defaults.replace_patterns,
        trip_allowlist=allowlist,
        scenery_portrait_cover_random=bool(
            raw.get("scenery_portrait_cover_random", defaults.scenery_portrait_cover_random)
        ),
    )


def layout_feedback_from_dict(raw: dict[str, Any]) -> LayoutFeedbackConfig:
    log_path = raw.get("log_path")
    return LayoutFeedbackConfig(
        enabled=bool(raw.get("enabled", False)),
        log_path=str(log_path).strip() if log_path else None,
    )


def layout_strategy_engine_from_dict(raw: dict[str, Any]) -> LayoutStrategyEngineConfig:
    defaults = LayoutStrategyEngineConfig()
    overrides_raw = raw.get("overrides") if isinstance(raw.get("overrides"), dict) else {}
    telemetry_raw = raw.get("telemetry") if isinstance(raw.get("telemetry"), dict) else {}
    feedback_raw = raw.get("feedback") if isinstance(raw.get("feedback"), dict) else {}
    caps_raw = raw.get("capabilities") if isinstance(raw.get("capabilities"), dict) else {}
    disable_stages = overrides_raw.get("disable_stages") or []
    disable_profiles = overrides_raw.get("disable_profiles") or []
    beat_raw = caps_raw.get("beat_profile", defaults.capabilities.beat_profile)
    beat_profile = str(beat_raw).strip() if beat_raw is not None else defaults.capabilities.beat_profile
    return LayoutStrategyEngineConfig(
        enabled=bool(raw.get("enabled", defaults.enabled)),
        default_strategy_id=str(
            raw.get("default_strategy_id", defaults.default_strategy_id)
        ),
        policy_path=str(raw.get("policy_path", defaults.policy_path)),
        runtime_store=str(raw.get("runtime_store", defaults.runtime_store)),
        overrides=LayoutStrategyOverridesConfig(
            disable_stages=tuple(str(x) for x in disable_stages if x)
            if isinstance(disable_stages, list)
            else (),
            disable_profiles=tuple(str(x) for x in disable_profiles if x)
            if isinstance(disable_profiles, list)
            else (),
        ),
        telemetry=LayoutStrategyTelemetryConfig(
            emit_per_window=bool(
                telemetry_raw.get("emit_per_window", defaults.telemetry.emit_per_window)
            ),
            decision_log_max_events=int(
                telemetry_raw.get(
                    "decision_log_max_events",
                    defaults.telemetry.decision_log_max_events,
                )
            ),
        ),
        feedback=layout_feedback_from_dict(feedback_raw or {}),
        capabilities=LayoutStrategyCapabilitiesConfig(
            saliency_scoring=bool(
                caps_raw.get("saliency_scoring", defaults.capabilities.saliency_scoring)
            ),
            beat_profile=beat_profile,
            tone_harmony=bool(caps_raw.get("tone_harmony", defaults.capabilities.tone_harmony)),
            hungarian_assignment=bool(
                caps_raw.get("hungarian_assignment", defaults.capabilities.hungarian_assignment)
            ),
            quality_unified=bool(
                caps_raw.get("quality_unified", defaults.capabilities.quality_unified)
            ),
            segment_order_optimizer=bool(
                caps_raw.get(
                    "segment_order_optimizer",
                    defaults.capabilities.segment_order_optimizer,
                )
            ),
            implicit_feedback_export=bool(
                caps_raw.get(
                    "implicit_feedback_export",
                    defaults.capabilities.implicit_feedback_export,
                )
            ),
            pace_profile=bool(caps_raw.get("pace_profile", defaults.capabilities.pace_profile)),
            highlight_windows=bool(
                caps_raw.get("highlight_windows", defaults.capabilities.highlight_windows)
            ),
            editorial_hints=bool(
                caps_raw.get("editorial_hints", defaults.capabilities.editorial_hints)
            ),
        ),
    )
