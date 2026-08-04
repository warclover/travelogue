"""Mosaic decision logging (M7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.layout_engine.mosaic.runtime import MOSAIC_ROUTER_VERSION


@dataclass
class MosaicWindowLog:
    segment_id: str = ""
    window_size: int = 5
    window_start: int = 0
    candidates_count: int = 0
    winner_pattern_id: str = ""
    winner_score: float = 0.0
    top3_patterns: list[str] = field(default_factory=list)
    top3_scores: list[float] = field(default_factory=list)
    winner_reason_codes: list[str] = field(default_factory=list)
    fallback_used: bool = False
    fallback_reason: str | None = None
    self_heal_applied: bool = False
    self_heal_step: str | None = None
    dropped_asset_ids: list[str] = field(default_factory=list)
    planner_path: str = "mosaic"
    scorer_version: str = "p15-s1"
    router_version: str = MOSAIC_ROUTER_VERSION
    weights_hash: str = ""
    template_version: int | None = None
    template_registry_version: str = ""
    slot_ar_match_score: float | None = None
    face_crop_proxy: bool = False
    rejected_templates: list[dict[str, Any]] = field(default_factory=list)
    usage_rule_rejects: list[dict[str, Any]] = field(default_factory=list)
    usage_rule_hits: list[dict[str, Any]] = field(default_factory=list)
    winner_penalties: dict[str, float] = field(default_factory=dict)
    scoring_weights: dict[str, float] = field(default_factory=dict)
    scoring_penalty_weights: dict[str, float] = field(default_factory=dict)
    slot_assignment_fallback: str | None = None
    # TPC §3.3 / AC-TPC-10 — raw geometry (record-only, never penalties)
    window_mix: str | None = None
    candidate_source: str | None = None
    square_relaxed: bool = False
    hero_prominence_ratio: float | None = None
    hero_coverage_ratio: float | None = None
    cell_area_cv: float | None = None
    # MTSO · selection funnel (AC-MTSO-03 · assert via drain_mosaic_capture)
    base_window_order: list[int] = field(default_factory=list)
    effective_window_order: list[int] = field(default_factory=list)
    reorder_reason: str | None = None
    structurally_qualified_six: bool = False
    admit_six_hero: bool = False
    # EGA PR-B · size=6 kept for equal-grid after hero-6 precheck fail
    ega_equal_six_kept: bool = False
    six_hero_opportunity_state: str = "idle"
    six_hero_family_id: str | None = None
    six_hero_qualify_reason: str | None = None
    six_hero_outcome: str | None = None
    quota_snapshot: dict[str, Any] | None = None
    atom_cap: int | None = None
    reject_funnel: list[dict[str, Any]] = field(default_factory=list)
    # MSA · slot adaptation (D-MSA-10 · assert via drain_mosaic_capture)
    msa_profile: dict[str, Any] | None = None
    r_hero_target: float | None = None
    track_override: dict[str, Any] | None = None
    slot_fits: list[str] | None = None
    crop_risk: list[float] | None = None
    crop_focals: list[dict[str, Any]] | None = None
    whitespace_ratio: float | None = None
    msa_outcome: str | None = None
    # MEGC · equal-grid selection gate (AC-MEGC-07 · assert via drain_mosaic_capture)
    megc_enabled: bool = False
    megc_outcome: str | None = None
    megc_land_peak: str | None = None
    megc_pattern_id: str | None = None
    # EGA · observability (PRD §6 / SHD-01 · keep in summary+window)
    ega_enabled: bool = False
    ega_anti_slice_mode: str | None = None
    ega_clone_mode: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "routerVersion": self.router_version,
            "segmentId": self.segment_id,
            "windowSize": self.window_size,
            "windowStart": self.window_start,
            "candidatesCount": self.candidates_count,
            "winnerPatternId": self.winner_pattern_id,
            "winnerScore": round(self.winner_score, 4),
            "winnerReasonCodes": list(self.winner_reason_codes),
            "fallbackUsed": self.fallback_used,
            "fallbackReason": self.fallback_reason,
            "selfHealApplied": self.self_heal_applied,
            "selfHealStep": self.self_heal_step,
            "droppedAssetIds": list(self.dropped_asset_ids),
            "plannerPath": self.planner_path,
            "scorerVersion": self.scorer_version,
            "weightsHash": self.weights_hash,
            "baseWindowOrder": list(self.base_window_order),
            "effectiveWindowOrder": list(self.effective_window_order),
            "reorderReason": self.reorder_reason,
            "atomCap": self.atom_cap,
            "structurallyQualifiedSix": bool(self.structurally_qualified_six),
            "admitSixHero": bool(self.admit_six_hero),
            "egaEqualSixKept": bool(self.ega_equal_six_kept),
            "egaEnabled": bool(self.ega_enabled),
            "egaAntiSliceMode": self.ega_anti_slice_mode,
            "egaCloneMode": self.ega_clone_mode,
            "sixHeroOpportunityState": self.six_hero_opportunity_state or "idle",
            "sixHeroFamilyId": self.six_hero_family_id,
            "sixHeroQualifyReason": self.six_hero_qualify_reason,
            "sixHeroOutcome": self.six_hero_outcome,
            "quotaSnapshot": self.quota_snapshot,
            "rejectFunnel": list(self.reject_funnel),
            "msaProfile": self.msa_profile,
            "rHeroTarget": self.r_hero_target,
            "trackOverride": self.track_override,
            "slotFits": list(self.slot_fits) if self.slot_fits is not None else None,
            "cropRisk": list(self.crop_risk) if self.crop_risk is not None else None,
            "cropFocals": list(self.crop_focals) if self.crop_focals is not None else None,
            "whitespaceRatio": self.whitespace_ratio,
            "msaOutcome": self.msa_outcome,
            "megcEnabled": bool(self.megc_enabled),
            "megcOutcome": self.megc_outcome,
            "megcLandPeak": self.megc_land_peak,
            "megcPatternId": self.megc_pattern_id,
        }
        if self.top3_patterns:
            out["top3Patterns"] = list(self.top3_patterns)
            out["top3Scores"] = [round(s, 4) for s in self.top3_scores]
        if self.template_version is not None:
            out["templateVersion"] = self.template_version
        if self.template_registry_version:
            out["templateRegistryVersion"] = self.template_registry_version
        if self.slot_ar_match_score is not None:
            out["slotArMatchScore"] = self.slot_ar_match_score
        if self.face_crop_proxy:
            out["faceCropProxy"] = True
        if self.rejected_templates:
            out["rejectedTemplates"] = list(self.rejected_templates)
        if self.usage_rule_rejects:
            out["usageRuleRejects"] = list(self.usage_rule_rejects)
        if self.usage_rule_hits:
            out["usageRuleHits"] = list(self.usage_rule_hits)
        if self.winner_penalties:
            out["winnerPenalties"] = {
                k: round(float(v), 4) for k, v in self.winner_penalties.items()
            }
        if self.scoring_weights:
            out["scoringWeights"] = dict(self.scoring_weights)
        if self.scoring_penalty_weights:
            out["scoringPenaltyWeights"] = dict(self.scoring_penalty_weights)
        if self.slot_assignment_fallback:
            out["slotAssignmentFallback"] = self.slot_assignment_fallback
        if self.window_mix:
            out["windowMix"] = self.window_mix
        if self.candidate_source:
            out["candidateSource"] = self.candidate_source
        if self.square_relaxed:
            out["squareRelaxed"] = True
        # AC-TPC-10 · always emit keys when computed (incl. null skip)
        if self.hero_prominence_ratio is not None:
            out["heroProminenceRatio"] = self.hero_prominence_ratio
        if self.hero_coverage_ratio is not None:
            out["heroCoverageRatio"] = self.hero_coverage_ratio
        if self.cell_area_cv is not None:
            out["cellAreaCv"] = self.cell_area_cv
        return out


_WINDOW_REJECT_TOP_N = 3


def stamp_ega_observability(log: MosaicWindowLog, cfg: Any = None) -> None:
    """SHD-01 · fill egaEnabled / anti_slice / clone mode shorts on a window log."""
    from travelogue.config.mosaic import (
        ega_anti_slice_mode,
        ega_clone_mode,
        effective_equal_grid_admission_enabled,
    )

    enabled = bool(effective_equal_grid_admission_enabled(cfg))
    log.ega_enabled = enabled
    if enabled:
        log.ega_anti_slice_mode = ega_anti_slice_mode(cfg)
        log.ega_clone_mode = ega_clone_mode(cfg)
    else:
        log.ega_anti_slice_mode = None
        log.ega_clone_mode = None


def _compact_reject(entry: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "templateId": entry.get("templateId"),
        "reason": entry.get("reason"),
    }
    if entry.get("detail"):
        out["detail"] = entry["detail"]
    return out


def format_log_entry(raw: dict[str, Any], log_level: str = "window") -> dict[str, Any]:
    """Filter persisted log fields by level (D-MCS-10 · summary/window/debug).

    LTN H2 · window keeps rejectedTemplates Top3 (compact) for Studio/C6 explain;
    AC/metrics must consume raw buffers via drain_mosaic_capture, not this output.
    EGA SHD-01 · summary/window keep egaEnabled / egaEqualSixKept / mode shorts.
    """
    if log_level == "debug":
        return dict(raw)
    summary_keys = (
        "segmentId",
        "windowSize",
        "windowStart",
        "winnerPatternId",
        "winnerScore",
        "winnerReasonCodes",
        "fallbackUsed",
        "fallbackReason",
        "selfHealApplied",
        "plannerPath",
        "scorerVersion",
        "routerVersion",
        "isWinnerPlan",
        "planPhase",
        "egaEnabled",
        "egaEqualSixKept",
        "egaAntiSliceMode",
        "egaCloneMode",
    )
    if log_level == "summary":
        return {k: raw[k] for k in summary_keys if k in raw}
    # window: drop top3 score arrays; keep Top3 rejects + geom/mainAr summaries
    out = dict(raw)
    out.pop("top3Scores", None)
    # MTSO / MSA funnel fields stay in raw (drain_mosaic_capture) + debug only.
    # EGA shorts (egaEnabled / egaEqualSixKept / modes) stay for G-05 dogfood.
    for heavy in (
        "baseWindowOrder",
        "effectiveWindowOrder",
        "reorderReason",
        "atomCap",
        "structurallyQualifiedSix",
        "admitSixHero",
        "sixHeroOpportunityState",
        "sixHeroFamilyId",
        "sixHeroQualifyReason",
        "sixHeroOutcome",
        "quotaSnapshot",
        "rejectFunnel",
        "msaProfile",
        "rHeroTarget",
        "trackOverride",
        "slotFits",
        "cropRisk",
        "cropFocals",
        "whitespaceRatio",
        "msaOutcome",
        "megcEnabled",
        "megcOutcome",
        "megcLandPeak",
        "megcPatternId",
        "candidatesCount",
        "weightsHash",
        "droppedAssetIds",
        "selfHealStep",
    ):
        out.pop(heavy, None)
    rejected = list(raw.get("rejectedTemplates") or [])
    geom_rejected = [
        {"templateId": r["templateId"], "reason": r["reason"]}
        for r in rejected
        if r.get("reason") == "geometry_invalid"
    ]
    if geom_rejected:
        out["geometryRejectedTemplates"] = geom_rejected
    main_ar_rejected = [
        {
            "templateId": r["templateId"],
            "reason": r["reason"],
            **({"detail": r["detail"]} if r.get("detail") else {}),
        }
        for r in rejected
        if r.get("reason") == "main_ar_ineligible"
    ]
    if main_ar_rejected:
        out["mainArRejectedTemplates"] = main_ar_rejected
    if rejected:
        out["rejectedTemplates"] = [
            _compact_reject(r) for r in rejected[:_WINDOW_REJECT_TOP_N]
        ]
    else:
        out.pop("rejectedTemplates", None)
    return out


def annotate_winner_plan_logs(
    logs: list[dict[str, Any]], chapters: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """LTN H2 / E5 · mark entries whose winnerPatternId appears on the final plan."""
    on_screen: set[tuple[str, str]] = set()
    on_screen_patterns: set[str] = set()
    for ch in chapters:
        seg = str((ch.get("curation") or {}).get("segmentId") or ch.get("id") or "")
        for sc in ch.get("screens") or []:
            pid = str(sc.get("patternId") or "")
            if not pid:
                continue
            on_screen_patterns.add(pid)
            on_screen.add((seg, pid))
    out: list[dict[str, Any]] = []
    for entry in logs:
        row = dict(entry)
        seg = str(row.get("segmentId") or "")
        pid = str(row.get("winnerPatternId") or "")
        if seg and (seg, pid) in on_screen:
            winner = True
        elif not seg and pid in on_screen_patterns:
            winner = True
        else:
            winner = bool(pid) and pid in on_screen_patterns
        row["isWinnerPlan"] = winner
        row.setdefault("planPhase", "pass1")
        out.append(row)
    return out
