"""Unified rollout bucket util (P19 R-P19-105)."""

from __future__ import annotations

import hashlib
from typing import Literal

RolloutOffPolicy = Literal["deny_all", "allow_all"]


def rollout_bucket(trip_id: str, *, cohort_salt: str, traffic_percent: float) -> int:
    """Deterministic bucket 0..99 for ``trip_id`` (stable across runs)."""
    if traffic_percent <= 0:
        return 100
    if traffic_percent >= 100:
        return 0
    digest = hashlib.sha256(f"{cohort_salt}:{trip_id}".encode()).hexdigest()
    return int(digest[:8], 16) % 100


def in_rollout_cohort(
    trip_id: str,
    *,
    cohort_salt: str,
    traffic_percent: float,
    stage: str,
    allowlist: tuple[str, ...] | list[str] = (),
    blocklist: tuple[str, ...] | list[str] = (),
    global_enabled: bool = False,
    off_policy: RolloutOffPolicy = "deny_all",
) -> bool:
    """Shared LTE / LSE / Phase6 cohort gate."""
    if global_enabled:
        return True
    tid = str(trip_id or "").strip()
    if not tid:
        return False
    block = frozenset(str(x).strip() for x in blocklist if str(x).strip())
    allow = frozenset(str(x).strip() for x in allowlist if str(x).strip())
    if tid in block:
        return False
    if tid in allow:
        return True
    stage_norm = str(stage or "off").strip().lower()
    if stage_norm in ("off", ""):
        return off_policy == "allow_all"
    if traffic_percent <= 0:
        return off_policy == "allow_all"
    if traffic_percent >= 100:
        return True
    bucket = rollout_bucket(
        tid,
        cohort_salt=cohort_salt,
        traffic_percent=traffic_percent,
    )
    return bucket < int(round(traffic_percent))
