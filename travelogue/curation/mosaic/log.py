"""Mosaic decision logging (M7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.curation.mosaic.runtime import MOSAIC_ROUTER_VERSION


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
        return out


def format_log_entry(raw: dict[str, Any], log_level: str = "window") -> dict[str, Any]:
    """Filter persisted log fields by level (D-MCS-10 · summary/window/debug)."""
    if log_level == "debug":
        return dict(raw)
    summary_keys = (
        "segmentId",
        "windowSize",
        "windowStart",
        "winnerPatternId",
        "winnerScore",
        "fallbackUsed",
        "fallbackReason",
        "selfHealApplied",
        "plannerPath",
        "scorerVersion",
        "routerVersion",
    )
    if log_level == "summary":
        return {k: raw[k] for k in summary_keys if k in raw}
    # window: drop top3 score arrays; keep compact geometry rejections for guard verification
    out = dict(raw)
    out.pop("top3Scores", None)
    geom_rejected = [
        {"templateId": r["templateId"], "reason": r["reason"]}
        for r in raw.get("rejectedTemplates") or []
        if r.get("reason") == "geometry_invalid"
    ]
    if geom_rejected:
        out["geometryRejectedTemplates"] = geom_rejected
    out.pop("rejectedTemplates", None)
    return out
