"""Portrait quality gate configuration (PRD-PORTRAIT-CULL §7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PortraitSubjectClarityWeights:
    face_sharp: float = 0.40
    eyes: float = 0.30
    frontal: float = 0.15
    base: float = 0.15


@dataclass
class PortraitEyesClosedConfig:
    mode: str = "off"
    sensitivity: str = "weak"
    thresholds: dict[str, float] = field(
        default_factory=lambda: {"weak": 0.35, "standard": 0.55, "strong": 0.70}
    )
    temperature: float = 0.08
    penalty_max: float = 0.25


@dataclass
class PortraitConfig:
    enabled: bool = True
    gate_changes_on_signal: bool = True
    min_confidence: float = 0.35
    bbox_pad_ratio: float = 0.20
    analyze_max_edge: int = 1280
    backend: str = "auto"  # auto | mediapipe | opencv | off
    debug_per_face: bool = False
    ingest_tiebreak_eyes_weight: float = 0.15
    multi_face_eyes_blend_primary: float = 0.7
    subject_clarity_weights: PortraitSubjectClarityWeights = field(
        default_factory=PortraitSubjectClarityWeights
    )
    subject_clarity_penalty_cap: float = 0.20
    eyes_closed: PortraitEyesClosedConfig = field(default_factory=PortraitEyesClosedConfig)

    def eyes_threshold(self) -> float:
        key = str(self.eyes_closed.sensitivity or "weak").lower()
        return float(self.eyes_closed.thresholds.get(key, 0.35))


def portrait_from_dict(raw: dict[str, Any] | None) -> PortraitConfig:
    if not isinstance(raw, dict):
        return PortraitConfig()
    sc_raw = raw.get("subject_clarity_weights") or raw.get("subjectClarityWeights") or {}
    ec_raw = raw.get("eyes_closed") or raw.get("eyesClosed") or {}
    thresholds_raw = ec_raw.get("thresholds") if isinstance(ec_raw, dict) else {}
    thresholds = {"weak": 0.35, "standard": 0.55, "strong": 0.70}
    if isinstance(thresholds_raw, dict):
        for k, v in thresholds_raw.items():
            try:
                thresholds[str(k)] = float(v)
            except (TypeError, ValueError):
                pass
    sc_weights = PortraitSubjectClarityWeights(
        face_sharp=float(sc_raw.get("face_sharp", sc_raw.get("faceSharp", 0.40))),
        eyes=float(sc_raw.get("eyes", 0.30)),
        frontal=float(sc_raw.get("frontal", 0.15)),
        base=float(sc_raw.get("base", 0.15)),
    )
    eyes_closed = PortraitEyesClosedConfig(
        mode=str(ec_raw.get("mode", "off")),
        sensitivity=str(ec_raw.get("sensitivity", "weak")),
        thresholds=thresholds,
        temperature=float(ec_raw.get("temperature", 0.08)),
        penalty_max=float(ec_raw.get("penalty_max", ec_raw.get("penaltyMax", 0.25))),
    )
    mf_raw = raw.get("multi_face") or raw.get("multiFace") or {}
    return PortraitConfig(
        enabled=bool(raw.get("enabled", True)),
        gate_changes_on_signal=bool(
            raw.get("gate_changes_on_signal", raw.get("gateChangesOnSignal", True))
        ),
        min_confidence=float(raw.get("min_confidence", raw.get("minConfidence", 0.35))),
        bbox_pad_ratio=float(raw.get("bbox_pad_ratio", raw.get("bboxPadRatio", 0.20))),
        analyze_max_edge=int(raw.get("analyze_max_edge", raw.get("analyzeMaxEdge", 1280))),
        backend=str(raw.get("backend", raw.get("portrait_backend", "auto"))),
        debug_per_face=bool(raw.get("debug_per_face", raw.get("debugPortraitPerFace", False))),
        ingest_tiebreak_eyes_weight=float(
            raw.get("ingest_tiebreak_eyes_weight", raw.get("ingestTiebreakEyesWeight", 0.15))
        ),
        multi_face_eyes_blend_primary=float(
            mf_raw.get("eyes_blend_primary", mf_raw.get("eyesBlendPrimary", 0.7))
            if isinstance(mf_raw, dict)
            else 0.7
        ),
        subject_clarity_weights=sc_weights,
        subject_clarity_penalty_cap=float(
            raw.get("subject_clarity_penalty_cap", raw.get("subjectClarityPenaltyCap", 0.20))
        ),
        eyes_closed=eyes_closed,
    )
