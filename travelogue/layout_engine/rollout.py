"""LSE dogfood rollout gate (W3a · AC-P17-01 · R-P17-20).

Global ``layout.strategy_engine.enabled`` stays ``false`` by default; allowlisted
or bucketed trips may still receive LSE via policy + runtime rollout merge.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from travelogue.config import AppConfig
from travelogue.layout_engine.rollout_bucket import rollout_bucket
from travelogue.layout_engine.policy import load_policy
from travelogue.layout_engine.runtime_store import load_lse_runtime


@dataclass(frozen=True)
class LseRolloutConfig:
    stage: str = "off"
    traffic_percent: float = 0.0
    cohort_salt: str = "travelogue-p17"
    allowlist_trip_ids: tuple[str, ...] = ()
    blocklist_trip_ids: tuple[str, ...] = ()


def _trip_ids(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, list):
        return ()
    return tuple(str(x).strip() for x in raw if str(x).strip())


def _rollout_from_mapping(raw: dict[str, Any] | None) -> LseRolloutConfig:
    if not isinstance(raw, dict):
        return LseRolloutConfig()
    allow = raw.get("allowlistTripIds") or raw.get("allowlist_trip_ids") or []
    block = raw.get("blocklistTripIds") or raw.get("blocklist_trip_ids") or []
    try:
        traffic = float(
            raw.get("traffic_percent", raw.get("trafficPercent", raw.get("default_traffic_percent", 0)))
        )
    except (TypeError, ValueError):
        traffic = 0.0
    return LseRolloutConfig(
        stage=str(raw.get("stage", "off")).strip().lower() or "off",
        traffic_percent=traffic,
        cohort_salt=str(raw.get("cohort_salt", raw.get("cohortSalt", "travelogue-p17"))),
        allowlist_trip_ids=_trip_ids(allow),
        blocklist_trip_ids=_trip_ids(block),
    )


def effective_rollout(cfg: AppConfig) -> LseRolloutConfig:
    """Policy rollout merged with L3 runtime overrides (runtime wins)."""
    se = cfg.layout.strategy_engine
    policy_raw = load_policy(se.policy_path).raw.get("rollout")
    policy = _rollout_from_mapping(policy_raw if isinstance(policy_raw, dict) else {})
    rt_raw = load_lse_runtime(se.runtime_store).get("rollout")
    if not isinstance(rt_raw, dict) or not rt_raw:
        return policy
    runtime = _rollout_from_mapping(rt_raw)
    return LseRolloutConfig(
        stage=runtime.stage if runtime.stage != "off" else policy.stage,
        traffic_percent=runtime.traffic_percent if runtime.traffic_percent > 0 else policy.traffic_percent,
        cohort_salt=runtime.cohort_salt or policy.cohort_salt,
        allowlist_trip_ids=runtime.allowlist_trip_ids or policy.allowlist_trip_ids,
        blocklist_trip_ids=runtime.blocklist_trip_ids or policy.blocklist_trip_ids,
    )


def lse_in_rollout_cohort(trip_id: str, cfg: AppConfig) -> bool:
    """True when trip should run LSE while global enabled=false."""
    if cfg.layout.strategy_engine.enabled:
        return True
    rollout = effective_rollout(cfg)
    tid = str(trip_id or "").strip()
    if not tid:
        return False
    if tid in rollout.blocklist_trip_ids:
        return False
    if tid in rollout.allowlist_trip_ids:
        return True
    if rollout.stage in ("off", "") or rollout.traffic_percent <= 0:
        return False
    if rollout.traffic_percent >= 100:
        return True
    bucket = rollout_bucket(
        tid,
        cohort_salt=rollout.cohort_salt,
        traffic_percent=rollout.traffic_percent,
    )
    return bucket < int(round(rollout.traffic_percent))


def resolve_lse_config_for_trip(cfg: AppConfig, trip_id: str) -> AppConfig:
    """Enable strategy_engine for rollout cohort trips without flipping global default."""
    if cfg.layout.strategy_engine.enabled:
        return cfg
    if not lse_in_rollout_cohort(trip_id, cfg):
        return cfg
    se = replace(cfg.layout.strategy_engine, enabled=True)
    return replace(cfg, layout=replace(cfg.layout, strategy_engine=se))


def lse_rollout_snapshot(cfg: AppConfig) -> dict[str, Any]:
    r = effective_rollout(cfg)
    return {
        "stage": r.stage,
        "trafficPercent": r.traffic_percent,
        "cohortSalt": r.cohort_salt,
        "allowlistTripIds": list(r.allowlist_trip_ids),
        "blocklistTripIds": list(r.blocklist_trip_ids),
        "globalEnabled": cfg.layout.strategy_engine.enabled,
    }
