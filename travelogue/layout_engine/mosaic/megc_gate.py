"""MEGC · equal-grid selection gate (P-选 · PR-B / M2).

Pure functions: window peak via ``build_msa_profile`` (MSA parent OFF still OK),
then allow / soft ``score_mul`` / hard reject. Mixed-orient equal grids always
hard-reject on non-cinema peaks (D-MEGC-06). SUP-MEGC-03: empty candidate pool
after hard reject may soft-reemit with ``megcGateFallback``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from travelogue.config.mosaic import (
    EqualGridContractConfig,
    EqualGridSelectionGateConfig,
    MosaicConfig,
    SlotAdaptationConfig,
    effective_megc_selection_gate_enabled,
)
from travelogue.layout_engine.mosaic.msa_profile import MsaProfile, build_msa_profile

# Equal-grid patterns that mix portrait + landscape roles into 16:9 cells.
MEGC_MIXED_ORIENT_PATTERNS: frozenset[str] = frozenset(
    {
        "screen-portrait-2-landscape-2",
        "screen-mosaic-4-2l2p-weighted",
        "screen-editorial-4mix",
    }
)

MEGC_REJECT_REASON = "megc_gate"


@dataclass(frozen=True)
class MegcGateDecision:
    """Decision for one pattern against a window peak."""

    active: bool
    outcome: str  # skipped | gate_allow | gate_penalize | gate_reject
    land_peak: str | None
    land_median_r: float | None
    score_mul: float
    hard_reject: bool
    mixed_orient: bool
    pattern_id: str
    detail: str | None = None

    def to_log_fields(self) -> dict[str, Any]:
        return {
            "megcOutcome": self.outcome,
            "megcLandPeak": self.land_peak,
            "megcPatternId": self.pattern_id,
        }


def _egc(cfg: MosaicConfig | None) -> EqualGridContractConfig:
    if cfg is None:
        return EqualGridContractConfig()
    return getattr(cfg, "equal_grid_contract", None) or EqualGridContractConfig()


def _gate(cfg: MosaicConfig | None) -> EqualGridSelectionGateConfig:
    return _egc(cfg).selection_gate


def is_megc_pattern(pattern_id: str, cfg: MosaicConfig | None) -> bool:
    pid = str(pattern_id or "")
    if not pid:
        return False
    return pid in set(_egc(cfg).patterns)


def is_megc_mixed_orient(pattern_id: str) -> bool:
    return str(pattern_id or "") in MEGC_MIXED_ORIENT_PATTERNS


def window_assets_for_megc(
    asset_ids: Sequence[str],
    assets_map: Mapping[str, Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    out: list[Mapping[str, Any]] = []
    for aid in asset_ids:
        asset = assets_map.get(aid)
        if isinstance(asset, Mapping):
            out.append(asset)
    return out


def peak_allowed(profile: MsaProfile, gate: EqualGridSelectionGateConfig) -> bool:
    """Cinema / wide-enough mixed medians are first-class equal-grid citizens."""
    peak = str(profile.land_peak or "")
    allow = {str(p) for p in gate.allow_peaks}
    if peak in allow:
        return True
    if peak == "mixed":
        med = profile.land_median_r
        if med is not None and float(med) >= float(gate.allow_mixed_median_min):
            return True
    return False


def build_megc_profile(
    assets: Sequence[Mapping[str, Any]],
    *,
    cfg: MosaicConfig | None = None,
) -> MsaProfile:
    """Peak profile for MEGC; reuses MSA ladder even when MSA parent is OFF."""
    sa = None
    if cfg is not None:
        sa = getattr(cfg, "slot_adaptation", None)
    if not isinstance(sa, SlotAdaptationConfig):
        sa = SlotAdaptationConfig()
    # Force-read peaks without requiring MSA ``enabled`` (BLK-MEGC-07).
    return build_msa_profile(assets, cfg=sa)


def evaluate_megc_gate(
    pattern_id: str,
    assets: Sequence[Mapping[str, Any]],
    cfg: MosaicConfig | None,
    *,
    profile: MsaProfile | None = None,
) -> MegcGateDecision:
    """Evaluate P-选 for one pattern.

    Soft path (``mode=soft_penalty``): pure landscape → ``score_mul``; mixed-orient
    still hard-rejects (D-06). Hard path: both families hard-reject on mismatch.
    """
    pid = str(pattern_id or "")
    if not effective_megc_selection_gate_enabled(cfg) or not is_megc_pattern(pid, cfg):
        return MegcGateDecision(
            active=False,
            outcome="skipped",
            land_peak=None,
            land_median_r=None,
            score_mul=1.0,
            hard_reject=False,
            mixed_orient=is_megc_mixed_orient(pid),
            pattern_id=pid,
            detail="gate_inactive_or_non_pattern",
        )

    gate = _gate(cfg)
    prof = profile if profile is not None else build_megc_profile(assets, cfg=cfg)
    mixed = is_megc_mixed_orient(pid)
    if peak_allowed(prof, gate):
        return MegcGateDecision(
            active=True,
            outcome="gate_allow",
            land_peak=prof.land_peak,
            land_median_r=prof.land_median_r,
            score_mul=1.0,
            hard_reject=False,
            mixed_orient=mixed,
            pattern_id=pid,
            detail=None,
        )

    mul = float(gate.score_mul)
    if mixed:
        return MegcGateDecision(
            active=True,
            outcome="gate_reject",
            land_peak=prof.land_peak,
            land_median_r=prof.land_median_r,
            score_mul=mul,
            hard_reject=True,
            mixed_orient=True,
            pattern_id=pid,
            detail=f"mixed_orient_peak={prof.land_peak}",
        )

    if gate.mode == "hard_reject":
        return MegcGateDecision(
            active=True,
            outcome="gate_reject",
            land_peak=prof.land_peak,
            land_median_r=prof.land_median_r,
            score_mul=mul,
            hard_reject=True,
            mixed_orient=False,
            pattern_id=pid,
            detail=f"hard_reject_peak={prof.land_peak}",
        )

    return MegcGateDecision(
        active=True,
        outcome="gate_penalize",
        land_peak=prof.land_peak,
        land_median_r=prof.land_median_r,
        score_mul=mul,
        hard_reject=False,
        mixed_orient=False,
        pattern_id=pid,
        detail=f"soft_mul={mul:.3f};peak={prof.land_peak}",
    )


def resolve_megc_log_outcome(
    *,
    parent_enabled: bool,
    decision: MegcGateDecision,
    winner_feature_summary: Mapping[str, Any] | None,
    rejected: Sequence[Mapping[str, Any]] | None,
) -> str:
    """Window-level ``megcOutcome`` for MosaicWindowLog."""
    if not parent_enabled:
        return "skipped"
    feat = winner_feature_summary or {}
    if feat.get("megcGateFallback"):
        return "gate_fallback"
    if decision.active:
        return decision.outcome
    for row in rejected or ():
        if str(row.get("reason") or "") == MEGC_REJECT_REASON:
            return "gate_reject"
    return "skipped"
