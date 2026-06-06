"""Phase 6 observability and rollout configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class Phase6AcThresholds:
    """AC-P6 acceptance gates (Phase 6 §18)."""

    cluster_noise_ratio_drop_pct: float = 15.0
    event_boundary_f1_lift_pct: float = 10.0
    layout_repeat_streak_drop_pct: float = 25.0
    pipeline_time_regression_pct: float = 10.0
    peak_memory_regression_pct: float = 15.0
    cover_blind_review_winrate_pct: float = 60.0


@dataclass
class Phase6AlertThresholds:
    """Operational alert thresholds (PRD-PHASE6 §18.2)."""

    export_success_rate_min: float = 0.97
    pipeline_time_regression_alert_pct: float = 15.0
    cover_preference_winrate_min: float = 0.50


@dataclass
class Phase6RolloutConfig:
    """Gray rollout gate (PRD-PHASE6 §14). Buckets by tripId + cohortSalt."""

    stage: Literal["off", "G0", "G1", "G2", "G3"] = "off"
    traffic_percent: float = 0.0
    cohort_salt: str = "travelogue-p6"
    allowlist_trip_ids: tuple[str, ...] = ()
    blocklist_trip_ids: tuple[str, ...] = ()


@dataclass
class Phase6ObservabilityConfig:
    ac: Phase6AcThresholds = field(default_factory=Phase6AcThresholds)
    alerts: Phase6AlertThresholds = field(default_factory=Phase6AlertThresholds)
    rollout: Phase6RolloutConfig = field(default_factory=Phase6RolloutConfig)


def phase6_ac_from_dict(raw: dict[str, Any]) -> Phase6AcThresholds:
    defaults = Phase6AcThresholds()
    return Phase6AcThresholds(
        cluster_noise_ratio_drop_pct=float(
            raw.get("clusterNoiseRatioDropPct", raw.get("cluster_noise_ratio_drop_pct", defaults.cluster_noise_ratio_drop_pct))
        ),
        event_boundary_f1_lift_pct=float(
            raw.get("eventBoundaryF1LiftPct", raw.get("event_boundary_f1_lift_pct", defaults.event_boundary_f1_lift_pct))
        ),
        layout_repeat_streak_drop_pct=float(
            raw.get("layoutRepeatStreakDropPct", raw.get("layout_repeat_streak_drop_pct", defaults.layout_repeat_streak_drop_pct))
        ),
        pipeline_time_regression_pct=float(
            raw.get("pipelineTimeRegressionPct", raw.get("pipeline_time_regression_pct", defaults.pipeline_time_regression_pct))
        ),
        peak_memory_regression_pct=float(
            raw.get("peakMemoryRegressionPct", raw.get("peak_memory_regression_pct", defaults.peak_memory_regression_pct))
        ),
        cover_blind_review_winrate_pct=float(
            raw.get("coverBlindReviewWinratePct", raw.get("cover_blind_review_winrate_pct", defaults.cover_blind_review_winrate_pct))
        ),
    )


def phase6_alerts_from_dict(raw: dict[str, Any]) -> Phase6AlertThresholds:
    defaults = Phase6AlertThresholds()
    return Phase6AlertThresholds(
        export_success_rate_min=float(
            raw.get("exportSuccessRateMin", raw.get("export_success_rate_min", defaults.export_success_rate_min))
        ),
        pipeline_time_regression_alert_pct=float(
            raw.get(
                "pipelineTimeRegressionAlertPct",
                raw.get("pipeline_time_regression_alert_pct", defaults.pipeline_time_regression_alert_pct),
            )
        ),
        cover_preference_winrate_min=float(
            raw.get("coverPreferenceWinrateMin", raw.get("cover_preference_winrate_min", defaults.cover_preference_winrate_min))
        ),
    )


def phase6_from_dict(raw: dict[str, Any]) -> Phase6ObservabilityConfig:
    ac_raw = raw.get("ac") if isinstance(raw.get("ac"), dict) else {}
    alerts_raw = raw.get("alerts") if isinstance(raw.get("alerts"), dict) else {}
    rollout_raw = raw.get("rollout") if isinstance(raw.get("rollout"), dict) else {}
    stage_raw = str(rollout_raw.get("stage", "off")).strip().upper()
    if stage_raw == "OFF" or stage_raw not in ("G0", "G1", "G2", "G3"):
        stage_key: Literal["off", "G0", "G1", "G2", "G3"] = "off"
    else:
        stage_key = stage_raw  # type: ignore[assignment]
    allow_raw = rollout_raw.get("allowlistTripIds") or rollout_raw.get("allowlist_trip_ids") or []
    block_raw = rollout_raw.get("blocklistTripIds") or rollout_raw.get("blocklist_trip_ids") or []
    rollout = Phase6RolloutConfig(
        stage=stage_key,
        traffic_percent=float(
            rollout_raw.get("trafficPercent", rollout_raw.get("traffic_percent", 0.0))
        ),
        cohort_salt=str(rollout_raw.get("cohortSalt", rollout_raw.get("cohort_salt", "travelogue-p6"))),
        allowlist_trip_ids=tuple(str(x) for x in allow_raw if x) if isinstance(allow_raw, list) else (),
        blocklist_trip_ids=tuple(str(x) for x in block_raw if x) if isinstance(block_raw, list) else (),
    )
    return Phase6ObservabilityConfig(
        ac=phase6_ac_from_dict(ac_raw),
        alerts=phase6_alerts_from_dict(alerts_raw),
        rollout=rollout,
    )
